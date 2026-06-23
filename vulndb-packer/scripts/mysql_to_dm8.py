# -*- coding: utf-8 -*-
"""
MySQL -> 达梦8 (DM8) SQL 脚本转换器
=====================================
针对 va_library.sql 这类"纯 INSERT"导出脚本做转换, 输出符合
AAS_VS.VA_LIBRARY 表结构 (DM8) 的可一次性执行 SQL 脚本。

为什么之前在 DM8 执行时报 "违反列[VA_LEVEL]非空约束"?
------------------------------------------------------
1. MySQL 字符串字面量使用 C 风格反斜杠转义 (\\n \\r \\t \\' \\" 等),
   达梦默认使用 SQL 标准 (单引号 '' 转义, 反斜杠不参与转义).
   直接把 MySQL 文本丢给达梦执行, 会让 \\' 之类的转义失效、
   字符串字面量被提前结束, 后续字段整体错位 —— 错位后 VA_LEVEL 列
   接收到 NULL, 而 VA_LEVEL 是 NOT NULL 列, 触发 23502 非空约束错误.

2. 本转换器对每个字符串字面量按 MySQL 规则解析回真实字符,
   再按达梦规则重新生成:
   - 控制字符 (换行/回车/制表/退格/NUL) 使用 CHR(n) || '...' 拼接
   - 单引号使用 '' 转义
   - 日期时间统一使用 TO_DATE('...', 'YYYY-MM-DD HH24:MI:SS')

3. 同时根据 DM8 表结构做类型感知:
   - VA_LEVEL (TINYINT NOT NULL): 字符串数字 -> 数字字面量, 绝不会变 NULL
   - 整型字段 (TINYINT/BIGINT): 字符串数字 -> 数字字面量
   - 时间字段 (TIMESTAMP): 字符串 -> TO_DATE()
   - 大字段 (CLOB/TEXT): 长字符串无长度限制
   - VARCHAR(N): 长度超限自动告警

4. VA_ID 在目标表是 IDENTITY(8208, 1) 自增列,
   头部 SET IDENTITY_INSERT AAS_VS.VA_LIBRARY ON 才能显式插入值.

用法
----
    python mysql_to_dm8.py <输入MySQL脚本> <输出DM8脚本>

    python mysql_to_dm8.py va_library.sql va_library_dm8.sql
"""

import datetime
import io
import os
import re
import sys


# ===========================================================================
# 目标表元数据 (来自 CREATE TABLE AAS_VS.VA_LIBRARY)
# ===========================================================================
DM_SCHEMA = 'AAS_VS'
DM_TABLE = 'VA_LIBRARY'
DM_QUALIFIED_TABLE = '%s.%s' % (DM_SCHEMA, DM_TABLE)

# MySQL 列名 (小写) -> DM8 列名 (大写)
DM_COLUMN_MAP = {
    'va_id':           'VA_ID',
    'va_name':         'VA_NAME',
    'va_time':         'VA_TIME',
    'db_type':         'DB_TYPE',
    'va_type':         'VA_TYPE',
    'va_rule':         'VA_RULE',
    'va_check_way':    'VA_CHECK_WAY',
    'va_desc':         'VA_DESC',
    'va_sql':          'VA_SQL',
    'va_level':        'VA_LEVEL',
    'va_verify':       'VA_VERIFY',
    'va_suggest':      'VA_SUGGEST',
    'va_cve':          'VA_CVE',
    'va_cnnvd':        'VA_CNNVD',
    'va_db_version':   'VA_DB_VERSION',
    'va_lib_version':  'VA_LIB_VERSION',
    'public_poc_exp':  'PUBLIC_POC_EXP',
}

# 默认列名顺序（当INSERT语句未指定列名时使用）
DEFAULT_COLUMNS = [
    'va_id', 'va_name', 'va_time', 'db_type', 'va_type', 'va_rule',
    'va_check_way', 'va_desc', 'va_sql', 'va_level', 'va_verify',
    'va_suggest', 'va_cve', 'va_cnnvd', 'va_db_version', 'va_lib_version',
    'public_poc_exp'
]

# DM8 列类型 (用于类型感知的字面量生成)
DM_COLUMN_TYPES = {
    'VA_ID':           'BIGINT',
    'VA_NAME':         'VARCHAR(255)',
    'VA_TIME':         'TIMESTAMP',
    'DB_TYPE':         'TINYINT',
    'VA_TYPE':         'TINYINT',
    'VA_RULE':         'CLOB',
    'VA_CHECK_WAY':    'TINYINT',
    'VA_DESC':         'CLOB',
    'VA_SQL':          'TEXT',
    'VA_LEVEL':        'TINYINT',
    'VA_VERIFY':       'TINYINT',
    'VA_SUGGEST':      'TEXT',
    'VA_CVE':          'VARCHAR(32)',
    'VA_CNNVD':        'VARCHAR(32)',
    'VA_DB_VERSION':   'VARCHAR(255)',
    'VA_LIB_VERSION':  'VARCHAR(32)',
    'PUBLIC_POC_EXP':  'TINYINT',
}

# VARCHAR(N) 长度提取
_VARCHAR_RE = re.compile(r'^VARCHAR\((\d+)\)$', re.IGNORECASE)


def varchar_limit(col_type):
    m = _VARCHAR_RE.match(col_type or '')
    return int(m.group(1)) if m else None


# ===========================================================================
# 1. MySQL INSERT 语句解析器 (严格状态机)
# ===========================================================================

class MysqlInsertParser:
    """
    把一行 (或一段) MySQL INSERT 语句解析成:
        table_name : str
        columns    : list[str]   MySQL 原始小写列名, 省略时为 []
        values     : list[list[str]]  每个 inner list 是一组 MySQL 字面量原文
    """

    def parse(self, text):
        text = text.strip()
        m = re.match(
            r'(?is)^INSERT\s+INTO\s+(`[^`]+`|[A-Za-z_][\w$]*)\s*'
            r'(\([^)]*\))?\s*VALUES\s*(.*)$',
            text)
        if not m:
            return None

        table_raw = m.group(1)
        table_name = table_raw.strip('`')

        cols_raw = m.group(2)
        columns = []
        if cols_raw:
            inside = cols_raw.strip()[1:-1]
            columns = [c.strip().strip('`') for c in self._split_top_level(inside)]

        values_text = m.group(3).rstrip(';').strip()
        if not values_text.startswith('('):
            return table_name, columns, []
        values = []
        for tup_body in self._split_top_level_tuples(values_text):
            values.append(self._split_top_level(tup_body))
        return table_name, columns, values

    @staticmethod
    def _split_top_level(text):
        """按逗号切分, 但跳过字符串/标识符/括号内部."""
        out = []
        buf = []
        depth = 0
        state = None
        i, n = 0, len(text)
        while i < n:
            c = text[i]
            if state == 'sq':
                buf.append(c)
                if c == '\\' and i + 1 < n:
                    buf.append(text[i + 1]); i += 2; continue
                if c == "'":
                    if i + 1 < n and text[i + 1] == "'":
                        buf.append("'"); i += 2; continue
                    state = None
                i += 1; continue
            if state == 'dq':
                buf.append(c)
                if c == '\\' and i + 1 < n:
                    buf.append(text[i + 1]); i += 2; continue
                if c == '"':
                    state = None
                i += 1; continue
            if state == 'bt':
                buf.append(c)
                if c == '`':
                    state = None
                i += 1; continue
            if state == 'line_comment':
                buf.append(c)
                if c == '\n':
                    state = None
                i += 1; continue
            if state == 'block_comment':
                buf.append(c)
                if c == '*' and i + 1 < n and text[i + 1] == '/':
                    buf.append('/'); i += 2; state = None; continue
                i += 1; continue
            if c == "'":
                state = 'sq'; buf.append(c); i += 1; continue
            if c == '"':
                state = 'dq'; buf.append(c); i += 1; continue
            if c == '`':
                state = 'bt'; buf.append(c); i += 1; continue
            if c == '-' and i + 1 < n and text[i + 1] == '-':
                state = 'line_comment'; buf.append('-'); buf.append('-'); i += 2; continue
            if c == '/' and i + 1 < n and text[i + 1] == '*':
                state = 'block_comment'; buf.append('/'); buf.append('*'); i += 2; continue
            if c == '(':
                depth += 1; buf.append(c); i += 1; continue
            if c == ')':
                depth -= 1; buf.append(c); i += 1; continue
            if c == ',' and depth == 0:
                out.append(''.join(buf)); buf = []; i += 1; continue
            buf.append(c); i += 1
        if buf:
            out.append(''.join(buf))
        return [x.strip() for x in out]

    @staticmethod
    def _split_top_level_tuples(text):
        """VALUES (...) , (...) , (...) 切分为多个子串,
        返回每个元组的内部内容 (已剥外层括号)."""
        out = []
        depth = 0
        buf = []
        state = None
        i, n = 0, len(text)
        while i < n:
            c = text[i]
            if state == 'sq':
                buf.append(c)
                if c == '\\' and i + 1 < n:
                    buf.append(text[i + 1]); i += 2; continue
                if c == "'":
                    if i + 1 < n and text[i + 1] == "'":
                        buf.append("'"); i += 2; continue
                    state = None
                i += 1; continue
            if state == 'dq':
                buf.append(c)
                if c == '\\' and i + 1 < n:
                    buf.append(text[i + 1]); i += 2; continue
                if c == '"':
                    state = None
                i += 1; continue
            if state is None:
                if c == "'":
                    state = 'sq'; buf.append(c); i += 1; continue
                if c == '"':
                    state = 'dq'; buf.append(c); i += 1; continue
                if c == '(':
                    if depth == 0:
                        buf = []
                    else:
                        buf.append(c)
                    depth += 1; i += 1; continue
                if c == ')':
                    depth -= 1
                    if depth == 0:
                        out.append(''.join(buf)); buf = []
                    else:
                        buf.append(c)
                    i += 1; continue
                if c == ',' and depth == 0:
                    i += 1; continue
                if depth > 0:
                    buf.append(c)
                i += 1; continue
            i += 1
        return out


# ===========================================================================
# 2. MySQL 字面量 -> Python 值
# ===========================================================================

MYSQL_ESCAPE_MAP = {
    'n': '\n', 'N': '\n',
    'r': '\r', 'R': '\r',
    't': '\t', 'T': '\t',
    'b': '\b', 'B': '\b',
    '0': '\x00',
    'Z': '\x1a', 'z': '\x1a',
    '\\': '\\',
    "'": "'",
    '"': '"',
    '`': '`',
    '%': '%',
    '_': '_',
    ' ': ' ',
}


def parse_mysql_string(literal):
    """MySQL 单引号字符串字面量 (含外层引号) -> Python str."""
    assert literal[0] == "'" and literal[-1] == "'"
    body = literal[1:-1]
    out = []
    i, n = 0, len(body)
    while i < n:
        c = body[i]
        if c == '\\' and i + 1 < n:
            nxt = body[i + 1]
            out.append(MYSQL_ESCAPE_MAP.get(nxt, nxt))
            i += 2
            continue
        if c == "'" and i + 1 < n and body[i + 1] == "'":
            out.append("'")
            i += 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def classify_value(raw):
    """
    返回 (kind, value):
      'null' -> None
      'str'  -> Python str (MySQL 单引号字面量解析后)
      'num'  -> 原始数字字符串 (如 1, 1.5, -2)
      'hex'  -> 0x...
      'raw'  -> 其它 (TRUE/FALSE/函数表达式等)
    """
    s = raw.strip()
    if not s:
        return 'raw', ''
    up = s.upper()
    if up == 'NULL':
        return 'null', None
    if s.startswith("'") and s.endswith("'") and len(s) >= 2:
        return 'str', parse_mysql_string(s)
    if s.startswith('"') and s.endswith('"') and len(s) >= 2:
        inner = s[1:-1]
        inner = inner.replace('\\"', '"').replace('\\\\', '\\').replace("''", "'")
        return 'str', inner
    if re.fullmatch(r'-?\d+', s):
        return 'num', s
    if re.fullmatch(r'-?\d+\.\d+', s):
        return 'num', s
    if re.fullmatch(r'-?\d+(\.\d+)?[eE]-?\d+', s):
        return 'num', s
    if up.startswith('0X') and re.fullmatch(r'0[xX][0-9a-fA-F]+', s):
        return 'hex', s
    return 'raw', s


# ===========================================================================
# 3. Python 值 -> DM8 字面量 (类型感知)
# ===========================================================================

def to_dm_string_literal(s):
    """Python str -> DM8 安全字符串表达式."""
    if s == '':
        return "''"
    parts = []
    cur = []
    for ch in s:
        o = ord(ch)
        if o in (10, 13, 9, 8, 0, 26):
            if cur:
                parts.append("'" + ''.join(cur).replace("'", "''") + "'")
                cur = []
            parts.append('CHR(%d)' % o)
        else:
            cur.append(ch)
    if cur:
        parts.append("'" + ''.join(cur).replace("'", "''") + "'")
    return ' || '.join(parts)


_DATE_RE = re.compile(r'^(\d{4})-(\d{1,2})-(\d{1,2})[ T](\d{1,2}):(\d{1,2}):(\d{1,2})$')
_DATE_ONLY_RE = re.compile(r'^(\d{4})-(\d{1,2})-(\d{1,2})$')

_INT_TYPES = {'TINYINT', 'SMALLINT', 'INTEGER', 'INT', 'BIGINT', 'BYTE'}
_DEC_TYPES = {'FLOAT', 'DOUBLE', 'DECIMAL', 'NUMERIC', 'REAL'}
_TIME_TYPES = {'TIMESTAMP', 'DATETIME', 'DATE'}


def to_dm_value_for_column(kind, value, mysql_col_name):
    """根据目标 DM8 列类型生成更精确的字面量."""
    dm_col = DM_COLUMN_MAP.get(mysql_col_name.lower(), mysql_col_name.upper())
    col_type = DM_COLUMN_TYPES.get(dm_col, 'VARCHAR(4000)')
    up_type = (col_type or '').upper()

    if kind == 'null':
        return 'NULL'

    # 整型列: 字符串数字 -> 数字字面量 (避免隐式转换)
    if up_type in _INT_TYPES:
        if kind == 'num':
            # 整型不接受小数, 截断
            return value.split('.')[0]
        if kind == 'str':
            if re.fullmatch(r'-?\d+', value):
                return value
            # 字符串非纯数字 (例如 '2.0'), 尝试取整
            if re.fullmatch(r'-?\d+\.\d+', value):
                return value.split('.')[0]
            # 非数字字符串, 让 DM 隐式转换 (转成 ASCII 码)
            # 此处为安全起见, 输出 NULL 的替代是不可能的, 输出字面值让 DM 处理
            return to_dm_string_literal(value)
        return value

    # 小数/浮点列
    if up_type in _DEC_TYPES:
        if kind == 'num':
            return value
        if kind == 'str' and re.fullmatch(r'-?\d+(\.\d+)?', value):
            return value
        return to_dm_string_literal(value)

    # 时间列
    if up_type in _TIME_TYPES:
        if kind == 'str':
            m = _DATE_RE.match(value)
            if m:
                y, mo, d, h, mi, se = m.groups()
                return "TO_DATE('%04d-%02d-%02d %02d:%02d:%02d','YYYY-MM-DD HH24:MI:SS')" % (
                    int(y), int(mo), int(d), int(h), int(mi), int(se))
            m = _DATE_ONLY_RE.match(value)
            if m:
                y, mo, d = m.groups()
                return "TO_DATE('%04d-%02d-%02d','YYYY-MM-DD')" % (int(y), int(mo), int(d))
            return to_dm_string_literal(value)
        return value

    # 字符串/大字段列 (VARCHAR / CLOB / TEXT)
    if kind == 'str':
        # VARCHAR 长度校验
        limit = varchar_limit(col_type)
        if limit is not None:
            # 计算字符数 (DM8 默认长度语义按字符计, GB18030 中文 1 字符)
            if len(value) > limit:
                # 不截断, 仅在 stderr 警告; 由用户决定是否手动处理
                sys.stderr.write(
                    '  [警告] 列 %s 长度超限: %d > %d, 行值预览: %r\n'
                    % (dm_col, len(value), limit, value[:80]))
        return to_dm_string_literal(value)
    if kind == 'num':
        return value
    return value


# ===========================================================================
# 4. INSERT 语句生成
# ===========================================================================

def render_dm_insert(columns, rows):
    """
    rows: list[list[(kind, value)]]   已 classify 的多行值
    返回多条 INSERT 语句字符串 (用 \\n 连接).
    
    当 columns 为空时，使用默认列名列表。
    """
    # 如果没有指定列名，使用默认列名
    if not columns:
        columns = DEFAULT_COLUMNS
    
    dm_cols = [DM_COLUMN_MAP.get(c.lower(), c.upper()) for c in columns]
    col_clause = '(%s)' % ', '.join(dm_cols)

    out = []
    for row in rows:
        vals = []
        for idx, (kind, value) in enumerate(row):
            # 获取对应的MySQL列名
            mysql_col = columns[idx] if idx < len(columns) else DEFAULT_COLUMNS[idx] if idx < len(DEFAULT_COLUMNS) else f'col_{idx}'
            vals.append(to_dm_value_for_column(kind, value, mysql_col))
        out.append('INSERT INTO %s%s VALUES (%s);'
                   % (DM_QUALIFIED_TABLE, col_clause, ', '.join(vals)))
    return '\n'.join(out)


# ===========================================================================
# 5. 语句切分
# ===========================================================================

def split_statements(text):
    """按 ';' 切分语句, 跳过字符串/标识符/括号/注释内部."""
    out = []
    buf = []
    state = None
    depth = 0
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if state == 'sq':
            buf.append(c)
            if c == '\\' and i + 1 < n:
                buf.append(text[i + 1]); i += 2; continue
            if c == "'":
                if i + 1 < n and text[i + 1] == "'":
                    buf.append("'"); i += 2; continue
                state = None
            i += 1; continue
        if state == 'dq':
            buf.append(c)
            if c == '\\' and i + 1 < n:
                buf.append(text[i + 1]); i += 2; continue
            if c == '"':
                state = None
            i += 1; continue
        if state == 'bt':
            buf.append(c)
            if c == '`':
                state = None
            i += 1; continue
        if state == 'line_comment':
            buf.append(c)
            if c == '\n':
                state = None
            i += 1; continue
        if state == 'block_comment':
            buf.append(c)
            if c == '*' and i + 1 < n and text[i + 1] == '/':
                buf.append('/'); i += 2; state = None; continue
            i += 1; continue
        if c == "'":
            state = 'sq'; buf.append(c); i += 1; continue
        if c == '"':
            state = 'dq'; buf.append(c); i += 1; continue
        if c == '`':
            state = 'bt'; buf.append(c); i += 1; continue
        if c == '-' and i + 1 < n and text[i + 1] == '-':
            state = 'line_comment'; buf.append('-'); buf.append('-'); i += 2; continue
        if c == '/' and i + 1 < n and text[i + 1] == '*':
            state = 'block_comment'; buf.append('/'); buf.append('*'); i += 2; continue
        if c == '(':
            depth += 1; buf.append(c); i += 1; continue
        if c == ')':
            depth -= 1; buf.append(c); i += 1; continue
        if c == ';' and depth == 0:
            out.append(''.join(buf)); buf = []; i += 1; continue
        buf.append(c); i += 1
    if ''.join(buf).strip():
        out.append(''.join(buf))
    return out


# ===========================================================================
# 6. 主流程
# ===========================================================================

HEAD_TEMPLATE = """\
set define off;
TRUNCATE TABLE "AAS_VS"."VA_LIBRARY";
SET IDENTITY_INSERT "AAS_VS"."VA_LIBRARY" ON;
-- 数据插入SQL，一条数据一个insert语句
"""


def convert(input_path, output_path):
    with io.open(input_path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()

    parser = MysqlInsertParser()
    raw_statements = split_statements(content)

    out_lines = []
    insert_count = 0
    skipped = 0
    max_stmt_len = 0

    for stmt in raw_statements:
        s = stmt.strip()
        if not s:
            continue
        if not s[:20].upper().startswith('INSERT'):
            skipped += 1
            continue
        parsed = parser.parse(s)
        if not parsed:
            skipped += 1
            continue
        _, columns, value_rows = parsed
        if not value_rows:
            skipped += 1
            continue
        rows = [[classify_value(v) for v in row] for row in value_rows]
        rendered = render_dm_insert(columns, rows)
        out_lines.append(rendered)
        insert_count += len(rows)
        if len(rendered) > max_stmt_len:
            max_stmt_len = len(rendered)

    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with io.open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(HEAD_TEMPLATE)
        f.write('\n'.join(out_lines))
        f.write('\n\nSET IDENTITY_INSERT "AAS_VS"."VA_LIBRARY" OFF;\ncommit;\nexit;\n')

    return insert_count, skipped, max_stmt_len


def main():
    if len(sys.argv) >= 3:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
    elif len(sys.argv) == 2:
        input_path = sys.argv[1]
        base, _ = os.path.splitext(input_path)
        output_path = base + '_dm8.sql'
    else:
        sys.stderr.write(
            '用法: python mysql_to_dm8.py <输入MySQL脚本> <输出DM8脚本>\n'
            '示例: python mysql_to_dm8.py va_library.sql va_library_dm8.sql\n')
        sys.exit(2)

    if not os.path.isfile(input_path):
        sys.stderr.write('错误: 输入文件不存在: %s\n' % input_path)
        sys.exit(1)

    insert_count, skipped, max_stmt_len = convert(input_path, output_path)
    sys.stdout.write(
        '转换完成:\n'
        '  源文件:        %s\n'
        '  达梦8 输出:     %s\n'
        '  目标表:         %s\n'
        '  INSERT 条数:    %d\n'
        '  跳过语句:       %d\n'
        '  最长 INSERT:    %d 字符\n'
        % (input_path, output_path, DM_QUALIFIED_TABLE,
           insert_count, skipped, max_stmt_len))


if __name__ == '__main__':
    main()
