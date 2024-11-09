import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, Any
import json
import re
import subprocess
import platform
import requests
import pathlib

class AIService:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        # 设置项目根目录
        self.root_dir = str(pathlib.Path(__file__).parent.parent.absolute())
        self.conversation_history = []
        
    def get_response(self, prompt: str, include_execution_result: bool = False, execution_result: str = None) -> Dict[str, Any]:
        """获取AI响应并自动执行命令"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = self._prepare_messages(prompt, include_execution_result, execution_result)
            
            # 构建请求数据
            request_data = {
                "model": "qwen2.5-3b-instruct",
                "input": {
                    "messages": [
                        {"role": "system", "content": messages[0]["content"]},
                        {"role": "user", "content": messages[-1]["content"]}
                    ]
                }
            }
            
            # 打印请求信息（用于调试）
            print(f"API请求URL: {request_data}")
            print(f"API请求头: {headers}")
            
            # 发送请求
            response = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers=headers,
                json=request_data  # 使用 json 参数而不是手动序列化
            )
            
            print(f"API响应状态码: {response.status_code}")
            print(f"API响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                content = result['output']['text']
                
                # 解析并执行命令
                execution_result = self._process_and_execute_commands(content)
                
                # 保存对话历史
                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": content})
                
                return {
                    "content": content,
                    "execution_result": execution_result,
                    "is_completed": "TASK_COMPLETED" in content,
                    "requires_execution": bool(execution_result)
                }
            else:
                raise Exception(f"API请求失败: {response.text}")
                
        except Exception as e:
            print(f"错误详情: {str(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")  # 添加堆栈跟踪
            return {
                "content": f"Error: {str(e)}",
                "execution_result": None,
                "is_completed": False,
                "requires_execution": False
            }
    def _prepare_messages(self, prompt: str, include_execution_result: bool, execution_result: str) -> list:
        """准备消息历史"""
        system_prompt = """你是一个帮助用户执行命令的AI助手。请按照以下格式提供响应：
1. 用中文清晰解释每个步骤
2. 使用 ```bash 代码块提供具体命令
3. 确保命令是可执行的，并使用绝对路径
4. 在命令执行后验证结果
5. 如果任务完成，请在最后说明 'TASK_COMPLETED'

注意：所有文件操作���应该在项目根目录下执行。"""
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.conversation_history)
        
        if include_execution_result:
            prompt = f"上一次执行结果: {execution_result}\n\n当前指令: {prompt}"
            
        # 添加项目根目录信息到提示词中
        prompt = f"请在此目录下执行操作 '{self.root_dir}':\n{prompt}"
        
        messages.append({"role": "user", "content": prompt})
        return messages

    def _process_and_execute_commands(self, response: str) -> str:
        """解析并执行命令"""
        try:
            # 使用正则表达式提取命令块
            command_blocks = re.findall(r'```(?:bash|shell|cmd)?\n(.*?)\n```', response, re.DOTALL)
            if not command_blocks:
                return "未找到可执行的命令"
                
            execution_results = []
            for commands in command_blocks:
                # 分割多行命令
                command_lines = [cmd.strip() for cmd in commands.split('\n') if cmd.strip()]
                for cmd in command_lines:
                    try:
                        print(f"原始命令: {cmd}")  # 调试信息
                        
                        # 切换到项目根目录
                        os.chdir(self.root_dir)
                        
                        # 命令转换（Linux 风格 -> Windows 风格）
                        if platform.system() == 'Windows':
                            # 替换路径分隔符
                            cmd = cmd.replace('/', '\\')
                            
                            # 命令映射
                            cmd_mapping = {
                                'ls': 'dir',
                                'cat': 'type',
                                'less': 'type',
                                'echo': 'echo',
                            }
                            
                            # 处理特殊命令
                            if cmd.startswith('cd /mnt/'):
                                # 将 /mnt/x/ 转换为 x:\
                                drive_letter = cmd[8:9].upper()
                                path = cmd[9:].replace('/', '\\')
                                cmd = f"cd /d {drive_letter}:{path}"
                            else:
                                # 替换其他命令
                                for linux_cmd, win_cmd in cmd_mapping.items():
                                    if cmd.startswith(linux_cmd):
                                        cmd = cmd.replace(linux_cmd, win_cmd, 1)
                                        break
                            
                            print(f"转换后的命令: {cmd}")  # 调试信息
                            
                            # 处理重定向和中文内容
                            if '>' in cmd and '"' in cmd:
                                # 分离命令和文件名
                                cmd_part, file_part = cmd.split('>', 1)
                                file_part = file_part.strip().strip('"')
                                content = cmd_part.split('"')[1]
                                
                                # 直接使用 Python 写入文件
                                with open(file_part, 'w', encoding='utf-8') as f:
                                    f.write(content)
                                output = f"已创建文件: {file_part}"
                            else:
                                # 执行其他命令
                                result = subprocess.run(
                                    cmd, 
                                    shell=True, 
                                    capture_output=True, 
                                    text=True, 
                                    encoding='gbk'  # 使用 GBK 编码处理中文
                                )
                                output = result.stdout if result.returncode == 0 else result.stderr
                            
                            execution_results.append(f"命令 '{cmd}' 执行结果:\n{output}")
                            print(f"命令执行结果: {output}")  # 调试信息
                            
                        else:
                            # Linux/Mac 系统的处理保持不变
                            result = subprocess.run(['bash', '-c', cmd], capture_output=True, text=True, encoding='utf-8')
                            output = result.stdout if result.returncode == 0 else result.stderr
                            execution_results.append(f"命令 '{cmd}' 执行结果:\n{output}")
                            
                    except Exception as e:
                        error_msg = f"命令 '{cmd}' 执行失败: {str(e)}"
                        execution_results.append(error_msg)
                        print(error_msg)  # 调试信息
            
            return "\n".join(execution_results)
        except Exception as e:
            error_msg = f"命令处理失败: {str(e)}"
            print(error_msg)  # 调试信息
            return error_msg

    def reset_conversation(self):
        """重置对话历史"""
        self.conversation_history = []
