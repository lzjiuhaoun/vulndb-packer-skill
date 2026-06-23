"""
SQL转换器模块
将MySQL SQL转换为达梦8 SQL
"""

from typing import List, Dict, Any


class SQLConverterError(Exception):
    """SQL转换错误"""
    pass


class SQLConverter:
    """SQL转换器"""
    
    def __init__(self):
        """初始化转换器"""
        # 数据类型映射
        self.type_mapping = {
            "int": "BIGINT",
            "varchar": "VARCHAR",
            "datetime": "TIMESTAMP",
            "longtext": "CLOB",
            "text": "TEXT",
            "tinyint": "TINYINT"
        }
        
        # 达梦8表结构定义
        self.dm_table_name = '"AAS_VS"."VA_LIBRARY"'
        
    def convert_to_dm(self, mysql_data: Dict[str, Any]) -> str:
        """
        将MySQL数据转换为达梦8 SQL脚本
        
        Args:
            mysql_data: MySQLParser返回的数据
            
        Returns:
            达梦8 SQL脚本内容
            
        Raises:
            SQLConverterError: 转换错误
        """
        try:
            # 生成达梦8表结构头
            dm_header = self.generate_dm_header()
            
            # 生成INSERT语句
            dm_inserts = []
            for insert_stmt in mysql_data.get("insert_statements", []):
                dm_insert = self.convert_insert_statement(insert_stmt, mysql_data.get("columns", []))
                dm_inserts.append(dm_insert)
            
            # 组合完整的达梦8 SQL脚本
            dm_sql = self._combine_dm_sql(dm_header, dm_inserts)
            
            return dm_sql
            
        except Exception as e:
            if isinstance(e, SQLConverterError):
                raise
            raise SQLConverterError(f"SQL转换失败: {str(e)}")
    
    def generate_dm_header(self) -> str:
        """
        生成达梦8表结构头
        
        Returns:
            达梦8表结构SQL
        """
        header = """set define off;
TRUNCATE TABLE "AAS_VS"."VA_LIBRARY";
SET IDENTITY_INSERT "AAS_VS"."VA_LIBRARY" ON;
-- 数据插入SQL，一条数据一个insert语句"""
        return header
    
    def generate_dm_footer(self) -> str:
        """
        生成达梦8表结构尾
        
        Returns:
            达梦8表结构SQL
        """
        footer = """SET IDENTITY_INSERT "AAS_VS"."VA_LIBRARY" OFF;
commit;
exit;"""
        return footer
    
    def convert_insert_statement(self, mysql_insert: Dict[str, Any], columns: List[str]) -> str:
        """
        转换单条INSERT语句
        
        Args:
            mysql_insert: MySQL INSERT语句数据
            columns: 列名列表
            
        Returns:
            达梦8 INSERT语句
        """
        values = mysql_insert.get("values", [])
        
        # 如果没有列名，使用默认列名
        if not columns:
            columns = self._get_default_columns()
        
        # 确保列名和值的数量匹配
        if len(values) != len(columns):
            # 如果数量不匹配，尝试调整
            if len(values) > len(columns):
                # 值多于列名，截断值
                values = values[:len(columns)]
            else:
                # 值少于列名，用None填充
                values.extend([None] * (len(columns) - len(values)))
        
        # 转换列名为大写
        dm_columns = [col.upper() for col in columns]
        
        # 转换值
        dm_values = []
        for i, value in enumerate(values):
            column_name = columns[i] if i < len(columns) else f"COL_{i}"
            dm_value = self.convert_value(value, column_name)
            dm_values.append(dm_value)
        
        # 生成INSERT语句
        columns_str = ", ".join([f'"{col}"' for col in dm_columns])
        values_str = ", ".join(dm_values)
        
        return f'INSERT INTO {self.dm_table_name} ({columns_str}) VALUES ({values_str});'
    
    def convert_value(self, value: Any, column_name: str) -> str:
        """
        转换单个值
        
        Args:
            value: 原始值
            column_name: 字段名
            
        Returns:
            转换后的值
        """
        if value is None:
            return "NULL"
        
        # 字符串值
        if isinstance(value, str):
            # 转义单引号：' → ''（达梦8和MySQL都使用这种方式）
            escaped_value = value.replace("'", "''")
            return f"'{escaped_value}'"
        
        # 数值
        if isinstance(value, (int, float)):
            return str(value)
        
        # 其他类型转为字符串
        return f"'{str(value)}'"
    
    def _get_default_columns(self) -> List[str]:
        """获取默认列名"""
        return [
            "va_id",
            "va_name",
            "va_time",
            "db_type",
            "va_type",
            "va_rule",
            "va_check_way",
            "va_desc",
            "va_sql",
            "va_level",
            "va_verify",
            "va_suggest",
            "va_cve",
            "va_cnnvd",
            "va_db_version",
            "va_lib_version",
            "public_poc_exp"
        ]
    
    def _combine_dm_sql(self, header: str, inserts: List[str]) -> str:
        """组合完整的达梦8 SQL脚本"""
        parts = [header]
        parts.extend(inserts)
        parts.append(self.generate_dm_footer())
        
        # 使用Unix(LF)换行符
        return "\n".join(parts)
    
    def validate_conversion(self, mysql_data: Dict[str, Any], dm_sql: str) -> bool:
        """
        验证转换结果
        
        Args:
            mysql_data: MySQL数据
            dm_sql: 达梦8 SQL脚本
            
        Returns:
            True/False
        """
        try:
            # 检查INSERT语句数量
            mysql_insert_count = len(mysql_data.get("insert_statements", []))
            
            # 计算达梦8 SQL中的INSERT语句数量
            dm_insert_count = dm_sql.count("INSERT INTO")
            
            return mysql_insert_count == dm_insert_count
        except Exception:
            return False
    
    def get_dm_table_name(self) -> str:
        """获取达梦8表名"""
        return self.dm_table_name
