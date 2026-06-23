# 测试数据说明

## 1. MySQL SQL文件 (va_library.sql)
包含3条测试数据，用于验证SQL解析和转换功能。

## 2. Excel文件
需要手动创建测试用的Excel文件，格式如下：

### 文件名: 2026-05漏扫数据库变化.xlsx

### 内容示例:
```
| 漏洞变化统计 |
| --- |
| 共调整60个 |
| 1 新增漏洞60个： |
|     1.1 DB2新增：18个 |
|     1.2 MySQL新增：11个 |
|     1.3 Oracle新增：2个 |
|     1.4 SQLServer新增：1个 |
|     1.5 Yashan新增：11个 |
|     1.6 Yashan_MySQL新增：17个 |
| 2 修改漏洞0个： |
| 3 删除漏洞0个： |
| 日期范围：2025年12月1日 - 2026年1月30日 |
```

## 3. 测试命令
```bash
python vulndb-packer/scripts/main.py \
  --mysql-sql vulndb-packer/evals/test_cases/sample_data/va_library.sql \
  --excel-files vulndb-packer/evals/test_cases/sample_data/2026-05漏扫数据库变化.xlsx \
  --current-version V1.0.2.19 \
  --new-version V1.0.2.20 \
  --output-dir vulndb-packer/evals/test_cases/output
```

## 4. 预期输出
- VSLib20260623_001.zip
- 包含: source.txt, va_library.sql, va_library_dm.sql
