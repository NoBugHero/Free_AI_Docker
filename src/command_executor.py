import subprocess
import platform
import os
import logging
import time
from typing import Dict, Union, List
from security_config import SecurityConfig

logger = logging.getLogger(__name__)

class CommandExecutor:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.command_history = []
        self.max_history = 100
        # 添加工作目录管理
        self.workspace_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "workspace"
        )
        self._ensure_workspace()
    
    def _ensure_workspace(self):
        """确保工作目录存在"""
        try:
            if not os.path.exists(self.workspace_dir):
                os.makedirs(self.workspace_dir)
                logger.info(f"Created workspace directory: {self.workspace_dir}")
            
            # 创建基本子目录
            subdirs = ['scripts', 'data', 'logs', 'temp', 'projects']
            for subdir in subdirs:
                subdir_path = os.path.join(self.workspace_dir, subdir)
                if not os.path.exists(subdir_path):
                    os.makedirs(subdir_path)
                    logger.info(f"Created subdirectory: {subdir_path}")
        except Exception as e:
            logger.error(f"Failed to create workspace: {str(e)}")
            raise
    
    def _create_project_env(self, project_name: str) -> str:
        """创建项目专用的虚拟环境"""
        try:
            project_dir = os.path.join(self.workspace_dir, 'projects', project_name)
            venv_dir = os.path.join(project_dir, '.venv')
            
            # 创建项目目录
            if not os.path.exists(project_dir):
                os.makedirs(project_dir)
                logger.info(f"Created project directory: {project_dir}")
            
            # 创建虚拟环境
            if not os.path.exists(venv_dir):
                import venv
                venv.create(venv_dir, with_pip=True)
                logger.info(f"Created virtual environment: {venv_dir}")
            
            # 返回项目目录路径
            return project_dir
        except Exception as e:
            logger.error(f"Failed to create project environment: {str(e)}")
            raise
    
    def _get_venv_python(self, project_name: str) -> str:
        """获取项目虚拟环境中的Python解释器路径"""
        venv_dir = os.path.join(self.workspace_dir, 'projects', project_name, '.venv')
        if self.os_type == 'windows':
            python_path = os.path.join(venv_dir, 'Scripts', 'python.exe')
        else:
            python_path = os.path.join(venv_dir, 'bin', 'python')
        return python_path
    
    def _prepare_command(self, command: str) -> str:
        """准备命令，添加工作目录上下文"""
        try:
            # 如果是项目创建命令，使用特殊处理
            if command.startswith('create_project'):
                parts = command.split()
                if len(parts) >= 2:
                    project_name = parts[1]
                    project_dir = self._create_project_env(project_name)
                    return f"echo Created project: {project_dir}"
            
            # 如果是虚拟环境相关命令，使用项目特定的Python
            if command.startswith(('pip install', 'python')):
                parts = command.split()
                if len(parts) >= 3 and parts[0] == 'pip':
                    project_name = os.path.basename(os.getcwd())
                    python_path = self._get_venv_python(project_name)
                    return f'"{python_path}" -m pip {" ".join(parts[1:])}'
                elif parts[0] == 'python':
                    project_name = os.path.basename(os.getcwd())
                    python_path = self._get_venv_python(project_name)
                    return f'"{python_path}" {" ".join(parts[1:])}'
            
            # 如果是HTML、CSS或JS内容，创建在项目目录中
            if command.startswith(('<!DOCTYPE', 'body {', 'document.')):
                project_name = os.path.basename(os.getcwd())
                file_ext = '.html' if command.startswith('<!DOCTYPE') else \
                          '.css' if command.startswith('body') else '.js'
                file_path = os.path.join(self.workspace_dir, 'projects', project_name, f'index{file_ext}')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(command)
                logger.info(f"Created file: {file_path}")
                return f"echo Created file: {file_path}"

            # 处理其他命令
            if any(cmd in command.lower() for cmd in ['cd', 'dir', 'ls', 'mkdir', 'touch', 'echo']):
                # 替换相对路径为绝对路径
                command = command.replace('./', f'{self.workspace_dir}/')
                command = command.replace('.\\', f'{self.workspace_dir}\\')
                
                # 处理文件创建命令
                if command.startswith('touch'):
                    filename = command.split()[-1]
                    project_name = os.path.basename(os.getcwd())
                    file_path = os.path.join(self.workspace_dir, 'projects', project_name, filename)
                    open(file_path, 'a').close()
                    return f"echo Created file: {file_path}"
                
                # 处理echo命令创建文件
                if '>' in command:
                    parts = command.split('>')
                    content = parts[0].replace('echo', '').strip().strip('"\'')
                    filename = parts[1].strip().strip('"\'')
                    project_name = os.path.basename(os.getcwd())
                    file_path = os.path.join(self.workspace_dir, 'projects', project_name, filename)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return f"echo Created file: {file_path}"
                
                # 处理mkdir命令
                if command.startswith('mkdir'):
                    dir_name = command.split()[-1]
                    if not os.path.isabs(dir_name):
                        project_name = os.path.basename(os.getcwd())
                        dir_path = os.path.join(self.workspace_dir, 'projects', project_name, dir_name)
                        os.makedirs(dir_path, exist_ok=True)
                        return f"echo Created directory: {dir_path}"
                
                # 处理cd命令
                if command.startswith('cd'):
                    path = command.split()[-1]
                    if not os.path.isabs(path):
                        project_name = os.path.basename(os.getcwd())
                        path = os.path.join(self.workspace_dir, 'projects', project_name, path)
                    os.chdir(path)
                    return f"echo Changed directory to: {path}"
            
            return command
        except Exception as e:
            logger.error(f"命令准备失败: {str(e)}")
            return command
    
    def validate_command(self, command: str) -> bool:
        """验证命令的安全性"""
        # 忽略注释和说明文本
        if any([
            command.strip().startswith('#'),  # 注释
            command.strip().startswith(('###', '注意:', '说明:', '请', '现在', '-', '资源列表')),
            command.strip().endswith(('：', ':')),
            len(command.split('\n')) > 1,  # 多行文本
            command.startswith(('*', '>', '#')),  # Markdown格式
            '：' in command or ': ' in command,  # 包含说明符号
            command.strip() in ['GOAL_ACHIEVED', 'TASK_COMPLETED'],  # 特殊标记
            not command.strip()  # 空命令
        ]):
            return False
        
        # 禁止的命令列表
        forbidden_commands = [
            'rm -rf', 'format', 'mkfs',
            'dd', 'fdisk', 'mkfs',
            ':(){:|:&};:', '>()', '<()',  # Fork炸弹模式
            'sudo', 'su'  # 提权命令
        ]
        
        command = command.lower()
        for forbidden in forbidden_commands:
            if forbidden in command:
                logger.warning(f"检测到危险命令: {command}")
                return False
                
        return True
    
    def convert_command(self, command: str) -> str:
        """转换命令以适应不同操作系统"""
        if self.os_type == 'windows':
            # Linux/macOS 命令转 Windows 命令
            conversions = {
                'sudo apt-get update': 'echo "Windows环境请手动安装所需软件"',
                'sudo apt-get install': 'echo "Windows环境请手动安装所需软件"',
                'npm install -g': 'npm install --global',  # 修复npm全局安装命令
                'vue create': 'npx @vue/cli create',  # 使用npx运行vue cli
                'curl -sL': 'curl -L',  # Windows curl不支持-s选项
                'wget': 'curl -O',
                'ls': 'dir',
                'rm': 'del',
                'cp': 'copy',
                'mv': 'move',
                'cat': 'type',
                'clear': 'cls',
                'mkdir': 'md',
                'rmdir': 'rd',
                'touch': 'echo.>',
                'nano': 'notepad',
                'vim': 'notepad'
            }
            
            # 处理路径分隔符
            command = command.replace('/', '\\')
            
            # 处理环境变量
            command = command.replace('$HOME', '%USERPROFILE%')
            command = command.replace('$PATH', '%PATH%')
            
            # 处理特殊命令
            if command.startswith('npm'):
                # 确保在项目目录中执行npm命令
                project_name = os.path.basename(os.getcwd())
                project_dir = os.path.join(self.workspace_dir, 'projects', project_name)
                os.makedirs(project_dir, exist_ok=True)
                os.chdir(project_dir)
            
            # 转换命令
            for linux_cmd, win_cmd in conversions.items():
                if command.startswith(linux_cmd):
                    return command.replace(linux_cmd, win_cmd, 1)
        
        return command
    
    def check_docker_installed(self) -> bool:
        """检查Docker是否已安装"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                 capture_output=True, 
                                 text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def check_pip_installed(self) -> bool:
        """检查pip是否已安装"""
        try:
            result = subprocess.run(['pip', '--version'], 
                                 capture_output=True, 
                                 text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def check_homebrew_installed(self) -> bool:
        """检查Homebrew是否已安装"""
        try:
            result = subprocess.run(['brew', '--version'], 
                                 capture_output=True, 
                                 text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def execute(self, command: str) -> Dict[str, Union[str, bool, int]]:
        """执行命令并返回结果"""
        result = {
            "success": False,
            "output": "",
            "error": "",
            "exit_code": -1
        }
        
        try:
            # 如果是项目创建命令，使用特殊处理
            if command.startswith('create_project'):
                parts = command.split()
                if len(parts) >= 2:
                    project_name = parts[1]
                    project_dir = self._create_project_env(project_name)
                    result["success"] = True
                    result["output"] = f"Created project: {project_dir}"
                    return result
            
            # 验证命令安全性
            if not self.validate_command(command):
                if command.strip().startswith('#') or not command.strip():
                    result["success"] = True
                    result["output"] = "跳过注释或说明文本"
                    return result
                
                result["error"] = "无效命令或危险命令已被阻止"
                return result
            
            # 准备命令
            command = self._prepare_command(command)
            
            # 转换命令
            converted_command = self.convert_command(command)
            logger.info(f"执行命令: {converted_command}")
            
            # 设置工作目录
            cwd = os.getcwd()  # 使用当前目录
            
            # 执行命令
            process = subprocess.Popen(
                converted_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                encoding='utf-8'  # 指定编码为utf-8
            )
            
            # 获取输出
            stdout, stderr = process.communicate(timeout=30)
            
            # 更新结果
            result["success"] = process.returncode == 0
            result["output"] = stdout
            result["error"] = stderr
            result["exit_code"] = process.returncode
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"命令执行错误: {str(e)}")
        
        return result
    
    def add_to_history(self, command: str, result: Dict):
        """添加命令到历史记录"""
        history_entry = {
            "command": command,
            "success": result["success"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.command_history.append(history_entry)
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)
    
    def get_history(self) -> List[Dict]:
        """获取命令历史"""
        return self.command_history
    
    def clear_history(self):
        """清除命令历史"""
        self.command_history = [] 