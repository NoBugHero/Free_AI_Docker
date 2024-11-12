import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';
import iconv from 'iconv-lite';

const execAsync = promisify(exec);

export class CommandExecutor {
  static async execute(command: string, savePath: string, language?: string): Promise<{
    success: boolean;
    output: string;
    error?: string;
  }> {
    try {
      await fs.mkdir(savePath, { recursive: true });
      
      const psCommand = `
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
        [Console]::InputEncoding = [System.Text.Encoding]::UTF8;
        $OutputEncoding = [System.Text.Encoding]::UTF8;
        $env:PYTHONIOENCODING = "utf-8";
        Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass;
        ${command}
      `;

      const { stdout, stderr } = await execAsync(
        `powershell -NoProfile -NonInteractive -Command "${psCommand}"`,
        {
          cwd: savePath,
          env: {
            ...process.env,
            PYTHONIOENCODING: 'utf-8',
            LANG: 'zh_CN.UTF-8'
          },
          encoding: 'buffer',
          maxBuffer: 1024 * 1024 * 10
        }
      );

      const decodedOutput = iconv.decode(stdout, 'utf8');
      const decodedError = stderr ? iconv.decode(stderr, 'utf8') : undefined;

      return {
        success: !decodedError,
        output: decodedOutput || '命令执行成功',
        error: decodedError
      };
    } catch (error: any) {
      console.error('Command execution error:', error);
      const errorMessage = error.message ? iconv.decode(Buffer.from(error.message), 'utf8') : '未知错误';
      return {
        success: false,
        output: '',
        error: errorMessage
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
      
      await fs.mkdir(dir, { recursive: true });
      
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