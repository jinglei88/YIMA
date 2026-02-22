# yima/环境.py
# 记录所有的名字和它们对应的值

from .错误 import 名字找不到报错

class 环境:
    def __init__(self, 爸爸环境=None, 禁止向上赋值=False):
        self.记录本 = {}
        self.爸爸 = 爸爸环境
        self.禁止向上赋值 = 禁止向上赋值

    def 记住(self, 名字, 值):
        if self.禁止向上赋值:
            self.记录本[名字] = 值
            return

        # 如果在上级环境中存在这个名字，就优先修改上级的，保持状态更新（闭包）
        当前环境 = self
        while 当前环境 is not None:
            if 名字 in 当前环境.记录本:
                当前环境.记录本[名字] = 值
                return
            当前环境 = 当前环境.爸爸
            
        # 否则作为一个新变量记在当前作用域
        self.记录本[名字] = 值

    def 告诉(self, 名字, 行号=None):
        if 名字 in self.记录本:
            return self.记录本[名字]
            
        if self.爸爸 is not None:
            return self.爸爸.告诉(名字, 行号)
            
        raise 名字找不到报错(名字, 行号)
