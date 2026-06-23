# VulnDB Packer Skill

漏洞库升级包制作工具，用于根据用户提供的材料制作漏洞库升级包。

## 功能特性

- 解析MySQL SQL脚本，提取INSERT语句
- 将MySQL SQL转换为达梦8 SQL
- 读取Excel文件，提取漏洞变化统计信息
- 生成升级包zip文件
- 生成安全漏洞规则库变化说明（包含漏洞详情）
- 版本号校验（格式和大小）
- 升级包验证
- 完整的日志记录

## 文件结构

```
vulndb-packer/
├── SKILL.md                    # skill说明文档
├── README.md                   # 本文件
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

## 安装依赖

```bash
pip install pywin32
```

## 使用方法

### 命令行调用

```bash
python vulndb-packer/scripts/main.py \
  --mysql-sql "path/to/va_library.sql" \
  --excel-files "path/to/2026-05漏扫数据库变化.xlsx" \
  --current-version "V1.0.2.19" \
  --new-version "V1.0.2.20" \
  --output-dir "path/to/output"
```

### 参数说明

| 参数 | 说明 | 必需 |
|------|------|------|
| --mysql-sql | MySQL SQL脚本文件路径 | 是 |
| --excel-files | Excel文件路径列表 | 是 |
| --current-version | 当前漏洞库版本号 | 是 |
| --new-version | 新漏洞库版本号 | 是 |
| --output-dir | 输出目录 | 否（默认当前目录） |

### 多个Excel文件

```bash
python vulndb-packer/scripts/main.py \
  --mysql-sql "path/to/va_library.sql" \
  --excel-files "path/to/2026-05漏扫数据库变化.xlsx" "path/to/2026-04漏扫数据库变化.xlsx" \
  --current-version "V1.0.2.19" \
  --new-version "V1.0.2.20" \
  --output-dir "path/to/output"
```

## 版本号校验规则

1. **格式校验**: 版本号必须是`Vx.y.z.w`格式（如V1.0.2.19）
2. **大小校验**: 新版本号必须大于当前版本号

### 版本号示例

| 当前版本 | 新版本 | 结果 |
|----------|--------|------|
| V1.0.2.19 | V1.0.2.20 | ✅ 通过 |
| V1.0.2.20 | V1.0.2.19 | ❌ 失败（新版本必须大于当前版本）|
| 1.0.2.19 | V1.0.2.20 | ❌ 失败（格式错误，必须以V开头）|

## 输出结果

### 1. 漏洞库升级包

- 文件名: `VSLib{YYYYMMDD}_{序号}.zip`
- 包含文件:
  - `source.txt`: 版本信息
  - `va_library.sql`: MySQL SQL脚本（包含表结构定义）
  - `va_library_dm.sql`: 达梦8 SQL脚本

### 2. 安全漏洞规则库变化说明

- 文件名: `安全漏洞规则库变化说明_{新版本号}.txt`
- 内容: 漏洞变化统计信息（包含详细漏洞分类）

### 3. 执行日志

记录完整的执行过程和结果。

## 输出文件格式

### source.txt
```txt
# 漏洞库版本号
version: V1.0.2.20

# 漏洞库版本发布日期
date: 2026-06-23
```

### va_library.sql (MySQL脚本)
```sql
DROP TABLE IF EXISTS `va_library`;
CREATE TABLE `va_library`  (
  `va_id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `va_name` varchar(255) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL COMMENT '漏洞名称',
  ...
  PRIMARY KEY (`va_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '漏洞库信息表' ROW_FORMAT = Dynamic;
INSERT INTO `va_library` VALUES (...);
```

### va_library_dm.sql (达梦8脚本)
```sql
set define off;
TRUNCATE TABLE "AAS_VS"."VA_LIBRARY";
SET IDENTITY_INSERT "AAS_VS"."VA_LIBRARY" ON;
INSERT INTO "AAS_VS"."VA_LIBRARY" ("VA_ID", "VA_NAME", ...) VALUES (...);
SET IDENTITY_INSERT "AAS_VS"."VA_LIBRARY" OFF;
commit;
exit;
```

### 安全漏洞规则库变化说明
```txt
安全漏洞规则库补丁版本V1.0.2.20为全量升级版本，兼容并包含此前所有版本的漏洞规则，基于 V1.0.2.19 版本迭代优化；2026 年 4 月 1 日 - 5 月 31 日期间新增调整漏扫规则75项，其中新增漏洞75个，修改漏洞0个，删除漏洞0个。

新增漏洞75个：
DB2新增：10个
MariaDB新增：1个
Memcached新增：2个
Mongodb新增：10个
MySQL新增：25个
Oracle新增：9个
PostgreSQL新增：11个
Redis新增：3个
Server新增：4个
修改漏洞0个
删除漏洞0个
```

## 测试

### 运行单元测试

```bash
python -m pytest vulndb-packer/evals/test_cases/ -v
```

### 测试SQL解析和转换

```bash
python vulndb-packer/evals/test_cases/test_sql.py
```

## 注意事项

1. **平台要求**: 仅支持Windows平台
2. **软件要求**: 需要安装Microsoft Excel
3. **依赖项**: 需要安装pywin32库
4. **文件格式**: Excel文件支持.xls和.xlsx格式
5. **编码要求**: SQL文件使用UTF-8编码
6. **换行符**: 生成的SQL文件使用Unix(LF)换行符
7. **Excel文件名**: 建议使用YYYY-MM漏扫数据库变化.xlsx格式
8. **版本号格式**: 必须是Vx.y.z.w格式
9. **版本号大小**: 新版本号必须大于当前版本号

## 错误处理

工具会处理以下错误情况：
- 输入文件不存在
- SQL语法错误
- Excel文件读取失败
- 版本号格式错误
- 版本号大小错误
- 升级包验证失败

所有错误都会记录到日志中。

## 示例

### 输入文件

1. **MySQL SQL文件** (va_library.sql)
```sql
INSERT INTO `va_library` VALUES (1, 'CVE-2024-1234', '2024-01-15 10:30:00', 1, 1, 'check_rule_1', 1, 'MySQL权限提升漏洞', 'ALTER USER root IDENTIFIED BY new_password;', 3, 1, '建议升级MySQL到最新版本', 'CVE-2024-1234', 'CNNVD-202401-1234', 'MySQL 5.7', 'V1.0.2.19', 1);
```

2. **Excel文件** (2026-05漏扫数据库变化.xlsx)
```
共调整40个
1 新增漏洞40个：
    1.1 DB2新增：9个
    1.2 Memcached新增：2个
    1.3 Mongodb新增：8个
    1.4 Oracle新增：6个
    1.5 PostgreSQL新增：11个
    1.6 Redis新增：3个
    1.7 SQL Server新增：1个
2 修改漏洞0个：
3 删除漏洞0个：
```

### 输出文件

1. **升级包**: `VSLib20260623_001.zip`
2. **变化说明**: `安全漏洞规则库变化说明_V1.0.2.20.txt`

## 执行流程

```
[步骤 1] 验证输入文件... 开始
[步骤 1] 验证输入文件... 完成
[步骤 2] 读取Excel文件... 开始
[步骤 2] 读取Excel文件... 完成
[步骤 3] 提取漏洞变化信息... 开始
[步骤 3] 提取漏洞变化信息... 完成
[步骤 4] 生成变化说明... 开始
[步骤 4] 生成变化说明... 完成
[步骤 5] 解析MySQL SQL... 开始
[步骤 5] 解析MySQL SQL... 完成
[步骤 6] 转换为达梦8 SQL... 开始
[步骤 6] 转换为达梦8 SQL... 完成
[步骤 7] 生成升级包... 开始
[步骤 7] 生成升级包... 完成
[步骤 8] 验证升级包... 开始
升级包验证通过: output\VSLib20260623_001.zip (大小: 1493209 字节)
[步骤 8] 验证升级包... 完成
```

## 许可证

MIT License
