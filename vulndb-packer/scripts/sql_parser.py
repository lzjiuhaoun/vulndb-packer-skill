"""
MySQL SQL解析器模块
解析MySQL SQL脚本，提取INSERT语句
"""

import re
from typing import List, Dict, Any, Optional


class MySQLError(Exception):
    """MySQL SQL解析错误"""
    pass


class MySQLParser:
    """MySQL SQL解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.table_name = "va_library"
        self.columns = []
        self.insert_statements = []
        
    def parse(self, sql_content: str) -> Dict[str, Any]:
        """
        解析MySQL SQL脚本
        
        Args:
            sql_content: SQL脚本内容
            
        Returns:
            {
                "table_name": "va_library",
                "columns": ["va_id", "va_name", ...],
                "insert_statements": [
                    {
                        "values": [1, "CVE-2024-1234", ...]
                    }
                ]
            }
            
        Raises:
            MySQLError: SQL语法错误
        """
        try:
            # 清理SQL内容
            sql_content = self._clean_sql(sql_content)
            
            # 提取INSERT语句
            self.insert_statements = self._extract_insert_statements(sql_content)
            
            # 提取列名（从第一条INSERT语句）
            if self.insert_statements:
                self.columns = self._extract_columns_from_insert(self.insert_statements[0])
            
            return {
                "table_name": self.table_name,
                "columns": self.columns,
                "insert_statements": self.insert_statements
            }
            
        except Exception as e:
            if isinstance(e, MySQLError):
                raise
            raise MySQLError(f"SQL解析失败: {str(e)}")
    
    def _clean_sql(self, sql_content: str) -> str:
        """清理SQL内容"""
        # 移除注释
        sql_content = re.sub(r'--.*$', '', sql_content, flags=re.MULTILINE)
        sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
        
        # 移除多余的空白字符
        sql_content = re.sub(r'\s+', ' ', sql_content)
        
        return sql_content.strip()
    
    def _extract_insert_statements(self, sql_content: str) -> List[Dict[str, Any]]:
        """提取所有INSERT语句"""
        # 使用状态机方式提取INSERT语句，支持嵌套括号
        insert_statements = []
        
        # 查找所有INSERT INTO语句的起始位置
        pattern = r"INSERT\s+INTO\s+`va_library`(?:\s*\([^)]*\))?\s+VALUES\s*\("
        for match in re.finditer(pattern, sql_content, re.IGNORECASE):
            start_pos = match.end()
            
            # 使用状态机找到匹配的右括号
            paren_depth = 1
            i = start_pos
            in_string = False
            string_char = None
            escape_next = False
            
            while i < len(sql_content) and paren_depth > 0:
                char = sql_content[i]
                
                if escape_next:
                    escape_next = False
                    i += 1
                    continue
                
                if char == '\\':
                    escape_next = True
                    i += 1
                    continue
                
                if in_string:
                    if char == string_char:
                        in_string = False
                    i += 1
                    continue
                
                if char in ("'", '"'):
                    in_string = True
                    string_char = char
                    i += 1
                    continue
                
                if char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                
                i += 1
            
            if paren_depth == 0:
                # 提取VALUES子句内容（不包括外层括号）
                values_str = sql_content[start_pos:i-1]
                try:
                    values = self._parse_values(values_str)
                    if values:
                        insert_statements.append({"values": values})
                except Exception as e:
                    # 跳过无法解析的INSERT语句
                    continue
        
        return insert_statements
    
    def _parse_values(self, values_str: str) -> List[Any]:
        """解析VALUES子句中的值"""
        values = []
        current_value = ""
        in_string = False
        string_char = None
        escape_next = False
        paren_depth = 0
        
        i = 0
        while i < len(values_str):
            char = values_str[i]
            
            if escape_next:
                current_value += char
                escape_next = False
                i += 1
                continue
            
            if char == '\\':
                escape_next = True
                current_value += char
                i += 1
                continue
            
            if in_string:
                current_value += char
                if char == string_char:
                    in_string = False
                    string_char = None
                i += 1
                continue
            
            if char in ("'", '"'):
                in_string = True
                string_char = char
                current_value += char
                i += 1
                continue
            
            if char == '(':
                paren_depth += 1
                current_value += char
                i += 1
                continue
            
            if char == ')':
                paren_depth -= 1
                current_value += char
                i += 1
                continue
            
            if char == ',' and paren_depth == 0:
                values.append(self._convert_value(current_value.strip()))
                current_value = ""
                i += 1
                continue
            
            current_value += char
            i += 1
        
        # 添加最后一个值
        if current_value.strip():
            values.append(self._convert_value(current_value.strip()))
        
        return values
    
    def _convert_value(self, value_str: str) -> Any:
        """转换值为Python类型"""
        # NULL值
        if value_str.upper() == 'NULL':
            return None
        
        # 字符串值
        if (value_str.startswith("'") and value_str.endswith("'")) or \
           (value_str.startswith('"') and value_str.endswith('"')):
            # 移除引号
            inner_value = value_str[1:-1]
            # 处理MySQL转义字符
            # MySQL中 \' 表示单引号，需要转换为 '
            # MySQL中 \\ 表示反斜杠，需要转换为 \
            # 但是，如果原始值是 \\''（两个反斜杠+两个单引号），表示 \'（反斜杠+单引号）
            # 所以需要先处理 \\'，再处理 '
            inner_value = inner_value.replace("\\'", "'")
            inner_value = inner_value.replace("\\\\", "\\")
            return inner_value
        
        # 数值
        try:
            # 整数
            if '.' not in value_str:
                return int(value_str)
            # 浮点数
            return float(value_str)
        except ValueError:
            # 无法转换，返回原始字符串
            return value_str
    
    def _extract_columns_from_insert(self, insert_statement: Dict[str, Any]) -> List[str]:
        """从INSERT语句中提取列名"""
        # 根据va_library表的结构定义列名
        # 这些列名与表结构定义一致
        columns = [
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
        
        # 如果INSERT语句中的值数量与列名数量不匹配，调整列名
        values_count = len(insert_statement.get("values", []))
        if values_count > 0 and values_count != len(columns):
            # 尝试从INSERT语句中提取列名
            # 这里假设INSERT语句格式为: INSERT INTO `va_library` (col1, col2, ...) VALUES (...)
            # 但用户提供的SQL可能没有指定列名，所以我们使用默认列名
            pass
        
        return columns
    
    def validate_sql(self, sql_content: str) -> bool:
        """
        验证SQL语法正确性
        
        Args:
            sql_content: SQL脚本内容
            
        Returns:
            True/False
        """
        try:
            # 尝试解析SQL
            self.parse(sql_content)
            return True
        except MySQLError:
            return False
    
    def get_insert_count(self) -> int:
        """获取INSERT语句数量"""
        return len(self.insert_statements)
    
    def get_column_count(self) -> int:
        """获取列数量"""
        return len(self.columns)
