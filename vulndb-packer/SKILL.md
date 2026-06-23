---
name: vulndb-packer
description: 根据用户提供的材料制作漏洞库升级包。输入MySQL SQL脚本、Excel漏洞变化文档和版本号，生成包含MySQL和达梦8 SQL脚本的升级包zip文件。
allowed-tools:
  - Bash
compatibility: Requires Windows platform with Microsoft Excel installed. Uses pywin32 for COM automation.
license: MIT
---

# VulnDB Packer Skill

你是漏洞库升级包制作助手。用户请求制作漏洞库升级包时：

## 功能说明

根据用户提供的材料制作漏洞库升级包，包括：
- MySQL数据库SQL脚本 (va_library.sql)
- 按月份的漏扫数据库变化Excel文档
- 漏洞库版本号信息

## 输入要求

### 1. MySQL SQL脚本
- 文件格式: .sql
- 内容: INSERT语句
- 编码: UTF-8

### 2. Excel文档
- 文件格式: .xls 或 .xlsx
- 内容: 按月份的漏扫数据库变化
- 支持多个Excel文件
- 文件名格式: YYYY-MM漏扫数据库变化.xlsx

### 3. 版本号信息
- 当前版本号 (如: V1.0.2.19)
- 新版本号 (如: V1.0.2.20)
- **版本号格式必须是Vx.y.z.w**
- **新版本号必须大于当前版本号**

## 输出结果

### 1. 漏洞库升级包
- 文件名: VSLib{YYYYMMDD}_{序号}.zip
- 内容:
  - source.txt: 版本信息
  - va_library.sql: MySQL SQL脚本（包含表结构定义）
  - va_library_dm.sql: 达梦8 SQL脚本

### 2. 安全漏洞规则库变化说明
- 文件名: 安全漏洞规则库变化说明_{新版本号}.txt
- 内容: 漏洞变化统计信息（包含详细漏洞分类）

### 3. 执行日志
- 记录执行过程和结果

## 使用方式

通过 Bash 工具调用 main.py：

**基本用法:**
```bash
python vulndb-packer/scripts/main.py \
  --mysql-sql "path/to/va_library.sql" \
  --excel-files "path/to/2026-05漏扫数据库变化.xlsx" \
  --current-version "V1.0.2.19" \
  --new-version "V1.0.2.20" \
  --output-dir "path/to/output"
```

**多个Excel文件:**
```bash
python vulndb-packer/scripts/main.py \
  --mysql-sql "path/to/va_library.sql" \
  --excel-files "path/to/2026-05漏扫数据库变化.xlsx" "path/to/2026-04漏扫数据库变化.xlsx" \
  --current-version "V1.0.2.19" \
  --new-version "V1.0.2.20" \
  --output-dir "path/to/output"
```

## 参数说明

| 参数 | 说明 | 必需 |
|------|------|------|
| --mysql-sql | MySQL SQL脚本文件路径 | 是 |
| --excel-files | Excel文件路径列表 | 是 |
| --current-version | 当前漏洞库版本号 | 是 |
| --new-version | 新漏洞库版本号 | 是 |
| --output-dir | 输出目录 | 否（默认当前目录） |

## 版本号校验规则

1. **格式校验**: 版本号必须是`Vx.y.z.w`格式（如V1.0.2.19）
2. **大小校验**: 新版本号必须大于当前版本号
3. **错误提示**:
   - 格式错误: "当前版本格式不正确，必须是Vx.y.z.w格式"
   - 大小错误: "新版本号(V1.0.2.19)必须大于当前版本号(V1.0.2.20)"

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

## 错误处理

- **输入文件不存在**: 明确告知用户哪个文件不存在
- **SQL语法错误**: 报告SQL解析错误详情
- **Excel读取失败**: 报告Excel读取错误原因
- **版本号格式错误**: 提示正确的版本号格式
- **版本号大小错误**: 提示新版本必须大于当前版本
- **升级包验证失败**: 报告升级包不存在或为空

## 限制

- **平台限制**: 仅支持 Windows（COM 接口要求）
- **软件要求**: 需要安装 Microsoft Excel
- **文件格式**: 仅支持 .xls 和 .xlsx 格式的Excel文件
- **依赖项**: 需要安装 pywin32 库
- **Excel文件名**: 建议使用 YYYY-MM漏扫数据库变化.xlsx 格式

## 示例

### 示例1: 单个Excel文件
```bash
python vulndb-packer/scripts/main.py \
  --mysql-sql "C:\data\va_library.sql" \
  --excel-files "C:\data\2026-05漏扫数据库变化.xlsx" \
  --current-version "V1.0.2.19" \
  --new-version "V1.0.2.20" \
  --output-dir "C:\output"
```

### 示例2: 多个Excel文件
```bash
python vulndb-packer/scripts/main.py \
  --mysql-sql "C:\data\va_library.sql" \
  --excel-files "C:\data\2026-05漏扫数据库变化.xlsx" "C:\data\2026-04漏扫数据库变化.xlsx" \
  --current-version "V1.0.2.19" \
  --new-version "V1.0.2.20" \
  --output-dir "C:\output"
```

## 输出示例

```
[执行开始]
输入文件:
  - MySQL SQL: C:\data\va_library.sql
  - Excel文件: C:\data\2026-05漏扫数据库变化.xlsx
  - 版本: V1.0.2.19 → V1.0.2.20

[处理步骤]
1. 验证输入文件... 完成
2. 读取Excel文件... 完成
3. 提取漏洞变化信息... 完成
4. 生成变化说明... 完成
5. 解析MySQL SQL... 完成
6. 转换为达梦8 SQL... 完成
7. 生成升级包... 完成
8. 验证升级包... 完成

[执行结果]
升级包: C:\output\VSLib20260623_001.zip
变化说明: 安全漏洞规则库补丁版本V1.0.2.20为全量升级版本...

[执行完成]
```
