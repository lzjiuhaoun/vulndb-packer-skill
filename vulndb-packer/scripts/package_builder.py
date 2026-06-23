"""
升级包构建器模块
生成升级包的所有文件并打包
"""

import os
import zipfile
from datetime import datetime
from typing import Dict, List, Any, Optional


class PackageBuilderError(Exception):
    """升级包构建错误"""
    pass


# MySQL表结构定义
MYSQL_TABLE_HEADER = """DROP TABLE IF EXISTS `va_library`;
CREATE TABLE `va_library`  (
  `va_id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `va_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '漏洞名称',
  `va_time` datetime(0) NULL DEFAULT NULL COMMENT '漏洞发布时间',
  `db_type` tinyint(2) NOT NULL COMMENT '漏洞数据库类型',
  `va_type` tinyint(1) NOT NULL COMMENT '漏洞类型',
  `va_rule` longtext CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '漏洞检查规则',
  `va_check_way` tinyint(1) NULL DEFAULT NULL COMMENT '漏洞检查方式 1jdbc查询 2对比版本',
  `va_desc` longtext CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '漏洞描述',
  `va_sql` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '漏洞sql修复语句',
  `va_level` tinyint(1) NOT NULL COMMENT '漏洞级别',
  `va_verify` tinyint(1) NULL DEFAULT NULL COMMENT '漏洞校验方式 1-YES_NO  2-RESULT_SET  3-PROCEDURE 4-UNIX_YES_NO',
  `va_suggest` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL COMMENT '漏洞修复建议',
  `va_cve` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '漏洞cve号',
  `va_cnnvd` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '漏洞cnnvd号',
  `va_db_version` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '漏洞影响的DB版本',
  `va_lib_version` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL DEFAULT '' COMMENT '漏洞库版本',
  `public_poc_exp` tinyint(1) NOT NULL DEFAULT 0 COMMENT '此漏洞是否有公开的poc或exp，0代表无，1代表有',
  PRIMARY KEY (`va_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '漏洞库信息表' ROW_FORMAT = Dynamic;
"""


class PackageBuilder:
    """升级包构建器"""
    
    def __init__(self, output_dir: str = "."):
        """
        初始化构建器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        self.today = datetime.now().strftime("%Y%m%d")
        
    def build_package(self, config: Dict[str, Any]) -> str:
        """
        构建升级包
        
        Args:
            config: {
                "mysql_sql_content": "MySQL SQL内容",
                "dm_sql_content": "达梦8 SQL内容",
                "new_version": "V1.0.2.20",
                "current_version": "V1.0.2.19",
                "output_dir": "输出目录"（可选）
            }
            
        Returns:
            zip文件路径
            
        Raises:
            PackageBuilderError: 构建错误
        """
        try:
            # 获取配置
            mysql_sql_content = config.get("mysql_sql_content", "")
            dm_sql_content = config.get("dm_sql_content", "")
            new_version = config.get("new_version", "")
            current_version = config.get("current_version", "")
            output_dir = config.get("output_dir", self.output_dir)
            report = config.get("report", "")
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成文件内容
            source_txt = self.generate_source_txt(new_version)
            
            # 生成带表结构的MySQL SQL脚本
            mysql_sql_with_header = self.generate_mysql_sql(mysql_sql_content)
            
            # 生成zip文件名
            zip_filename = self._generate_zip_filename()
            zip_path = os.path.join(output_dir, zip_filename)
            
            # 创建zip文件
            files = {
                "source.txt": source_txt,
                "va_library.sql": mysql_sql_with_header,
                "va_library_dm.sql": dm_sql_content
            }
            
            self.create_zip_package(files, zip_path)
            
            # 生成变化说明文件
            if report:
                report_filename = f"安全漏洞规则库变化说明_{new_version}.txt"
                report_path = os.path.join(output_dir, report_filename)
                with open(report_path, 'w', encoding='utf-8') as f:
                    f.write(report)
            
            return zip_path
            
        except Exception as e:
            if isinstance(e, PackageBuilderError):
                raise
            raise PackageBuilderError(f"构建升级包失败: {str(e)}")
    
    def generate_source_txt(self, version: str) -> str:
        """
        生成source.txt内容
        
        Args:
            version: 版本号
            
        Returns:
            source.txt内容
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        content = f"""# 漏洞库版本号
version: {version}

# 漏洞库版本发布日期
date: {today}"""
        
        return content
    
    def generate_mysql_sql(self, sql_content: str) -> str:
        """
        生成MySQL SQL脚本（带表结构定义）
        
        Args:
            sql_content: 原始SQL内容（INSERT语句）
            
        Returns:
            MySQL SQL脚本内容（包含表结构定义）
        """
        # 添加表结构定义头
        return MYSQL_TABLE_HEADER + sql_content
    
    def generate_dm_sql(self, dm_sql_content: str) -> str:
        """
        生成达梦8 SQL脚本
        
        Args:
            dm_sql_content: 达梦8 SQL内容
            
        Returns:
            达梦8 SQL脚本内容
        """
        return dm_sql_content
    
    def create_zip_package(self, files: Dict[str, str], output_path: str) -> str:
        """
        创建zip压缩包
        
        Args:
            files: {
                "source.txt": "内容",
                "va_library.sql": "内容",
                "va_library_dm.sql": "内容"
            }
            output_path: zip文件路径
            
        Returns:
            zip文件路径
        """
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename, content in files.items():
                    # 使用Unix(LF)换行符
                    content_lf = content.replace('\r\n', '\n').replace('\r', '\n')
                    
                    # 写入zip文件
                    zipf.writestr(filename, content_lf)
            
            return output_path
            
        except Exception as e:
            raise PackageBuilderError(f"创建zip文件失败: {str(e)}")
    
    def _generate_zip_filename(self) -> str:
        """
        生成zip文件名
        
        Returns:
            zip文件名，格式: VSLib{YYYYMMDD}_{序号}.zip
        """
        # 查找当天最大的序号
        max_seq = 0
        
        if os.path.exists(self.output_dir):
            for filename in os.listdir(self.output_dir):
                if filename.startswith(f"VSLib{self.today}_") and filename.endswith(".zip"):
                    try:
                        seq_str = filename[len(f"VSLib{self.today}_"):-4]
                        seq = int(seq_str)
                        max_seq = max(max_seq, seq)
                    except ValueError:
                        continue
        
        # 新序号
        new_seq = max_seq + 1
        
        return f"VSLib{self.today}_{new_seq:03d}.zip"
    
    def get_package_info(self, zip_path: str) -> Dict[str, Any]:
        """
        获取升级包信息
        
        Args:
            zip_path: zip文件路径
            
        Returns:
            升级包信息字典
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                file_list = zipf.namelist()
                file_sizes = {}
                
                for filename in file_list:
                    info = zipf.getinfo(filename)
                    file_sizes[filename] = info.file_size
                
                return {
                    "path": zip_path,
                    "filename": os.path.basename(zip_path),
                    "files": file_list,
                    "file_sizes": file_sizes,
                    "total_size": sum(file_sizes.values())
                }
                
        except Exception as e:
            raise PackageBuilderError(f"获取升级包信息失败: {str(e)}")
