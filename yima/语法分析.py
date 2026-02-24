#
# Ownership Marker (Open Source Prep)
# Author: 景磊 (Jing Lei)
# Copyright (c) 2026 景磊
# Project: 易码 / Yima
# Marker-ID: YIMA-JINGLEI-CORE

__author__ = "景磊"
__copyright__ = "Copyright (c) 2026 景磊"
__marker_id__ = "YIMA-JINGLEI-CORE"


# yima/语法分析.py
# 易码语法分析器 - 通过中文句式生成 AST

from .词法分析 import Token类型
from .语法树 import *
from .错误 import 语法报错

class 语法分析器:
    def __init__(self, tokens):
        self.tokens = tokens
        self.当前位置 = 0
        self.长度 = len(tokens)

    def _当前Token(self):
        if self.当前位置 >= self.长度:
            return self.tokens[-1] # EOF
        return self.tokens[self.当前位置]

    def _前进(self):
        self.当前位置 += 1

    def _查看(self, 步数=1):
        idx = self.当前位置 + 步数
        if idx >= self.长度:
            return self.tokens[-1]
        return self.tokens[idx]

    def _token可读文本(self, token):
        if token is None:
            return "未知"
        特殊映射 = {
            Token类型.换行: "换行",
            Token类型.文件结束: "文件结束",
            Token类型.缩进: "缩进",
            Token类型.退缩: "退缩",
        }
        if token.类型 in 特殊映射:
            return 特殊映射[token.类型]
        if token.值 is not None and str(token.值) != "":
            return str(token.值)
        return token.类型.value

    def _吃掉(self, 期望类型, 报错消息=""):
        当前 = self._当前Token()
        if 当前.类型 == 期望类型:
            self._前进()
            return 当前
        
        # 报错处理，尽量用大白话
        读取到文本 = self._token可读文本(当前)
        如果不给报错 = f"此处应为【{期望类型.value}】，实际读取到【{读取到文本}】。"
        跳过消息 = 报错消息 if 报错消息 else 如果不给报错
        建议 = f"请检查当前位置前后是否缺少【{期望类型.value}】，或多写了其它符号。"
        raise 语法报错(跳过消息, 当前.行号, 当前.列号, 建议)

    def _跳过多余换行(self):
        while self._当前Token().类型 == Token类型.换行:
            self._前进()

    def _跳过容器空白(self):
        while self._当前Token().类型 in (Token类型.换行, Token类型.缩进, Token类型.退缩):
            self._前进()

    def 解析(self):
        语句列表 = []
        self._跳过多余换行()
        while self._当前Token().类型 != Token类型.文件结束:
            语句 = self._解析语句()
            if 语句:
                语句列表.append(语句)
            self._跳过多余换行()
            
        return 程序节点(语句列表)

    def _解析语句(self):
        当前 = self._当前Token()
        
        if 当前.类型 == Token类型.关键字_显示:
            return self._解析显示语句()
        elif 当前.类型 == Token类型.关键字_引入:
            return self._解析引入语句()
        elif 当前.类型 == Token类型.关键字_用:
            raise 语法报错(
                "【用 ... 中的 ...】写法已停用。请改为【引入 \"模块\" 叫做 名称】。",
                当前.行号,
                当前.列号,
                "示例：把 `用 \"math\" 中的 pi` 改为 `引入 \"math\" 叫做 pi`。",
            )
        elif 当前.类型 == Token类型.关键字_如果:
            return self._解析如果语句()
        elif 当前.类型 == Token类型.关键字_尝试:
            return self._解析尝试语句()
        elif 当前.类型 == Token类型.关键字_当:
            return self._解析当循环()
        elif 当前.类型 == Token类型.关键字_重复:
            return self._解析重复循环()
        elif 当前.类型 == Token类型.关键字_遍历:
            return self._解析遍历循环()
        elif 当前.类型 == Token类型.关键字_停下:
            停下Token = self._吃掉(Token类型.关键字_停下)
            return 跳出语句节点(停下Token.行号)
        elif 当前.类型 == Token类型.关键字_略过:
            略过Token = self._吃掉(Token类型.关键字_略过)
            return 继续语句节点(略过Token.行号)
        elif 当前.类型 == Token类型.关键字_功能:
            return self._解析定义函数()
        elif 当前.类型 == Token类型.关键字_返回:
            return self._解析返回语句()
        elif 当前.类型 == Token类型.关键字_定义图纸:
            return self._解析定义图纸()
        elif 当前.类型 == Token类型.关键字_它的:
            return self._解析它的语句()
        elif 当前.类型 == Token类型.标识符:
            后置 = self._查看(1)
            # 是否为直接赋值 A = B
            if 后置.类型 == Token类型.赋值符号:
                return self._解析直接赋值语句()
            # 是否为复合赋值 A += B
            if 后置.类型 in [Token类型.复合加等, Token类型.复合减等, Token类型.复合乘等, Token类型.复合除等]:
                return self._解析复合赋值语句()
            # 否则先解析为表达式，再检查是否有点赋值 (A.B = expr) 或索引赋值 (A[i] = expr)
            表达式 = self._解析表达式()
            # 检查是否是属性赋值
            if isinstance(表达式, 属性访问节点) and self._当前Token().类型 == Token类型.赋值符号:
                self._前进()  # 越过 =
                值 = self._解析表达式()
                if self._当前Token().类型 == Token类型.换行:
                    self._前进()
                return 属性设置节点(表达式.对象节点, 表达式.属性名, 值, 表达式.行号)
            # 检查是否是索引赋值
            if isinstance(表达式, 索引访问节点) and self._当前Token().类型 == Token类型.赋值符号:
                self._前进()  # 越过 =
                值 = self._解析表达式()
                if self._当前Token().类型 == Token类型.换行:
                    self._前进()
                return 索引设置节点(表达式.对象节点, 表达式.索引节点, 值, 表达式.行号)
            if self._当前Token().类型 == Token类型.换行:
                self._前进()
            return 表达式
        else:
            表达式 = self._解析表达式()
            if self._当前Token().类型 == Token类型.换行:
                self._前进()
            return 表达式

    def _解析引入语句(self):
        引入Token = self._吃掉(Token类型.关键字_引入)
        模块Token = self._吃掉(Token类型.文本, "【引入】后应使用引号包裹模块名，例如：引入 \"math\"")
        模块名 = 模块Token.值
        if self._当前Token().类型 != Token类型.关键字_叫做:
            raise 语法报错(
                "引入语句必须使用统一写法：`引入 \"模块\" 叫做 别名`。",
                self._当前Token().行号,
                self._当前Token().列号,
                "例如：引入 \"系统工具\" 叫做 系统",
            )
        self._前进()
        别名Token = self._吃掉(Token类型.标识符, "【叫做】后应提供模块别名。")
        别名 = 别名Token.值
            
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
        return 引入语句节点(模块名, 别名, 引入Token.行号)

    def _解析返回语句(self):
        返回Token = self._吃掉(Token类型.关键字_返回)
        # 支持空返回
        当前 = self._当前Token()
        if 当前.类型 in (Token类型.换行, Token类型.文件结束, Token类型.退缩):
            表达式 = None
        else:
            表达式 = self._解析表达式()
        return 返回语句节点(表达式, 返回Token.行号)

    def _解析定义图纸(self):
        自我Token = self._吃掉(Token类型.关键字_定义图纸)
        图纸名Token = self._吃掉(Token类型.标识符, "【定义图纸】后应填写类型名称。")
        图纸名 = 图纸名Token.值
        
        # 解析参数列表 (构造参数)
        参数列表 = []
        if self._当前Token().类型 == Token类型.左括号:
            self._前进()
            while self._当前Token().类型 != Token类型.右括号:
                词 = self._吃掉(Token类型.标识符, "参数必须是名称（标识符）。")
                参数列表.append(词.值)
                if self._当前Token().类型 == Token类型.逗号:
                    self._前进()
            self._吃掉(Token类型.右括号)
        elif self._当前Token().类型 == Token类型.关键字_需要:
            raise 语法报错(
                "图纸参数写法已统一为括号形式，不再支持【需要】。",
                self._当前Token().行号,
                self._当前Token().列号,
                "示例：定义图纸 玩家(名字, 血量)",
            )
                    
        代码块 = self._解析代码块()
        return 图纸定义节点(图纸名, 参数列表, 代码块, 自我Token.行号)

    def _解析它的语句(self):
        它的Token = self._吃掉(Token类型.关键字_它的)
        # 期待 它的 后面跟标识符
        属性Token = self._吃掉(Token类型.标识符, "【它的】后应为属性名。")
        属性名 = 属性Token.值
        
        # 检查是否是赋值
        if self._当前Token().类型 == Token类型.赋值符号:
            self._前进()  # 越过 =
            值 = self._解析表达式()
            if self._当前Token().类型 == Token类型.换行:
                self._前进()
            return 自身属性设置节点(属性名, 值, 它的Token.行号)
        else:
            # 解析为表达式上下文 (读取属性)
            节点 = 自身属性访问节点(属性名, 它的Token.行号)
            if self._当前Token().类型 == Token类型.换行:
                self._前进()
            return 节点

    def _解析定义函数(self):
        自我Token = self._当前Token()
        self._吃掉(Token类型.关键字_功能)
            
        函数名Token = self._吃掉(Token类型.标识符, "【功能】后应填写函数名，例如：功能 打招呼")
        函数名 = 函数名Token.值
        
        参数列表 = []
        当前 = self._当前Token()
        if 当前.类型 == Token类型.左括号:
            self._前进()
            while self._当前Token().类型 != Token类型.右括号:
                词 = self._吃掉(Token类型.标识符, "参数必须是名称（标识符）。")
                参数列表.append(词.值)
                if self._当前Token().类型 == Token类型.逗号:
                    self._前进()
                else: break
            self._吃掉(Token类型.右括号, "参数列表缺少右括号。")
        elif 当前.类型 == Token类型.关键字_需要:
            raise 语法报错(
                "功能参数写法已统一为括号形式，不再支持【需要】。",
                当前.行号,
                当前.列号,
                "示例：功能 求和(a, b)",
            )
                    
        代码块 = self._解析代码块()
        return 定义函数节点(函数名, 参数列表, 代码块, 函数名Token.行号)

    def _解析如果语句(self):
        条件分支列表 = []
        否则分支列表 = None
        
        self._吃掉(Token类型.关键字_如果)
        条件 = self._解析表达式()
        当前 = self._当前Token()
        if 当前.类型 == Token类型.关键字_就:
            self._前进()
        self._跳过多余换行()
        
        真分支 = self._解析代码块()
        条件分支列表.append((条件, 真分支))
        
        while self._当前Token().类型 == Token类型.关键字_否则如果:
            self._前进()
            新条件 = self._解析表达式()
            当前 = self._当前Token()
            if 当前.类型 == Token类型.关键字_就:
                self._前进()
            新真分支 = self._解析代码块()
            条件分支列表.append((新条件, 新真分支))
            
        if self._当前Token().类型 == Token类型.关键字_不然:
            self._前进()
            否则分支列表 = self._解析代码块()
            
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
            
        return 如果语句节点(条件分支列表, 否则分支列表)

    def _解析尝试语句(self):
        尝试Token = self._吃掉(Token类型.关键字_尝试)
        尝试代码块 = self._解析代码块()
        
        错误名 = None
        出错代码块 = []
        
        如果出错Token = self._当前Token()
        if 如果出错Token.类型 == Token类型.关键字_如果出错:
            self._前进() # 越过 如果出错
            
            # 统一写法：如果需要错误变量，必须写 叫做 变量名
            如果叫做Token = self._当前Token()
            if 如果叫做Token.类型 == Token类型.关键字_叫做:
                self._前进()
                名字Token = self._吃掉(Token类型.标识符, "【如果出错 叫做】后应填写错误变量名。")
                错误名 = 名字Token.值
            elif 如果叫做Token.类型 == Token类型.标识符:
                raise 语法报错(
                    "错误捕获变量必须写成【如果出错 叫做 变量名】。",
                    如果叫做Token.行号,
                    如果叫做Token.列号,
                    "示例：如果出错 叫做 错误",
                )
                
            出错代码块 = self._解析代码块()
            
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
            
        return 尝试语句节点(尝试代码块, 错误名, 出错代码块, 尝试Token.行号)

    def _解析当循环(self):
        self._吃掉(Token类型.关键字_当)
        条件 = self._解析表达式()
        self._吃掉(Token类型.关键字_的时候, "【当】条件后缺少【的时候】。")
        self._跳过多余换行()
        
        循环体 = self._解析代码块()
        
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
            
        return 当循环节点(条件, 循环体)

    def _解析重复循环(self):
        self._吃掉(Token类型.关键字_重复)
        次数表达式 = self._解析表达式()
        self._吃掉(Token类型.关键字_次, "【重复】语句缺少【次】。")
        
        # 可选：叫做 变量名（给循环计数器取名）
        循环变量名 = None
        if self._当前Token().类型 == Token类型.关键字_叫做:
            self._前进()
            变量Token = self._吃掉(Token类型.标识符, "【叫做】后应填写循环变量名。")
            循环变量名 = 变量Token.值
        
        self._跳过多余换行()
        
        循环体 = self._解析代码块()
        
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
            
        return 重复循环节点(次数表达式, 循环体, 循环变量名)

    def _解析遍历循环(self):
        # 官方写法：遍历 列表 里的每一个 叫做 元素
        self._吃掉(Token类型.关键字_遍历)
        列表表达式 = self._解析表达式()
        self._吃掉(Token类型.关键字_里的每一个, "【遍历】后应写【里的每一个】。")
        self._吃掉(Token类型.关键字_叫做)
        元素名Token = self._吃掉(Token类型.标识符, "【叫做】后应填写元素变量名。")
        循环体 = self._解析代码块()
        
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
            
        return 遍历循环节点(列表表达式, 元素名Token.值, 循环体)
        
    def _解析代码块(self):
        语句列表 = []
        self._跳过多余换行()
        
        # 代码块必须以缩进开始，避免漏缩进造成语义静默错误
        if self._当前Token().类型 != Token类型.缩进:
            当前 = self._当前Token()
            raise 语法报错("此处需要缩进代码块。", 当前.行号, 当前.列号)
            
        self._前进() # 越过 INDENT
        
        while self._当前Token().类型 != Token类型.退缩 and self._当前Token().类型 != Token类型.文件结束:
            语句 = self._解析语句()
            if 语句:
                语句列表.append(语句)
            self._跳过多余换行()
            
        if self._当前Token().类型 == Token类型.退缩:
            self._前进()
            
        return 语句列表

    def _解析显示语句(self):
        self._吃掉(Token类型.关键字_显示)
            
        表达式 = self._解析表达式()
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
        return 显示语句节点(表达式)

    def _解析直接赋值语句(self):
        名字Token = self._吃掉(Token类型.标识符)
        名字 = 名字Token.值
        
        连接符 = self._当前Token()
        self._前进() # 越过 =
        
        表达式 = self._解析表达式()
            
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
        return 变量设定节点(名字, 表达式)
        
    def _可选的函数参数解析(self):
        参数列表 = []
        if self._当前Token().类型 == Token类型.左括号:
            self._前进()
            while self._当前Token().类型 != Token类型.右括号:
                参数列表.append(self._解析表达式())
                if self._当前Token().类型 == Token类型.逗号:
                    self._前进()
                else: break
            self._吃掉(Token类型.右括号)
        return 参数列表

    def _解析复合赋值语句(self):
        名字Token = self._吃掉(Token类型.标识符)
        名字 = 名字Token.值
        操作Token = self._当前Token()
        self._前进()  # 越过 +=, -=, *=, /=
        
        # 将 X += expr 脱糖为 X = X + expr
        运算符映射 = {
            Token类型.复合加等: (Token类型.算符_加上, "+"),
            Token类型.复合减等: (Token类型.算符_减去, "-"),
            Token类型.复合乘等: (Token类型.算符_乘以, "*"),
            Token类型.复合除等: (Token类型.算符_除以, "/"),
        }
        右边表达式 = self._解析表达式()
        from .词法分析 import Token
        目标类型, 目标值 = 运算符映射[操作Token.类型]
        伪运算符 = Token(目标类型, 目标值, 操作Token.行号, 操作Token.列号)
        合成表达式 = 二元运算节点(变量访问节点(名字, 名字Token.行号), 伪运算符, 右边表达式, 操作Token.行号)
        
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
        return 变量设定节点(名字, 合成表达式)



    # --- 中文算符优先级定义 ---
    优先级字典 = {
        Token类型.算符_幂: 50,
        Token类型.算符_乘以: 40,
        Token类型.算符_除以: 40,
        Token类型.算符_整除: 40,
        Token类型.算符_取余: 40,
        Token类型.算符_加上: 30,
        Token类型.算符_减去: 30,
        Token类型.比较_大于: 20,
        Token类型.比较_小于: 20,
        Token类型.比较_等于: 20,
        Token类型.比较_不等于: 20,
        Token类型.比较_至少是: 20,
        Token类型.比较_最多是: 20,
        Token类型.逻辑_而且: 8,
        Token类型.逻辑_并且: 8,
        Token类型.逻辑_或者: 5,
    }

    def _获取优先级(self, token_type):
        return self.优先级字典.get(token_type, 0)

    def _解析表达式(self, 最低优先级=0):
        # 1. 解析前缀 (左操作数)
        左边节点 = self._解析基本表达式()
        
        # 2. 尝试吃掉中缀运算符 (右操作数)
        while True:
            当前 = self._当前Token()
            当前优先级 = self._获取优先级(当前.类型)
            
            if 当前优先级 == 0 or 当前优先级 <= 最低优先级:
                break
                
            运算符Token = 当前
            self._前进()
            
            右边节点 = self._解析表达式(当前优先级)
            左边节点 = 二元运算节点(左边节点, 运算符Token, 右边节点, 运算符Token.行号)
            
        return 左边节点

    def _解析基本表达式(self):
        当前 = self._当前Token()
        primary = None
        
        if 当前.类型 in (Token类型.逻辑_取反, Token类型.算符_减去):
            操作符Token = 当前
            self._前进()
            # 优先级设定为 15，介于比较运算和逻辑运算之间 (或者是数学强优先)
            优先级 = 15 if 操作符Token.类型 != Token类型.算符_减去 else 35
            操作数 = self._解析表达式(优先级)
            primary = 一元运算节点(操作符Token, 操作数, 操作符Token.行号)
            
        elif 当前.类型 == Token类型.关键字_输入:
            self._前进()
            提示节点 = self._解析表达式(0)
            primary = 输入表达式节点(提示节点)
            

        elif 当前.类型 == Token类型.关键字_造一个:
            造一个Token = 当前
            self._前进()
            图纸名Token = self._吃掉(Token类型.标识符, "【造一个】后应填写图纸名。")
            参数列表 = self._可选的函数参数解析()
            primary = 实例化节点(图纸名Token.值, 参数列表, 造一个Token.行号)
            
        elif 当前.类型 == Token类型.关键字_它的:
            self._前进()
            属性Token = self._吃掉(Token类型.标识符, "【它的】后应填写属性名。")
            primary = 自身属性访问节点(属性Token.值, 当前.行号)
            
        elif 当前.类型 in (Token类型.布尔_对, Token类型.布尔_错):
            # 直接用文本字面量节点包裹真假值，因为解释器对于它的处理就是返回值本身
            primary = 文本字面量节点(True if 当前.类型 == Token类型.布尔_对 else False)
            self._前进()
            
        elif 当前.类型 == Token类型.文本:
            primary = 文本字面量节点(当前.值)
            self._前进()
            
        elif 当前.类型 == Token类型.模板文本:
            primary = 模板字符串节点(当前.值)
            self._前进()
            
        elif 当前.类型 == Token类型.空值_空:
            primary = 文本字面量节点(None)
            self._前进()
            
        elif 当前.类型 == Token类型.数字:
            字面的 = 当前.值
            primary = 数字字面量节点(float(字面的) if '.' in 字面的 else int(字面的))
            self._前进()
            
        elif 当前.类型 == Token类型.标识符:
            primary = 变量访问节点(当前.值, 当前.行号)
            self._前进()
            
        elif 当前.类型 == Token类型.左括号:
            self._前进()
            primary = self._解析表达式(0)
            self._吃掉(Token类型.右括号, "括号未闭合，缺少右括号。")
            
        elif 当前.类型 == Token类型.左方括号:
            # 解析列表字面量 [1, 2, 3] 或 【1, 2, 3】
            行号 = 当前.行号
            self._前进()
            元素列表 = []
            self._跳过容器空白()
            while self._当前Token().类型 != Token类型.右方括号:
                元素列表.append(self._解析表达式())
                self._跳过容器空白()
                if self._当前Token().类型 == Token类型.逗号:
                    self._前进()
                    self._跳过容器空白()
                elif self._当前Token().类型 == Token类型.右方括号:
                    break
                else:
                    raise 语法报错("列表元素之间应使用逗号分隔。", self._当前Token().行号, self._当前Token().列号)
            self._吃掉(Token类型.右方括号, "列表未闭合，缺少右方括号。")
            primary = 列表字面量节点(元素列表, 行号)
            
        elif 当前.类型 == Token类型.左花括号:
            # 解析字典字面量 {"键": 值, ...}
            行号 = 当前.行号
            self._前进()
            键值对列表 = []
            self._跳过容器空白()
            while self._当前Token().类型 != Token类型.右花括号:
                # 解析键
                键表达式 = self._解析表达式()
                self._吃掉(Token类型.冒号, "字典的键和值之间必须使用冒号【:】。")
                self._跳过容器空白()
                # 解析值
                值表达式 = self._解析表达式()
                键值对列表.append((键表达式, 值表达式))
                self._跳过容器空白()
                
                if self._当前Token().类型 == Token类型.逗号:
                    self._前进()
                    self._跳过容器空白()
                elif self._当前Token().类型 == Token类型.右花括号:
                    break
                else:
                    raise 语法报错("字典元素之间应使用逗号分隔。", self._当前Token().行号, self._当前Token().列号)
            self._吃掉(Token类型.右花括号, "字典未闭合，缺少右花括号。")
            primary = 字典字面量节点(键值对列表, 行号)
            
        else:
            读取到文本 = self._token可读文本(当前)
            raise 语法报错(f"此处需要一个值或表达式，但读取到【{读取到文本}】。", 当前.行号, 当前.列号)
            
        # 解析后缀：属性访问(.) 和 动态调用()
        while True:
            if self._当前Token().类型 == Token类型.点:
                self._前进()
                属性Token = self._当前Token()
                if 属性Token.类型 != Token类型.标识符:
                    raise 语法报错("点号后必须是属性或方法名。", 属性Token.行号, 属性Token.列号)
                self._前进()
                primary = 属性访问节点(primary, 属性Token.值, 属性Token.行号)
                
            elif self._当前Token().类型 == Token类型.左方括号:
                左方刮Token = self._当前Token()
                self._前进()
                索引表达式 = self._解析表达式()
                self._吃掉(Token类型.右方括号, "中括号没有闭合！")
                primary = 索引访问节点(primary, 索引表达式, 左方刮Token.行号)
                
            elif self._当前Token().类型 == Token类型.左括号:
                左刮Token = self._当前Token()
                self._前进()
                参数列表 = []
                while self._当前Token().类型 != Token类型.右括号:
                    参数列表.append(self._解析表达式())
                    if self._当前Token().类型 == Token类型.逗号:
                        self._前进()
                    elif self._当前Token().类型 == Token类型.右括号:
                        break
                    else:
                        raise 语法报错("参数之间应使用逗号分隔。", self._当前Token().行号, self._当前Token().列号)
                self._吃掉(Token类型.右括号, "参数列表未闭合，缺少右括号。")
                primary = 动态调用节点(primary, 参数列表, 左刮Token.行号)
                
            else:
                break
                
        return primary

