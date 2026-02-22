# yima/词法分析.py
# 易码词法分析器（官方关键词版）

from enum import Enum
from .错误 import 词法报错

class Token类型(Enum):
    # --- 核心动作 ---
    关键字_显示 = "显示"
    关键字_输入 = "输入"
    关键字_功能 = "功能"
    关键字_返回 = "返回"
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
    关键字_遍历 = "遍历"
    关键字_里的每一个 = "里的每一个"
    关键字_停下 = "停下"
    关键字_略过 = "略过"

    # --- 面向对象 ---
    关键字_定义图纸 = "定义图纸"
    关键字_造一个 = "造一个"
    关键字_它的 = "它的"

    # --- 运算符与逻辑 ---
    逻辑_而且 = "而且"
    逻辑_并且 = "并且"
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
    缩进 = "缩进"      # INDENT
    退缩 = "退缩"      # DEDENT

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

# 官方关键词词典。只保留一套标准词，避免同义词造成学习和维护成本。
多字词典 = {
    "里的每一个": Token类型.关键字_里的每一个,
    "否则如果": Token类型.关键字_否则如果,
    "定义图纸": Token类型.关键字_定义图纸,
    "如果出错": Token类型.关键字_如果出错,
    "的时候": Token类型.关键字_的时候,
    "造一个": Token类型.关键字_造一个,
    "功能": Token类型.关键字_功能,
    "它的": Token类型.关键字_它的,
    "显示": Token类型.关键字_显示,
    "如果": Token类型.关键字_如果,
    "重复": Token类型.关键字_重复,
    "遍历": Token类型.关键字_遍历,
    "叫做": Token类型.关键字_叫做,
    "停下": Token类型.关键字_停下,
    "略过": Token类型.关键字_略过,
    "需要": Token类型.关键字_需要,
    "返回": Token类型.关键字_返回,
    "引入": Token类型.关键字_引入,
    "中的": Token类型.关键字_中的,
    "尝试": Token类型.关键字_尝试,
    "不然": Token类型.关键字_不然,
    "而且": Token类型.逻辑_并且,
    "并且": Token类型.逻辑_并且,
    "或者": Token类型.逻辑_或者,
    "取反": Token类型.逻辑_取反,
    "输入": Token类型.关键字_输入,
    "就": Token类型.关键字_就,
    "当": Token类型.关键字_当,
    "次": Token类型.关键字_次,
    "用": Token类型.关键字_用,
    "对": Token类型.布尔_对,
    "错": Token类型.布尔_错,
    "空": Token类型.空值_空,
}

# 运算与标点符号
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
        # 兼容带 BOM 的 UTF-8 文件
        self.源码 = 源代码.lstrip('\ufeff')
        self.当前位置 = 0
        self.当前行 = 1
        self.当前列 = 1
        self.长度 = len(self.源码)

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

    def _是标识符字符(self, ch):
        return ch is not None and (ch.isalnum() or ch == '_' or '\u4e00' <= ch <= '\u9fff')

    def _匹配词边界(self, 词):
        词长 = len(词)
        if self._查看(词长) != 词:
            return False
        下一字符 = self._查看(词长 + 1)
        if 下一字符 and len(下一字符) > 词长:
            尾巴 = 下一字符[-1]
            if self._是标识符字符(尾巴):
                return False
        return True

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
            # 记录当前行的起始位置和前导空格数
            行起始位置 = self.当前位置
            前导空格数 = 0
            
            # 如果是在行首（哪怕是文件开头或者刚换过行），我们需要计算缩进
            if self.当前列 == 1:
                while self._当前字符() in ' \t':
                    if self._当前字符() == ' ':
                        前导空格数 += 1
                    elif self._当前字符() == '\t':
                        前导空格数 += 4  # 假设 tab 是 4 个空格
                    self._前进()
                
                # 如果这行只有空格和注释，就跳过它，不用生成缩进 token
                c = self._当前字符()
                if c == '\n' or c == '#' or self._查看(3) == "标注：" or c is None:
                    # 吃掉这行剩余的空间和注释，并吃掉换行符
                    self._跳过空白和注释()
                    if self._当前字符() == '\n':
                        self._前进()
                    continue
                    
                # 记录这行的真实缩进
                tokens.append(("INDENT_INFO", 前导空格数, self.当前行, self.当前列))
            
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
                
            # 处理字符串 (兼容中英文全半角双定引号)
            if c in '"\'“‘':
                起引号 = c
                止引号 = '”' if 起引号 == '“' else '’' if 起引号 == '‘' else 起引号
                文本内容 = ""
                self._前进() # 越过左边引号
                
                while self._当前字符() is not None and self._当前字符() != 止引号:
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
                    
                if self._当前字符() == 止引号:
                    self._前进() # 越过右边引号
                    # 检测是否包含模板变量 【...】
                    if '【' in 文本内容 and '】' in 文本内容:
                        tokens.append(Token(Token类型.模板文本, 文本内容, 行, 列))
                    else:
                        tokens.append(Token(Token类型.文本, 文本内容, 行, 列))
                else:
                    建议 = f"补上右引号【{止引号}】，或检查字符串里的转义符是否写错。"
                    raise 词法报错(f"字符串没有闭合，缺少右引号【{止引号}】。", 行, 列, 建议)
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

            # 匹配官方关键字（贪婪匹配，从长到短）
            匹配到了词 = False
            for 词, t类型 in 多字词典.items():
                if self._匹配词边界(词):
                    词长 = len(词)
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
            建议 = "请检查是否输入了非法字符，或是否把全角/半角符号写错。"
            raise 词法报错(f"我不认识这个符号或字：【{c}】", 行, 列, 建议)

        tokens.append(Token(Token类型.文件结束, '', self.当前行, self.当前列))
        
        # 处理缩进逻辑 (Python-style INDENT/DEDENT)
        精简Tokens = []
        缩进栈 = [0]
        上一Token是换行 = True
        
        for t in tokens:
            if isinstance(t, tuple) and t[0] == "INDENT_INFO":
                当前缩进 = t[1]
                行 = t[2]
                列 = t[3]
                
                if 当前缩进 > 缩进栈[-1]:
                    缩进栈.append(当前缩进)
                    精简Tokens.append(Token(Token类型.缩进, '', 行, 列))
                elif 当前缩进 < 缩进栈[-1]:
                    while len(缩进栈) > 1 and 当前缩进 < 缩进栈[-1]:
                        缩进栈.pop()
                        精简Tokens.append(Token(Token类型.退缩, '', 行, 列))
                    if 当前缩进 != 缩进栈[-1]:
                        建议 = "同一层级请使用一致缩进宽度，避免混用空格和 Tab。"
                        raise 词法报错(f"缩进不一致。期望缩进层级为 {缩进栈[-1]}，实际为 {当前缩进} 个空格。", 行, 列, 建议)
                continue
                
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
        
        # 文件结束时，弹出所有剩余的缩进
        eof_token = 精简Tokens.pop() if len(精简Tokens) > 0 and 精简Tokens[-1].类型 == Token类型.文件结束 else Token(Token类型.文件结束, '', self.当前行, self.当前列)
        
        if len(精简Tokens) > 0 and 精简Tokens[-1].类型 == Token类型.换行:
            精简Tokens.pop()
            
        while len(缩进栈) > 1:
            缩进栈.pop()
            精简Tokens.append(Token(Token类型.退缩, '', eof_token.行号, eof_token.列号))
            
        精简Tokens.append(eof_token)
        
        return 精简Tokens

