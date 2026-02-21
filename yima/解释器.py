# yima/解释器.py
# 阅读并执行解析好的 AST（抽象语法树）

from .语法树 import *
from .环境 import 环境

class 解释器:
    def __init__(self):
        self.全局环境 = 环境()
        self._植入内置函数()
        
    def _植入内置函数(self):
        import random
        def 获取随机数(最小值, 最大值):
            return random.randint(最小值, 最大值)
            
        def 变数字(内容):
            内容文字 = str(内容).strip()
            if not 内容文字:
                return 0
            if '.' in 内容文字:
                return float(内容文字)
            return int(内容文字)
        
        def 变文字(内容):
            return str(内容)
        
        # --- 列表/数组操作 ---
        def 排列(*元素):
            return list(元素)
            
        def 加入(列表, 元素):
            列表.append(元素)
            return 列表
            
        def 长度(对象):
            return len(对象)
            
        def 取第(列表, 序号):
            return 列表[int(序号)]
            
        def 删除(列表, 序号):
            return 列表.pop(int(序号))
        
        self.全局环境.记住("取随机数", 获取随机数)
        self.全局环境.记住("变数字", 变数字)
        self.全局环境.记住("转数字", 变数字)  # 新名兼容
        self.全局环境.记住("变文字", 变文字)
        self.全局环境.记住("转文字", 变文字)  # 新名兼容
        self.全局环境.记住("排列", 排列)
        self.全局环境.记住("新列表", 排列)    # 新名兼容
        self.全局环境.记住("加入", 加入)
        self.全局环境.记住("长度", 长度)
        self.全局环境.记住("取第", 取第)
        self.全局环境.记住("提取", 取第)        # 新名兼容
        self.全局环境.记住("删除", 删除)
        
        # --- 字典操作 ---
        def 所有键(字典):
            return list(字典.keys())
        def 所有值(字典):
            return list(字典.values())
        def 有没有(集合, 元素):
            return 元素 in 集合
        self.全局环境.记住("所有键", 所有键)
        self.全局环境.记住("所有值", 所有值)
        self.全局环境.记住("有没有", 有没有)
        
        # --- 字符串操作 ---
        def 截取(文本, 起, 止):
            return str(文本)[int(起):int(止)]
        def 查找(文本, 子串):
            return str(文本).find(str(子串))
        def 替换(文本, 旧, 新):
            return str(文本).replace(str(旧), str(新))
        def 分割(文本, 分隔符):
            return str(文本).split(str(分隔符))
        def 去空格(文本):
            return str(文本).strip()
        def 包含(文本, 子串):
            return str(子串) in str(文本)
        self.全局环境.记住("截取", 截取)
        self.全局环境.记住("查找", 查找)
        self.全局环境.记住("替换", 替换)
        self.全局环境.记住("分割", 分割)
        self.全局环境.记住("去空格", 去空格)
        self.全局环境.记住("包含", 包含)
        
        # --- 文件读写 ---
        def 读文件(路径):
            with open(路径, 'r', encoding='utf-8') as f:
                return f.read()
        def 写文件(路径, 内容):
            with open(路径, 'w', encoding='utf-8') as f:
                f.write(str(内容))
        def 追加文件(路径, 内容):
            with open(路径, 'a', encoding='utf-8') as f:
                f.write(str(内容))
        self.全局环境.记住("读文件", 读文件)
        self.全局环境.记住("写文件", 写文件)
        self.全局环境.记住("追加文件", 追加文件)
        
        # 尝试植入图形界面相关函数
        try:
            self._植入图形库()
        except:
            pass

    def _植入图形库(self):
        import tkinter as tk
        from tkinter import messagebox
        
        def _创建窗口(标题="易码程序", 宽=400, 高=300):
            窗口 = tk.Tk()
            窗口.title(标题)
            窗口.geometry(f"{宽}x{高}")
            # 高清适配
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except: pass
            return 窗口
            
        def _加上文字(窗口, 内容):
            标签 = tk.Label(窗口, text=内容, font=("Microsoft YaHei", 12))
            标签.pack(pady=5)
            return 标签
            
        def _加上输入框(窗口):
            输入框 = tk.Entry(窗口, font=("Microsoft YaHei", 12))
            输入框.pack(pady=5)
            return 输入框
            
        def _读取输入(输入框):
            return 输入框.get()
            
        def _修改文字(标签, 新内容):
            标签.config(text=新内容)
            
        def _加上按钮(窗口, 文字, 绑定的函数名):
            def 点击动作():
                try:
                    from .语法树 import 函数调用节点
                    虚拟调用 = 函数调用节点(绑定的函数名, [], 行号=0)
                    self._做_函数调用节点(虚拟调用, self.全局环境)
                except Exception as e:
                    messagebox.showerror("按钮发神经了", f"找不到你指定的本事或者执行失败：{e}")
                    
            按钮 = tk.Button(窗口, text=文字, font=("Microsoft YaHei", 12), command=点击动作)
            按钮.pack(pady=5)
            return 按钮
            
        def _弹窗提醒(标题, 内容):
            messagebox.showinfo(标题, 内容)
            
        def _展示窗口(窗口):
            窗口.mainloop()
            
        self.全局环境.记住("建窗口", _创建窗口)
        self.全局环境.记住("加文字", _加上文字)
        self.全局环境.记住("加输入框", _加上输入框)
        self.全局环境.记住("读输入", _读取输入)
        self.全局环境.记住("改文字", _修改文字)
        self.全局环境.记住("加按钮", _加上按钮)
        self.全局环境.记住("弹窗", _弹窗提醒)
        self.全局环境.记住("打开界面", _展示窗口)

    def 执行代码(self, 程序树: 程序节点): # 后期在这里注册内置本事，比如 询问()
        return self.执行(程序树)

    def 执行(self, 节点, 当前环境=None):
        环境上下文 = 当前环境 if 当前环境 else self.全局环境
        
        类型名字 = type(节点).__name__
        方法名 = f"_做_{类型名字}"
        
        做点事 = getattr(self, 方法名, None)
        if 做点事 is None:
            raise Exception(f"解释器还不知道怎么做【{类型名字}】哦 (开发中)")
            
        return 做点事(节点, 环境上下文)

    def _做_程序节点(self, 节点: 程序节点, 环境上下文: 环境):
        结果 = None
        for 语句 in 节点.语句列表:
            结果 = self.执行(语句, 环境上下文)
        return 结果

    def _做_显示语句节点(self, 节点: 显示语句节点, 环境上下文: 环境):
        值 = self.执行(节点.表达式, 环境上下文)
        # 用 Python 原生 print 最终输出
        print(值)
        return 空值() # 暂时使用 Python 的 None 代替

    def _做_变量设定节点(self, 节点: 变量设定节点, 环境上下文: 环境):
        值 = self.执行(节点.表达式, 环境上下文)
        环境上下文.记住(节点.名称, 值)
        return 值

    def _做_如果语句节点(self, 节点: 如果语句节点, 环境上下文: 环境):
        for 条件, 语句块 in 节点.条件分支列表:
            条件值 = self.执行(条件, 环境上下文)
            if 条件值: # Python 的真假判断
                结果 = None
                for 语句 in 语句块:
                    结果 = self.执行(语句, 环境上下文)
                return 结果
        
        if 节点.否则分支列表 is not None:
            结果 = None
            for 语句 in 节点.否则分支列表:
                结果 = self.执行(语句, 环境上下文)
            return 结果
            
        return 空值()

    def _做_当循环节点(self, 节点: 当循环节点, 环境上下文: 环境):
        from .信号 import 停下信号, 略过信号
        结果 = 空值()
        while self.执行(节点.条件, 环境上下文):
            try:
                for 语句 in 节点.循环体:
                    结果 = self.执行(语句, 环境上下文)
            except 停下信号:
                break
            except 略过信号:
                continue
        return 结果

    def _做_重复循环节点(self, 节点: 重复循环节点, 环境上下文: 环境):
        from .信号 import 停下信号, 略过信号
        次数 = self.执行(节点.次数表达式, 环境上下文)
        if type(次数) is not int:
            from .错误 import 运行报错
            raise 运行报错(f"你要我重复的次数不是一个整数（现在是 {次数}），臣妾做不到啊！")
        
        结果 = 空值()
        for i in range(次数):
            try:
                for 语句 in 节点.循环体:
                    结果 = self.执行(语句, 环境上下文)
            except 停下信号:
                break
            except 略过信号:
                continue
        return 结果

    def _做_遍历循环节点(self, 节点: 遍历循环节点, 环境上下文: 环境):
        from .信号 import 停下信号, 略过信号
        列表集 = self.执行(节点.列表表达式, 环境上下文)
        
        from .错误 import 运行报错
        try:
            迭代器 = iter(列表集)
        except TypeError:
            raise 运行报错(f"你要我取出的东西【{列表集}】不是一个可以遍历的列表或文字哦。", 节点.列表表达式.行号 if hasattr(节点.列表表达式, '行号') else 0)
            
        结果 = 空值()
        for 元素 in 迭代器:
            环境上下文.记住(节点.元素名, 元素)
            try:
                for 语句 in 节点.循环体:
                    结果 = self.执行(语句, 环境上下文)
            except 停下信号:
                break
            except 略过信号:
                continue
        return 结果

    def _做_尝试语句节点(self, 节点: 尝试语句节点, 环境上下文: 环境):
         from .信号 import 停下信号, 略过信号, 交出信号
         结果 = 空值()
         try:
             for 语句 in 节点.尝试代码块:
                 结果 = self.执行(语句, 环境上下文)
         except (停下信号, 略过信号, 交出信号):
             # 控制流信号不应该被 try..catch 拦截
             raise
         except Exception as e:
             # 捕获到了真正的运行时错误
             出错环境 = 环境(爸爸环境=环境上下文)
             if 节点.错误捕获名:
                 错误内容 = str(e)
                 if "❌" in 错误内容: # 尝试提纯易码错误信息
                     错误内容 = 错误内容.split("：\n   ")[-1]
                 出错环境.记住(节点.错误捕获名, 错误内容)
                 
             for 语句 in 节点.出错代码块:
                 结果 = self.执行(语句, 出错环境)
                 
         return 结果

    def _做_跳出语句节点(self, 节点: 跳出语句节点, 环境上下文: 环境):
        from .信号 import 停下信号
        raise 停下信号()

    def _做_继续语句节点(self, 节点: 继续语句节点, 环境上下文: 环境):
        from .信号 import 略过信号
        raise 略过信号()

    def _做_定义函数节点(self, 节点: 定义函数节点, 环境上下文: 环境):
        环境上下文.记住(节点.函数名, 节点)
        return 空值()

    def _做_函数调用节点(self, 节点: 函数调用节点, 环境上下文: 环境):
        函数定义 = 环境上下文.告诉(节点.函数名, 节点.行号)
        
        # 1. 检查是不是 Python 的内置原生函数
        if hasattr(函数定义, '__call__'):
            传入的参数值 = []
            for 参数表达式 in 节点.参数列表:
                传入的参数值.append(self.执行(参数表达式, 环境上下文))
            return 函数定义(*传入的参数值)
            
        # 2. 普通易码函数
        if not hasattr(函数定义, '参数列表'):
            from .错误 import 运行报错
            raise 运行报错(f"你叫我用【{节点.函数名}】这个本事，但这好像不是一个教过我的本事哦。", 节点.行号)
            
        if len(节点.参数列表) != len(函数定义.参数列表):
            from .错误 import 运行报错
            raise 运行报错(f"使用【{节点.函数名}】需要 {len(函数定义.参数列表)} 个材料，但你给了 {len(节点.参数列表)} 个哦。", 节点.行号)
            
        传入的参数值 = []
        for 参数表达式 in 节点.参数列表:
            传入的参数值.append(self.执行(参数表达式, 环境上下文))
            
        函数环境 = 环境(爸爸环境=环境上下文)
        
        for 名字, 值 in zip(函数定义.参数列表, 传入的参数值):
            函数环境.记住(名字, 值)
            
        from .信号 import 交出信号
        结果 = 空值()
        for 语句 in 函数定义.代码块:
            try:
                self.执行(语句, 函数环境)
            except 交出信号 as 信号:
                return 信号.值
                
        return 结果

    def _做_动态调用节点(self, 节点: 动态调用节点, 环境上下文: 环境):
        可调用对象 = self.执行(节点.目标节点, 环境上下文)
        
        传入的参数值 = []
        for 参数表达式 in 节点.参数列表:
            传入的参数值.append(self.执行(参数表达式, 环境上下文))
            
        # 1. 检查是不是 Python 原生或库函数
        if hasattr(可调用对象, '__call__'):
            return 可调用对象(*传入的参数值)
            
        # 2. 普通易码函数 (定义函数节点)
        if not hasattr(可调用对象, '参数列表'):
            from .错误 import 运行报错
            raise 运行报错("你想要调用的这个东西并不是一个可以使用的本事（不能加括号调用）哦。", 节点.行号)
            
        if len(传入的参数值) != len(可调用对象.参数列表):
            from .错误 import 运行报错
            raise 运行报错(f"这个本事需要 {len(可调用对象.参数列表)} 个材料，但你给了 {len(传入的参数值)} 个哦。", 节点.行号)
            
        函数环境 = 环境(爸爸环境=环境上下文)
        
        for 名字, 值 in zip(可调用对象.参数列表, 传入的参数值):
            函数环境.记住(名字, 值)
            
        from .信号 import 交出信号
        结果 = 空值()
        for 语句 in 可调用对象.代码块:
            try:
                self.执行(语句, 函数环境)
            except 交出信号 as 信号:
                return 信号.值
                
        return 结果

    def _做_引入语句节点(self, 节点: 引入语句节点, 环境上下文: 环境):
        import importlib
        import os
        from .错误 import 运行报错
        
        注册名 = 节点.别名 if 节点.别名 else 节点.模块名.split('/')[-1].split('.')[0]
        
        # 判断如果是 .ym 后缀，走易码原生模块加载逻辑
        if 节点.模块名.endswith(".ym"):
            寻找路径 = 节点.模块名
            # 为了支持相对路径，尝试基于工作目录查找，如果找不到，尝试在当前执行的文件所在目录查找
            # (暂时用最简单的 fallback：当前工作目录 -> '示例' 子目录)
            绝对路径 = os.path.join(os.getcwd(), 寻找路径)
            if not os.path.exists(绝对路径):
                绝对路径_备选 = os.path.join(os.getcwd(), "示例", 寻找路径)
                if os.path.exists(绝对路径_备选):
                    绝对路径 = 绝对路径_备选
                else:
                    raise 运行报错(f"找不到你要引入的易码文件：{寻找路径}", 节点.行号)
                
            try:
                with open(绝对路径, 'r', encoding='utf-8') as f:
                    源码 = f.read()
            except Exception as e:
                raise 运行报错(f"读取模块文件失败：{e}", 节点.行号)
                
            # 解析目标代码
            from .词法分析 import 词法分析器
            from .语法分析 import 语法分析器
            
            模块Tokens = 词法分析器(源码).分析()
            模块AST = 语法分析器(模块Tokens).解析()
            
            # 创建隔离的模块环境
            # 模块环境不直接继承当前 caller，而是用全新的全局环境，这样不会受到 caller 局部变量污染
            # 注意：可以植入所有的内置函数
            模块环境 = 环境()
            # 拷贝当前内置函数池到模块环境中（基于根环境）
            根环境 = 环境上下文
            while 根环境.爸爸 is not None:
                根环境 = 根环境.爸爸
            # 导入所有原有的全局函数，这一步可以更精细化
            模块环境.记录本.update(根环境.记录本)
            
            # 独立执行模块代码
            自己 = 解释器()
            自己.全局环境 = 模块环境
            自己.执行代码(模块AST)
            
            # 执行完毕后，把模块环境里产生的所有东西打包成一个对象返回
            class 命名空间:
                pass
                
            模块对象 = 命名空间()
            for key, value in 模块环境.记录本.items():
                if key not in 根环境.记录本:
                    setattr(模块对象, key, value)
                    
            环境上下文.记住(注册名, 模块对象)
            return 空值()
            
        else:
            # 走 Python 原生库引入
            try:
                库模块 = importlib.import_module(节点.模块名)
            except ImportError:
                raise 运行报错(f"你想借用的【{节点.模块名}】这个库我找不到呀，是不是名字拼错了？或者环境没有安装它。", 节点.行号)
                
            环境上下文.记住(注册名, 库模块)
            return 空值()

    def _做_属性访问节点(self, 节点: 属性访问节点, 环境上下文: 环境):
        对象 = self.执行(节点.对象节点, 环境上下文)
        from .错误 import 运行报错
        if not hasattr(对象, 节点.属性名):
            raise 运行报错(f"这个东西身上没有【{节点.属性名}】这个属性或本事哦。", 节点.行号)
        return getattr(对象, 节点.属性名)

    def _做_列表字面量节点(self, 节点: 列表字面量节点, 环境上下文: 环境):
        return [self.执行(元素, 环境上下文) for 元素 in 节点.元素列表]

    def _做_字典字面量节点(self, 节点: 字典字面量节点, 环境上下文: 环境):
        字典值 = {}
        for 键表达式, 值表达式 in 节点.键值对列表:
            键 = self.执行(键表达式, 环境上下文)
            值 = self.执行(值表达式, 环境上下文)
            字典值[键] = 值
        return 字典值
        
    def _做_一元运算节点(self, 节点: 一元运算节点, 环境上下文: 环境):
        操作数 = self.执行(节点.操作数, 环境上下文)
        操作符 = 节点.运算符.值
        
        if 操作符 in ["取反", "反过来说"]:
            return not 操作数
            
        from .错误 import 运行报错
        raise 运行报错(f"解释器还不认识一元运算符：【{操作符}】", 节点.行号)

    def _做_索引访问节点(self, 节点: 索引访问节点, 环境上下文: 环境):
        对象 = self.执行(节点.对象节点, 环境上下文)
        索引 = self.执行(节点.索引节点, 环境上下文)
        from .错误 import 运行报错
        try:
            if isinstance(对象, dict):
                return 对象[索引]
            return 对象[int(索引)]
        except (IndexError, KeyError):
            raise 运行报错(f"你想取的索引【{索引}】不存在或越界啦。", 节点.行号)
        except TypeError:
            raise 运行报错(f"这个东西不支持用方括号取值哦。", 节点.行号)

    def _做_交出语句节点(self, 节点: 交出语句节点, 环境上下文: 环境):
        from .信号 import 交出信号
        if 节点.表达式 is None:
            raise 交出信号(空值())
        else:
            返回值 = self.执行(节点.表达式, 环境上下文)
            raise 交出信号(返回值)

    def _做_询问表达式节点(self, 节点: 询问表达式节点, 环境上下文: 环境):
        提示文 = str(self.执行(节点.提示语句表达式, 环境上下文))
        try:
            return input(提示文)
        except EOFError:
            return ""

    def _做_文本字面量节点(self, 节点: 文本字面量节点, 环境上下文: 环境):
        return 节点.值

    def _做_模板字符串节点(self, 节点: 模板字符串节点, 环境上下文: 环境):
        import re
        结果文本 = 节点.原始文本
        找出的变量 = re.findall(r'【([^】]+)】', 结果文本)
        for 变量名 in 找出的变量:
            变量名 = 变量名.strip()
            try:
                值 = 环境上下文.告诉(变量名, 0)
                结果文本 = 结果文本.replace(f"【{变量名}】", str(值))
            except Exception:
                from .错误 import 运行报错
                raise 运行报错(f"你在文本里写了【{变量名}】，但我还没记住这个名字代表什么哦。", 0)
        return 结果文本

    def _做_数字字面量节点(self, 节点: 数字字面量节点, 环境上下文: 环境):
        return 节点.值

    def _做_变量访问节点(self, 节点: 变量访问节点, 环境上下文: 环境):
        return 环境上下文.告诉(节点.名称, 节点.行号)

    def _做_二元运算节点(self, 节点: 二元运算节点, 环境上下文: 环境):
        左边值 = self.执行(节点.左边, 环境上下文)
        操作符 = 节点.运算符.值
        
        # 逻辑运算优先处理，因为具有短路特性
        if 操作符 in ["而且", "并且"]:
            if not 左边值:
                return 左边值
            return self.执行(节点.右边, 环境上下文)
            
        if 操作符 == "或者":
            if 左边值:
                return 左边值
            return self.执行(节点.右边, 环境上下文)
            
        右边值 = self.执行(节点.右边, 环境上下文)
        
        from .错误 import 类型不匹配报错
        from .语法树 import 文本字面量节点
        # 拼接专门处理
        if 操作符 == "拼接":
            return str(左边值) + str(右边值)
        if 操作符 == "+":
            if isinstance(左边值, str) or isinstance(右边值, str):
                return str(左边值) + str(右边值)
            
        # 算术运算
        运算函数 = {
            "加上": lambda a, b: a + b,
            "+": lambda a, b: a + b,
            "减去": lambda a, b: a - b,
            "-": lambda a, b: a - b,
            "乘以": lambda a, b: a * b,
            "*": lambda a, b: a * b,
            "除以": lambda a, b: a / b,
            "/": lambda a, b: a / b,
            "取余": lambda a, b: a % b,
            "%": lambda a, b: a % b,
        }
        
        if 操作符 in 运算函数:
            # 简单类型检查
            if not isinstance(左边值, (int, float)) or not isinstance(右边值, (int, float)):
                raise 类型不匹配报错(f"你不能把【{type(左边值).__name__}】和【{type(右边值).__name__}】进行【{操作符}】操作哦。", 节点.行号)
            if 操作符 == "除以" and 右边值 == 0:
                raise 类型不匹配报错("除数不能是 0 哦！", 节点.行号)
            return 运算函数[操作符](左边值, 右边值)
            
        # 比较运算
        比较函数 = {
            "大于": lambda a, b: a > b,
            ">": lambda a, b: a > b,
            "小于": lambda a, b: a < b,
            "<": lambda a, b: a < b,
            "等于": lambda a, b: a == b,
            "==": lambda a, b: a == b,
            "是": lambda a, b: a == b,
            "不等于": lambda a, b: a != b,
            "!=": lambda a, b: a != b,
            "不是": lambda a, b: a != b,
            "至少是": lambda a, b: a >= b,
            ">=": lambda a, b: a >= b,
            "最多是": lambda a, b: a <= b,
            "<=": lambda a, b: a <= b,
        }
        
        if 操作符 in 比较函数:
            return 比较函数[操作符](左边值, 右边值)
            
        raise Exception(f"解释器还不认识运算符：【{操作符}】")

# 简单封装易码的空值
def 空值():
    return None
