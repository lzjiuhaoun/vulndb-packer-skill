# AGENTS.md

## 项目概述

VulnDB Packer - 漏洞库升级包制作工具，将 MySQL SQL 和 Excel 漏洞变化文档转换为升级包。

## 关键架构

- **入口**: `vulndb-packer/scripts/main.py`
- **核心模块**: sql_parser.py, sql_converter.py, excel_reader.py, excel_extractor.py, package_builder.py, report_generator.py
- **测试**: `vulndb-packer/evals/test_cases/`

## 开发命令

```bash
# 安装依赖
pip install pywin32

# 运行测试
python -m pytest vulndb-packer/evals/test_cases/ -v

# 运行主程序
python vulndb-packer/scripts/main.py --mysql-sql <sql文件> --excel-files <excel文件> --current-version <当前版本> --new-version <新版本> --output-dir <输出目录>
```

## 平台约束

- **仅支持 Windows** - 依赖 pywin32 COM 接口读取 Excel
- **需要 Microsoft Excel** - 用于解密加密的 Excel 文件
- **Python 3.8+** - 推荐 3.10

## 版本号规则

- 格式: `Vx.y.z.w` (如 V1.0.2.19)
- 新版本必须大于当前版本
- 正则: `^V\d+\.\d+\.\d+\.\d+$`

## 输入文件约定

- MySQL SQL: UTF-8 编码，INSERT 语句
- Excel 文件名: `YYYY-MM漏扫数据库变化.xlsx`
- 输出 SQL 使用 Unix (LF) 换行符

## 常见错误

- 版本号格式错误 → 必须 Vx.y.z.w
- Excel 读取失败 → 检查 Excel 是否安装、文件是否被占用
- pywin32 安装失败 → 使用镜像源: `pip install pywin32 -i https://pypi.tuna.tsinghua.edu.cn/simple`
