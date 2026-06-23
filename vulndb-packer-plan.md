# VulnDB-Packer Skill 执行计划

## 1. 项目概述

### 1.1 功能描述
根据用户提供的材料制作漏洞库升级包，包括：
- MySQL数据库SQL脚本
- 按月份的漏扫数据库变化Excel文档
- 漏洞库版本号信息

### 1.2 输入
- MySQL SQL脚本 (va_library.sql)
- Excel文档 (按月份的漏扫数据库变化，如：2026-05漏扫数据库变化.xlsx)
- 版本号信息 (当前版本和新版本，如：V1.0.2.19 → V1.0.2.20)

### 1.3 输出
- 漏洞库升级包zip文件 (VSLib20260201_001.zip)
- 安全漏洞规则库变化说明
- 执行日志

---

## 2. 文件结构设计

```
vulndb-packer/
├── SKILL.md                    # skill说明文档
├── scripts/
│   ├── __init__.py
│   ├── main.py                 # 主入口脚本
│   ├── sql_parser.py           # MySQL SQL解析器
│   ├── sql_converter.py        # MySQL转达梦8转换器
│   ├── excel_reader.py         # Excel读取器（集成COM接口）
│   ├── excel_extractor.py      # Excel漏洞变化数据提取器
│   ├── package_builder.py      # 升级包构建器
│   ├── report_generator.py     # 变化说明生成器
│   └── logger.py               # 日志记录器
├── templates/
│   ├── source.txt.template     # source.txt模板
│   ├── mysql_header.sql        # MySQL表结构头
│   └── dm_header.sql           # 达梦8表结构头
└── evals/
    └── test_cases/             # 测试用例
```

---

## 3. 核心功能模块

### 3.1 Excel读取器 (excel_reader.py)

集成excel-reader skill的核心功能，使用Windows COM接口读取Excel文件。

**类设计**:
```python
class ExcelReader:
    def __init__(self):
        """初始化Excel COM应用"""
        
    def read_excel(self, file_path: str) -> dict:
        """
        读取单个Excel文件
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            {
                "file_name": "文件名",
                "sheet_count": 1,
                "sheets": [
                    {
                        "name": "Sheet1",
                        "markdown": "Markdown表格字符串",
                        "row_count": 10,
                        "col_count": 5
                    }
                ]
            }
        """
        
    def read_multiple_excels(self, file_paths: list) -> dict:
        """
        批量读取多个Excel文件
        
        Args:
            file_paths: Excel文件路径列表
            
        Returns:
            {
                "success": [...],
                "failed": [...]
            }
        """
        
    def close(self):
        """关闭Excel应用，释放COM资源"""
```

**技术要点**:
- 使用`pythoncom`和`win32com.client`进行COM接口调用
- 支持透明加密的Excel文档
- 从UsedRange读取所有单元格数据
- 将Excel数据转换为Markdown表格格式
- 处理COM调用失败、文件不存在等异常

### 3.2 Excel漏洞变化数据提取器 (excel_extractor.py)

解析Excel读取器返回的数据，提取漏洞变化统计信息。

**类设计**:
```python
class VulnChangeExtractor:
    def extract_changes(self, excel_data: dict) -> dict:
        """
        从Excel数据中提取漏洞变化信息
        
        Args:
            excel_data: ExcelReader返回的数据
            
        Returns:
            {
                "total": 66,
                "added": 66,
                "modified": 0,
                "deleted": 0,
                "details": {
                    "DB2新增": 18,
                    "MySQL新增": 11,
                    "Oracle新增": 2,
                    "SQLServer新增": 1,
                    "Yashan新增": 11,
                    "Yashan_MySQL新增": 17
                }
            }
        """
        
    def extract_date_range(self, excel_data: dict) -> tuple:
        """
        提取日期范围
        
        Returns:
            (start_date, end_date)
        """
        
    def parse_monthly_changes(self, markdown_table: str) -> dict:
        """
        解析单个月份的漏洞变化数据
        
        Args:
            markdown_table: Markdown表格字符串
            
        Returns:
            漏洞变化数据字典
        """
```

**数据提取规则**:
- 查找包含"共调整"的单元格
- 提取"新增漏洞"、"修改漏洞"、"删除漏洞"的数量
- 支持多种格式：
  - "共调整60个"
  - "新增漏洞60个"
  - "修改漏洞0个"
  - "删除漏洞0个"
- 支持多个月份的数据汇总

### 3.3 SQL解析器 (sql_parser.py)

解析MySQL SQL脚本，提取INSERT语句。

**类设计**:
```python
class MySQLParser:
    def parse(self, sql_content: str) -> dict:
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
        """
        
    def validate_sql(self, sql_content: str) -> bool:
        """
        验证SQL语法正确性
        
        Returns:
            True/False
        """
        
    def extract_insert_statements(self, sql_content: str) -> list:
        """
        提取所有INSERT语句
        
        Returns:
            INSERT语句列表
        """
```

### 3.4 SQL转换器 (sql_converter.py)

将MySQL SQL转换为达梦8 SQL。

**类设计**:
```python
class SQLConverter:
    def convert_to_dm(self, mysql_data: dict) -> str:
        """
        将MySQL数据转换为达梦8 SQL脚本
        
        Args:
            mysql_data: MySQLParser返回的数据
            
        Returns:
            达梦8 SQL脚本内容
        """
        
    def generate_dm_header(self) -> str:
        """
        生成达梦8表结构头
        
        Returns:
            达梦8表结构SQL
        """
        
    def convert_insert_statement(self, mysql_insert: dict) -> str:
        """
        转换单条INSERT语句
        
        Args:
            mysql_insert: MySQL INSERT语句数据
            
        Returns:
            达梦8 INSERT语句
        """
        
    def convert_value(self, value, column_name: str) -> str:
        """
        转换单个值
        
        Args:
            value: 原始值
            column_name: 字段名
            
        Returns:
            转换后的值
        """
```

**数据类型映射**:
| MySQL类型 | 达梦8类型 |
|-----------|-----------|
| int | BIGINT |
| varchar | VARCHAR |
| datetime | TIMESTAMP |
| longtext | CLOB |
| text | TEXT |
| tinyint | TINYINT |

**表名和字段名转换**:
- 表名: `va_library` → `"AAS_VS"."VA_LIBRARY"`
- 字段名: 小写 → 大写

### 3.5 升级包构建器 (package_builder.py)

生成升级包的所有文件并打包。

**类设计**:
```python
class PackageBuilder:
    def build_package(self, config: dict) -> str:
        """
        构建升级包
        
        Args:
            config: {
                "mysql_sql_path": "MySQL SQL文件路径",
                "new_version": "V1.0.2.20",
                "current_version": "V1.0.2.19",
                "output_dir": "输出目录"
            }
            
        Returns:
            zip文件路径
        """
        
    def generate_source_txt(self, version: str, date: str) -> str:
        """
        生成source.txt内容
        
        Returns:
            source.txt内容
        """
        
    def generate_mysql_sql(self, sql_content: str) -> str:
        """
        生成MySQL SQL脚本
        
        Returns:
            MySQL SQL脚本内容
        """
        
    def generate_dm_sql(self, dm_sql_content: str) -> str:
        """
        生成达梦8 SQL脚本
        
        Returns:
            达梦8 SQL脚本内容
        """
        
    def create_zip_package(self, files: dict, output_path: str) -> str:
        """
        创建zip压缩包
        
        Args:
            files: {
                "source.txt": "内容",
                "va_library.sql": "内容",
                "va_library_dm.sql": "内容"
            }
            
        Returns:
            zip文件路径
        """
```

**文件命名规则**:
- zip文件名: `VSLib{YYYYMMDD}_{序号}.zip`
- 日期为当天日期
- 序号从001开始递增

**换行符要求**:
- 所有SQL文件使用Unix(LF)换行符

### 3.6 变化说明生成器 (report_generator.py)

生成安全漏洞规则库变化说明。

**类设计**:
```python
class ReportGenerator:
    def generate_report(self, changes: dict, date_range: tuple, 
                       current_version: str, new_version: str) -> str:
        """
        生成变化说明
        
        Args:
            changes: VulnChangeExtractor返回的数据
            date_range: (start_date, end_date)
            current_version: 当前版本号
            new_version: 新版本号
            
        Returns:
            变化说明文本
        """
        
    def format_date_range(self, start_date: str, end_date: str) -> str:
        """
        格式化日期范围
        
        Returns:
            格式化后的日期范围字符串
        """
```

**输出格式**:
```
安全漏洞规则库补丁版本V1.0.2.20为全量升级版本，兼容并包含此前所有版本的漏洞规则，基于 V1.0.2.19 版本迭代优化；2025 年 12 月 1 日 - 2026 年1 月 30 日期间新增调整漏扫规则66项，其中新增漏洞66个，修改漏洞0个，删除漏洞0个。
```

### 3.7 日志记录器 (logger.py)

记录skill执行过程和结果。

**类设计**:
```python
class Logger:
    def __init__(self, log_file: str = None):
        """
        初始化日志记录器
        
        Args:
            log_file: 日志文件路径（可选）
        """
        
    def info(self, message: str):
        """记录信息日志"""
        
    def error(self, message: str):
        """记录错误日志"""
        
    def warning(self, message: str):
        """记录警告日志"""
        
    def debug(self, message: str):
        """记录调试日志"""
        
    def log_execution_start(self, inputs: dict):
        """记录执行开始"""
        
    def log_execution_end(self, result: dict):
        """记录执行结束"""
```

**日志内容**:
- 执行开始时间
- 输入文件信息
- 处理步骤记录（包括Excel读取过程）
- 执行结果
- 执行结束时间
- 错误信息（如有）

---

## 4. 执行流程

### 4.1 输入验证
1. 检查MySQL SQL文件是否存在
2. 检查Excel文件是否存在（支持多个Excel文件）
3. 验证版本号格式（如：V1.0.2.19）

### 4.2 Excel处理（集成处理）
1. 使用内置ExcelReader读取Excel文件
2. 使用VulnChangeExtractor提取漏洞变化信息
3. 提取日期范围
4. 生成变化说明

### 4.3 SQL处理
1. 解析MySQL SQL脚本
2. 转换为达梦8 SQL
3. 验证转换结果

### 4.4 升级包生成
1. 生成source.txt
2. 生成MySQL SQL脚本
3. 生成达梦8 SQL脚本
4. 打包成zip文件

### 4.5 结果输出
1. 输出升级包路径
2. 输出变化说明
3. 输出执行日志

---

## 5. 输出文件格式

### 5.1 source.txt
```txt
# 漏洞库版本号
version: V1.0.2.20

# 漏洞库版本发布日期
date: 2026-06-23
```

### 5.2 va_library.sql (MySQL脚本)
```sql
DROP TABLE IF EXISTS `va_library`;
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
-- 数据插入SQL，一条数据一个insert语句
INSERT INTO `va_library` VALUES (...);
```

### 5.3 va_library_dm.sql (达梦8脚本)
```sql
set define off;
TRUNCATE TABLE "AAS_VS"."VA_LIBRARY";
SET IDENTITY_INSERT "AAS_VS"."VA_LIBRARY" ON;
-- 数据插入SQL，一条数据一个insert语句
INSERT INTO "AAS_VS"."VA_LIBRARY" ("VA_ID", "VA_NAME", ...) VALUES (1, 'CVE-2024-1234', ...);
SET IDENTITY_INSERT "AAS_VS"."VA_LIBRARY" OFF;
commit;
exit;
```

### 5.4 安全漏洞规则库变化说明
```txt
安全漏洞规则库补丁版本V1.0.2.20为全量升级版本，兼容并包含此前所有版本的漏洞规则，基于 V1.0.2.19 版本迭代优化；2025 年 12 月 1 日 - 2026 年1 月 30 日期间新增调整漏扫规则66项，其中新增漏洞66个，修改漏洞0个，删除漏洞0个。
```

---

## 6. 依赖项

### 6.1 Python依赖
```txt
pywin32>=306  # Windows COM接口
```

### 6.2 标准库
- argparse
- json
- os
- re
- sys
- logging
- zipfile
- datetime
- typing

---

## 7. 错误处理

### 7.1 输入错误
- 输入文件不存在
- 版本号格式错误
- 文件权限问题

### 7.2 处理错误
- SQL语法错误
- Excel COM初始化失败
- Excel文件读取失败
- Excel格式不支持
- 数据解析错误

### 7.3 输出错误
- 文件打包失败
- 输出目录权限问题

---

## 8. 使用方式

### 8.1 命令行调用
```bash
python scripts/main.py \
  --mysql-sql "path/to/va_library.sql" \
  --excel-files "path/to/2026-05漏扫数据库变化.xlsx" "path/to/2026-04漏扫数据库变化.xlsx" \
  --current-version "V1.0.2.19" \
  --new-version "V1.0.2.20" \
  --output-dir "path/to/output"
```

### 8.2 参数说明
| 参数 | 说明 | 必需 |
|------|------|------|
| --mysql-sql | MySQL SQL脚本文件路径 | 是 |
| --excel-files | Excel文件路径列表 | 是 |
| --current-version | 当前漏洞库版本号 | 是 |
| --new-version | 新漏洞库版本号 | 是 |
| --output-dir | 输出目录 | 否（默认当前目录） |

---

## 9. 测试用例

### 9.1 正常流程测试
- 提供有效的MySQL SQL文件
- 提供有效的Excel文件（单个月份）
- 提供有效的Excel文件（多个月份）
- 验证生成的zip包内容
- 验证变化说明格式

### 9.2 边界条件测试
- 空SQL文件
- 空Excel文件
- 大量数据的SQL文件
- 多个月份的Excel文件

### 9.3 错误处理测试
- 不存在的文件
- 无效的SQL语法
- 无效的Excel格式
- 无效的版本号格式

---

## 10. 开发计划

### 10.1 阶段一：基础框架
- [ ] 创建skill目录结构
- [ ] 创建SKILL.md文件
- [ ] 实现日志记录器

### 10.2 阶段二：核心功能
- [ ] 实现Excel读取器
- [ ] 实现Excel漏洞变化数据提取器
- [ ] 实现SQL解析器
- [ ] 实现SQL转换器

### 10.3 阶段三：打包功能
- [ ] 实现升级包构建器
- [ ] 实现变化说明生成器
- [ ] 创建模板文件

### 10.4 阶段四：集成测试
- [ ] 实现主入口脚本
- [ ] 编写测试用例
- [ ] 进行集成测试

---

## 11. 注意事项

### 11.1 平台要求
- 仅支持Windows平台
- 需要安装Microsoft Excel
- 需要安装pywin32库

### 11.2 编码要求
- SQL文件使用UTF-8编码
- 换行符使用Unix(LF)
- Excel文件支持.xls和.xlsx格式

### 11.3 性能考虑
- 大量数据时考虑内存使用
- Excel COM接口可能较慢
- 建议使用批量处理模式

### 11.4 安全考虑
- SQL注入防护
- 文件路径验证
- 敏感信息保护
