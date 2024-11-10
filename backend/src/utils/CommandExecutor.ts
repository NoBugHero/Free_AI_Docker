import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

const execAsync = promisify(exec);

export class CommandExecutor {
  static async execute(command: string, savePath: string, language?: string): Promise<{
    success: boolean;
    output: string;
    error?: string;
  }> {
    try {
      // 确保保存路径存在
      await fs.mkdir(savePath, { recursive: true });
      
      console.log(`Executing command:`, {
        command,
        language,
        savePath
      });

      if (language === 'cmd' || language === 'batch') {
        // 创建临时批处理文件
        const tempBatFile = path.join(os.tmpdir(), `temp_${Date.now()}.bat`);
        const batContent = `
@echo off
cd /d "${savePath}"
${command}
`;
        
        console.log('Creating batch file:', {
          path: tempBatFile,
          content: batContent
        });

        // 写入批处理文件
        await fs.writeFile(tempBatFile, batContent, 'utf-8');

        try {
          // 执行批处理文件
          const { stdout, stderr } = await execAsync(`"${tempBatFile}"`, {
            cwd: savePath,
            shell: 'cmd.exe',
            windowsHide: true
          });

          // 删除临时文件
          await fs.unlink(tempBatFile);

          return {
            success: !stderr,
            output: stdout || '命令执行成功',
            error: stderr
          };
        } catch (error: any) {
          // 确保清理临时文件
          await fs.unlink(tempBatFile).catch(() => {});
          throw error;
        }
      } else if (language === 'powershell') {
        // PowerShell 命令执行
        const psScript = `
Set-Location "${savePath}"
${command}
`;
        
        const { stdout, stderr } = await execAsync(`powershell -Command "${psScript}"`, {
          cwd: savePath
        });

        return {
          success: !stderr,
          output: stdout,
          error: stderr
        };
      } else if (language === 'python') {
        // Python 代码执行
        const tempFile = path.join(os.tmpdir(), `temp_${Date.now()}.py`);
        await fs.writeFile(tempFile, command, 'utf-8');
        
        try {
          const { stdout, stderr } = await execAsync(`python "${tempFile}"`, {
            cwd: savePath
          });

          await fs.unlink(tempFile);

          return {
            success: !stderr,
            output: stdout,
            error: stderr
          };
        } catch (error: any) {
          await fs.unlink(tempFile).catch(() => {});
          throw error;
        }
      } else {
        // 其他命令直接执行
        const { stdout, stderr } = await execAsync(command, {
          cwd: savePath,
          timeout: 30000,
          maxBuffer: 1024 * 1024
        });

        return {
          success: true,
          output: stdout,
          error: stderr || undefined
        };
      }
    } catch (error: any) {
      console.error('Command execution error:', error);
      return {
        success: false,
        output: '',
        error: error.message
      };
    }
  }

  static async writeFile(filePath: string, content: string, savePath: string): Promise<{
    success: boolean;
    error?: string;
  }> {
    try {
      const fullPath = path.join(savePath, filePath);
      const dir = path.dirname(fullPath);
      
      // 确保目录存在
      await fs.mkdir(dir, { recursive: true });
      
      // 写入文件
      await fs.writeFile(fullPath, content, 'utf-8');
      
      return { success: true };
    } catch (error: any) {
      console.error('File writing error:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }
} 