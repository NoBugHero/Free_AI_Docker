from encryption import Encryption
from security_config import SecurityConfig
import json
import os
from logger import logger
import re

class ResourceManager:
    def __init__(self):
        self.encryption = Encryption()
        self.resources_file = "resources.enc"
    
    def save_resource(self, resource_type: str, resource_data: dict):
        """安全保存资源信息"""
        try:
            # 获取现有的资源
            resources = self.get_all_resources()
            
            # 如果这个类型的资源不存在，创建一个新的字典
            if resource_type not in resources:
                resources[resource_type] = {}
            
            # 添加或更新资源
            if isinstance(resource_data, dict) and 'name' in resource_data:
                name = resource_data['name']
                resources[resource_type][name] = resource_data
            else:
                logger.error(f"Invalid resource data format: {resource_data}")
                raise ValueError("Resource data must contain 'name' field")

            # 加密并保存所有资源
            encrypted_data = self.encryption.encrypt(json.dumps(resources))
            with open(self.resources_file, 'w') as f:
                f.write(encrypted_data)
                
            logger.info(f"Resource saved successfully: {resource_type}")
        except Exception as e:
            logger.error(f"Failed to save resource: {str(e)}")
            raise
    
    def get_all_resources(self) -> dict:
        """获取所有资源"""
        try:
            if not os.path.exists(self.resources_file):
                return {}
                
            with open(self.resources_file, 'r') as f:
                data = f.read().strip()
                if not data:
                    return {}
                return json.loads(self.encryption.decrypt(data))
        except Exception as e:
            logger.error(f"Failed to get all resources: {str(e)}")
            return {}
    
    def get_resource(self, resource_type: str) -> dict:
        """获取指定类型的资源"""
        try:
            resources = self.get_all_resources()
            return resources.get(resource_type, {})
        except Exception as e:
            logger.error(f"Error reading resource: {str(e)}")
            return {}
    
    def validate_resource_format(self, resource_type: str, resource_data: dict) -> bool:
        """验证资源格式"""
        required_fields = {
            "API密钥": ["name", "value", "type", "created_at"],
            "钱包地址": ["name", "value", "type", "created_at", "network"],
            "账号密码": ["name", "value", "type", "created_at", "platform"],
            "其他资源": ["name", "value", "type", "created_at", "description"]
        }
        
        # 检查必需字段
        if resource_type not in required_fields:
            return False
            
        for field in required_fields[resource_type]:
            if field not in resource_data:
                return False
                
        # 验证字段格式
        if not re.match(SecurityConfig.RESOURCE_VALIDATORS[resource_type], 
                       resource_data["value"]):
            return False
            
        return True