from cryptography.fernet import Fernet
from security_config import SecurityConfig
import base64

class Encryption:
    def __init__(self):
        self.cipher_suite = Fernet(SecurityConfig.ENCRYPTION_KEY)
    
    def encrypt(self, data: str) -> str:
        """加密数据"""
        if not data:
            return ""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        if not encrypted_data:
            return ""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def mask_sensitive_data(self, data: str) -> str:
        """数据脱敏"""
        if not data or len(data) < 8:
            return "****"
        return data[:4] + "*" * (len(data) - 4) 