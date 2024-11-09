from cryptography.fernet import Fernet
import os
from datetime import datetime, timedelta

class SecurityConfig:
    # 加密密钥管理
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', Fernet.generate_key())
    
    # 安全策略配置
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_COMPLEXITY = True
    SESSION_TIMEOUT = timedelta(hours=1)
    
    # API访问控制
    API_RATE_LIMIT = 100  # 每小时请求次数限制
    API_KEY_EXPIRY = timedelta(days=30)
    
    # 日志配置
    SENSITIVE_FIELDS = ['password', 'api_key', 'wallet_address', 'private_key']
    LOG_RETENTION_DAYS = 30 
    
    # 添加资源类型的明确定义
    RESOURCE_TYPES = {
        "API密钥": "api_keys",
        "钱包地址": "wallets",
        "账号密码": "accounts",
        "其他资源": "others"
    }
    
    # 添加每种资源类型的验证规则
    RESOURCE_VALIDATORS = {
        "API密钥": r"^[A-Za-z0-9\-_]{20,}$",  # API密钥格式验证
        "钱包地址": r"^(0x)?[A-Fa-f0-9]{40}$",  # ETH钱包地址格式
        "账号密码": r".{8,}",  # 至少8个字符
        "其他资源": r".*"  # 任意格式
    }
    
    # 添加风险等级定义
    RISK_LEVELS = {
        "低风险": {
            "max_loss_percentage": 20,
            "description": "保守型投资，最大损失20%资源",
            "allowed_operations": ["查询", "分析", "小额交易"]
        },
        "中风险": {
            "max_loss_percentage": 60,
            "description": "平衡型投资，最大损失60%资源",
            "allowed_operations": ["查询", "分析", "交易", "杠杆"]
        },
        "高风险": {
            "max_loss_percentage": 100,
            "description": "激进型投资，可能损失全部资源",
            "allowed_operations": ["查询", "分析", "交易", "杠杆", "期权"]
        }
    }
    
    # 添加执行模式定义
    EXECUTION_MODES = {
        "手动档": {
            "requires_confirmation": True,
            "auto_execute": False,
            "description": "每个操作都需要用户确认"
        },
        "全自动": {
            "requires_confirmation": False,
            "auto_execute": True,
            "description": "AI自动执行所有操作",
            "warning": "可能消耗大量资源，请谨慎使用"
        }
    }
    
    # 添加扫描间隔定义
    SCAN_INTERVALS = {
        1: {
            "description": "每小时扫描",
            "resource_impact": "高",
            "recommended_for": "高风险环境"
        },
        4: {
            "description": "每4小时扫描",
            "resource_impact": "中",
            "recommended_for": "一般环境"
        },
        8: {
            "description": "每8小时扫描",
            "resource_impact": "低",
            "recommended_for": "稳定环境"
        },
        24: {
            "description": "每天扫描",
            "resource_impact": "最低",
            "recommended_for": "低风险环境"
        }
    }
    
    # 添加命令验证规则
    COMMAND_VALIDATION = {
        "max_length": 1000,  # 命令最大长度
        "max_arguments": 10,  # 最大参数数量
        "forbidden_patterns": [
            r"rm\s+-rf\s+[/\\]",  # 删除根目录
            r">(>)?[/\\]dev[/\\]",  # 写入设备文件
            r"mkfs\.",  # 格式化命令
            r":(){",  # Fork炸弹
            r"sudo\s+su",  # 提权命令
        ],
        "required_patterns": {
            "file_operations": r"^(在项目目录下)",  # 文件操作必须指定在项目目录下
            "network_operations": r"^(使用安全连接)"  # 网络操作必须使用安全连接
        }
    }