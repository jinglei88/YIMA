# yima/词法分析.py
# 针对中文词组特别打造的词法分析器

from enum import Enum, auto
from .错误 import 词法报错

class Token类型(Enum):
    # --- 核心动作 ---
    关键字_显示 = "显示"
    关键字_询问 = "询问"
    关键字_功能 = "功能"
    关键字_交出 = "交出"
    关键字_引入 = "引入"
    关键字_用 = "用"
    关键字_中的 = "中的"
    关键字_叫做 = "叫做"
    关键字_需要 = "需要"

    # --- 逻辑控制 ---
    关键字_如果 = "如果"
    关键字_就 = "就"
    关键字_不然 = "不然"
    关键字_否则如果 = "否则如果"
    关键字_尝试 = "尝试"
    关键字_如果出错 = "如果出错"

    # --- 循环 ---
    关键字_当 = "当"
    关键字_的时候 = "的时候"
    关键字_重复 = "重复"
    关键字_次 = "次"
    关键字_取出 = "取出"
    关键字_里的每一个 = "里的每一个"
    关键字_完事 = "完事"
    关键字_停下 = "停下"
    关键字_略过 = "略过"

    # --- 面向对象 ---
    关键字_制造图纸 = "制造图纸"
    关键字_制造 = "制造"
    关键字_它的 = "它的"

    # --- 运算符与逻辑 ---
    逻辑_而且 = "而且"
    逻辑_或者 = "或者"
    逻辑_取反 = "取反"
    
    算符_加上 = "加上"
    算符_减去 = "减去"
    算符_乘以 = "乘以"
    算符_除以 = "除以"
    算符_取余 = "取余"
    算符_幂 = "幂"
    算符_整除 = "整除"
    
    比较_大于 = "大于"
    比较_小于 = "小于"
    比较_等于 = "等于"
    比较_不等于 = "不等于"
    比较_至少是 = "至少是"
    比较_最多是 = "最多是"

    # --- 数据字面量 ---
    数字 = "数字"
    文本 = "文本"
    模板文本 = "模板文本"
    布尔_对 = "对"
    布尔_错 = "错"
    空值_空 = "空"

    # --- 标点符号与特殊结构 ---
    标识符 = "标识符"
    逗号 = "逗号"
    点 = "点"
    冒号 = "冒号"
    左括号 = "左括号"
    右括号 = "右括号"
    左方括号 = "左方括号"
    右方括号 = "右方括号"
    左花括号 = "左花括号"
    右花括号 = "右花括号"
    赋值符号 = "赋值符号"
    复合加等 = "复合加等"
    复合减等 = "复合减等"
    复合乘等 = "复合乘等"
    复合除等 = "复合除等"
    换行 = "换行"
    文件结束 = "EOF"

# 所有长词组大全，按长度降序排列，确保优先匹配长词（贪婪匹配）
多字词典 = {
    "里的每一个": Token类型.关键字_里的每一个,
    "否则如果": Token类型.关键字_否则如果,
    "制造图纸": Token类型.关键字_制造图纸,
    "如果出错": Token类型.关键字_如果出错,
    "的时候": Token类型.关键字_的时候,
    "制造": Token类型.关键字_制造,
    "功能": Token类型.关键字_功能,
    "完事": Token类型.关键字_完事,
    "它的": Token类型.关键字_它的,
    "显示": Token类型.关键字_显示,
    "如果": Token类型.关键字_如果,
    "重复": Token类型.关键字_重复,
    "取出": Token类型.关键字_取出,
    "叫做": Token类型.关键字_叫做,
    "停下": Token类型.关键字_停下,
    "略过": Token类型.关键字_略过,
    "需要": Token类型.关键字_需要,
    "交出": Token类型.关键字_交出,
    "引入": Token类型.关键字_引入,
    "中的": Token类型.关键字_中的,
    "尝试": Token类型.关键字_尝试,
    "不然": Token类型.关键字_不然,
    "而且": Token类型.逻辑_而且,
    "或者": Token类型.逻辑_或者,
    "取反": Token类型.逻辑_取反,
    "问": Token类型.关键字_询问,
    "就": Token类型.关键字_就,
    "当": Token类型.关键字_当,
    "次": Token类型.关键字_次,
    "用": Token类型.关键字_用,
    "对": Token类型.布尔_对,
    "错": Token类型.布尔_错,
    "空": Token类型.空值_空,
}

# 兼容符号
符号典 = {
    "**": Token类型.算符_幂,
    "//": Token类型.算符_整除,
    "+=": Token类型.复合加等,
    "-=": Token类型.复合减等,
    "*=": Token类型.复合乘等,
    "/=": Token类型.复合除等,
    ">=": Token类型.比较_至少是,
    "<=": Token类型.比较_最多是,
    "==": Token类型.比较_等于,
    "!=": Token类型.比较_不等于,
    "=": Token类型.赋值符号,
    "+": Token类型.算符_加上,
    "-": Token类型.算符_减去,
    "*": Token类型.算符_乘以,
    "/": Token类型.算符_除以,
    "%": Token类型.算符_取余,
    ">": Token类型.比较_大于,
    "<": Token类型.比较_小于,
    "!": Token类型.逻辑_取反,
    "（": Token类型.左括号,
    "(": Token类型.左括号,
    "）": Token类型.右括号,
    ")": Token类型.右括号,
    "。": Token类型.点,
    ".": Token类型.点,
    "，": Token类型.逗号,
    ",": Token类型.逗号,
    "【": Token类型.左方括号,
    "[": Token类型.左方括号,
    "】": Token类型.右方括号,
    "]": Token类型.右方括号,
    "{": Token类型.左花括号,
    "}": Token类型.右花括号,
    ":": Token类型.冒号,
    "：": Token类型.冒号,
}


class Token:
    def __init__(self, token_type, value, line, col):
        self.类型 = token_type
        self.值 = value
        self.行号 = line
        self.列号 = col

    def __repr__(self):
        return f"Token({self.类型.name}, '{self.值}', 行={self.行号}, 列={self.列号})"


class 词法分析器:
    def __init__(self, 源代码: str):
        self.源码 = 源代码
        self.当前位置 = 0
        self.当前行 = 1
        self.当前列 = 1
        self.长度 = len(源代码)

    def _前进(self, 步数=1):
        for _ in range(步数):
            if self.当前位置 < self.长度:
                if self.源码[self.当前位置] == '\n':
                    self.当前行 += 1
                    self.当前列 = 1
                else:
                    self.当前列 += 1
                self.当前位置 += 1

    def _当前字符(self):
        if self.当前位置 >= self.长度:
            return None
        return self.源码[self.当前位置]

    def _查看(self, 向前看几位):
        if self.当前位置 + 向前看几位 > self.长度:
            return None
        return self.源码[self.当前位置 : self.当前位置 + 向前看几位]

    def _跳过空白和注释(self):
        while self._当前字符() is not None:
            c = self._当前字符()
            if c in ' \t\r':
                self._前进()
            # 井号注释
            elif c == '#':
                while self._当前字符() is not None and self._当前字符() != '\n':
                    self._前进()
            # 中文标注
            elif self._查看(3) == "标注：":
                while self._当前字符() is not None and self._当前字符() != '\n':
                    self._前进()
            else:
                break

    def 分析(self) -> list[Token]:
        tokens = []
        
        while self.当前位置 < self.长度:
            self._跳过空白和注释()
            
            c = self._当前字符()
            if c is None:
                break
                
            行, 列 = self.当前行, self.当前列
            
            # 换行
            if c == '\n':
                tokens.append(Token(Token类型.换行, '\n', 行, 列))
                self._前进()
                continue
                
            # 处理字符串 (兼容易双引号和单引号)
            if c in '"\'':
                引号类型 = c
                文本内容 = ""
                self._前进() # 越过左边引号
                
                while self._当前字符() is not None and self._当前字符() != 引号类型:
                    if self._当前字符() == '\\':
                        self._前进()
                        转义字 = self._当前字符()
                        if 转义字 == 'n':
                            文本内容 += '\n'
                        elif 转义字 == 't':
                            文本内容 += '\t'
                        elif 转义字 == '\\':
                            文本内容 += '\\'
                        elif 转义字 == '"':
                            文本内容 += '"'
                        elif 转义字 == "'":
                            文本内容 += "'"
                        else:
                            文本内容 += '\\' + (转义字 or '')
                        self._前进()
                        continue
                    文本内容 += self._当前字符()
                    self._前进()
                    
                if self._当前字符() == 引号类型:
                    self._前进() # 越过右边引号
                    # 检测是否包含模板变量 【...】
                    if '【' in 文本内容 and '】' in 文本内容:
                        tokens.append(Token(Token类型.模板文本, 文本内容, 行, 列))
                    else:
                        tokens.append(Token(Token类型.文本, 文本内容, 行, 列))
                else:
                    raise 词法报错(f"字符串没有写完，找不到右边的 {引号类型} 呢！", 行, 列)
                continue

            # 处理数字 (整数和小数)
            if c.isdigit():
                数字内容 = ""
                小点个数 = 0
                while self._当前字符() is not None and (self._当前字符().isdigit() or self._当前字符() == '.'):
                    if self._当前字符() == '.':
                        小点个数 += 1
                        if 小点个数 > 1:
                            break
                    数字内容 += self._当前字符()
                    self._前进()
                tokens.append(Token(Token类型.数字, 数字内容, 行, 列))
                continue

            # 尝试匹配多字词汇 (贪婪匹配，从长到短)
            匹配到了词 = False
            for 词, t类型 in 多字词典.items():
                词长 = len(词)
                if self._查看(词长) == 词:
                    # 如果词是纯文字（可以做标识符），那么后面一个字符不能也是文字，否则就是长名字的一部分
                    下一字符 = self._查看(词长 + 1)
                    if 下一字符 and len(下一字符) > 词长:
                        尾巴 = 下一字符[-1]
                        # 检查尾巴是不是中英文或数字或下划线
                        if 尾巴.isalnum() or 尾巴 == '_' or '\u4e00' <= 尾巴 <= '\u9fff':
                            # 未完全匹配单词边界，跳过
                            continue
                    
                    tokens.append(Token(t类型, 词, 行, 列))
                    self._前进(词长)
                    匹配到了词 = True
                    break
            if 匹配到了词:
                continue
                
            # 尝试匹配符号
            匹配到了符号 = False
            for 符长 in [2, 1]:  # 先看两位的符号如 >=, ==, !=
                片段 = self._查看(符长)
                if 片段 in 符号典:
                    tokens.append(Token(符号典[片段], 片段, 行, 列))
                    self._前进(符长)
                    匹配到了符号 = True
                    break
            if 匹配到了符号:
                continue

            # 标识符 (变量名，支持中文/英文/数字/下划线组合)
            # 中文范围大致用 \u4e00-\u9fa5 判定，或者简单点就是 isalpha / _ 
            c = self._当前字符()
            if c.isalpha() or c == '_' or '\u4e00' <= c <= '\u9fff':
                标识符内容 = ""
                while self._当前字符() is not None:
                    ch = self._当前字符()
                    if ch.isalnum() or ch == '_' or '\u4e00' <= ch <= '\u9fff':
                        标识符内容 += ch
                        self._前进()
                    else:
                        break
                tokens.append(Token(Token类型.标识符, 标识符内容, 行, 列))
                continue

            # 如果都匹配不上，就是一个词法错误
            raise 词法报错(f"我不认识这个符号或字：【{c}】", 行, 列)

        tokens.append(Token(Token类型.文件结束, '', self.当前行, self.当前列))
        
        # 过滤多余的连续换行，简化 Parser 处理
        精简Tokens = []
        上一Token是换行 = True
        for t in tokens:
            if t.类型 == Token类型.换行:
                if not 上一Token是换行:
                    精简Tokens.append(t)
                上一Token是换行 = True
            else:
                精简Tokens.append(t)
                上一Token是换行 = False
                
        # 移除文件开头末尾的换行
        if len(精简Tokens) > 0 and 精简Tokens[0].类型 == Token类型.换行:
            精简Tokens.pop(0)
        if len(精简Tokens) > 1 and 精简Tokens[-2].类型 == Token类型.换行: # -1 是 EOF
            p = 精简Tokens.pop(-2)
        
        return 精简Tokens

