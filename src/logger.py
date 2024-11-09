import logging
from datetime import datetime
import json
import time

# 添加错误类型定义
class FreeAIDockerError(Exception):
    """基础错误类"""
    pass

class ResourceError(FreeAIDockerError):
    """资源相关错误"""
    pass

class SecurityError(FreeAIDockerError):
    """安全相关错误"""
    pass

class CommandError(FreeAIDockerError):
    """命令执行错误"""
    pass

def setup_logger():
    logging.basicConfig(
        filename=f'logs/free_ai_docker_{datetime.now().strftime("%Y%m%d")}.log',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger('FreeAIDocker')

logger = setup_logger()

# 在 logger.py 中添加错误处理
def log_error(error: Exception, context: dict = None):
    """统一的错误日志记录"""
    error_info = {
        "type": type(error).__name__,
        "message": str(error),
        "context": context or {},
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    logger.error(f"Error occurred: {json.dumps(error_info, ensure_ascii=False)}") 