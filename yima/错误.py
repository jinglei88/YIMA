# yima/错误.py
# 易码错误系统（专业中文）

class 易码错误(Exception):
    """易码所有异常的基类"""
    def __init__(self, 错误类型, 消息, 行号=None, 列号=None, 建议=None):
        self.错误类型 = 错误类型
        self.消息 = 消息
        self.行号 = 行号
        self.列号 = 列号
        self.建议 = 建议

    def _位置文本(self):
        if self.行号 and self.列号:
            return f"（第 {self.行号} 行，第 {self.列号} 列）"
        if self.行号:
            return f"（第 {self.行号} 行）"
        if self.列号:
            return f"（第 {self.列号} 列）"
        return ""

    def _自动建议(self):
        消息 = str(self.消息)
        if "除数不能为 0" in 消息:
            return "把除数改为非 0 值后再运行。"
        if "未定义名称" in 消息 or "未定义" in 消息:
            return "先给该名称赋值，或检查拼写是否一致（含全角/半角）。"
        if "找不到模块" in 消息 or "读取模块文件失败" in 消息 or "加载模块失败" in 消息:
            return "检查模块名与路径；易码模块建议使用 .ym 后缀并确认文件存在。"
        if "参数" in 消息 and ("需要" in 消息 or "传入" in 消息):
            return "检查函数/方法定义与调用处的参数个数是否一致。"
        if "缩进" in 消息:
            return "统一同一层级缩进宽度，避免混用空格和 Tab。"
        if "字符串没有闭合" in 消息:
            return "补上匹配的右引号，或检查字符串中的转义写法。"
        if "逗号分隔" in 消息:
            return "在相邻元素之间补上逗号。"
        if "缺少右括号" in 消息 or "未闭合" in 消息:
            return "检查括号是否成对出现。"

        if self.错误类型 == "词法错误":
            return "检查非法字符、引号闭合和缩进层级。"
        if self.错误类型 == "语法错误":
            return "检查关键字顺序、括号闭合和代码块缩进。"
        if self.错误类型 == "运行错误":
            return "检查变量定义、函数参数、数据类型和导入路径。"
        return None

    def __str__(self):
        位置 = self._位置文本()
        建议 = self.建议 if self.建议 else self._自动建议()
        文本 = [f"{self.错误类型}{位置}：", f"  原因：{self.消息}"]
        if 建议:
            文本.append(f"  建议：{建议}")
        return "\n".join(文本)


class 词法报错(易码错误):
    def __init__(self, 消息, 行号=None, 列号=None, 建议=None):
        super().__init__("词法错误", 消息, 行号, 列号, 建议)


class 语法报错(易码错误):
    def __init__(self, 消息, 行号=None, 列号=None, 建议=None):
        super().__init__("语法错误", 消息, 行号, 列号, 建议)


class 运行报错(易码错误):
    def __init__(self, 消息, 行号=None, 列号=None, 建议=None):
        super().__init__("运行错误", 消息, 行号, 列号, 建议)


class 名字找不到报错(运行报错):
    def __init__(self, 名字, 行号=None, 列号=None):
        消息 = f"未定义名称【{名字}】。"
        建议 = "先给该名称赋值，或检查拼写是否一致（含全角/半角）。"
        super().__init__(消息, 行号, 列号, 建议=建议)


class 类型不匹配报错(运行报错):
    def __init__(self, 消息, 行号=None, 列号=None, 建议=None):
        super().__init__(消息, 行号, 列号, 建议)
