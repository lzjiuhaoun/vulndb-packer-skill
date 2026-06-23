"""
日志记录器模块
记录skill执行过程和结果
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional


class Logger:
    """日志记录器"""
    
    def __init__(self, log_file: Optional[str] = None, level: int = logging.INFO):
        """
        初始化日志记录器
        
        Args:
            log_file: 日志文件路径（可选）
            level: 日志级别
        """
        self.logger = logging.getLogger("vulndb-packer")
        self.logger.setLevel(level)
        
        # 清除现有的处理器
        self.logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器（如果指定了日志文件）
        if log_file:
            self._setup_file_handler(log_file, formatter, level)
        
        self.execution_start_time = None
        
    def _setup_file_handler(self, log_file: str, formatter: logging.Formatter, level: int):
        """设置文件处理器"""
        try:
            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.warning(f"无法创建日志文件 {log_file}: {e}")
    
    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
    
    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
    
    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
    
    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)
    
    def log_execution_start(self, inputs: dict):
        """
        记录执行开始
        
        Args:
            inputs: 输入参数字典
        """
        self.execution_start_time = datetime.now()
        self.info("=" * 50)
        self.info("漏洞库升级包制作开始")
        self.info("=" * 50)
        self.info(f"开始时间: {self.execution_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.info("")
        self.info("输入参数:")
        for key, value in inputs.items():
            if isinstance(value, list):
                self.info(f"  {key}:")
                for item in value:
                    self.info(f"    - {item}")
            else:
                self.info(f"  {key}: {value}")
        self.info("")
    
    def log_step(self, step: int, description: str, status: str = "开始"):
        """
        记录处理步骤
        
        Args:
            step: 步骤编号
            description: 步骤描述
            status: 状态
        """
        self.info(f"[步骤 {step}] {description}... {status}")
    
    def log_execution_end(self, result: dict):
        """
        记录执行结束
        
        Args:
            result: 执行结果字典
        """
        end_time = datetime.now()
        duration = None
        if self.execution_start_time:
            duration = end_time - self.execution_start_time
        
        self.info("")
        self.info("=" * 50)
        self.info("执行结果")
        self.info("=" * 50)
        
        for key, value in result.items():
            if isinstance(value, list):
                self.info(f"{key}:")
                for item in value:
                    self.info(f"  - {item}")
            else:
                self.info(f"{key}: {value}")
        
        self.info("")
        self.info(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if duration:
            self.info(f"执行时长: {duration.total_seconds():.2f} 秒")
        self.info("=" * 50)
    
    def log_error(self, error: Exception, context: str = ""):
        """
        记录错误
        
        Args:
            error: 异常对象
            context: 错误上下文
        """
        self.error(f"错误: {context}")
        self.error(f"类型: {type(error).__name__}")
        self.error(f"详情: {str(error)}")
