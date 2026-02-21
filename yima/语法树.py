# yima/语法树.py
# 易码大白话 AST 节点定义

class AST节点:
    pass

class 程序节点(AST节点):
    def __init__(self, 语句列表):
        self.语句列表 = 语句列表

# -----------------
# 表达式节点
# -----------------
class 文本字面量节点(AST节点):
    def __init__(self, 值):
        self.值 = 值

class 模板字符串节点(AST节点):
    """含有【变量名】占位符的字符串，运行时自动替换"""
    def __init__(self, 原始文本):
        self.原始文本 = 原始文本

class 数字字面量节点(AST节点):
    def __init__(self, 值):
        self.值 = 值

class 变量访问节点(AST节点):
    def __init__(self, 名称, 行号):
        self.名称 = 名称
        self.行号 = 行号

class 属性访问节点(AST节点):
    def __init__(self, 对象节点, 属性名, 行号):
        self.对象节点 = 对象节点
        self.属性名 = 属性名
        self.行号 = 行号

class 列表字面量节点(AST节点):
    def __init__(self, 元素列表, 行号):
        self.元素列表 = 元素列表
        self.行号 = 行号

class 索引访问节点(AST节点):
    def __init__(self, 对象节点, 索引节点, 行号):
        self.对象节点 = 对象节点
        self.索引节点 = 索引节点
        self.行号 = 行号

class 二元运算节点(AST节点):
    def __init__(self, 左边, 运算符, 右边, 行号):
        self.左边 = 左边
        self.运算符 = 运算符
        self.右边 = 右边
        self.行号 = 行号

# -----------------
# 语句节点
# -----------------
class 引入语句节点(AST节点):
    def __init__(self, 模块名, 别名, 行号):
        self.模块名 = 模块名
        self.别名 = 别名
        self.行号 = 行号

class 显示语句节点(AST节点):
    def __init__(self, 表达式):
        self.表达式 = 表达式

class 变量设定节点(AST节点):
    def __init__(self, 名称, 表达式):
        self.名称 = 名称
        self.表达式 = 表达式

class 如果语句节点(AST节点):
    def __init__(self, 条件分支列表, 否则分支列表=None):
        self.条件分支列表 = 条件分支列表
        self.否则分支列表 = 否则分支列表

class 当循环节点(AST节点):
    def __init__(self, 条件, 循环体):
        self.条件 = 条件
        self.循环体 = 循环体

class 重复循环节点(AST节点):
    def __init__(self, 次数表达式, 循环体):
        self.次数表达式 = 次数表达式
        self.循环体 = 循环体

class 跳出语句节点(AST节点):
    pass

class 继续语句节点(AST节点):
    pass

class 定义函数节点(AST节点):
    def __init__(self, 函数名, 参数列表, 代码块, 行号=0):
        self.函数名 = 函数名
        self.参数列表 = 参数列表
        self.代码块 = 代码块
        self.行号 = 行号

class 函数调用节点(AST节点):
    def __init__(self, 函数名, 参数列表, 行号):
        self.函数名 = 函数名
        self.参数列表 = 参数列表
        self.行号 = 行号

class 动态调用节点(AST节点):
    def __init__(self, 目标节点, 参数列表, 行号):
        self.目标节点 = 目标节点
        self.参数列表 = 参数列表
        self.行号 = 行号

class 询问表达式节点(AST节点):
    def __init__(self, 提示语句表达式):
        self.提示语句表达式 = 提示语句表达式

class 交出语句节点(AST节点):
    def __init__(self, 表达式):
        self.表达式 = 表达式

class 遍历循环节点(AST节点):
    def __init__(self, 列表表达式, 元素名, 循环体, 行号=0):
        self.列表表达式 = 列表表达式
        self.元素名 = 元素名
        self.循环体 = 循环体
        self.行号 = 行号

class 一元运算节点(AST节点):
    def __init__(self, 运算符, 操作数, 行号=0):
        self.运算符 = 运算符
        self.操作数 = 操作数
        self.行号 = 行号

class 字典字面量节点(AST节点):
    def __init__(self, 键值对列表, 行号=0):
        self.键值对列表 = 键值对列表  # [(键节点, 值节点), ...]
        self.行号 = 行号

class 尝试语句节点(AST节点):
    def __init__(self, 尝试代码块, 错误捕获名, 出错代码块, 行号=0):
        self.尝试代码块 = 尝试代码块
        self.错误捕获名 = 错误捕获名
        self.出错代码块 = 出错代码块
        self.行号 = 行号
