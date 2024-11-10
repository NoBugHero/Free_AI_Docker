import { Request, Response } from 'express';
import fetch from 'node-fetch';
import https from 'https';
import { MessageParser } from '../utils/MessageParser';
import { CommandExecutor } from '../utils/CommandExecutor';

export class ChatController {
  static async handleChat(req: Request, res: Response) {
    try {
      const { message, config, isRetry } = req.body;
      
      global.io?.emit('terminal-log', {
        type: 'info',
        message: isRetry ? '重试请求' : '发送请求到AI服务器',
        details: {
          model: config.model,
          message: message,
          isRetry
        }
      });

      if (!config.apiKey) {
        throw new Error('API Key is required');
      }

      // 修改通义千问API请求格式
      const requestData = {
        model: config.model,
        input: {
          messages: [{
            role: "user",
            content: message
          }]
        }
      };

      console.log('Request data:', JSON.stringify(requestData, null, 2));

      // 使用 node-fetch 发送请求
      const response = await fetch(config.apiUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${config.apiKey}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-DashScope-Debug': '1'  // 添加调试头
        },
        body: JSON.stringify(requestData),
        // 忽略 SSL 证书验证
        agent: new https.Agent({
          rejectUnauthorized: false
        })
      });

      const responseText = await response.text();
      console.log('Raw API Response:', responseText);

      if (!response.ok) {
        throw new Error(`API responded with status ${response.status}: ${responseText}`);
      }

      let responseData;
      try {
        responseData = JSON.parse(responseText);
      } catch (e) {
        console.error('Failed to parse response:', e);
        throw new Error('Invalid JSON response from API');
      }

      console.log('Parsed API Response:', responseData);

      global.io?.emit('terminal-log', {
        type: 'success',
        message: 'API响应',
        details: responseData
      });

      // 从通义千问响应中获取文本内容
      const aiMessage = responseData.output?.text || 
                       responseData.output?.message?.content ||
                       responseData.choices?.[0]?.message?.content ||
                       responseData.response;
      
      if (!aiMessage) {
        console.error('Unexpected API response format:', responseData);
        throw new Error('Invalid API response format: ' + JSON.stringify(responseData));
      }

      // 解析AI返回的消息
      const blocks = MessageParser.parse(aiMessage);
      const results = [];
      
      // 处理每个解析出的块
      for (const block of blocks) {
        switch (block.type) {
          case 'text':
            results.push({
              type: 'text',
              content: block.content
            });
            break;
            
          case 'command':
            global.io?.emit('terminal-log', {
              type: 'info',
              message: isRetry ? '执行重试命令' : '执行命令',
              details: {
                content: block.content,
                language: block.language
              }
            });

            const cmdResult = await CommandExecutor.execute(
              block.content,
              config.savePath,
              block.language
            );

            if (!cmdResult.success) {
              global.io?.emit('terminal-log', {
                type: 'error',
                message: '命令执行失败',
                details: cmdResult.error
              });
            }

            results.push({
              type: 'command',
              content: block.content,
              language: block.language,
              result: cmdResult
            });
            break;
            
          case 'code':
            if (block.path) {
              global.io?.emit('terminal-log', {
                type: 'info',
                message: '写入文件',
                details: { path: block.path }
              });

              const fileResult = await CommandExecutor.writeFile(
                block.path,
                block.content,
                config.savePath
              );

              results.push({
                type: 'code',
                path: block.path,
                content: block.content,
                language: block.language,
                result: fileResult
              });
            } else {
              results.push({
                type: 'code',
                content: block.content,
                language: block.language
              });
            }
            break;
        }
      }

      res.json({
        message: aiMessage,
        blocks: results
      });
      
    } catch (error: any) {
      console.error('Chat error:', {
        message: error.message,
        response: error.response,
        stack: error.stack,
        cause: error.cause,
        name: error.name
      });
      
      global.io?.emit('terminal-log', {
        type: 'error',
        message: '请求错误',
        details: {
          message: error.message,
          response: error.response
        }
      });
      
      res.status(500).json({ 
        error: '处理请求时发生错误',
        details: error.message
      });
    }
  }
} 