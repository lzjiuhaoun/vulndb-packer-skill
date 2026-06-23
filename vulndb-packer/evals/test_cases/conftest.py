"""
Pytest配置文件
"""

import os
import sys

# 添加脚本目录到Python路径
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))
sys.path.insert(0, scripts_dir)
