import { Request, Response } from 'express';
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';
import { io } from '../index';
import { AIProviderFactory } from '../services/ai/factory';
import { Message } from '../services/ai/types';
import * as iconv from 'iconv-lite';

// 存储当前配置
let currentConfig: any = null;

// 修改系统提示词
const SYSTEM_PROMPT = `你是一个专门执行PowerShell命令的AI助手。请严格按照以下规则执行任务：

1. 命令格式必须严格遵循：
   [COMMAND]
   <PowerShell命令>
   [/COMMAND]
   [CHECK]
   <检查命令>
   [/CHECK]

2. PowerShell命令规则：
   - 使用 "C:\\Path\\To\\Create\\Folder" 作为基础路径（系统会自动替换为实际路径）
   - 每个命令必须是完整的、可独立执行的
   - 每次只返回一个命令对
   - 不要返回任何自然语言解释

3. 检查命令必须返回布尔值：
   - Test-Path 检查文件是否存在
   - (Get-Content).Trim() -eq "期望内容" 检查文件内容
   - 使用 -and 组合多个检查条件

4. 基于检查结果：
   - 如果返回 True：继续下一步或完成
   - 如果返回 False：返回新的修正命令
   - 最多重试 3 次，超过则报告失败

5. 完成时返回：[COMPLETE]任务已完成[/COMPLETE]`;



// 添加重试计数器接口
interface RetryCounter {
  [key: string]: number;
}

// 初始化重试计数器
const retryCounters: RetryCounter = {};

// 添加命令执行上下文
interface CommandContext {
  variables: { [key: string]: string };
  currentDir: string;
}

// 添加命令格式检查函数
function isPowerShellCommand(command: string): boolean {
  // PowerShell 命令的特征
  const powerShellPatterns = [
    'New-Item',
    'Set-Content',
    'Get-Content',
    'Test-Path',
    'Set-Location',
    'Get-ChildItem',
    'Remove-Item',
    'Move-Item',
    'Copy-Item',
    'Write-Output',
    'Out-File',
    'Out-Null'
  ];

  return powerShellPatterns.some(pattern => command.includes(pattern));
}

// 处理聊天请求
export const handleChat = async (req: Request, res: Response) => {
  try {
    // 验证请求体
    if (!req.body || typeof req.body.message !== 'string') {
      return res.status(400).json({
        success: false,
        message: '无效的请求格式'
      });
    }

    const { message } = req.body;

    // 验证配置
    if (!currentConfig || !currentConfig.apiUrl || !currentConfig.model || !currentConfig.savePath) {
      return res.status(400).json({
        success: false,
        message: '请先完成 API 配置'
      });
    }

    const provider = AIProviderFactory.getProvider(currentConfig);
    console.log('Using provider:', provider.constructor.name);

    // 置 SSE 头
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    });

    const messages: Message[] = [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: message }
    ].map(msg => ({
      role: msg.role as 'system' | 'user' | 'assistant',
      content: msg.content
    }));
    console.log('Sending messages to AI:', messages);

    const aiResponse = await provider.sendMessage(messages, currentConfig);
    console.log('Received AI response:', {
      success: aiResponse.success,
      hasContent: !!aiResponse.content,
      hasStream: !!aiResponse.stream,
      error: aiResponse.error
    });

    let accumulatedContent = '';

    if (aiResponse.stream) {
      const reader = aiResponse.stream.getReader();
      const decoder = new TextDecoder();
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          console.log('Stream completed');
          break;
        }
        
        const chunk = decoder.decode(value);
        console.log('Received chunk:', chunk);
        
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.trim() || line === 'data: [DONE]') continue;
          
          try {
            // 移除 'data: ' 前缀
            const jsonStr = line.replace(/^data: /, '');
            console.log('Parsing JSON:', jsonStr);
            
            const data = JSON.parse(jsonStr);
            
            // 检查是否有 delta 内容
            if (data.choices?.[0]?.delta?.content) {
              const content = data.choices[0].delta.content;
              accumulatedContent += content;
              
              // 发送到客户端
              res.write(`data: ${JSON.stringify({ 
                type: 'ai-response', 
                content: content 
              })}\n\n`);
            }
          } catch (e) {
            console.error('Error parsing stream chunk:', e, 'Line:', line);
          }
        }
      }

      console.log('Accumulated content:', accumulatedContent);

      // 处理命令执行
      if (accumulatedContent.includes('[COMMAND]')) {
        await handleCommandExecution(accumulatedContent, res);
      }
    } else if (aiResponse.content) {
      res.write(`data: ${JSON.stringify({ type: 'ai-response', content: aiResponse.content })}\n\n`);
      await handleCommandExecution(aiResponse.content, res);
    }

  } catch (error: unknown) {
    console.error('Chat error:', error);
    const errorMessage = error instanceof Error ? error.message : '未知错误';
    
    // 如果响应头已经发送，使用 SSE 格式发送错误
    if (res.headersSent) {
      res.write(`data: ${JSON.stringify({ type: 'error', content: errorMessage })}\n\n`);
      res.end();
    } else {
      // 否则发送普通的 JSON 响应
      res.status(500).json({
        success: false,
        message: errorMessage
      });
    }
  }
};

// 修改 handleCommandExecution 函数
async function handleCommandExecution(content: string, res: Response) {
  console.log('Handling command execution, raw content:', content);

  // 清理内容：规范化换行和空格
  content = content.replace(/\r\n/g, '\n')
                  .replace(/\[\/COMMAND\]\s*\[COMMAND\]/g, '[/COMMAND]\n[COMMAND]') // 分隔多个命令组
                  .trim();
  
  // 规范化命令格式
  content = content
    .replace(/\[END\]/g, '[/CHECK]')  // 替换 [END] 为 [/CHECK]
    .replace(/\[COMMAND\]([\s\S]*?)\[CHECK\]/g, (match, p1) => {
      // 为没有闭合的 [COMMAND] 添加闭合标签
      return `[COMMAND]${p1}[/COMMAND][CHECK]`;
    });

  console.log('Normalized content:', content);

  // 使用非贪婪模式匹配命令组
  const commandPattern = /\[COMMAND\]([\s\S]*?)\[\/COMMAND\]\s*\[CHECK\]([\s\S]*?)\[\/CHECK\]/gs;
  const matches = Array.from(content.matchAll(commandPattern));

  if (!matches || matches.length === 0) {
    console.log('No valid command groups found');
    res.write(`data: ${JSON.stringify({ 
      type: 'error', 
      content: '无法识别命令格式' 
    })}\n\n`);
    return;
  }

  // 处理第一组命令
  const [_, commandBlock, checkBlock] = matches[0];

  if (!commandBlock || !checkBlock) {
    console.log('Invalid command or check block:', { commandBlock, checkBlock });
    return;
  }

  // 清理命令文本，正确处理多行命令
  const commands = commandBlock.split('\n')
    .map(cmd => cmd.trim())
    .filter(cmd => cmd && !cmd.includes('[/COMMAND]') && !cmd.includes('[RETRY]')); // 过滤掉标签和空行

  const cleanCheckCommand = checkBlock.trim();

  console.log('Processing command group:', {
    commands,
    checkCommand: cleanCheckCommand
  });

  try {
    // 替换所有命令中的路径
    const modifiedCommands = commands.map(cmd => {
      let modified = cmd
        .replace(/C:\\Path\\To\\Create\\Folder/g, currentConfig.savePath)
        .replace(/C:\\Users\\{YourUsername}\\Documents/g, currentConfig.savePath)
        .replace(/cd\s+([^;]+)/g, `cd "${currentConfig.savePath}"`); // 修正 cd 命令

      // 处理文件路径中的引号
      if (modified.includes('echo') && modified.includes('>')) {
        const parts = modified.split('>').map(p => p.trim());
        const content = parts[0].replace(/^echo\s+/, '').trim();
        const path = parts[1].trim().replace(/^"(.*)"$/, '$1');
        modified = `Set-Content -Path "${path}" -Value ${content}`;
      }

      return modified;
    });

    const modifiedCheckCommand = cleanCheckCommand
      .replace(/C:\\Path\\To\\Create\\Folder/g, currentConfig.savePath)
      .replace(/C:\\Users\\{YourUsername}\\Documents/g, currentConfig.savePath)
      .replace(/Join-Path\s+([^"]+)\s+"/, `Join-Path "${currentConfig.savePath}" "`); // 修正 Join-Path

    console.log('Executing commands with modified paths:', {
      original: commands,
      modified: modifiedCommands,
      savePath: currentConfig.savePath
    });

    // 按顺序执行所有命令
    let cmdOutput = '';
    for (const cmd of modifiedCommands) {
      const output = await executeCommand(cmd);
      cmdOutput += output + '\n';
    }
    
    // 执行检查命令
    const checkOutput = await executeCommand(modifiedCheckCommand);

    // 解析检查结果
    const checkResult = checkOutput.toLowerCase().includes('true') || 
                      (checkOutput.includes('1') && !checkOutput.includes('0')) ||
                      checkOutput.includes('文件内容正确');
    
    // 构建执行结果
    const executionResult = `执行结果：\n命令：${modifiedCommands.join('\n')}\n输出：${cmdOutput}\n\n检查结果：\n命令：${modifiedCheckCommand}\n输出：${checkOutput}\n结果：${checkResult ? '成功' : '失败'}`;
    
    // 发送执行结果到客户端
    res.write(`data: ${JSON.stringify({ 
      type: 'execution-result', 
      content: executionResult
    })}\n\n`);

    // 将执行结果发送给 AI 进行判断
    const provider = AIProviderFactory.getProvider(currentConfig);
    const aiResponse = await provider.sendMessage([
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: content },
      { role: 'assistant', content: executionResult },
      { 
        role: 'user', 
        content: checkResult 
          ? '检查通过。如果还有未完成的任务，请继续执行；如果所有任务都已完成，请返回 [COMPLETE]任务已完成[/COMPLETE]' 
          : '检查失败，请提供修正命令' 
      }
    ], currentConfig);

    // 处理 AI 的响应
    if (aiResponse.stream) {
      const reader = aiResponse.stream.getReader();
      const decoder = new TextDecoder();
      let aiContent = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.trim() || line === 'data: [DONE]') continue;
          
          try {
            const jsonStr = line.replace(/^data: /, '');
            const data = JSON.parse(jsonStr);
            
            if (data.choices?.[0]?.delta?.content) {
              aiContent += data.choices[0].delta.content;
              res.write(`data: ${JSON.stringify({ 
                type: 'ai-response', 
                content: data.choices[0].delta.content 
              })}\n\n`);
            }
          } catch (e) {
            console.error('Error parsing AI response:', e);
          }
        }
      }

      // 如果 AI 返回了新的命令，递归处理
      if (aiContent.includes('[COMMAND]')) {
        await handleCommandExecution(aiContent, res);
      }
    }
  } catch (error: any) {
    console.error('Command execution error:', error);
    res.write(`data: ${JSON.stringify({ 
      type: 'error', 
      content: `执行错误：${error.message}` 
    })}\n\n`);
  }
}

// 修改 executeCommand 函数
const executeCommand = async (command: string): Promise<string> => {
  return new Promise((resolve, reject) => {
    try {
      console.log('Executing command:', command);
      
      // 检查是否是多行命令
      const commands = command.split('\n').filter(cmd => cmd.trim());
      
      if (commands.length > 1) {
        // 如果是多行命令，使用分号连接
        command = commands.join(';');
      }

      // 处理 -and 条件语句
      if (command.includes('-and')) {
        command = `$result = ${command}; if($result) { Write-Output "True" } else { Write-Output "False" }`;
      }
      
      // 发送命令到终端
      io.emit('command-output', `\n> ${command}\n`);

      const ps = spawn('powershell.exe', [
        '-NoProfile',
        '-NonInteractive',
        '-Command',
        `
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
        [Console]::InputEncoding = [System.Text.Encoding]::UTF8;
        $OutputEncoding = [System.Text.Encoding]::UTF8;
        ${command}
        `
      ], {
        env: {
          ...process.env,
          PYTHONIOENCODING: 'utf-8',
          LANG: 'zh_CN.UTF-8'
        }
      });

      let output = '';

      ps.stdout.on('data', (data) => {
        try {
          const text = iconv.decode(data, 'utf8');
          output += text;
          io.emit('command-output', text);
        } catch (error) {
          console.error('Error decoding stdout:', error);
        }
      });

      ps.stderr.on('data', (data) => {
        try {
          const text = iconv.decode(data, 'utf8');
          output += text;
          io.emit('command-output', `Error: ${text}`);
        } catch (error) {
          console.error('Error decoding stderr:', error);
        }
      });

      ps.on('close', (code) => {
        try {
          const status = code === 0 ? 'Success' : 'Failed';
          io.emit('command-output', `\n=== Command ${status} (Exit Code: ${code}) ===\n`);
          
          const result = `${output}\n命令执行状态: ${status} (退出代码: ${code})`;
          resolve(result);
        } catch (error) {
          console.error('Error in close handler:', error);
          resolve(`Error in close handler\n命令执行状态: Failed`);
        }
      });

      ps.on('error', (err) => {
        try {
          const errorMessage = err instanceof Error ? err.message : String(err);
          const decodedError = iconv.decode(Buffer.from(errorMessage), 'utf8');
          io.emit('command-output', `\nError: ${decodedError}\n`);
          resolve(`Error: ${decodedError}\n命令执行状态: Failed`);
        } catch (error) {
          console.error('Error in error handler:', error);
          resolve('Error in error handler\n命令执行状态: Failed');
        }
      });
    } catch (error) {
      console.error('Error in executeCommand:', error);
      resolve(`Error in executeCommand: ${error instanceof Error ? error.message : 'Unknown error'}\n命令执行状态: Failed`);
    }
  });
};

// 处理配置保存
export const saveConfig = async (req: Request, res: Response) => {
  try {
    const config = req.body;
    
    // 验证必要的配置字段
    if (!config.apiKey || !config.apiUrl || !config.model || !config.savePath) {
      return res.status(400).json({ 
        success: false, 
        message: '所有配置字段都是必填的' 
      });
    }

    // 验证 URL 格式
    try {
      new URL(config.apiUrl);
    } catch (e) {
      return res.status(400).json({
        success: false,
        message: 'API URL 格式不正确'
      });
    }

    // 验证保存路径
    if (!config.savePath.match(/^[a-zA-Z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*$/)) {
      return res.status(400).json({
        success: false,
        message: '保存路径格式不正确'
      });
    }

    // 保存配置到内存
    currentConfig = config;
    
    // 保存配置到文件
    const configPath = path.join(__dirname, '../../config.json');
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

    console.log('Config saved:', config); // 调试日志

    res.json({ 
      success: true, 
      message: '配置保存成功' 
    });
  } catch (error) {
    console.error('保存配置错误:', error);
    res.status(500).json({ 
      success: false, 
      message: error instanceof Error ? error.message : '保存配置失败' 
    });
  }
};

// 获取API状态
export const getApiStatus = async (req: Request, res: Response) => {
  try {
    if (!currentConfig) {
      return res.status(503).json({ 
        success: false, 
        message: 'API未配置' 
      });
    }

    // 尝试调用API检查连接状态
    const response = await fetch(currentConfig.apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${currentConfig.apiKey}`
      },
      body: JSON.stringify({
        model: currentConfig.model,
        messages: [{ role: 'system', content: 'test' }]
      })
    });

    if (response.ok) {
      res.json({ success: true, message: 'API连接正常' });
    } else {
      throw new Error('API连接失败');
    }
  } catch (error) {
    res.status(503).json({ 
      success: false, 
      message: 'API连接失败' 
    });
  }
};

// 获取配置
export const getConfig = async (req: Request, res: Response) => {
  try {
    // 如果内存中没有配置，尝试从文件读取
    if (!currentConfig) {
      const configPath = path.join(__dirname, '../../config.json');
      if (fs.existsSync(configPath)) {
        const configData = fs.readFileSync(configPath, 'utf8');
        currentConfig = JSON.parse(configData);
      }
    }
    
    res.json({ 
      success: true, 
      config: currentConfig 
    });
  } catch (error) {
    console.error('获取配置错误:', error);
    res.status(500).json({ 
      success: false, 
      message: '获取配置失败' 
    });
  }
};