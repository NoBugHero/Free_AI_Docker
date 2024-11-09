import gradio as gr
from ai_service import AIService
from prompt_optimizer import PromptOptimizer
from resource_manager import ResourceManager
from encryption import Encryption
from scanner import SystemScanner
from logger import logger
from command_executor import CommandExecutor
import time
from typing import Dict
import platform
import json

class Free_AI_Docker:
    def __init__(self):
        logger.info("Initializing Free_AI_Docker...")
        self.ai_service = AIService()
        self.prompt_optimizer = PromptOptimizer()
        self.resource_manager = ResourceManager()
        self.encryption = Encryption()
        self.scanner = SystemScanner(self.resource_manager)
        self.current_risk_level = "低风险"
        self.execution_mode = "手动档"
        self.command_executor = CommandExecutor()
        logger.info("Free_AI_Docker initialized successfully")
        
    def process_input(self, 
                     user_prompt: str, 
                     chat_history: str) -> tuple[str, str, str, str]:
        """
        处理用户输入并返回结果
        """
        try:
            # 获取保存的赚钱目标和创意
            money_goals = self.resource_manager.get_resource("money_goals")
            if money_goals:
                goal = money_goals.get("goal", "")
                idea = money_goals.get("idea", "")
                # 将目标和创意添加到提示词中
                user_prompt = f"""
目标: {goal}
创意: {idea}

用户输入: {user_prompt}
"""
                logger.info(f"Added money goals to prompt: {goal}, {idea}")
            
            # 1. 优化提示词
            optimized_prompt = self.prompt_optimizer.optimize_prompt(user_prompt)
            
            # 2. 获取AI响应并自动执行命令
            response = self.ai_service.get_response(optimized_prompt)
            
            # 3. 更新聊天历史
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            new_history = f"{chat_history}\n\n[{timestamp}] 用户: {user_prompt}"
            new_history += f"\n\n优化后的提示词: {optimized_prompt}"
            new_history += f"\n\nAI: {response['content']}"
            
            # 如果有执行结果，添加到历史记录
            if response.get('execution_result'):
                new_history += f"\n\n执行结果:\n{response['execution_result']}"
            
            # 4. 确定执行状态
            status = "命令已执行" if response.get('execution_result') else (
                "任务完成" if response["is_completed"] else "等待下一步"
            )
            
            return (
                optimized_prompt,  # 优化后的提示词
                response['content'],  # AI响应
                status,              # 执行状态
                new_history         # 更新后的聊天历史
            )
        except Exception as e:
            logger.error(f"处理输入失败: {str(e)}")
            return (
                user_prompt,
                f"处理失败: {str(e)}",
                "错误",
                chat_history
            )
    
    def execute_command(self, command: str, chat_history: str) -> tuple[str, str]:
        """执行命令并返回结果"""
        result = self.command_executor.execute(command)
        
        # 格式化输出
        if result["success"]:
            execution_result = f"命令执行成功:\n{result['output']}"
        else:
            execution_result = f"命令执行失败:\n错误: {result['error']}"
        
        # 更新历史记录
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        new_history = f"{chat_history}\n\n[{timestamp}] 执行命令: {command}\n{execution_result}"
        
        return execution_result, new_history

    def save_resource_info(self, 
                          resource_type: str, 
                          resource_name: str, 
                          resource_value: str) -> str:
        """保存资源信息"""
        try:
            if not resource_name:
                return "❌ 资源名称不能为空"
                
            # 构建资源数据结构
            resource_data = {
                "name": resource_name,  # 确保包含 name 字段
                "value": self.encryption.encrypt(resource_value),  # 加密存储值
                "type": resource_type,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 保存资源
            self.resource_manager.save_resource(resource_type, resource_data)
            
            # 更新状态
            self.save_app_state({
                f"last_{resource_type}_name": resource_name
            })
            
            return f"✅ {resource_type} '{resource_name}' 已安全保存"
        except Exception as e:
            logger.error(f"保存资源失败: {str(e)}")
            return f"❌ 保存失败: {str(e)}"

    def update_risk_level(self, risk_level: str) -> str:
        """更新风险等级"""
        risk_limits = {
            "低风险": "20%",
            "中风险": "60%",
            "高风险": "100%"
        }
        self.current_risk_level = risk_level
        return f"风险等级已更新为: {risk_level}，最大资源损失限制: {risk_limits[risk_level]}"

    def update_execution_mode(self, mode: str) -> str:
        """更新执行模式"""
        self.execution_mode = mode
        return f"执行模式已更新为: {mode}"

    def update_scan_interval(self, hours: int) -> str:
        """更新扫描间隔"""
        logger.info(f"Updating scan interval to {hours} hours")
        return self.scanner.set_scan_interval(hours)

    def toggle_scanning(self, is_active: bool) -> str:
        """切换扫描状态"""
        if is_active:
            logger.info("Starting system scanner")
            return self.scanner.start_scanning()
        else:
            logger.info("Stopping system scanner")
            return self.scanner.stop_scanning()

    def save_money_goal(self, goal: str, idea: str) -> str:
        """保存赚钱目标和创意"""
        try:
            if not goal:
                return "❌ 赚钱目标不能为空"
                
            # 构建目标数据结构
            goal_data = {
                "name": goal,  # 使用目标作为名称
                "value": {
                    "goal": goal,
                    "idea": idea or ""
                },
                "type": "money_goals",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 保存目标
            try:
                self.resource_manager.save_resource("money_goals", goal_data)
                logger.info(f"保存赚钱目标成功: {goal}")
                
                # 更新状态
                self.save_app_state({
                    "last_money_goal": goal,
                    "last_money_idea": idea
                })
                
                return "✅ 赚钱目标和创意已保存"
            except ValueError as ve:
                logger.error(f"保存赚钱目标失败，数据格式错误: {str(ve)}")
                return f"❌ 保存失败: 数据格式错误"
            except Exception as e:
                logger.error(f"保存赚钱目标失败: {str(e)}")
                return f"❌ 保存失败: {str(e)}"
                
        except Exception as e:
            logger.error(f"保存赚钱目标失败: {str(e)}")
            return f"❌ 保存失败: {str(e)}"

    def save_api_config(self, api_name: str, api_key: str, api_url: str) -> str:
        """保存API配置"""
        try:
            if not api_name:
                return "❌ API名称不能为空"
                
            # 加密存储API信息
            encrypted_key = self.encryption.encrypt(api_key)
            encrypted_url = self.encryption.encrypt(api_url)
            
            # 构建API配置数据
            api_config = {
                "name": api_name,  # 确保包含 name 字段
                "value": {  # 将其他信息放在 value 字段中
                    "key": encrypted_key,
                    "url": encrypted_url,
                    "calls": 0,
                    "last_used": None
                }
            }
            
            # 保存API配置
            self.resource_manager.save_resource("API密钥", api_config)
            
            # 保存最后使用的API名称
            self.save_app_state({"last_api_name": api_name})
            
            return f" API配置 '{api_name}' 已安全保存"
        except Exception as e:
            logger.error(f"保存API配置失败: {str(e)}")
            return f"❌ 保存失败: {str(e)}"

    def get_api_usage(self, api_name: str) -> str:
        """获取API使用情况"""
        try:
            api_configs = self.resource_manager.get_resource("API密钥") or {}
            if not api_configs:
                return "未找到任何API配置"
                
            if not api_name:
                return "请输入API名称"
                
            api_config = api_configs.get(api_name)
            if not api_config:
                api_list = ", ".join(api_configs.keys())
                return f"未找到API: {api_name}\n可用的API: {api_list}"
                
            value = api_config.get("value", {})
            return (f"API: {api_name}\n"
                    f"调用次数: {value.get('calls', 0)}\n"
                    f"最后使用: {value.get('last_used') or '从未使用'}")
        except Exception as e:
            logger.error(f"获取API使用情况失败: {str(e)}")
            return f"获取失败: {str(e)}"

    def load_saved_state(self) -> Dict:
        """加载保存的状态"""
        try:
            # 加载应用状态
            app_state = self.resource_manager.get_resource("app_state") or {}
            
            # 加载赚钱目标
            money_goals = self.resource_manager.get_resource("money_goals") or {}
            
            # 加载API配置
            api_configs = self.resource_manager.get_resource("api_configs") or {}
            
            # 合并所有状态
            state = {
                "risk_level": "低风险",
                "execution_mode": "手动档",
                "scan_interval": 1,
                "last_api_name": "",
                "last_money_goal": "",
                "last_money_idea": "",
                "system_env": platform.system()
            }
            
            # 更新默认值
            state.update(app_state)
            
            # 添加赚钱目标和创意
            if money_goals:
                state["last_money_goal"] = money_goals.get("goal", "")
                state["last_money_idea"] = money_goals.get("idea", "")
            
            return state
        except Exception as e:
            logger.error(f"加载状态失败: {str(e)}")
            return {}

    def save_app_state(self, state_updates: Dict) -> None:
        """保存应用状态"""
        try:
            current_state = self.load_saved_state()
            current_state.update(state_updates)
            self.resource_manager.save_resource("app_state", current_state)
        except Exception as e:
            logger.error(f"保存状态失败: {str(e)}")

    def update_system_env(self, os_type: str) -> str:
        """更新系统环境配置"""
        try:
            env_config = {
                "os_type": os_type,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.resource_manager.save_resource("system_env", env_config)
            self.save_app_state({"system_env": os_type})
            
            # 更新命令执行器的系统类型
            self.command_executor.os_type = os_type.lower()
            
            return f"✅ 系统环境已更新为: {os_type}"
        except Exception as e:
            logger.error(f"更新系统环境失败: {str(e)}")
            return f"❌ 更新失败: {str(e)}"

    def get_current_system_env(self) -> str:
        """获取当前系统环境配置"""
        try:
            env_config = self.resource_manager.get_resource("system_env")
            return env_config.get("os_type", platform.system())
        except Exception as e:
            logger.error(f"获取系统环境失败: {str(e)}")
            return platform.system()

    def execute_money_plan_by_resources(self, chat_history: str) -> tuple[str, str, str, str]:
        """根据当前资源情况执行赚钱方案"""
        try:
            # 获取所有资源
            all_resources = self.resource_manager.get_all_resources()
            
            # 格式化资源列表
            resources_info = []
            for resource_type, type_resources in all_resources.items():
                if type_resources:
                    resources_info.append(f"\n{resource_type}:")
                    for name, data in type_resources.items():
                        # 对敏���信息进行脱敏处理
                        if isinstance(data.get('value'), dict):
                            # 处理API类型的资源
                            masked_value = {
                                k: self.encryption.mask_sensitive_data(str(v))
                                for k, v in data['value'].items()
                            }
                        else:
                            # 处理普通资源
                            masked_value = self.encryption.mask_sensitive_data(
                                str(data.get('value', ''))
                            )
                        resources_info.append(f"  - {name}: {masked_value}")
            
            resources_text = "\n".join(resources_info) if resources_info else "暂无可用资源"
            
            prompt = f"""
请根据以下资源情况制定并执行赚钱方案：

当前可用资源：
{resources_text}

请基于这些资源：
1. 评估每个资源的价值和潜力
2. 制定最优化的赚钱方案
3. 给出具体的执行步骤
4. 预估可能的收益
5. 考虑当前的风险等级：{self.current_risk_level}

注意：
- 请只提供可执行的具体命令
- 每个命令都应该是完整的
- 如果需要创建文件，请使用完整路径
- 如果某个资源无法直接使用，请说明原因
"""
            # 处理响应
            response = self.process_input(prompt, chat_history)
            
            # 记录执行情况
            logger.info(f"基于资源执行计划完成，资源数量: {len(resources_info)}")
            
            return response
        except Exception as e:
            logger.error(f"执行资源赚钱方案失败: {str(e)}")
            return ("", f"执行失败: {str(e)}", "错误", chat_history)

    def execute_money_plan_by_goals(self, chat_history: str) -> tuple[str, str, str, str]:
        """根据当前目标和创意执行赚钱方案"""
        try:
            # 获取赚钱目标和创意
            money_goals = self.resource_manager.get_resource("money_goals") or {}
            
            # 检查数据结构
            if not money_goals:
                return ("", "请先设置赚钱目标和创意", "错误", chat_history)
                
            # 从正确的数据结构中获取值
            goal_data = list(money_goals.values())[0] if money_goals else {}
            if not goal_data or 'value' not in goal_data:
                return ("", "赚钱目标数据格式错误", "错误", chat_history)
                
            goal_value = goal_data['value']
            goal = goal_value.get('goal', '')
            idea = goal_value.get('idea', '')
            
            if not goal:
                return ("", "请先设置赚钱目标和创意", "错误", chat_history)
            
            # 构建初始提示词
            initial_prompt = f"""
请根据以下目标和创意制定并执行赚钱方案：
目标：{goal}
创意：{idea}

请基于这些内容：
1. 分析目标的可行性
2. 评估创意的市场潜力
3. 制定详细的执行计划
4. 列出具体的行动步骤
5. 考虑当前的风险等级：{self.current_risk_level}

注意：
- 请提供具体可执行的命令
- 所有文件操作都在工作目录下进行
- 考虑当前系统环境的兼容性
- 每个步骤执行后，请说明下一步计划
- 如果目标已达成，请说明 'GOAL_ACHIEVED'
"""
            # 处理初始响应
            optimized_prompt, ai_response, status, new_history = self.process_input(initial_prompt, chat_history)
            
            # 如果是全自动模式，继续执行后续步骤
            if self.execution_mode == "全自动" and status != "错误":
                max_iterations = 10  # 防止无限循环
                iteration = 0
                
                while iteration < max_iterations:
                    # 检查是否达成目标
                    if "GOAL_ACHIEVED" in ai_response:
                        logger.info(f"目标已达成: {goal}")
                        break
                        
                    # 构建后续提示词
                    follow_up_prompt = f"""
基于之前的执行结果，请继续执行下一步：
目标：{goal}
创意：{idea}
当前状态：{status}

请：
1. 评估当前进度
2. 执行下一步操作
3. 如果目标已达成，请说明 'GOAL_ACHIEVED'
4. 如果遇到问题，请说明原因和解决方案

注意：
- 请提供具体可执行的命令
- 所有文件操作都在工作目录下进行
- 考虑当前系统环境的兼容性
"""
                    # 处理后续响应
                    optimized_prompt, ai_response, status, new_history = self.process_input(
                        follow_up_prompt, new_history
                    )
                    
                    # 记录执行情况
                    logger.info(f"执行第 {iteration + 1} 轮 - 状态: {status}")
                    
                    # 检查是否需要继续
                    if status == "错误" or "TASK_COMPLETED" in ai_response:
                        break
                        
                    iteration += 1
                    
                if iteration >= max_iterations:
                    logger.warning(f"达到最大迭代次数 ({max_iterations})")
                    new_history += "\n\n注意：已达到最大迭代次数，执行已停止。"
            
            return optimized_prompt, ai_response, status, new_history
                
        except Exception as e:
            logger.error(f"执行目标赚钱方案失败: {str(e)}")
            return ("", f"执行失败: {str(e)}", "错误", chat_history)

    def get_saved_resources(self) -> str:
        """获取已保存的资源列表"""
        try:
            # 获取所有资源
            resources = self.resource_manager.get_all_resources()
            result = []
            
            # 遍历每种资源类型
            for resource_type, type_resources in resources.items():
                if type_resources:  # 如果这种类型有资源
                    result.append(f"\n{resource_type}:")
                    for name, data in type_resources.items():
                        # 对敏感信息进行脱敏处理
                        masked_value = self.encryption.mask_sensitive_data(
                            data.get("value", "")
                        )
                        result.append(f"  - {name}: {masked_value}")
            
            if not result:
                return "暂无保存的资源"
                
            return "\n".join(result)
        except Exception as e:
            logger.error(f"获取资源列表失败: {str(e)}")
            return f"获取资源列表失败: {str(e)}"

    def create_interface(self):
        with gr.Blocks(title="Free_AI_Docker") as interface:
            # 加载保存的状态
            saved_state = self.load_saved_state()
            
            gr.Markdown("# Free_AI_Docker")
            
            with gr.Tabs():
                # 资源配置标签页
                with gr.Tab("资源配置"):
                    with gr.Group():
                        with gr.Row():
                            with gr.Column(scale=1):
                                resource_type = gr.Dropdown(
                                    choices=["API密钥", "钱包地址", "账号密码", "其他资源"],
                                    label="资源类型"
                                )
                                resource_name = gr.Textbox(label="资源名称")
                                resource_value = gr.Textbox(
                                    label="资源值",
                                    type="password"
                                )
                                save_btn = gr.Button("保存资源")
                                resource_status = gr.Textbox(
                                    label="保存状态",
                                    interactive=False
                                )
                                
                            with gr.Column(scale=1):
                                resource_list = gr.Textbox(
                                    label="已保存的资源",
                                    value=lambda: self.get_saved_resources(),  # 初始加载
                                    lines=10,
                                    interactive=False
                                )
                                refresh_btn = gr.Button("刷新资源列表")
                                
                        gr.Markdown("""
                        ### 资源说明
                        1. API密钥：用于连接各种服务的密钥
                        2. 钱包地址：加密货币钱包地址
                        3. 账号密码：各类服务账号
                        4. 其他资源：其他类型的资源
                        
                        ### 安全提示
                        - 所有资源信息都经过加密存储
                        - 密码类信息会进行脱敏显示
                        - 定期检查资源状态和有效性
                        """)

                # 风险设置标签页
                with gr.Tab("风险设置"):
                    with gr.Group():
                        risk_level = gr.Radio(
                            choices=["低风险", "中风险", "高风险"],
                            label="风险等级",
                            value=saved_state.get("risk_level", "低风险")
                        )
                        risk_status = gr.Textbox(
                            label="当前风险状态",
                            interactive=False
                        )
                        gr.Markdown("""
                        ### 风险等级说明
                        - 低风险: 最大损失20%资源
                        - 中风险: 最大损失60%资源
                        - 高风险: 可能损失全部资源
                        """)

                # 执行模式标签页
                with gr.Tab("执行模式"):
                    with gr.Group():
                        execution_mode = gr.Radio(
                            choices=["手动档", "全自动"],
                            label="执行模式",
                            value=saved_state.get("execution_mode", "手动档")
                        )
                        gr.Markdown("""
                        ### ⚠️ 警告
                        1. 不要暴露docker接口，存在被恶意攻击的风险
                        2. 项目处于早期阶段，安全性待改进
                        3. 全自动模式会大量消耗资源，请谨慎使用
                        """)

                # 定时扫描标签页
                with gr.Tab("定时扫描"):
                    with gr.Group():
                        scan_interval = gr.Radio(
                            choices=[1, 4, 8, 24],
                            label="扫描间（小时）",
                            value=saved_state.get("scan_interval", 1)
                        )
                        scanner_active = gr.Checkbox(
                            label="启用扫描器",
                            value=saved_state.get("scanner_active", False)
                        )
                        scanner_status = gr.Textbox(
                            label="扫描器状态",
                            interactive=False
                        )
                        gr.Markdown("""
                        ### 扫描内容
                        1. 资源状态检查
                        2. 项目文件结构
                        3. 运行状态监控
                        """)

                # 主对话界面标签页
                with gr.Tab("AI对话"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            input_prompt = gr.Textbox(
                                label="输入提示词",
                                placeholder="请输入您的指令...",
                                lines=3
                            )
                            with gr.Row():
                                submit_btn = gr.Button("提交")
                                reset_btn = gr.Button("重置对话")
                            
                            # 添加新的按钮组
                            with gr.Row():
                                resource_plan_btn = gr.Button(
                                    "📊 基于资源执行",
                                    variant="secondary"
                                )
                                goal_plan_btn = gr.Button(
                                    "🎯 基于目标执行",
                                    variant="secondary"
                                )
                            
                            command_input = gr.Textbox(
                                label="令输入",
                                placeholder="输入要执行的命令...",
                                lines=2,
                                visible=lambda: self.execution_mode == "手动档"
                            )
                            execute_btn = gr.Button(
                                "执行命令",
                                visible=lambda: self.execution_mode == "手动档"
                            )
                            
                            # 添加说明文本
                            gr.Markdown("""
                            ### 执行方式说明
                            1. 📊 基于资源执行：
                               - 分析当前可用资源
                               - 制定最优化方案
                               - 自动执行赚钱计划
                            
                            2. 🎯 基于目标执行：
                               - 分析目标和创意
                               - 制定实现方案
                               - 自动执行计划步骤
                            """)
                        
                        with gr.Column(scale=2):
                            optimized_prompt = gr.Textbox(
                                label="优化后的提示词",
                                lines=3,
                                interactive=False
                            )
                            ai_response = gr.Textbox(
                                label="AI响应",
                                lines=5,
                                interactive=False
                            )
                            execution_status = gr.Textbox(
                                label="执行状态",
                                interactive=False
                            )
                            chat_history = gr.Textbox(
                                label="对话历史",
                                lines=10,
                                interactive=False
                            )

                # 赚钱目标标签页
                with gr.Tab("赚钱目标"):
                    with gr.Group():
                        money_goal = gr.Textbox(
                            label="赚钱目标",
                            placeholder="请输入您的赚钱目标...",
                            lines=3,
                            value=saved_state.get("last_money_goal", "")
                        )
                        money_idea = gr.Textbox(
                            label="创意想法",
                            placeholder="请输入您的创意想法...",
                            lines=3,
                            value=saved_state.get("last_money_idea", "")
                        )
                        save_goal_btn = gr.Button("保存目标")
                        goal_status = gr.Textbox(
                            label="保存状态",
                            interactive=False
                        )
                        gr.Markdown("""
                        ### 提示
                        1. 明确的目标有助于AI制定更精准的方案
                        2. 创意想法可以帮助AI拓展思路
                        3. 目标应该是具体、可衡量的
                        """)

                # API配置标签页
                with gr.Tab("API配置"):
                    with gr.Group():
                        api_name = gr.Textbox(
                            label="API名称",
                            placeholder="给这个API起个名字...",
                            value=saved_state.get("last_api_name", "")
                        )
                        api_key = gr.Textbox(
                            label="API密钥",
                            type="password",
                            placeholder="输入API密钥..."
                        )
                        api_url = gr.Textbox(
                            label="API地址",
                            placeholder="输��API的URL地址..."
                        )
                        with gr.Row():
                            save_api_btn = gr.Button("保存API")
                            check_usage_btn = gr.Button("查看使用情况")
                        api_status = gr.Textbox(
                            label="API状态",
                            interactive=False
                        )
                        gr.Markdown("""
                        ### 安全提示
                        1. API密钥将被加密存储
                        2. 定期更换API密钥以提高安全性
                        3. 请勿分享您的API密钥
                        """)

                # 系统环境标签页
                with gr.Tab("系统环境"):
                    with gr.Group():
                        system_env = gr.Radio(
                            choices=["Windows", "Linux", "macOS"],
                            label="系统环境",
                            value=saved_state.get("system_env", platform.system())
                        )
                        env_status = gr.Textbox(
                            label="环境状态",
                            interactive=False
                        )
                        gr.Markdown("""
                        ### 系统环境说明
                        1. Windows环境：
                           - 自动转换Linux命令为Windows命令
                           - 使用Windows特定的路径格式
                           - 适配Windows特有的系统调用
                        
                        2. Linux环境：
                           - 使用原生Linux命令
                           - 使用Linux路径格式
                           - 支持更多系统级操作
                        
                        3. macOS环境：
                           - 使用Unix风格命令
                           - 支持homebrew包管理
                           - 适配macOS特有功能
                        
                        ### 注意事项
                        - 请选择与实际运行环境相匹配的系统类型
                        - 系统环境的变更会影响命令的执行方式
                        - 某些功能在不同系统环境下可能有所差异
                        """)

            # 事件处理
            save_btn.click(
                fn=lambda t, n, v: (
                    self.save_resource_info(t, n, v),
                    self.get_saved_resources()
                ),
                inputs=[resource_type, resource_name, resource_value],
                outputs=[resource_status, resource_list]
            )
            
            risk_level.change(
                fn=self.update_risk_level,
                inputs=[risk_level],
                outputs=[risk_status]
            )
            
            execution_mode.change(
                fn=self.update_execution_mode,
                inputs=[execution_mode],
                outputs=[gr.Textbox(label="执行状态")]
            )
            
            scan_interval.change(
                fn=self.update_scan_interval,
                inputs=[scan_interval],
                outputs=[scanner_status]
            )
            
            scanner_active.change(
                fn=self.toggle_scanning,
                inputs=[scanner_active],
                outputs=[scanner_status]
            )
            
            # 对话相关事件处理
            submit_btn.click(
                fn=self.process_input,
                inputs=[input_prompt, chat_history],
                outputs=[optimized_prompt, ai_response, execution_status, chat_history]
            )
            
            reset_btn.click(
                fn=lambda: ("", "", "对话已重置", ""),
                inputs=[],
                outputs=[input_prompt, optimized_prompt, execution_status, chat_history]
            )
            
            execute_btn.click(
                fn=self.execute_command,
                inputs=[command_input, chat_history],
                outputs=[execution_status, chat_history]
            )

            save_goal_btn.click(
                fn=self.save_money_goal,
                inputs=[money_goal, money_idea],
                outputs=[goal_status]
            )

            save_api_btn.click(
                fn=self.save_api_config,
                inputs=[api_name, api_key, api_url],
                outputs=[api_status]
            )

            check_usage_btn.click(
                fn=self.get_api_usage,
                inputs=[api_name],
                outputs=[api_status]
            )

            system_env.change(
                fn=self.update_system_env,
                inputs=[system_env],
                outputs=[env_status]
            )

            resource_plan_btn.click(
                fn=self.execute_money_plan_by_resources,
                inputs=[chat_history],
                outputs=[optimized_prompt, ai_response, execution_status, chat_history]
            )
            
            goal_plan_btn.click(
                fn=self.execute_money_plan_by_goals,
                inputs=[chat_history],
                outputs=[optimized_prompt, ai_response, execution_status, chat_history]
            )

            refresh_btn.click(
                fn=self.get_saved_resources,
                inputs=[],
                outputs=[resource_list]
            )

        return interface

if __name__ == "__main__":
    assistant = Free_AI_Docker()
    interface = assistant.create_interface()
    interface.launch(server_name="0.0.0.0", server_port=7860)