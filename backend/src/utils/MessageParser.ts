interface ParsedBlock {
  type: 'text' | 'code' | 'command';
  content: string;
  language?: string;
  path?: string;
}

export class MessageParser {
  static parse(message: string): ParsedBlock[] {
    const blocks: ParsedBlock[] = [];
    const lines = message.split('\n');
    let currentBlock: ParsedBlock | null = null;
    let codeBlockRegex = /^```(\w+)(?::(.+))?$/;  // 匹配代码块开始

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // 跳过空行
      if (!line && !currentBlock) continue;
      
      // 检查代码块开始和结束
      if (line.startsWith('```')) {
        if (currentBlock) {
          // 结束当前代码块
          blocks.push(currentBlock);
          currentBlock = null;
        } else {
          // 开始新代码块
          const match = line.match(codeBlockRegex);
          if (match) {
            const [_, language, path] = match;
            // 根据语言类型决定是代码块还是命令
            if (language === 'python' || 
                language === 'bash' || 
                language === 'cmd' || 
                language === 'shell' ||
                language === 'batch') {  // 添加 batch 类型
              // 提取命令中的文件路径
              currentBlock = {
                type: 'command',
                content: '',
                language: language
              };
            } else if (language === 'html') {
              currentBlock = {
                type: 'code',
                content: '',
                language: language,
                path: path ? path.trim() : '我爱陈妙云.html'
              };
            } else {
              currentBlock = {
                type: 'code',
                content: '',
                language: language || undefined,
                path: path ? path.trim() : undefined
              };
            }
          }
        }
        continue;
      }

      // 处理块内容或普通文本
      if (currentBlock) {
        currentBlock.content += line + '\n';
      } else if (line) {
        // 只有非空行才添加到文本块
        if (blocks.length === 0 || blocks[blocks.length - 1].type !== 'text') {
          blocks.push({
            type: 'text',
            content: line + '\n'
          });
        } else {
          blocks[blocks.length - 1].content += line + '\n';
        }
      }
    }

    // 添加最后一个块
    if (currentBlock) {
      blocks.push(currentBlock);
    }

    // 清理每个块的内容并处理路径
    return blocks.map(block => {
      let cleanedBlock = { ...block };
      
      if (block.type === 'command') {
        // 清理命令内容
        cleanedBlock.content = block.content
          .replace(/@echo off\n/, '')  // 移除 batch 文件头
          .replace(/setlocal\n/, '')   // 移除 setlocal
          .replace(/REM.*\n/g, '')     // 移除注释
          .replace(/pause\n/g, '')     // 移除 pause
          .replace(/echo 文件已成功创建。\n/g, '')  // 移除提示信息
          .trim();

        // 从命令中提取路径
        if (block.language === 'python') {
          const pathMatch = block.content.match(/path\s*=\s*["'](.+?)["']/);
          const fileMatch = block.content.match(/filename\s*=\s*["'](.+?)["']/);
          if (pathMatch && fileMatch) {
            cleanedBlock.path = `${pathMatch[1]}\\${fileMatch[1]}`;
          }
        } else if (['bash', 'cmd', 'shell', 'batch'].includes(block.language || '')) {
          // 提取文件路径
          const filePathMatch = block.content.match(/set\s+"filePath=([^"]+)"/);
          if (filePathMatch) {
            cleanedBlock.path = filePathMatch[1];
          } else {
            // 尝试从重定向中提取路径
            const redirectMatch = block.content.match(/>\s*"?([^"\s]+)"?/);
            if (redirectMatch) {
              cleanedBlock.path = redirectMatch[1];
            }
          }
        }
      }

      return {
        ...cleanedBlock,
        content: cleanedBlock.content.trim()
      };
    });
  }
} 