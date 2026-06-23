"""
Excel漏洞变化数据提取器模块
解析Excel读取器返回的数据，提取漏洞变化统计信息
"""

import os
import re
import calendar
from typing import Dict, List, Any, Optional, Tuple


class VulnChangeExtractorError(Exception):
    """漏洞变化数据提取错误"""
    pass


class VulnChangeExtractor:
    """漏洞变化数据提取器"""
    
    def __init__(self):
        """初始化提取器"""
        # 漏洞变化统计
        self.total_changes = 0
        self.added_vulns = 0
        self.modified_vulns = 0
        self.deleted_vulns = 0
        self.details = {}
        
    def extract_changes(self, excel_data: Dict[str, Any]) -> Dict[str, Any]:
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
        try:
            # 重置统计
            self.total_changes = 0
            self.added_vulns = 0
            self.modified_vulns = 0
            self.deleted_vulns = 0
            self.details = {}
            
            # 处理多个Excel文件的数据
            if isinstance(excel_data, dict):
                if "success" in excel_data:
                    # 批量读取的结果
                    for item in excel_data["success"]:
                        self._extract_from_single_excel(item["data"])
                elif "sheets" in excel_data:
                    # 单个Excel文件的结果
                    self._extract_from_single_excel(excel_data)
            
            return {
                "total": self.total_changes,
                "added": self.added_vulns,
                "modified": self.modified_vulns,
                "deleted": self.deleted_vulns,
                "details": self.details
            }
            
        except Exception as e:
            raise VulnChangeExtractorError(f"提取漏洞变化信息失败: {str(e)}")
    
    def _extract_from_single_excel(self, excel_data: Dict[str, Any]):
        """从单个Excel文件数据中提取信息"""
        for sheet in excel_data.get("sheets", []):
            markdown = sheet.get("markdown", "")
            if markdown:
                self._extract_from_markdown(markdown)
    
    def _extract_from_markdown(self, markdown: str):
        """从Markdown表格中提取漏洞变化信息（累加模式）"""
        # 将Markdown转换为纯文本处理
        text = markdown.replace("|", " ").replace("<br>", "\n")
        
        # 提取"共调整X个"（累加）
        total_match = re.search(r'共调整\s*(\d+)\s*个', text)
        if total_match:
            self.total_changes += int(total_match.group(1))
        
        # 提取"新增漏洞X个"（累加）
        added_match = re.search(r'新增漏洞\s*(\d+)\s*个', text)
        if added_match:
            self.added_vulns += int(added_match.group(1))
        
        # 提取"修改漏洞X个"（累加）
        modified_match = re.search(r'修改漏洞\s*(\d+)\s*个', text)
        if modified_match:
            self.modified_vulns += int(modified_match.group(1))
        
        # 提取"删除漏洞X个"（累加）
        deleted_match = re.search(r'删除漏洞\s*(\d+)\s*个', text)
        if deleted_match:
            self.deleted_vulns += int(deleted_match.group(1))
        
        # 提取详细信息（如"DB2新增：18个"）（累加）
        detail_pattern = r'([\w_]+(?:新增|修改|删除))\s*[:：]\s*(\d+)\s*个'
        detail_matches = re.findall(detail_pattern, text)
        for detail_name, detail_count in detail_matches:
            if detail_name in self.details:
                self.details[detail_name] += int(detail_count)
            else:
                self.details[detail_name] = int(detail_count)
    
    def extract_date_range(self, excel_data: Dict[str, Any], excel_files: List[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        提取日期范围
        
        Args:
            excel_data: ExcelReader返回的数据
            excel_files: Excel文件路径列表（用于从文件名提取日期）
            
        Returns:
            (start_date, end_date) 或 (None, None)
        """
        try:
            start_dates = []
            end_dates = []
            
            # 从文件名提取日期
            if excel_files:
                for file_path in excel_files:
                    start_date, end_date = self._extract_date_range_from_filename(file_path)
                    if start_date:
                        start_dates.append(start_date)
                    if end_date:
                        end_dates.append(end_date)
            
            if start_dates and end_dates:
                start_dates.sort()
                end_dates.sort()
                return (start_dates[0], end_dates[-1])
            
            return (None, None)
            
        except Exception as e:
            raise VulnChangeExtractorError(f"提取日期范围失败: {str(e)}")
    
    def _extract_date_range_from_filename(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        从文件名中提取日期范围
        
        Args:
            file_path: 文件路径
            
        Returns:
            (start_date, end_date) 元组，如("2026年1月1日", "2026年1月31日")
        """
        try:
            file_name = os.path.basename(file_path)
            # 匹配文件名格式：YYYY-MM漏扫数据库变化.xlsx
            match = re.search(r'(\d{4})-(\d{1,2})', file_name)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                # 获取该月的最后一天
                last_day = calendar.monthrange(year, month)[1]
                start_date = f"{year}年{month}月1日"
                end_date = f"{year}年{month}月{last_day}日"
                return (start_date, end_date)
            return (None, None)
        except Exception:
            return (None, None)
    
    def _extract_dates_from_excel(self, excel_data: Dict[str, Any]) -> List[str]:
        """从单个Excel文件数据中提取日期"""
        dates = []
        
        for sheet in excel_data.get("sheets", []):
            markdown = sheet.get("markdown", "")
            if markdown:
                sheet_dates = self._extract_dates_from_markdown(markdown)
                dates.extend(sheet_dates)
        
        return dates
    
    def _extract_dates_from_markdown(self, markdown: str) -> List[str]:
        """从Markdown表格中提取日期"""
        dates = []
        
        # 匹配日期格式：2025年12月1日、2026年1月30日等
        date_pattern = r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日'
        matches = re.findall(date_pattern, markdown)
        
        for year, month, day in matches:
            date_str = f"{year}年{month}月{day}日"
            dates.append(date_str)
        
        # 匹配日期范围格式：2025年12月1日 - 2026年1月30日
        range_pattern = r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日\s*[-–]\s*(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日'
        range_matches = re.findall(range_pattern, markdown)
        
        for start_year, start_month, start_day, end_year, end_month, end_day in range_matches:
            start_date = f"{start_year}年{start_month}月{start_day}日"
            end_date = f"{end_year}年{end_month}月{end_day}日"
            dates.extend([start_date, end_date])
        
        return dates
    
    def parse_monthly_changes(self, markdown_table: str) -> Dict[str, Any]:
        """
        解析单个月份的漏洞变化数据
        
        Args:
            markdown_table: Markdown表格字符串
            
        Returns:
            漏洞变化数据字典
        """
        try:
            # 重置统计
            total = 0
            added = 0
            modified = 0
            deleted = 0
            details = {}
            
            # 将Markdown转换为纯文本处理
            text = markdown_table.replace("|", " ").replace("<br>", "\n")
            
            # 提取"共调整X个"
            total_match = re.search(r'共调整\s*(\d+)\s*个', text)
            if total_match:
                total = int(total_match.group(1))
            
            # 提取"新增漏洞X个"
            added_match = re.search(r'新增漏洞\s*(\d+)\s*个', text)
            if added_match:
                added = int(added_match.group(1))
            
            # 提取"修改漏洞X个"
            modified_match = re.search(r'修改漏洞\s*(\d+)\s*个', text)
            if modified_match:
                modified = int(modified_match.group(1))
            
            # 提取"删除漏洞X个"
            deleted_match = re.search(r'删除漏洞\s*(\d+)\s*个', text)
            if deleted_match:
                deleted = int(deleted_match.group(1))
            
            # 提取详细信息（如"DB2新增：18个"）
            detail_pattern = r'([\w_]+(?:新增|修改|删除))\s*[:：]\s*(\d+)\s*个'
            detail_matches = re.findall(detail_pattern, text)
            for detail_name, detail_count in detail_matches:
                details[detail_name] = int(detail_count)
            
            return {
                "total": total,
                "added": added,
                "modified": modified,
                "deleted": deleted,
                "details": details
            }
            
        except Exception as e:
            raise VulnChangeExtractorError(f"解析月度变化数据失败: {str(e)}")
    
    def get_summary(self) -> str:
        """获取漏洞变化摘要"""
        summary_parts = []
        
        if self.total_changes > 0:
            summary_parts.append(f"共调整{self.total_changes}个")
        
        if self.added_vulns > 0:
            summary_parts.append(f"新增漏洞{self.added_vulns}个")
        
        if self.modified_vulns > 0:
            summary_parts.append(f"修改漏洞{self.modified_vulns}个")
        
        if self.deleted_vulns > 0:
            summary_parts.append(f"删除漏洞{self.deleted_vulns}个")
        
        return "，".join(summary_parts)
