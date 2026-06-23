"""
变化说明生成器模块
生成安全漏洞规则库变化说明
"""

from typing import Dict, Any, Optional, Tuple


class ReportGeneratorError(Exception):
    """变化说明生成错误"""
    pass


class ReportGenerator:
    """变化说明生成器"""
    
    def __init__(self):
        """初始化生成器"""
        pass
    
    def generate_report(self, changes: Dict[str, Any], date_range: Tuple[Optional[str], Optional[str]], 
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
            
        Raises:
            ReportGeneratorError: 生成错误
        """
        try:
            # 获取变化统计
            total = changes.get("total", 0)
            added = changes.get("added", 0)
            modified = changes.get("modified", 0)
            deleted = changes.get("deleted", 0)
            details = changes.get("details", {})
            
            # 获取日期范围
            start_date, end_date = date_range
            
            # 格式化日期范围
            date_range_str = self.format_date_range(start_date, end_date)
            
            # 生成变化说明第一段
            report = f"安全漏洞规则库补丁版本{new_version}为全量升级版本，兼容并包含此前所有版本的漏洞规则，基于 {current_version} 版本迭代优化；{date_range_str}期间新增调整漏扫规则{total}项，其中新增漏洞{added}个，修改漏洞{modified}个，删除漏洞{deleted}个。"
            
            # 生成详细信息
            if added > 0:
                report += f"\n\n新增漏洞{added}个："
                # 按类型分组显示新增漏洞详情
                added_details = {k: v for k, v in details.items() if '新增' in k}
                for category, count in sorted(added_details.items()):
                    report += f"\n{category}：{count}个"
            
            if modified > 0:
                report += f"\n修改漏洞{modified}个"
                # 按类型分组显示修改漏洞详情
                modified_details = {k: v for k, v in details.items() if '修改' in k}
                for category, count in sorted(modified_details.items()):
                    report += f"\n{category}：{count}个"
            else:
                report += f"\n修改漏洞{modified}个"
            
            if deleted > 0:
                report += f"\n删除漏洞{deleted}个"
                # 按类型分组显示删除漏洞详情
                deleted_details = {k: v for k, v in details.items() if '删除' in k}
                for category, count in sorted(deleted_details.items()):
                    report += f"\n{category}：{count}个"
            else:
                report += f"\n删除漏洞{deleted}个"
            
            return report
            
        except Exception as e:
            raise ReportGeneratorError(f"生成变化说明失败: {str(e)}")
    
    def format_date_range(self, start_date: Optional[str], end_date: Optional[str]) -> str:
        """
        格式化日期范围
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            格式化后的日期范围字符串
        """
        if not start_date or not end_date:
            return "未知日期范围"
        
        # 解析日期
        start_parts = self._parse_date(start_date)
        end_parts = self._parse_date(end_date)
        
        if not start_parts or not end_parts:
            return f"{start_date} - {end_date}"
        
        start_year, start_month, start_day = start_parts
        end_year, end_month, end_day = end_parts
        
        # 格式化日期范围
        if start_year == end_year:
            if start_month == end_month:
                # 同年同月
                return f"{start_year} 年 {start_month} 月 {start_day} 日 - {end_month} 月 {end_day} 日"
            else:
                # 同年不同月
                return f"{start_year} 年 {start_month} 月 {start_day} 日 - {end_month} 月 {end_day} 日"
        else:
            # 不同年
            return f"{start_year} 年 {start_month} 月 {start_day} 日 - {end_year} 年 {end_month} 月 {end_day} 日"
    
    def _parse_date(self, date_str: str) -> Optional[Tuple[int, int, int]]:
        """
        解析日期字符串
        
        Args:
            date_str: 日期字符串，如"2025年12月1日"或"2026年5月1日"
            
        Returns:
            (year, month, day) 或 None
        """
        import re
        
        # 匹配格式：2025年12月1日
        match = re.match(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', date_str)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            return (year, month, day)
        
        # 匹配格式：2026年5月（只有年月）
        match = re.match(r'(\d{4})\s*年\s*(\d{1,2})\s*月', date_str)
        if match:
            year = int(match.group(1))
            month = int(match.group(2))
            return (year, month, 1)
        
        return None
    
    def generate_summary(self, changes: Dict[str, Any]) -> str:
        """
        生成变化摘要
        
        Args:
            changes: VulnChangeExtractor返回的数据
            
        Returns:
            变化摘要文本
        """
        total = changes.get("total", 0)
        added = changes.get("added", 0)
        modified = changes.get("modified", 0)
        deleted = changes.get("deleted", 0)
        
        parts = []
        
        if total > 0:
            parts.append(f"共调整{total}个")
        
        if added > 0:
            parts.append(f"新增漏洞{added}个")
        
        if modified > 0:
            parts.append(f"修改漏洞{modified}个")
        
        if deleted > 0:
            parts.append(f"删除漏洞{deleted}个")
        
        return "，".join(parts) if parts else "无变化"
    
    def generate_detailed_report(self, changes: Dict[str, Any]) -> str:
        """
        生成详细变化报告
        
        Args:
            changes: VulnChangeExtractor返回的数据
            
        Returns:
            详细变化报告文本
        """
        details = changes.get("details", {})
        
        if not details:
            return "无详细信息"
        
        lines = []
        for category, count in details.items():
            lines.append(f"{category}：{count}个")
        
        return "\n".join(lines)
