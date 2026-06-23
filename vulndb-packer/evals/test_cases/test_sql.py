"""
VulnDB Packer 测试脚本
用于验证skill功能
"""

import os
import sys
import unittest

# 添加脚本目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(current_dir, '..', '..', 'scripts')
scripts_dir = os.path.abspath(scripts_dir)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

# 导入模块
try:
    from sql_parser import MySQLParser, MySQLError
    from sql_converter import SQLConverter, SQLConverterError
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"Python路径: {sys.path}")
    raise


class TestSQLParser(unittest.TestCase):
    """测试SQL解析器"""
    
    def setUp(self):
        """初始化测试"""
        self.parser = MySQLParser()
        
    def test_parse_insert_statements(self):
        """测试解析INSERT语句"""
        sql_content = """
        INSERT INTO `va_library` VALUES (1, 'CVE-2024-1234', '2024-01-15 10:30:00', 1, 1, 'check_rule_1', 1, 'MySQL权限提升漏洞', 'ALTER USER root IDENTIFIED BY new_password;', 3, 1, '建议升级MySQL到最新版本', 'CVE-2024-1234', 'CNNVD-202401-1234', 'MySQL 5.7', 'V1.0.2.19', 1);
        INSERT INTO `va_library` VALUES (2, 'CVE-2024-5678', '2024-02-20 14:15:00', 1, 2, 'check_rule_2', 2, 'Oracle SQL注入漏洞', 'SELECT * FROM v$version;', 2, 2, '建议应用Oracle补丁', 'CVE-2024-5678', 'CNNVD-202402-5678', 'Oracle 11g', 'V1.0.2.19', 1);
        """
        
        result = self.parser.parse(sql_content)
        
        self.assertEqual(result["table_name"], "va_library")
        self.assertEqual(len(result["insert_statements"]), 2)
        self.assertEqual(len(result["columns"]), 17)
        
    def test_parse_empty_sql(self):
        """测试解析空SQL"""
        sql_content = ""
        
        result = self.parser.parse(sql_content)
        
        self.assertEqual(len(result["insert_statements"]), 0)


class TestSQLConverter(unittest.TestCase):
    """测试SQL转换器"""
    
    def setUp(self):
        """初始化测试"""
        self.converter = SQLConverter()
        
    def test_generate_dm_header(self):
        """测试生成达梦8表结构头"""
        header = self.converter.generate_dm_header()
        
        self.assertIn('set define off;', header)
        self.assertIn('TRUNCATE TABLE "AAS_VS"."VA_LIBRARY";', header)
        self.assertIn('SET IDENTITY_INSERT "AAS_VS"."VA_LIBRARY" ON;', header)
        
    def test_generate_dm_footer(self):
        """测试生成达梦8表结构尾"""
        footer = self.converter.generate_dm_footer()
        
        self.assertIn('SET IDENTITY_INSERT "AAS_VS"."VA_LIBRARY" OFF;', footer)
        self.assertIn('commit;', footer)
        self.assertIn('exit;', footer)
        
    def test_convert_value(self):
        """测试转换值"""
        # 测试NULL值
        self.assertEqual(self.converter.convert_value(None, "va_id"), "NULL")
        
        # 测试字符串值
        self.assertEqual(self.converter.convert_value("test", "va_name"), "'test'")
        
        # 测试数值
        self.assertEqual(self.converter.convert_value(123, "va_id"), "123")
        
    def test_convert_insert_statement(self):
        """测试转换INSERT语句"""
        mysql_insert = {
            "values": [1, "CVE-2024-1234", "2024-01-15 10:30:00", 1, 1, "check_rule_1", 1, "MySQL权限提升漏洞", "ALTER USER root IDENTIFIED BY new_password;", 3, 1, "建议升级MySQL到最新版本", "CVE-2024-1234", "CNNVD-202401-1234", "MySQL 5.7", "V1.0.2.19", 1]
        }
        
        columns = ["va_id", "va_name", "va_time", "db_type", "va_type", "va_rule", "va_check_way", "va_desc", "va_sql", "va_level", "va_verify", "va_suggest", "va_cve", "va_cnnvd", "va_db_version", "va_lib_version", "public_poc_exp"]
        
        dm_insert = self.converter.convert_insert_statement(mysql_insert, columns)
        
        self.assertIn('INSERT INTO "AAS_VS"."VA_LIBRARY"', dm_insert)
        self.assertIn("'CVE-2024-1234'", dm_insert)
        self.assertIn("1", dm_insert)


if __name__ == "__main__":
    unittest.main()
