import { Request, Response } from 'express';
import * as fs from 'fs';
import * as path from 'path';
import { spawn } from 'child_process';
import { io } from '../index';
import { AIProviderFactory } from '../services/ai/factory';
import { Message } from '../services/ai/types';

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
   - 使用完整的绝对路径
   - 每个命令必须是完整的、可独立执行的
   - 每次只返回一个命令对
   - 不要返回任何自然语言解释

3. 检查命令必须返回布尔值：
   - Test-Path 检查文件是否存在
   - (Get-Content).Trim() -eq "期望内容" 检查文件内容
   - 使用 -and 组合多个检查条件

4. 根据检查结果：
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

// 处理聊天请求
export const handleChat = async (req: Request, res: Response) => {
  try {
    if (!currentConfig) {
      return res.status(400).json({
        success: false,
        message: '请先配置API信息'
      });
    }

    const { message } = req.body;
    
    if (!message) {
      return res.status(400).json({
        success: false,
        message: '消息内容不能为空'
      });
    }

    console.log('Sending message to AI:', message);

    // 使用工厂获取对应的AI提供者
    const provider = AIProviderFactory.getProvider(currentConfig);

    let finalResponse = '';
    let isTaskComplete = false;
    let messageHistory: Message[] = [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: `用户请求：${message}` }
    ];

    // 重置重试计数器
    const taskId = Date.now().toString();
    retryCounters[taskId] = 0;

    // 使用 Response.write 来实现流式响应
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    });

    while (!isTaskComplete && retryCounters[taskId] < 3) {
      const aiResponse = await provider.sendMessage(messageHistory, currentConfig);
      
      if (!aiResponse.success) {
        throw new Error(aiResponse.error || 'AI服务响应失败');
      }

      const responseContent = aiResponse.content;
      console.log('AI Response:', responseContent);

      // 立即发送 AI 响应
      res.write(`data: ${JSON.stringify({ type: 'ai-response', content: responseContent })}\n\n`);

      // 检查是否任务完成
      if (responseContent.includes('[COMPLETE]')) {
        isTaskComplete = true;
        break;
      }

      // 提取命令对
      const commandMatch = responseContent.match(/\[COMMAND\]([\s\S]*?)\[\/COMMAND\]/);
      const checkMatch = responseContent.match(/\[CHECK\]([\s\S]*?)\[\/CHECK\]/);
      
      if (commandMatch && checkMatch) {
        const command = commandMatch[1].trim();
        const checkCommand = checkMatch[1].trim();

        try {
          // 执行主命令
          const cmdOutput = await executeCommand(command);
          
          // 执行检查命令
          const checkOutput = await executeCommand(checkCommand);

          // 解析检查结果，改进判断逻辑
          const checkResult = checkOutput.toLowerCase().includes('true') || 
                            (checkOutput.includes('1') && !checkOutput.includes('0')) ||
                            checkOutput.includes('文件内容正确');
          
          // 组合执行结果
          const executionResult = `执行结果：\n命令：${command}\n输出：${cmdOutput}\n\n检查结果：\n命令：${checkCommand}\n输出：${checkOutput}\n结果：${checkResult ? '成功' : '失败'}`;
          
          // 立即发送执行结果
          res.write(`data: ${JSON.stringify({ type: 'execution-result', content: executionResult })}\n\n`);

          // 将结果添加到消息历史
          messageHistory.push(
            { role: 'assistant', content: responseContent },
            { role: 'user', content: executionResult }
          );

          // 如果检查成功，继续下一步
          if (checkResult) {
            retryCounters[taskId] = 0;
          } else {
            retryCounters[taskId]++;
          }

        } catch (error: any) {
          const errorMessage = `执行错误：${error.message}`;
          res.write(`data: ${JSON.stringify({ type: 'error', content: errorMessage })}\n\n`);
          messageHistory.push(
            { role: 'assistant', content: responseContent },
            { role: 'user', content: errorMessage }
          );
          retryCounters[taskId]++;
        }
      }
    }

    // 结束响应
    res.write(`data: ${JSON.stringify({ type: 'complete' })}\n\n`);
    res.end();

  } catch (error: any) {
    console.error('Chat error:', error);
    res.write(`data: ${JSON.stringify({ type: 'error', content: error.message })}\n\n`);
    res.end();
  }
};

// 修改执行命令函数
const executeCommand = async (command: string): Promise<string> => {
  return new Promise((resolve, reject) => {
    console.log('Executing command:', command);
    
    // 发送命令到终端
    io.emit('command-output', `\n> ${command}\n`);

    const ps = spawn('powershell.exe', [
      '-NoProfile',
      '-NonInteractive',
      '-Command',
      command
    ]);

    let output = '';

    ps.stdout.on('data', (data) => {
      const text = data.toString('utf8');
      output += text;
      io.emit('command-output', text);
    });

    ps.stderr.on('data', (data) => {
      const text = data.toString('utf8');
      output += text;
      io.emit('command-output', `Error: ${text}`);
    });

    ps.on('close', (code) => {
      const status = code === 0 ? 'Success' : 'Failed';
      io.emit('command-output', `\n=== Command ${status} (Exit Code: ${code}) ===\n`);
      
      // 添加命令执行状态到输出
      const result = `${output}\n命令执行状态: ${status} (退出代码: ${code})`;
      resolve(result);
    });

    ps.on('error', (err) => {
      io.emit('command-output', `\nError: ${err.message}\n`);
      resolve(`Error: ${err.message}\n命令执行状态: Failed`);
    });
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