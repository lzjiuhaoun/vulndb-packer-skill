"""
VulnDB Packer 主入口脚本
漏洞库升级包制作工具
"""

import argparse
import os
import sys
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logger import Logger
from sql_parser import MySQLParser, MySQLError
from sql_converter import SQLConverter, SQLConverterError
from mysql_to_dm8 import convert as mysql_to_dm8_convert
from excel_reader import ExcelReader, ExcelReadError
from excel_extractor import VulnChangeExtractor, VulnChangeExtractorError
from package_builder import PackageBuilder, PackageBuilderError
from report_generator import ReportGenerator, ReportGeneratorError


class VulnDBPacker:
    """漏洞库升级包制作工具"""
    
    def __init__(self, output_dir: str = ".", log_file: Optional[str] = None):
        """
        初始化工具
        
        Args:
            output_dir: 输出目录
            log_file: 日志文件路径（可选）
        """
        self.output_dir = output_dir
        
        # 初始化日志记录器
        self.logger = Logger(log_file)
        
        # 初始化各个模块
        self.sql_parser = MySQLParser()
        self.sql_converter = SQLConverter()
        self.excel_reader = None
        self.excel_extractor = VulnChangeExtractor()
        self.package_builder = PackageBuilder(output_dir)
        self.report_generator = ReportGenerator()
        
    def run(self, mysql_sql_path: str, excel_files: List[str], 
            current_version: str, new_version: str) -> Dict[str, Any]:
        """
        执行升级包制作
        
        Args:
            mysql_sql_path: MySQL SQL文件路径
            excel_files: Excel文件路径列表
            current_version: 当前版本号
            new_version: 新版本号
            
        Returns:
            {
                "zip_path": "zip文件路径",
                "report": "变化说明",
                "success": True/False,
                "error": "错误信息"（如果有）
            }
        """
        # 记录执行开始
        inputs = {
            "MySQL SQL文件": mysql_sql_path,
            "Excel文件": excel_files,
            "当前版本": current_version,
            "新版本": new_version,
            "输出目录": self.output_dir
        }
        self.logger.log_execution_start(inputs)
        
        try:
            # 步骤1: 验证输入文件
            self.logger.log_step(1, "验证输入文件")
            self._validate_inputs(mysql_sql_path, excel_files, current_version, new_version)
            self.logger.log_step(1, "验证输入文件", "完成")
            
            # 步骤2: 读取Excel文件
            self.logger.log_step(2, "读取Excel文件")
            excel_data = self._read_excel_files(excel_files)
            self.logger.log_step(2, "读取Excel文件", "完成")
            
            # 步骤3: 提取漏洞变化信息
            self.logger.log_step(3, "提取漏洞变化信息")
            changes = self.excel_extractor.extract_changes(excel_data)
            date_range = self.excel_extractor.extract_date_range(excel_data, excel_files)
            self.logger.log_step(3, "提取漏洞变化信息", "完成")
            
            # 步骤4: 生成变化说明
            self.logger.log_step(4, "生成变化说明")
            report = self.report_generator.generate_report(
                changes, date_range, current_version, new_version
            )
            self.logger.log_step(4, "生成变化说明", "完成")
            
            # 步骤5: 读取MySQL SQL
            self.logger.log_step(5, "读取MySQL SQL")
            mysql_sql_content = self._read_file(mysql_sql_path)
            self.logger.log_step(5, "读取MySQL SQL", "完成")
            
            # 步骤6: 转换为达梦8 SQL
            self.logger.log_step(6, "转换为达梦8 SQL")
            dm_sql_content = self._convert_to_dm8(mysql_sql_path)
            self.logger.log_step(6, "转换为达梦8 SQL", "完成")
            
            # 步骤7: 生成升级包
            self.logger.log_step(7, "生成升级包")
            zip_path = self._build_package(
                mysql_sql_content, dm_sql_content, 
                current_version, new_version, report
            )
            self.logger.log_step(7, "生成升级包", "完成")
            
            # 步骤8: 验证升级包
            self.logger.log_step(8, "验证升级包")
            self._verify_package(zip_path)
            self.logger.log_step(8, "验证升级包", "完成")
            
            # 记录执行结束
            result = {
                "zip_path": zip_path,
                "report": report,
                "success": True
            }
            self.logger.log_execution_end(result)
            
            return result
            
        except Exception as e:
            # 记录错误
            self.logger.log_error(e, "执行过程中发生错误")
            
            # 返回错误结果
            result = {
                "zip_path": None,
                "report": None,
                "success": False,
                "error": str(e)
            }
            self.logger.log_execution_end(result)
            
            return result
        
        finally:
            # 关闭Excel读取器
            if self.excel_reader:
                self.excel_reader.close()
    
    def _validate_inputs(self, mysql_sql_path: str, excel_files: List[str], 
                        current_version: str, new_version: str):
        """
        验证输入文件和版本号
        
        Args:
            mysql_sql_path: MySQL SQL文件路径
            excel_files: Excel文件路径列表
            current_version: 当前版本号
            new_version: 新版本号
        """
        # 验证MySQL SQL文件
        if not os.path.exists(mysql_sql_path):
            raise FileNotFoundError(f"MySQL SQL文件不存在: {mysql_sql_path}")
        
        # 验证Excel文件
        for excel_file in excel_files:
            if not os.path.exists(excel_file):
                raise FileNotFoundError(f"Excel文件不存在: {excel_file}")
            
            # 验证文件扩展名
            if not excel_file.lower().endswith((".xls", ".xlsx")):
                raise ValueError(f"不支持的Excel文件格式: {excel_file}")
        
        # 验证版本号格式
        self._validate_version_format(current_version, "当前版本")
        self._validate_version_format(new_version, "新版本")
        
        # 验证版本号大小关系
        if not self._is_version_greater(new_version, current_version):
            raise ValueError(f"新版本号({new_version})必须大于当前版本号({current_version})")
    
    def _validate_version_format(self, version: str, version_name: str):
        """
        验证版本号格式
        
        Args:
            version: 版本号
            version_name: 版本名称（用于错误提示）
            
        Raises:
            ValueError: 版本号格式不正确
        """
        import re
        # 版本号格式：Vx.y.z.w，其中x,y,z,w都是数字
        pattern = r'^V\d+\.\d+\.\d+\.\d+$'
        if not re.match(pattern, version):
            raise ValueError(f"{version_name}格式不正确，必须是Vx.y.z.w格式（如V1.0.2.19），当前值：{version}")
    
    def _is_version_greater(self, version1: str, version2: str) -> bool:
        """
        比较两个版本号的大小
        
        Args:
            version1: 版本号1
            version2: 版本号2
            
        Returns:
            version1 > version2 返回True，否则返回False
        """
        # 移除V前缀，分割版本号
        v1_parts = version1[1:].split('.')
        v2_parts = version2[1:].split('.')
        
        # 逐段比较
        for i in range(4):
            v1_num = int(v1_parts[i])
            v2_num = int(v2_parts[i])
            if v1_num > v2_num:
                return True
            elif v1_num < v2_num:
                return False
        
        # 所有段都相等
        return False
    
    def _read_excel_files(self, excel_files: List[str]) -> Dict[str, Any]:
        """读取Excel文件"""
        try:
            # 初始化Excel读取器
            self.excel_reader = ExcelReader()
            
            # 将相对路径转换为绝对路径（COM接口需要绝对路径）
            absolute_excel_files = [os.path.abspath(f) for f in excel_files]
            
            # 批量读取Excel文件
            result = self.excel_reader.read_multiple_excels(absolute_excel_files)
            
            # 检查是否有失败的文件
            if result["failed"]:
                failed_files = [f["path"] for f in result["failed"]]
                self.logger.warning(f"以下Excel文件读取失败: {failed_files}")
            
            # 如果没有成功读取的文件，抛出异常
            if not result["success"]:
                raise ExcelReadError("", "所有Excel文件读取失败")
            
            return result
            
        except Exception as e:
            if isinstance(e, ExcelReadError):
                raise
            raise ExcelReadError("", f"读取Excel文件失败: {str(e)}")
    
    def _read_file(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except Exception as e:
                raise MySQLError(f"读取SQL文件失败: {str(e)}")
        except Exception as e:
            raise MySQLError(f"读取SQL文件失败: {str(e)}")
    
    def _convert_to_dm8(self, mysql_sql_path: str) -> str:
        """
        使用 mysql_to_dm8.py 将MySQL SQL转换为达梦8 SQL
        
        Args:
            mysql_sql_path: MySQL SQL文件路径
            
        Returns:
            达梦8 SQL内容
        """
        try:
            # 创建临时文件用于存储转换结果
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, encoding='utf-8') as tmp:
                tmp_path = tmp.name
            
            # 调用 mysql_to_dm8 的 convert 函数
            mysql_to_dm8_convert(mysql_sql_path, tmp_path)
            
            # 读取转换结果
            with open(tmp_path, 'r', encoding='utf-8') as f:
                dm_sql_content = f.read()
            
            # 删除临时文件
            os.unlink(tmp_path)
            
            return dm_sql_content
            
        except Exception as e:
            raise SQLConverterError(f"转换为达梦8 SQL失败: {str(e)}")
    
    def _build_package(self, mysql_sql_content: str, dm_sql_content: str,
                      current_version: str, new_version: str, report: str = "") -> str:
        """构建升级包"""
        config = {
            "mysql_sql_content": mysql_sql_content,
            "dm_sql_content": dm_sql_content,
            "new_version": new_version,
            "current_version": current_version,
            "output_dir": self.output_dir,
            "report": report
        }
        
        return self.package_builder.build_package(config)
    
    def _verify_package(self, zip_path: str):
        """
        验证升级包是否存在
        
        Args:
            zip_path: zip文件路径
            
        Raises:
            FileNotFoundError: 升级包不存在
        """
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"升级包文件不存在: {zip_path}")
        
        # 检查文件大小
        file_size = os.path.getsize(zip_path)
        if file_size == 0:
            raise ValueError(f"升级包文件为空: {zip_path}")
        
        self.logger.info(f"升级包验证通过: {zip_path} (大小: {file_size} 字节)")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="漏洞库升级包制作工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --mysql-sql va_library.sql --excel-files 2026-05漏扫数据库变化.xlsx --current-version V1.0.2.19 --new-version V1.0.2.20
  python main.py --mysql-sql va_library.sql --excel-files 2026-05漏扫数据库变化.xlsx 2026-04漏扫数据库变化.xlsx --current-version V1.0.2.19 --new-version V1.0.2.20 --output-dir output
        """
    )
    
    parser.add_argument(
        "--mysql-sql",
        required=True,
        help="MySQL SQL脚本文件路径"
    )
    
    parser.add_argument(
        "--excel-files",
        required=True,
        nargs="+",
        help="Excel文件路径列表"
    )
    
    parser.add_argument(
        "--current-version",
        required=True,
        help="当前漏洞库版本号"
    )
    
    parser.add_argument(
        "--new-version",
        required=True,
        help="新漏洞库版本号"
    )
    
    parser.add_argument(
        "--output-dir",
        default=".",
        help="输出目录（默认当前目录）"
    )
    
    parser.add_argument(
        "--log-file",
        help="日志文件路径（可选）"
    )
    
    args = parser.parse_args()
    
    try:
        # 创建工具实例
        packer = VulnDBPacker(
            output_dir=args.output_dir,
            log_file=args.log_file
        )
        
        # 执行升级包制作
        result = packer.run(
            mysql_sql_path=args.mysql_sql,
            excel_files=args.excel_files,
            current_version=args.current_version,
            new_version=args.new_version
        )
        
        # 输出结果
        if result["success"]:
            print("\n" + "=" * 50)
            print("执行成功!")
            print("=" * 50)
            print(f"升级包路径: {result['zip_path']}")
            print(f"\n变化说明:\n{result['report']}")
            print("=" * 50)
            sys.exit(0)
        else:
            print("\n" + "=" * 50)
            print("执行失败!")
            print("=" * 50)
            print(f"错误信息: {result['error']}")
            print("=" * 50)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
