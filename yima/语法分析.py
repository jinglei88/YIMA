# yima/语法分析.py
# 易码大白话解析器 - 通过匹配大白话句式生成 AST

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

    def _吃掉(self, 期望类型, 报错消息=""):
        当前 = self._当前Token()
        if 当前.类型 == 期望类型:
            self._前进()
            return 当前
        
        # 报错处理，尽量用大白话
        如果不给报错 = f"我期望在这里看到【{期望类型.value}】，但你写的是【{当前.值}】哦。"
        跳过消息 = 报错消息 if 报错消息 else 如果不给报错
        raise 语法报错(跳过消息, 当前.行号, 当前.列号)

    def _跳过多余换行(self):
        while self._当前Token().类型 == Token类型.换行:
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
        
        if 当前.类型 == Token类型.关键字_显示 or 当前.类型 == Token类型.关键字_说:
            return self._解析显示语句()
        elif 当前.类型 == Token类型.关键字_把 or 当前.类型 == Token类型.关键字_让:
            return self._解析设定语句()
        elif 当前.类型 == Token类型.关键字_引入:
            return self._解析引入语句()
        elif 当前.类型 == Token类型.关键字_如果:
            return self._解析如果语句()
        elif 当前.类型 == Token类型.关键字_尝试:
            return self._解析尝试语句()
        elif 当前.类型 == Token类型.关键字_当:
            return self._解析当循环()
        elif 当前.类型 == Token类型.关键字_重复:
            return self._解析重复循环()
        elif 当前.类型 == Token类型.关键字_取出:
            return self._解析遍历循环()
        elif 当前.类型 == Token类型.关键字_停下:
            self._吃掉(Token类型.关键字_停下)
            return 跳出语句节点()
        elif 当前.类型 == Token类型.关键字_略过:
            self._吃掉(Token类型.关键字_略过)
            return 继续语句节点()
        elif 当前.类型 == Token类型.关键字_功能:
            return self._解析定义函数()
        elif 当前.类型 == Token类型.关键字_交出:
            return self._解析交出语句()
        elif 当前.类型 == Token类型.标识符:
            后置 = self._查看(1)
            # 是否为直接赋值 A = B 或 A 是 B 或 A 变成 B 或 A 是一份清单()
            if 后置.类型 in [Token类型.关键字_设定为, Token类型.比较_等于, Token类型.关键字_变成, Token类型.关键字_是一份清单, Token类型.关键字_是一堆]:
                return self._解析直接赋值语句()
            # 如果不是直接赋值，那就回退按照表达式来解析
            表达式 = self._解析表达式()
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
        模块Token = self._吃掉(Token类型.文本, "【引入】后面得跟个用引号包起来的模块名称哦。比如：引入 \"math\"")
        模块名 = 模块Token.值
        别名 = None
        if self._当前Token().类型 == Token类型.关键字_叫做:
            self._前进()
            别名Token = self._吃掉(Token类型.标识符, "【叫做】后面得跟个别名哦。")
            别名 = 别名Token.值
            
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
        return 引入语句节点(模块名, 别名, 引入Token.行号)

    def _解析交出语句(self):
        self._吃掉(Token类型.关键字_交出)
        # 支持空返回
        当前 = self._当前Token()
        if 当前.类型 in (Token类型.换行, Token类型.文件结束, Token类型.关键字_结束, Token类型.关键字_学完了):
            表达式 = None
        else:
            表达式 = self._解析表达式()
        return 交出语句节点(表达式)

    def _解析定义函数(self):
        自我Token = self._当前Token()
        # 兼容 功能、教你、定义
        if 自我Token.类型 == Token类型.关键字_功能:
            self._吃掉(Token类型.关键字_功能)
        else:
            self._前进() # 越过未吃掉的等义词
            
        函数名Token = self._吃掉(Token类型.标识符, "定义指令后面得跟一个名字哦。比如：教你 打招呼")
        函数名 = 函数名Token.值
        
        参数列表 = []
        当前 = self._当前Token()
        # 支持 教你 打招呼 收取 名字, 年龄
        if 当前.类型 == Token类型.左括号:
            self._前进()
            while self._当前Token().类型 != Token类型.右括号:
                词 = self._吃掉(Token类型.标识符, "参数得是一个名字（标识符）。")
                参数列表.append(词.值)
                if self._当前Token().类型 == Token类型.逗号:
                    self._前进()
                else: break
            self._吃掉(Token类型.右括号, "参数写完记得把右括号补上。")
        elif 当前.类型 in (Token类型.关键字_需要, Token类型.标识符): # 如果看到的是个标识符，可能是 "收取" 或 "需要"
            if 当前.类型 == Token类型.关键字_需要:
                self._前进()
            elif 当前.值 in ("收取", "接受", "需要"):
                self._前进() # 越过口语修饰词
                
            while self._当前Token().类型 not in (Token类型.换行, Token类型.文件结束, Token类型.关键字_结束, Token类型.关键字_学完了, Token类型.关键字_搞定, Token类型.关键字_完事):
                词 = self._当前Token()
                if 词.类型 == Token类型.标识符:
                    参数列表.append(词.值)
                    self._前进()
                if self._当前Token().类型 == Token类型.逗号:
                    self._前进()
                elif self._当前Token().类型 == Token类型.标识符:
                    # 如果又是一个标识符，并且没逗号，那么如果是 "和" 也可以当逗号
                    if self._当前Token().值 == "和":
                        self._前进()
                    else:
                        pass # 处理连续的标识符可能出错，这里原逻辑是 pass
                else:
                    break
                    
        self._跳过多余换行()
        代码块 = self._解析代码块(截止标识=[Token类型.关键字_学完了, Token类型.关键字_结束, Token类型.关键字_搞定, Token类型.关键字_完事])
        
        结束符 = self._当前Token()
        if 结束符.类型 in (Token类型.关键字_学完了, Token类型.关键字_结束, Token类型.关键字_搞定, Token类型.关键字_完事):
            self._前进()
            if self._当前Token().类型 == Token类型.换行:
                self._前进()
            return 定义函数节点(函数名, 参数列表, 代码块, 函数名Token.行号)
        else:
            raise 语法报错("定义完动作以后，记得要说一句【结束】哦。", 结束符.行号, 结束符.列号)

    def _解析如果语句(self):
        条件分支列表 = []
        否则分支列表 = None
        
        self._吃掉(Token类型.关键字_如果)
        条件 = self._解析表达式()
        # “的话”或者“就”变成可选的，更口语化
        当前 = self._当前Token()
        if 当前.类型 in (Token类型.关键字_的话, Token类型.关键字_就):
            self._前进()
        self._跳过多余换行()
        
        真分支 = self._解析代码块(截止标识=[
            Token类型.关键字_否则如果,
            Token类型.关键字_不然的话,
            Token类型.关键字_不然,
            Token类型.关键字_结束,
            Token类型.关键字_搞定,
            Token类型.关键字_完事
        ])
        条件分支列表.append((条件, 真分支))
        
        while self._当前Token().类型 == Token类型.关键字_否则如果:
            self._前进()
            新条件 = self._解析表达式()
            当前 = self._当前Token()
            if 当前.类型 in (Token类型.关键字_的话, Token类型.关键字_就):
                self._前进()
            self._跳过多余换行()
            新真分支 = self._解析代码块(截止标识=[
                Token类型.关键字_否则如果,
                Token类型.关键字_不然的话,
                Token类型.关键字_不然,
                Token类型.关键字_结束,
                Token类型.关键字_搞定,
                Token类型.关键字_完事
            ])
            条件分支列表.append((新条件, 新真分支))
            
        if self._当前Token().类型 in (Token类型.关键字_不然的话, Token类型.关键字_不然):
            self._前进()
            self._跳过多余换行()
            否则分支列表 = self._解析代码块(截止标识=[Token类型.关键字_结束, Token类型.关键字_搞定, Token类型.关键字_完事])
            
        结束符 = self._当前Token()
        if 结束符.类型 in (Token类型.关键字_结束, Token类型.关键字_搞定, Token类型.关键字_完事):
            self._前进()
        else:
            raise 语法报错("逻辑分支写完了，记得要在末尾加上【搞定】或【完事】哦。", 结束符.行号, 结束符.列号)
        
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
            
        return 如果语句节点(条件分支列表, 否则分支列表)

    def _解析尝试语句(self):
        尝试Token = self._吃掉(Token类型.关键字_尝试)
        self._跳过多余换行()
        
        尝试代码块 = self._解析代码块(截止标识=[
            Token类型.关键字_如果出错,
            Token类型.关键字_结束,
            Token类型.关键字_搞定,
            Token类型.关键字_完事
        ])
        
        错误名 = None
        出错代码块 = []
        
        如果出错Token = self._当前Token()
        if 如果出错Token.类型 == Token类型.关键字_如果出错:
            self._前进() # 越过 如果出错
            
            # 有没有叫做 xxx 
            如果叫做Token = self._当前Token()
            if 如果叫做Token.类型 == Token类型.关键字_叫做:
                self._前进()
                名字Token = self._吃掉(Token类型.标识符, "【如果出错 叫做】的后面得跟个变量名字哦。")
                错误名 = 名字Token.值
                
            self._跳过多余换行()
            出错代码块 = self._解析代码块(截止标识=[Token类型.关键字_结束, Token类型.关键字_搞定, Token类型.关键字_完事])
            
        结束符 = self._当前Token()
        if 结束符.类型 in (Token类型.关键字_结束, Token类型.关键字_搞定, Token类型.关键字_完事):
            self._前进()
        else:
            raise 语法报错("尝试逻辑写完了，记得要在末尾加上【搞定】或【完事】哦。", 结束符.行号, 结束符.列号)
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
            
        return 尝试语句节点(尝试代码块, 错误名, 出错代码块, 尝试Token.行号)

    def _解析当循环(self):
        self._吃掉(Token类型.关键字_当)
        条件 = self._解析表达式()
        self._吃掉(Token类型.关键字_的时候, "【当】的条件写完后，别忘了加【的时候】哦。")
        self._跳过多余换行()
        
        循环体 = self._解析代码块(截止标识=[Token类型.关键字_结束, Token类型.关键字_搞定, Token类型.关键字_完事])
        
        结束符 = self._当前Token()
        if 结束符.类型 in (Token类型.关键字_结束, Token类型.关键字_搞定, Token类型.关键字_完事):
            self._前进()
        else:
            raise 语法报错("循环逻辑写完了，记得要在末尾加上【搞定】或【完事】哦。", 结束符.行号, 结束符.列号)
        
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
            
        return 当循环节点(条件, 循环体)

    def _解析重复循环(self):
        self._吃掉(Token类型.关键字_重复)
        次数表达式 = self._解析表达式()
        self._吃掉(Token类型.关键字_次, "要告诉我重复多少【次】哦。")
        self._跳过多余换行()
        
        循环体 = self._解析代码块(截止标识=[Token类型.关键字_结束, Token类型.关键字_搞定, Token类型.关键字_完事])
        
        结束符 = self._当前Token()
        if 结束符.类型 in (Token类型.关键字_结束, Token类型.关键字_搞定, Token类型.关键字_完事):
            self._前进()
        else:
            raise 语法报错("循环逻辑写完了，记得要在末尾加上【搞定】或【完事】哦。", 结束符.行号, 结束符.列号)
        
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
            
        return 重复循环节点(次数表达式, 循环体)

    def _解析遍历循环(self):
        # 取出 列表 里的每一个 叫做 元素
        self._吃掉(Token类型.关键字_取出)
        列表表达式 = self._解析表达式()
        self._吃掉(Token类型.关键字_里的每一个)
        self._吃掉(Token类型.关键字_叫做)
        元素名Token = self._吃掉(Token类型.标识符, "【叫做】后面得跟个变量名字哦。")
        self._跳过多余换行()
        
        循环体 = self._解析代码块(截止标识=[Token类型.关键字_结束, Token类型.关键字_搞定, Token类型.关键字_完事])
        
        结束符 = self._当前Token()
        if 结束符.类型 in (Token类型.关键字_结束, Token类型.关键字_搞定, Token类型.关键字_完事):
            self._前进()
        else:
            raise 语法报错("循环逻辑写完了，记得要在末尾加上【搞定】或【完事】哦。", 结束符.行号, 结束符.列号)
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
            
        return 遍历循环节点(列表表达式, 元素名Token.值, 循环体)
        
    def _解析代码块(self, 截止标识):
        语句列表 = []
        self._跳过多余换行()
        while self._当前Token().类型 not in 截止标识 and self._当前Token().类型 != Token类型.文件结束:
            语句 = self._解析语句()
            if 语句:
                语句列表.append(语句)
            self._跳过多余换行()
        return 语句列表

    def _解析显示语句(self):
        当前Token = self._当前Token()
        if 当前Token.类型 == Token类型.关键字_说:
            self._吃掉(Token类型.关键字_说)
        else:
            self._吃掉(Token类型.关键字_显示)
            
        表达式 = self._解析表达式()
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
        return 显示语句节点(表达式)

    def _解析直接赋值语句(self):
        名字Token = self._吃掉(Token类型.标识符)
        名字 = 名字Token.值
        
        连接符 = self._当前Token()
        self._前进() # 越过 =, 是, 变成, 是一份清单, 是一堆
        
        if 连接符.类型 in (Token类型.关键字_是一份清单, Token类型.关键字_是一堆):
            参数列表 = self._可选的函数参数解析()
            表达式 = 函数调用节点("新列表", 参数列表, 连接符.行号)
        else:
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

    def _解析设定语句(self):
        当前Token = self._当前Token()
        
        # 支持三种语法：
        # 1. 极致小白话: 让 变量 = 表达式    
        if 当前Token.类型 == Token类型.关键字_让:
            self._吃掉(Token类型.关键字_让)
            标签Token = self._当前Token()
            if 标签Token.类型 != Token类型.标识符:
                raise 语法报错("【让】的后面应该跟一个变量名哦。如：让 数字 = 1", 标签Token.行号, 标签Token.列号)
            名字 = 标签Token.值
            self._前进()
            
            # 支持 “设为”、“=”、“是”、“变成”、“是一份清单”
            如果等于 = self._当前Token()
            if 如果等于.类型 not in (Token类型.比较_等于, Token类型.关键字_设定为, Token类型.关键字_变成, Token类型.关键字_是一份清单, Token类型.关键字_是一堆):
                raise 语法报错("【让 某物】后面得跟一个等号或者【是】【变成】哦。", 如果等于.行号, 如果等于.列号)
            self._前进()
            
            if 如果等于.类型 in (Token类型.关键字_是一份清单, Token类型.关键字_是一堆):
                参数列表 = self._可选的函数参数解析()
                表达式 = 函数调用节点("新列表", 参数列表, 如果等于.行号)
            else:
                表达式 = self._解析表达式()
            
        # 2. 把 变量 设定为 表达式 (旧语法)
        else:
            self._吃掉(Token类型.关键字_把)
            标签Token = self._当前Token()
            if 标签Token.类型 != Token类型.标识符:
                raise 语法报错("【把】的后面应该跟一个名字（比如变量名），而不是别的哦。", 标签Token.行号, 标签Token.列号)
            名字 = 标签Token.值
            self._前进()
            self._吃掉(Token类型.关键字_设定为, "少了【设定为】哦！比如：把 名字 设定为 1")
            表达式 = self._解析表达式()
            
        if self._当前Token().类型 == Token类型.换行:
            self._前进()
            
        return 变量设定节点(名字, 表达式)

    # --- 中文算符优先级定义 ---
    优先级字典 = {
        Token类型.算符_乘以: 40,
        Token类型.算符_除以: 40,
        Token类型.算符_取余: 40,
        Token类型.算符_加上: 30,
        Token类型.算符_减去: 30,
        Token类型.算符_拼接: 30,
        Token类型.比较_大于: 20,
        Token类型.比较_小于: 20,
        Token类型.比较_等于: 20,
        Token类型.比较_不等于: 20,
        Token类型.比较_至少是: 20,
        Token类型.比较_最多是: 20,
        Token类型.逻辑_而且: 8,
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
        
        if 当前.类型 in (Token类型.逻辑_取反, Token类型.逻辑_反过来说):
            操作符Token = 当前
            self._前进()
            # 优先级设定为 15，介于比较运算和逻辑运算之间
            操作数 = self._解析表达式(15)
            primary = 一元运算节点(操作符Token, 操作数, 操作符Token.行号)
            
        elif 当前.类型 == Token类型.关键字_询问:
            self._前进()
            提示节点 = self._解析表达式(0)
            primary = 询问表达式节点(提示节点)
            
        elif 当前.类型 in (Token类型.关键字_是一份清单, Token类型.关键字_是一堆):
            自我Token = 当前
            self._前进()
            参数列表 = self._可选的函数参数解析()
            primary = 函数调用节点("新列表", 参数列表, 自我Token.行号)
            
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
            
        elif 当前.类型 in (Token类型.空值_无, Token类型.空值_空的):
            primary = 文本字面量节点(None if 当前.类型 == Token类型.空值_无 else "")
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
            self._吃掉(Token类型.右括号, "括号没有闭合哦，是不是忘了加右括号？")
            
        elif 当前.类型 == Token类型.左方括号:
            # 解析列表字面量 [1, 2, 3] 或 【1, 2, 3】
            行号 = 当前.行号
            self._前进()
            元素列表 = []
            while self._当前Token().类型 != Token类型.右方括号:
                元素列表.append(self._解析表达式())
                if self._当前Token().类型 == Token类型.逗号:
                    self._前进()
                elif self._当前Token().类型 == Token类型.右方括号:
                    break
                else:
                    raise 语法报错("列表的元素之间要用逗号隔开哦。", self._当前Token().行号, self._当前Token().列号)
            self._吃掉(Token类型.右方括号, "列表没有闭合哦，是不是忘了加右方括号？")
            primary = 列表字面量节点(元素列表, 行号)
            
        elif 当前.类型 == Token类型.左花括号:
            # 解析字典字面量 {"键": 值, ...}
            行号 = 当前.行号
            self._前进()
            键值对列表 = []
            while self._当前Token().类型 != Token类型.右花括号:
                # 解析键
                键表达式 = self._解析表达式()
                self._吃掉(Token类型.冒号, "字典的键和值之间要用冒号【:】隔开哦。")
                # 解析值
                值表达式 = self._解析表达式()
                键值对列表.append((键表达式, 值表达式))
                
                if self._当前Token().类型 == Token类型.逗号:
                    self._前进()
                elif self._当前Token().类型 == Token类型.右花括号:
                    break
                else:
                    raise 语法报错("字典的元素之间要用逗号隔开哦。", self._当前Token().行号, self._当前Token().列号)
            self._吃掉(Token类型.右花括号, "字典没有闭合哦，是不是忘了加右花括号？")
            primary = 字典字面量节点(键值对列表, 行号)
            
        else:
            raise 语法报错(f"这里期望得到一个值或表达式，但看到了【{当前.值}】。", 当前.行号, 当前.列号)
            
        # 解析后缀：属性访问(.) 和 动态调用()
        while True:
            if self._当前Token().类型 == Token类型.点:
                self._前进()
                属性Token = self._当前Token()
                if 属性Token.类型 != Token类型.标识符:
                    raise 语法报错("点【.】后面需要跟一个属性或方法名。", 属性Token.行号, 属性Token.列号)
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
                        raise 语法报错("给本事传入的材料之间要用逗号隔开哦。", self._当前Token().行号, self._当前Token().列号)
                self._吃掉(Token类型.右括号, "参数填写完没有闭合括号哦。")
                primary = 动态调用节点(primary, 参数列表, 左刮Token.行号)
                
            elif self._当前Token().类型 == Token类型.左方括号:
                # 索引访问 列表[0]
                左方Token = self._当前Token()
                self._前进()
                索引表达式 = self._解析表达式()
                self._吃掉(Token类型.右方括号, "索引访问没有闭合方括号哦。")
                primary = 索引访问节点(primary, 索引表达式, 左方Token.行号)
                
            else:
                break
                
        return primary
