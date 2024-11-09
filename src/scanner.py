import schedule
import time
import os
import json
from datetime import datetime
from typing import Dict, List
from resource_manager import ResourceManager
import logging

logger = logging.getLogger(__name__)

class SystemScanner:
    def __init__(self, resource_manager: ResourceManager):
        self.resource_manager = resource_manager
        self.scan_interval = 1  # 默认1小时
        self.is_running = False
        self.last_scan_time = None
        
    def set_scan_interval(self, hours: int) -> str:
        """设置扫描间隔"""
        if hours not in [1, 4, 8, 24]:
            return "❌ 无效的扫描间隔"
        self.scan_interval = hours
        return f"✅ 扫描间隔已设置为 {hours} 小时"

    def scan_project_structure(self) -> Dict:
        """扫描项目结构"""
        project_info = {
            "files": [],
            "directories": [],
            "last_scan": datetime.now().isoformat()
        }
        
        for root, dirs, files in os.walk("."):
            project_info["directories"].extend(dirs)
            project_info["files"].extend(
                [os.path.join(root, file) for file in files]
            )
            
        return project_info

    def scan_resources(self) -> Dict:
        """扫描资源状态"""
        try:
            resources = {
                "api_keys": self.resource_manager.get_resource("API密钥"),
                "wallets": self.resource_manager.get_resource("钱包地址"),
                "accounts": self.resource_manager.get_resource("账号密码")
            }
            logger.info("Resource scan completed successfully")
            return resources
        except Exception as e:
            logger.error(f"Error scanning resources: {str(e)}")
            return {
                "api_keys": {},
                "wallets": {},
                "accounts": {}
            }

    def format_scan_result(self, scan_result: Dict) -> str:
        """格式化扫描结果"""
        result = []
        result.append(f"扫描时间: {scan_result['timestamp']}")
        
        # 添加资源状态
        resources = scan_result['resources']
        result.append("\n资源状态:")
        for resource_type, resource_data in resources.items():
            if resource_data:
                result.append(f"- {resource_type}: {len(resource_data)} 个资源")
        
        # 添加项目结构信息
        structure = scan_result['project_structure']
        result.append("\n项目结构:")
        result.append(f"- 文件数量: {len(structure['files'])}")
        result.append(f"- 目录数量: {len(structure['directories'])}")
        
        return "\n".join(result)

    def perform_scan(self) -> Dict:
        """执行完整扫描"""
        try:
            scan_result = {
                "timestamp": datetime.now().isoformat(),
                "project_structure": self.scan_project_structure(),
                "resources": self.scan_resources()
            }
            
            # 格式化并记录扫描结果
            formatted_result = self.format_scan_result(scan_result)
            logger.info(f"Scan completed:\n{formatted_result}")
            
            self.last_scan_time = datetime.now()
            return scan_result
        except Exception as e:
            logger.error(f"Scan failed: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "failed"
            }

    def start_scanning(self):
        """启动定时扫描"""
        if self.is_running:
            return "扫描器已在运行"
            
        schedule.every(self.scan_interval).hours.do(self.perform_scan)
        self.is_running = True
        
        # 立即执行一次扫描
        self.perform_scan()
        
        return f"扫描器已启动，间隔: {self.scan_interval}小时"

    def stop_scanning(self):
        """停止定时扫描"""
        schedule.clear()
        self.is_running = False
        return "扫描器已停止" 