# yima/错误.py
# 易码大白话报错系统

class 易码错误(Exception):
    """易码所有异常的基类"""
    def __init__(self, 错误类型, 消息, 行号=None, 列号=None):
        self.错误类型 = 错误类型
        self.消息 = 消息
        self.行号 = 行号
        self.列号 = 列号

    def __str__(self):
        位置 = f"（第 {self.行号} 行）" if self.行号 else ""
        return f"❌ {self.错误类型}{位置}：\n   {self.消息}"


class 词法报错(易码错误):
    def __init__(self, 消息, 行号=None, 列号=None):
        super().__init__("看球不懂(词法错误)", 消息, 行号, 列号)


class 语法报错(易码错误):
    def __init__(self, 消息, 行号=None, 列号=None):
        super().__init__("说话结巴(语法错误)", 消息, 行号, 列号)


class 运行报错(易码错误):
    def __init__(self, 消息, 行号=None, 列号=None):
        super().__init__("脑子卡壳(运行错误)", 消息, 行号, 列号)


class 名字找不到报错(运行报错):
    def __init__(self, 名字, 行号=None, 列号=None):
        消息 = f"你提到了【{名字}】，但我以前从来没听说过这个东西哦，是不是写错了？"
        super().__init__(消息, 行号, 列号)


class 类型不匹配报错(运行报错):
    def __init__(self, 消息, 行号=None, 列号=None):
        super().__init__(消息, 行号, 列号)
