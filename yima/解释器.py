# yima/解释器.py
# 阅读并执行解析好的 AST（抽象语法树）

#
# Ownership Marker (Open Source Prep)
# Author: 景磊 (Jing Lei)
# Copyright (c) 2026 景磊
# Project: 易码 / Yima
# Marker-ID: YIMA-JINGLEI-CORE

__author__ = "景磊"
__copyright__ = "Copyright (c) 2026 景磊"
__marker_id__ = "YIMA-JINGLEI-CORE"

import os

from .语法树 import *
from .环境 import 环境

class 易码函数:
    def __init__(self, 定义节点: 定义函数节点, 定义环境: 环境):
        self.函数名 = 定义节点.函数名
        self.参数列表 = list(定义节点.参数列表)
        self.代码块 = 定义节点.代码块
        self.行号 = getattr(定义节点, "行号", 0)
        self.定义环境 = 定义环境

class 解释器:
    def __init__(self, 严格局部作用域=False):
        self.当前目录 = os.getcwd()
        self.全局环境 = 环境()
        self.严格局部作用域 = 严格局部作用域
        self._模块缓存 = {}
        self._可选能力告警 = []
        self._植入内置函数()
        self._内置名称集合 = set(self.全局环境.记录本.keys())

    def 设置当前目录(self, 目录路径):
        if 目录路径 and os.path.isdir(目录路径):
            self.当前目录 = os.path.abspath(目录路径)

    def _获取根环境(self, 环境上下文: 环境) -> 环境:
        根环境 = 环境上下文
        while 根环境.爸爸 is not None:
            根环境 = 根环境.爸爸
        return 根环境

    def _模块搜索路径(self):
        import sys

        候选路径 = []
        候选路径.extend([self.当前目录, os.path.join(self.当前目录, "示例")])

        当前工作目录 = os.getcwd()
        候选路径.extend([当前工作目录, os.path.join(当前工作目录, "示例")])

        if hasattr(sys, "_MEIPASS"):
            候选路径.insert(0, sys._MEIPASS)

        结果 = []
        for 路径 in 候选路径:
            if 路径 and 路径 not in 结果:
                结果.append(路径)
        return 结果

    def _定位易码模块文件(self, 模块名: str):
        寻找路径 = 模块名
        带后缀路径 = 寻找路径 if 寻找路径.endswith(".ym") else 寻找路径 + ".ym"

        for 基础路径 in self._模块搜索路径():
            候选列表 = [
                os.path.join(基础路径, 带后缀路径),
                os.path.join(基础路径, 寻找路径),
            ]
            for 候选 in 候选列表:
                if os.path.isfile(候选):
                    return os.path.abspath(候选)
        return None

    def _生成模块缓存键(self, 绝对路径: str, 根环境: 环境):
        try:
            修改时间 = os.stat(绝对路径).st_mtime_ns
        except OSError:
            修改时间 = 0
        return (os.path.abspath(绝对路径), 修改时间, id(根环境))

    def _加载易码模块(self, 绝对路径: str, 环境上下文: 环境):
        根环境 = self._获取根环境(环境上下文)
        缓存键 = self._生成模块缓存键(绝对路径, 根环境)
        if 缓存键 in self._模块缓存:
            return self._模块缓存[缓存键]

        with open(绝对路径, 'r', encoding='utf-8') as f:
            源码 = f.read()

        from .词法分析 import 词法分析器
        from .语法分析 import 语法分析器

        模块Tokens = 词法分析器(源码).分析()
        模块AST = 语法分析器(模块Tokens).解析()

        模块环境 = 环境()
        模块环境.记录本.update(根环境.记录本)

        子解释器 = 解释器(严格局部作用域=self.严格局部作用域)
        子解释器.全局环境 = 模块环境
        子解释器._模块缓存 = self._模块缓存
        子解释器.设置当前目录(os.path.dirname(绝对路径))
        子解释器.执行代码(模块AST)

        模块导出 = {}
        for key, value in 模块环境.记录本.items():
            if key not in 根环境.记录本:
                模块导出[key] = value

        缓存值 = {
            "导出": 模块导出,
            "全量": dict(模块环境.记录本),
        }
        self._模块缓存[缓存键] = 缓存值
        return 缓存值

    def _内置模块命名空间(self, 模块名: str, 环境上下文: 环境):
        根环境 = self._获取根环境(环境上下文)
        导出映射 = {
            "文件管理": ["读文件", "写文件", "追加文件"],
            "系统工具": ["文件存在", "目录存在", "创建目录", "列出目录", "删除文件", "删除目录", "拼路径", "绝对路径", "当前目录"],
            "数据工具": ["解析JSON", "生成JSON", "读JSON", "写JSON"],
            "网络请求": ["发起请求", "发GET", "发POST", "发GET_JSON", "发POST_JSON", "读响应JSON"],
            "本地数据库": ["打开数据库", "执行SQL", "查询SQL", "关闭数据库", "开始事务", "提交事务", "回滚事务"],
            "图形界面": [
                "建窗口", "加文字", "加输入框", "读输入", "改文字", "加按钮", "弹窗", "弹窗输入", "打开界面",
                "加表格", "表格加行", "表格清空", "表格所有行", "表格选中行", "表格选中序号", "表格删行", "表格改行",
            ],
            "画板": [
                "画布", "标题", "图标", "向前走", "向后走", "左转", "右转", "抬笔", "落笔", "画笔颜色",
                "背景颜色", "去", "笔粗", "画圆", "停一下", "定格", "速度", "隐藏画笔", "关闭动画",
                "刷新画面", "清除", "写字", "开始监听", "绑定按键", "计算距离", "当前X", "当前Y",
            ],
        }
        if 模块名 == "魔法生态库":
            名称列表 = sorted(self._内置名称集合)
        else:
            名称列表 = 导出映射.get(模块名, [])

        命名空间 = {}
        for 名称 in 名称列表:
            if 名称 in 根环境.记录本:
                命名空间[名称] = 根环境.记录本[名称]
        return 命名空间
        
    def _植入内置函数(self):
        import random
        def 获取随机数(最小值, 最大值):
            return random.randint(最小值, 最大值)
            
        def 转数字(内容):
            内容文字 = str(内容).strip()
            if not 内容文字:
                return 0
            if '.' in 内容文字:
                return float(内容文字)
            return int(内容文字)
        
        def 转文字(内容):
            return self._转为白话文本(内容)
        
        # --- 列表/数组操作 ---
        def 新列表(*元素):
            return list(元素)
            
        def 加入(列表, 元素):
            列表.append(元素)
            return 列表
            
        def 长度(对象):
            return len(对象)
            
        def 插入(列表, 序号, 元素):
            列表.insert(int(序号), 元素)
            return 列表
            
        def 删除(对象, 键或索引):
            if isinstance(对象, dict):
                return 对象.pop(键或索引, None)
            else:
                return 对象.pop(int(键或索引))
        
        self.全局环境.记住("取随机数", 获取随机数)
        self.全局环境.记住("转数字", 转数字)
        self.全局环境.记住("转文字", 转文字)
        self.全局环境.记住("新列表", 新列表)
        self.全局环境.记住("加入", 加入)
        self.全局环境.记住("插入", 插入)
        self.全局环境.记住("长度", 长度)
        self.全局环境.记住("删除", 删除)
        
        # --- 字典操作 ---
        def 所有键(字典):
            return list(字典.keys())
        def 所有值(字典):
            return list(字典.values())
        def 存在(集合, 元素):
            return 元素 in 集合
        self.全局环境.记住("所有键", 所有键)
        self.全局环境.记住("所有值", 所有值)
        self.全局环境.记住("存在", 存在)
        
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

        # --- 路径与目录 ---
        def 文件存在(路径):
            return os.path.isfile(str(路径))
        def 目录存在(路径):
            return os.path.isdir(str(路径))
        def 创建目录(路径):
            路径文本 = str(路径).strip()
            if not 路径文本:
                return ""
            os.makedirs(路径文本, exist_ok=True)
            return os.path.abspath(路径文本)
        def 列出目录(路径="."):
            路径文本 = str(路径) if 路径 is not None else "."
            if not os.path.isdir(路径文本):
                return []
            return sorted(os.listdir(路径文本))
        def 删除文件(路径):
            路径文本 = str(路径)
            if not os.path.isfile(路径文本):
                return False
            os.remove(路径文本)
            return True
        def 删除目录(路径):
            import shutil
            路径文本 = str(路径)
            if not os.path.isdir(路径文本):
                return False
            shutil.rmtree(路径文本)
            return True
        def 拼路径(*片段):
            return os.path.join(*(str(片) for 片 in 片段))
        def 绝对路径(路径):
            return os.path.abspath(str(路径))
        def 当前目录():
            return os.getcwd()
        self.全局环境.记住("文件存在", 文件存在)
        self.全局环境.记住("目录存在", 目录存在)
        self.全局环境.记住("创建目录", 创建目录)
        self.全局环境.记住("列出目录", 列出目录)
        self.全局环境.记住("删除文件", 删除文件)
        self.全局环境.记住("删除目录", 删除目录)
        self.全局环境.记住("拼路径", 拼路径)
        self.全局环境.记住("绝对路径", 绝对路径)
        self.全局环境.记住("当前目录", 当前目录)

        # --- JSON 数据 ---
        def 解析JSON(文本):
            import json
            if isinstance(文本, (dict, list)):
                return 文本
            文本值 = str(文本).strip()
            if not 文本值:
                return {}
            return json.loads(文本值)
        def 生成JSON(对象, 美化=True):
            import json
            缩进 = 2 if bool(美化) else None
            return json.dumps(对象, ensure_ascii=False, indent=缩进)
        def 读JSON(路径):
            import json
            with open(str(路径), "r", encoding="utf-8") as f:
                return json.load(f)
        def 写JSON(路径, 对象, 美化=True):
            import json
            缩进 = 2 if bool(美化) else None
            with open(str(路径), "w", encoding="utf-8") as f:
                json.dump(对象, f, ensure_ascii=False, indent=缩进)
            return str(路径)
        self.全局环境.记住("解析JSON", 解析JSON)
        self.全局环境.记住("生成JSON", 生成JSON)
        self.全局环境.记住("读JSON", 读JSON)
        self.全局环境.记住("写JSON", 写JSON)

        # --- HTTP 请求 ---
        def _整理请求体(数据):
            if 数据 is None:
                return None, None
            if isinstance(数据, (bytes, bytearray)):
                return bytes(数据), None
            if isinstance(数据, (dict, list)):
                import json
                return json.dumps(数据, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8"
            文本 = str(数据)
            if not 文本:
                return None, None
            return 文本.encode("utf-8"), "text/plain; charset=utf-8"

        def 发起请求(网址, 方法="GET", 数据=None, 请求头=None, 超时秒=15):
            from urllib import request as _req
            from urllib.error import HTTPError, URLError
            目标网址 = str(网址).strip()
            if not 目标网址:
                return {"成功": False, "错误": "网址不能为空", "状态码": 0, "内容": "", "头": {}}

            方法文本 = str(方法).strip().upper() if 方法 else "GET"
            if not 方法文本:
                方法文本 = "GET"
            头 = dict(请求头) if isinstance(请求头, dict) else {}
            请求体, 默认类型 = _整理请求体(数据)
            if 默认类型 and "Content-Type" not in 头 and "content-type" not in 头:
                头["Content-Type"] = 默认类型

            req = _req.Request(目标网址, data=请求体, method=方法文本, headers=头)
            try:
                with _req.urlopen(req, timeout=float(超时秒)) as resp:
                    原始内容 = resp.read()
                    字符集 = resp.headers.get_content_charset() or "utf-8"
                    文本内容 = 原始内容.decode(字符集, errors="replace")
                    return {
                        "成功": True,
                        "状态码": int(getattr(resp, "status", 200)),
                        "内容": 文本内容,
                        "头": dict(resp.headers.items()),
                    }
            except HTTPError as e:
                原始内容 = e.read() if hasattr(e, "read") else b""
                文本内容 = 原始内容.decode("utf-8", errors="replace")
                return {"成功": False, "状态码": int(getattr(e, "code", 0)), "内容": 文本内容, "头": dict(getattr(e, "headers", {}).items()) if getattr(e, "headers", None) else {}, "错误": str(e)}
            except URLError as e:
                return {"成功": False, "状态码": 0, "内容": "", "头": {}, "错误": str(e)}
            except Exception as e:
                return {"成功": False, "状态码": 0, "内容": "", "头": {}, "错误": str(e)}

        def 发GET(网址, 请求头=None, 超时秒=15):
            return 发起请求(网址, "GET", None, 请求头, 超时秒)

        def 发POST(网址, 数据=None, 请求头=None, 超时秒=15):
            return 发起请求(网址, "POST", 数据, 请求头, 超时秒)

        def 读响应JSON(响应, 默认值=None):
            import json
            if isinstance(响应, dict):
                内容 = 响应.get("内容", "")
            else:
                内容 = 响应
            try:
                return json.loads(str(内容))
            except Exception:
                if 默认值 is not None:
                    return 默认值
                return {}

        def 发GET_JSON(网址, 请求头=None, 超时秒=15):
            响应 = 发GET(网址, 请求头, 超时秒)
            响应["JSON"] = 读响应JSON(响应, None)
            return 响应

        def 发POST_JSON(网址, 数据=None, 请求头=None, 超时秒=15):
            响应 = 发POST(网址, 数据, 请求头, 超时秒)
            响应["JSON"] = 读响应JSON(响应, None)
            return 响应

        self.全局环境.记住("发起请求", 发起请求)
        self.全局环境.记住("发GET", 发GET)
        self.全局环境.记住("发POST", 发POST)
        self.全局环境.记住("读响应JSON", 读响应JSON)
        self.全局环境.记住("发GET_JSON", 发GET_JSON)
        self.全局环境.记住("发POST_JSON", 发POST_JSON)

        # --- SQLite 本地数据库 ---
        数据库自动提交配置 = {}

        def _参数转元组(参数):
            if 参数 is None or 参数 == "":
                return ()
            if isinstance(参数, tuple):
                return 参数
            if isinstance(参数, list):
                return tuple(参数)
            return (参数,)

        def 打开数据库(路径, 自动提交=True):
            import sqlite3
            连接 = sqlite3.connect(str(路径))
            数据库自动提交配置[id(连接)] = bool(自动提交)
            return 连接

        def 执行SQL(连接, SQL, 参数=None):
            cur = 连接.cursor()
            cur.execute(str(SQL), _参数转元组(参数))
            if 数据库自动提交配置.get(id(连接), True):
                连接.commit()
            return cur.rowcount

        def 查询SQL(连接, SQL, 参数=None):
            cur = 连接.cursor()
            cur.execute(str(SQL), _参数转元组(参数))
            列定义 = [d[0] for d in (cur.description or [])]
            结果 = []
            for 行 in cur.fetchall():
                if 列定义:
                    结果.append({列定义[i]: 行[i] for i in range(len(列定义))})
                else:
                    结果.append(list(行))
            return 结果

        def 开始事务(连接):
            if 连接:
                连接.execute("BEGIN")
            return True

        def 提交事务(连接):
            if 连接:
                连接.commit()
            return True

        def 回滚事务(连接):
            if 连接:
                连接.rollback()
            return True

        def 关闭数据库(连接):
            if 连接:
                数据库自动提交配置.pop(id(连接), None)
                连接.close()
            return 空值()

        self.全局环境.记住("打开数据库", 打开数据库)
        self.全局环境.记住("执行SQL", 执行SQL)
        self.全局环境.记住("查询SQL", 查询SQL)
        self.全局环境.记住("开始事务", 开始事务)
        self.全局环境.记住("提交事务", 提交事务)
        self.全局环境.记住("回滚事务", 回滚事务)
        self.全局环境.记住("关闭数据库", 关闭数据库)
        
        # --- 类型判断 ---
        def 类型(对象):
            if 对象 is None: return "空"
            if isinstance(对象, bool): return "布尔"
            if isinstance(对象, int): return "整数"
            if isinstance(对象, float): return "小数"
            if isinstance(对象, str): return "文本"
            if isinstance(对象, list): return "列表"
            if isinstance(对象, dict): return "字典"
            return "对象"
        self.全局环境.记住("类型", 类型)
        
        # --- 常用列表操作 ---
        def 排序(列表): return sorted(列表)
        def 倒序(列表): return list(reversed(列表))
        def 去重(列表): return list(dict.fromkeys(列表))
        def 合并(列表, 分隔符=""): return str(分隔符).join(str(x) for x in 列表)
        def 最大值(列表): return max(列表)
        def 最小值(列表): return min(列表)
        self.全局环境.记住("排序", 排序)
        self.全局环境.记住("倒序", 倒序)
        self.全局环境.记住("去重", 去重)
        self.全局环境.记住("合并", 合并)
        self.全局环境.记住("最大值", 最大值)
        self.全局环境.记住("最小值", 最小值)
        
        # --- 数学函数 ---
        def 绝对值(数字): return abs(数字)
        def 四舍五入(数字, 位数=0): return round(数字, int(位数))
        self.全局环境.记住("绝对值", 绝对值)
        self.全局环境.记住("四舍五入", 四舍五入)
        
        # --- 时间函数 ---
        def 现在时间():
            import datetime
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        def 时间戳():
            import time
            return int(time.time())
        self.全局环境.记住("现在时间", 现在时间)
        self.全局环境.记住("时间戳", 时间戳)
        
        # 尝试植入图形界面相关函数
        try:
            self._植入图形库()
        except Exception as e:
            self._可选能力告警.append(f"图形界面加载失败：{e}")
            
        # 尝试植入画板引擎 (Turtle)
        try:
            self._植入画图库()
        except Exception as e:
            self._可选能力告警.append(f"画板加载失败：{e}")

    def _植入图形库(self):
        import tkinter as tk
        from tkinter import messagebox, ttk
        from tkinter import font as tkfont
        
        def _创建窗口(标题="易码程序", 宽=400, 高=300):
            窗口 = tk.Tk()
            窗口.title(标题)
            窗口.geometry(f"{宽}x{高}")
            # 高清适配
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass
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
                    messagebox.showerror("按钮执行失败", f"未找到目标函数或执行失败：{e}")
                    
            按钮 = tk.Button(窗口, text=文字, font=("Microsoft YaHei", 12), command=点击动作)
            按钮.pack(pady=5)
            return 按钮
            
        def _弹窗提醒(标题, 内容):
            messagebox.showinfo(标题, 内容)
            
        def _弹窗输入(标题, 提示=""):
            from tkinter import simpledialog
            结果 = simpledialog.askstring(标题, 提示)
            return 结果 if 结果 is not None else ""
            
        def _展示窗口(窗口):
            窗口.mainloop()

        def _规范列名(列定义):
            if isinstance(列定义, (list, tuple)):
                列名 = [str(列).strip() for 列 in 列定义 if str(列).strip()]
            else:
                文本 = str(列定义).strip()
                if not 文本:
                    列名 = []
                else:
                    分隔符 = None
                    for 候选 in [",", "，", "|", "｜", ";", "；"]:
                        if 候选 in 文本:
                            分隔符 = 候选
                            break
                    if 分隔符:
                        列名 = [片段.strip() for 片段 in 文本.split(分隔符) if 片段.strip()]
                    else:
                        列名 = [文本]

            if not 列名:
                列名 = ["列1", "列2"]
            return 列名

        def _定位表格项(表格, 序号或项):
            子项 = list(表格.get_children())
            if not 子项:
                return None

            if isinstance(序号或项, (int, float)):
                索引 = int(序号或项)
                if 0 <= 索引 < len(子项):
                    return 子项[索引]
                return None

            if 序号或项 is None:
                选中 = 表格.selection()
                return 选中[0] if 选中 else None

            文本参数 = str(序号或项).strip()
            if not 文本参数:
                选中 = 表格.selection()
                return 选中[0] if 选中 else None

            if 文本参数 in 子项:
                return 文本参数

            if 文本参数.lstrip("-").isdigit():
                索引 = int(文本参数)
                if 0 <= 索引 < len(子项):
                    return 子项[索引]
            return None

        def _规范表格行(表格, 行数据):
            列名 = list(getattr(表格, "_易码列名", []))
            列数 = len(列名)

            if isinstance(行数据, dict):
                值 = [self._转为白话文本(行数据.get(列, "")) for 列 in 列名]
            elif isinstance(行数据, (list, tuple)):
                值 = [self._转为白话文本(元素) for 元素 in 行数据]
            else:
                值 = [self._转为白话文本(行数据)]

            if 列数 <= 0:
                return 值
            if len(值) < 列数:
                值.extend([""] * (列数 - len(值)))
            if len(值) > 列数:
                值 = 值[:列数]
            return 值

        def _加上表格(窗口, 列定义, 高度=10):
            列名 = _规范列名(列定义)
            高度值 = max(3, int(高度))

            # 为表格单独设置字体和行高，避免中文在高 DPI 下被裁切
            # Tk 会自己处理系统缩放，这里不要再乘 DPI，避免行距被放大两次
            字号 = 11
            内容字体 = tkfont.Font(family="Microsoft YaHei", size=字号)
            表头字体 = tkfont.Font(family="Microsoft YaHei", size=字号, weight="bold")
            文字行高 = 内容字体.metrics("linespace")
            行高 = max(24, min(34, 文字行高 + 6))

            样式 = ttk.Style(窗口)
            样式名 = f"Yima{id(窗口)}.Treeview"
            样式.configure(样式名, font=内容字体, rowheight=行高)
            样式.configure(f"{样式名}.Heading", font=表头字体)

            容器 = tk.Frame(窗口)
            容器.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

            表格 = ttk.Treeview(容器, columns=列名, show="headings", selectmode="browse", height=高度值, style=样式名)
            for 列 in 列名:
                表格.heading(列, text=列)
                建议宽度 = max(90, min(260, 30 + len(str(列)) * 24))
                表格.column(列, anchor="w", stretch=True, width=建议宽度)

            纵向滚动条 = ttk.Scrollbar(容器, orient="vertical", command=表格.yview)
            横向滚动条 = ttk.Scrollbar(容器, orient="horizontal", command=表格.xview)
            表格.configure(yscrollcommand=纵向滚动条.set, xscrollcommand=横向滚动条.set)

            表格.grid(row=0, column=0, sticky="nsew")
            纵向滚动条.grid(row=0, column=1, sticky="ns")
            横向滚动条.grid(row=1, column=0, sticky="ew")
            容器.grid_rowconfigure(0, weight=1)
            容器.grid_columnconfigure(0, weight=1)

            表格._易码列名 = 列名
            表格._易码内容字体 = 内容字体
            表格._易码表头字体 = 表头字体
            return 表格

        def _表格加行(表格, 行数据):
            值 = _规范表格行(表格, 行数据)
            return 表格.insert("", "end", values=值)

        def _表格清空(表格):
            for 项 in 表格.get_children():
                表格.delete(项)

        def _表格所有行(表格):
            结果 = []
            for 项 in 表格.get_children():
                结果.append(list(表格.item(项, "values")))
            return 结果

        def _表格选中行(表格):
            选中 = 表格.selection()
            if not 选中:
                return None
            return list(表格.item(选中[0], "values"))

        def _表格选中序号(表格):
            选中 = 表格.selection()
            if not 选中:
                return -1
            子项 = list(表格.get_children())
            try:
                return 子项.index(选中[0])
            except ValueError:
                return -1

        def _表格删行(表格, 序号或项=""):
            目标项 = _定位表格项(表格, 序号或项)
            if not 目标项:
                return False
            表格.delete(目标项)
            return True

        def _表格改行(表格, 序号或项, 行数据):
            目标项 = _定位表格项(表格, 序号或项)
            if not 目标项:
                return False
            值 = _规范表格行(表格, 行数据)
            表格.item(目标项, values=值)
            return True
            
        self.全局环境.记住("建窗口", _创建窗口)
        self.全局环境.记住("加文字", _加上文字)
        self.全局环境.记住("加输入框", _加上输入框)
        self.全局环境.记住("读输入", _读取输入)
        self.全局环境.记住("改文字", _修改文字)
        self.全局环境.记住("加按钮", _加上按钮)
        self.全局环境.记住("弹窗", _弹窗提醒)
        self.全局环境.记住("弹窗输入", _弹窗输入)
        self.全局环境.记住("打开界面", _展示窗口)
        self.全局环境.记住("加表格", _加上表格)
        self.全局环境.记住("表格加行", _表格加行)
        self.全局环境.记住("表格清空", _表格清空)
        self.全局环境.记住("表格所有行", _表格所有行)
        self.全局环境.记住("表格选中行", _表格选中行)
        self.全局环境.记住("表格选中序号", _表格选中序号)
        self.全局环境.记住("表格删行", _表格删行)
        self.全局环境.记住("表格改行", _表格改行)

    def _植入画图库(self):
        import turtle
        def 转数字(内容):
            内容文字 = str(内容).strip()
            if not 内容文字: return 0
            if '.' in 内容文字: return float(内容文字)
            return int(内容文字)
            
        def 画布():
            turtle.setup(width=800, height=600)
            turtle.title("易码神奇画板")
        def 标题(文字): turtle.title(str(文字))
        def 设置图标(图标路径): 
            try:
                import os, sys
                目标 = str(图标路径)
                # 如果是打包的单文件，文件会被解压到 sys._MEIPASS
                if hasattr(sys, "_MEIPASS"):
                    测试 = os.path.join(sys._MEIPASS, os.path.basename(目标))
                    if os.path.exists(测试):
                        目标 = 测试
                
                # 获取底层的 Tkinter 根窗口并修改图标
                屏幕 = turtle.Screen()
                屏幕._root.iconbitmap(目标)
            except Exception as e:
                print(f"⚠️ 设置图标失败: {e}")
        def 前进(距离): turtle.forward(转数字(距离))
        def 后退(距离): turtle.backward(转数字(距离))
        def 左转(角度): turtle.left(转数字(角度))
        def 右转(角度): turtle.right(转数字(角度))
        def 抬笔(): turtle.penup()
        def 落笔(): turtle.pendown()
        def 停顿(时间): 
            import time
            time.sleep(转数字(时间))
        def 画笔颜色(颜色名): turtle.color(str(颜色名))
        def 背景颜色(颜色名): turtle.bgcolor(str(颜色名))
        def 去到(x, y): turtle.goto(转数字(x), 转数字(y))
        def 粗细(像素): turtle.pensize(转数字(像素))
        def 画圆(半径): turtle.circle(转数字(半径))
        def 速度(模式): turtle.speed(str(模式) if isinstance(模式, str) else int(模式))
        def 完成画画(): turtle.done()
        
        # 游戏引擎级画图函数
        def 隐藏画笔(): turtle.hideturtle()
        def 关闭动画(): turtle.tracer(0)
        def 刷新画面(): turtle.update()
        def 清除画面(): turtle.clear()
        def 写字(文字): turtle.write(str(文字), align="center", font=("Microsoft YaHei", 24, "normal"))
        def 监听按键():
            屏幕 = turtle.Screen()
            屏幕.listen()
            # 尽量把键盘焦点给画板，减少“按键无反应”的误判
            try:
                屏幕._root.focus_force()
            except Exception:
                pass
            try:
                屏幕.getcanvas().focus_force()
            except Exception:
                pass
        
        # 兼容“功能对象”与可调用对象，按键回调默认无参数
        def 绑定按键(可调用目标, 按键名):
            from .错误 import 运行报错
            函数对象 = self._转成易码函数对象(可调用目标, self.全局环境)
            if not 函数对象 and not hasattr(可调用目标, "__call__"):
                raise 运行报错("绑定按键的第一个参数必须是功能名称或可调用目标。", 0)

            按键文本 = str(按键名).strip()
            if not 按键文本:
                raise 运行报错("绑定按键的第二个参数不能为空。", 0)

            def 内部回调():
                try:
                    if 函数对象:
                        if len(函数对象.参数列表) != 0:
                            raise 运行报错(f"按键回调【{函数对象.函数名}】不能带参数。", 0)
                        self._执行易码函数对象(函数对象, [], 0)
                        return
                    可调用目标()
                except Exception as e:
                    print(f"⚠️ 按键回调失败（{按键文本}）：{e}")

            turtle.onkey(内部回调, 按键文本)

        def 计算距离(x, y):
            return turtle.distance(转数字(x), 转数字(y))
        
        def 获取X(): return turtle.xcor()
        def 获取Y(): return turtle.ycor()

        self.全局环境.记住("画布", 画布)
        self.全局环境.记住("标题", 标题)
        self.全局环境.记住("图标", 设置图标)
        self.全局环境.记住("向前走", 前进)
        self.全局环境.记住("向后走", 后退)
        self.全局环境.记住("左转", 左转)
        self.全局环境.记住("右转", 右转)
        self.全局环境.记住("抬笔", 抬笔)
        self.全局环境.记住("落笔", 落笔)
        self.全局环境.记住("画笔颜色", 画笔颜色)
        self.全局环境.记住("背景颜色", 背景颜色)
        self.全局环境.记住("去", 去到)
        self.全局环境.记住("笔粗", 粗细)
        self.全局环境.记住("画圆", 画圆)
        self.全局环境.记住("停一下", 停顿)
        self.全局环境.记住("定格", 完成画画)
        self.全局环境.记住("速度", 速度)
        self.全局环境.记住("隐藏画笔", 隐藏画笔)
        self.全局环境.记住("关闭动画", 关闭动画)
        self.全局环境.记住("刷新画面", 刷新画面)
        self.全局环境.记住("清除", 清除画面)
        self.全局环境.记住("写字", 写字)
        self.全局环境.记住("开始监听", 监听按键)
        self.全局环境.记住("绑定按键", 绑定按键)
        self.全局环境.记住("计算距离", 计算距离)
        self.全局环境.记住("当前X", 获取X)
        self.全局环境.记住("当前Y", 获取Y)

    def 执行代码(self, 程序树: 程序节点):
        return self.执行(程序树)

    def 执行(self, 节点, 当前环境=None):
        环境上下文 = 当前环境 if 当前环境 else self.全局环境
        
        类型名字 = type(节点).__name__
        方法名 = f"_做_{类型名字}"
        
        做点事 = getattr(self, 方法名, None)
        if 做点事 is None:
            raise Exception(f"解释器暂不支持节点类型【{类型名字}】。")
        try:
            return 做点事(节点, 环境上下文)
        except Exception as e:
            if type(e).__name__ == "Terminator":
                import sys
                sys.exit(0)
            raise

    def _做_程序节点(self, 节点: 程序节点, 环境上下文: 环境):
        结果 = None
        for 语句 in 节点.语句列表:
            结果 = self.执行(语句, 环境上下文)
        return 结果

    def _转为白话文本(self, 值, 内部嵌套=False):
        if type(值).__name__ == "空值" or 值 is None:
            return "空"
        if isinstance(值, 易码函数):
            return f"<功能 {值.函数名}>"
        if isinstance(值, 定义函数节点):
            return f"<功能 {值.函数名}>"
        if isinstance(值, bool):
            return "对" if 值 else "错"
        if isinstance(值, str):
            if 内部嵌套:
                return f'"{值}"'
            return 值
        if isinstance(值, list):
            元素文本 = [self._转为白话文本(x, True) for x in 值]
            return "[" + ", ".join(元素文本) + "]"
        if isinstance(值, dict):
            元素文本 = [f"{self._转为白话文本(k, True)}: {self._转为白话文本(v, True)}" for k, v in 值.items()]
            return "{" + ", ".join(元素文本) + "}"
        return str(值)

    def _做_显示语句节点(self, 节点: 显示语句节点, 环境上下文: 环境):
        值 = self.执行(节点.表达式, 环境上下文)
        # 用白话文格式最终输出
        print(self._转为白话文本(值))
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
            raise 运行报错(f"重复次数必须是整数，当前值为：{次数}")
        
        结果 = 空值()
        for i in range(次数):
            # 如果用户指定了循环变量名（重复 X 次 叫做 序号），就把当前序号存进环境
            if 节点.循环变量名:
                环境上下文.记住(节点.循环变量名, i)
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
            raise 运行报错(f"对象【{列表集}】不可遍历。", 节点.列表表达式.行号 if hasattr(节点.列表表达式, '行号') else 0)
            
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
         from .信号 import 停下信号, 略过信号, 返回信号
         结果 = 空值()
         try:
             for 语句 in 节点.尝试代码块:
                 结果 = self.执行(语句, 环境上下文)
         except (停下信号, 略过信号, 返回信号):
             # 控制流信号不应该被 try..catch 拦截
             raise
         except Exception as e:
             # 没写【如果出错】时，不应静默吞掉异常
             if not 节点.出错代码块:
                 raise
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
        环境上下文.记住(节点.函数名, 易码函数(节点, 环境上下文))
        return 空值()

    def _转成易码函数对象(self, 候选对象, 回退定义环境: 环境):
        if isinstance(候选对象, 易码函数):
            return 候选对象
        if isinstance(候选对象, 定义函数节点):
            定义环境 = getattr(候选对象, "_定义环境", 回退定义环境)
            return 易码函数(候选对象, 定义环境)
        return None

    def _执行易码函数对象(self, 函数对象: 易码函数, 参数值列表, 调用行号=0):
        from .错误 import 运行报错
        if len(参数值列表) != len(函数对象.参数列表):
            raise 运行报错(
                f"函数【{函数对象.函数名}】需要 {len(函数对象.参数列表)} 个参数，实际传入 {len(参数值列表)} 个。",
                调用行号,
            )

        定义环境 = 函数对象.定义环境 if 函数对象.定义环境 else self.全局环境
        函数环境 = 环境(爸爸环境=定义环境, 禁止向上赋值=self.严格局部作用域)
        for 名字, 值 in zip(函数对象.参数列表, 参数值列表):
            函数环境.记录本[名字] = 值

        from .信号 import 返回信号
        结果 = 空值()
        for 语句 in 函数对象.代码块:
            try:
                self.执行(语句, 函数环境)
            except 返回信号 as 信号:
                return 信号.值
        return 结果

    def _做_函数调用节点(self, 节点: 函数调用节点, 环境上下文: 环境):
        函数定义 = 环境上下文.告诉(节点.函数名, 节点.行号)
        
        # 1. 检查是不是 Python 的内置原生函数
        if hasattr(函数定义, '__call__'):
            传入的参数值 = []
            for 参数表达式 in 节点.参数列表:
                传入的参数值.append(self.执行(参数表达式, 环境上下文))
            return 函数定义(*传入的参数值)
            
        # 2. 普通易码函数
        函数对象 = self._转成易码函数对象(函数定义, 环境上下文)
        if not 函数对象:
            from .错误 import 运行报错
            raise 运行报错(f"名称【{节点.函数名}】不是可调用函数。", 节点.行号)
            
        传入的参数值 = []
        for 参数表达式 in 节点.参数列表:
            传入的参数值.append(self.执行(参数表达式, 环境上下文))
        return self._执行易码函数对象(函数对象, 传入的参数值, 节点.行号)

    def _做_动态调用节点(self, 节点: 动态调用节点, 环境上下文: 环境):
        可调用对象 = self.执行(节点.目标节点, 环境上下文)
        
        传入的参数值 = []
        for 参数表达式 in 节点.参数列表:
            传入的参数值.append(self.执行(参数表达式, 环境上下文))
            
        # 1. 检查是不是 Python 原生或库函数
        if hasattr(可调用对象, '__call__'):
            return 可调用对象(*传入的参数值)
            
        # 2. 普通易码函数 (定义函数节点)
        函数对象 = self._转成易码函数对象(可调用对象, 环境上下文)
        if not 函数对象:
            from .错误 import 运行报错
            raise 运行报错("当前对象不可调用（不能使用括号）。", 节点.行号)
        return self._执行易码函数对象(函数对象, 传入的参数值, 节点.行号)

    def _做_引入语句节点(self, 节点: 引入语句节点, 环境上下文: 环境):
        import importlib
        from .错误 import 易码错误, 运行报错
        
        注册名 = 节点.别名 if 节点.别名 else 节点.模块名.split('/')[-1].split('.')[0]
        
        # ========== 第一优先级：内置虚拟模块（它们的函数已经在启动时注入全局环境了）==========
        内置模块集 = {"图形界面", "魔法生态库", "文件管理", "画板", "系统工具", "数据工具", "网络请求", "本地数据库"}
        if 节点.模块名 in 内置模块集:
            if 节点.别名:
                环境上下文.记住(注册名, self._内置模块命名空间(节点.模块名, 环境上下文))
            return 空值()
        
        # ========== 第二优先级：易码源文件模块（.ym 文件）==========
        绝对路径 = self._定位易码模块文件(节点.模块名)
                
        if 绝对路径:
            try:
                模块缓存项 = self._加载易码模块(绝对路径, 环境上下文)
            except 易码错误:
                raise
            except Exception as e:
                raise 运行报错(f"加载模块失败：{e}", 节点.行号)

            环境上下文.记住(注册名, 模块缓存项["导出"])
            return 空值()
            
        # ========== 第三优先级：Python 原生库 ==========
        try:
            库模块 = importlib.import_module(节点.模块名)
        except ImportError:
            raise 运行报错(f"找不到模块【{节点.模块名}】。请检查名称或安装状态。", 节点.行号)
            
        环境上下文.记住(注册名, 库模块)
        return 空值()

    def _做_精确引入语句节点(self, 节点: 精确引入语句节点, 环境上下文: 环境):
        import importlib
        from .错误 import 易码错误, 运行报错

        内置模块集 = {"图形界面", "魔法生态库", "文件管理", "画板", "系统工具", "数据工具", "网络请求", "本地数据库"}
        if 节点.模块名 in 内置模块集:
            命名空间 = self._内置模块命名空间(节点.模块名, 环境上下文)
            if 节点.功能名 in 命名空间:
                环境上下文.记住(节点.功能名, 命名空间[节点.功能名])
                return 空值()
            raise 运行报错(f"内置模块【{节点.模块名}】中不存在名称【{节点.功能名}】。", 节点.行号)
        
        绝对路径 = self._定位易码模块文件(节点.模块名)
        if 绝对路径:
            try:
                模块缓存项 = self._加载易码模块(绝对路径, 环境上下文)
            except 易码错误:
                raise
            except Exception as e:
                raise 运行报错(f"加载模块失败：{e}", 节点.行号)

            模块全量符号 = 模块缓存项["全量"]

            # 从模块环境里捞出特定的功能
            if 节点.功能名 in 模块全量符号:
                环境上下文.记住(节点.功能名, 模块全量符号[节点.功能名])
            else:
                raise 运行报错(f"模块【{节点.模块名}】中不存在名称【{节点.功能名}】。", 节点.行号)
                
        else:
            # 走 Python 原生库引入
            try:
                库模块 = importlib.import_module(节点.模块名)
            except ImportError:
                raise 运行报错(f"找不到模块【{节点.模块名}】。", 节点.行号)
                
            if hasattr(库模块, 节点.功能名):
                环境上下文.记住(节点.功能名, getattr(库模块, 节点.功能名))
            else:
                raise 运行报错(f"Python 模块【{节点.模块名}】中不存在名称【{节点.功能名}】。", 节点.行号)
                
        return 空值()

    def _做_属性访问节点(self, 节点: 属性访问节点, 环境上下文: 环境):
        对象 = self.执行(节点.对象节点, 环境上下文)
        from .错误 import 运行报错
        
        # 如果是字典（比如导入的模块命名空间），用键名取值
        if isinstance(对象, dict):
            if 节点.属性名 in 对象:
                return 对象[节点.属性名]
            else:
                raise 运行报错(f"模块或字典中不存在属性【{节点.属性名}】。", 节点.行号)
                
        # 普通对象的属性访问
        if not hasattr(对象, 节点.属性名):
            raise 运行报错(f"对象不包含属性或方法【{节点.属性名}】。", 节点.行号)
        return getattr(对象, 节点.属性名)

    def _做_属性设置节点(self, 节点: 属性设置节点, 环境上下文: 环境):
        对象 = self.执行(节点.对象节点, 环境上下文)
        值 = self.执行(节点.值节点, 环境上下文)
        # 如果是字典，直接设置键值
        if isinstance(对象, dict):
            对象[节点.属性名] = 值
            return 值
        # 如果是对象，用 setattr
        setattr(对象, 节点.属性名, 值)
        return 值

    # --- 面向对象 ---
    def _做_图纸定义节点(self, 节点: 图纸定义节点, 环境上下文: 环境):
        # 把图纸定义储存在环境中
        环境上下文.记住(节点.图纸名, 节点)
        return 空值()

    def _做_实例化节点(self, 节点: 实例化节点, 环境上下文: 环境):
        from .错误 import 运行报错
        图纸 = 环境上下文.告诉(节点.图纸名, 节点.行号)
        if not isinstance(图纸, 图纸定义节点):
            raise 运行报错(f"名称【{节点.图纸名}】不是图纸定义，不能实例化。", 节点.行号)
        
        # 检查参数数量
        传入的参数值 = [self.执行(参, 环境上下文) for 参 in 节点.参数列表]
        if len(传入的参数值) != len(图纸.参数列表):
            raise 运行报错(f"创建【{节点.图纸名}】需要 {len(图纸.参数列表)} 个材料，但你给了 {len(传入的参数值)} 个。", 节点.行号)
            
        # 创建实例环境
        实例环境 = 环境(爸爸环境=环境上下文, 禁止向上赋值=self.严格局部作用域)
        for 名字, 值 in zip(图纸.参数列表, 传入的参数值):
            实例环境.记录本[名字] = 值
        
        # 保存旧的实例环境（支持嵌套）
        旧实例环境 = getattr(self, '_当前实例环境', None)
        self._当前实例环境 = 实例环境
        
        # 执行图纸的代码块（构造逻辑）
        from .信号 import 返回信号
        for 语句 in 图纸.代码块:
            try:
                self.执行(语句, 实例环境)
            except 返回信号:
                pass  # 构造函数中的返回会被忽略
        
        # 恢复旧实例环境
        self._当前实例环境 = 旧实例环境
        
        解释器引用 = self
        class 图纸实例:
            def __init__(self, 环境, 图纸名):
                super().__setattr__('_实例环境', 环境)
                super().__setattr__('_图纸名', 图纸名)
            
            def __getattr__(self, name):
                记录本 = self._实例环境.记录本
                if name in 记录本:
                    value = 记录本[name]
                    if isinstance(value, 易码函数) or isinstance(value, 定义函数节点):
                        # 动态生成绑定方法
                        原始函数 = value if isinstance(value, 易码函数) else 易码函数(value, self._实例环境)
                        绑定的实例环境 = self._实例环境
                        def 绑定方法(*参数值):
                            if len(参数值) != len(原始函数.参数列表):
                                from .错误 import 运行报错
                                raise 运行报错(f"方法参数数量不匹配：需要 {len(原始函数.参数列表)} 个，实际传入 {len(参数值)} 个。", 原始函数.行号)
                            函数环境 = 环境(爸爸环境=绑定的实例环境, 禁止向上赋值=解释器引用.严格局部作用域)
                            for 名字, 值 in zip(原始函数.参数列表, 参数值):
                                函数环境.记录本[名字] = 值
                            旧实例环境 = getattr(解释器引用, '_当前实例环境', None)
                            解释器引用._当前实例环境 = 绑定的实例环境
                            from .信号 import 返回信号
                            结果 = None
                            for 语句 in 原始函数.代码块:
                                try:
                                    解释器引用.执行(语句, 函数环境)
                                except 返回信号 as 信号:
                                    解释器引用._当前实例环境 = 旧实例环境
                                    return 信号.值
                            解释器引用._当前实例环境 = 旧实例环境
                            return 结果
                        return 绑定方法
                    return value
                raise AttributeError(name)
                
            def __setattr__(self, name, value):
                self._实例环境.记录本[name] = value

        对象 = 图纸实例(实例环境, 节点.图纸名)
        return 对象

    def _做_自身属性访问节点(self, 节点: 自身属性访问节点, 环境上下文: 环境):
        from .错误 import 运行报错
        实例环境 = getattr(self, '_当前实例环境', None)
        if 实例环境 is None:
            raise 运行报错("【它的】只能在图纸内部使用。", 节点.行号)
        if 节点.属性名 in 实例环境.记录本:
            return 实例环境.记录本[节点.属性名]
        raise 运行报错(f"实例上不存在属性【{节点.属性名}】。", 节点.行号)

    def _做_自身属性设置节点(self, 节点: 自身属性设置节点, 环境上下文: 环境):
        from .错误 import 运行报错
        实例环境 = getattr(self, '_当前实例环境', None)
        if 实例环境 is None:
            raise 运行报错("【它的】只能在图纸内部使用。", 节点.行号)
        值 = self.执行(节点.值节点, 环境上下文)
        实例环境.记录本[节点.属性名] = 值
        return 值

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
        
        if 操作符 in ["取反", "!"]:
            return not 操作数
        if 操作符 == "-":
            return -操作数
            
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
            raise 运行报错(f"索引【{索引}】不存在或越界。", 节点.行号)
        except TypeError:
            raise 运行报错("该对象不支持方括号取值。", 节点.行号)

    def _做_索引设置节点(self, 节点, 环境上下文):
        对象 = self.执行(节点.对象节点, 环境上下文)
        索引 = self.执行(节点.索引节点, 环境上下文)
        值 = self.执行(节点.值节点, 环境上下文)
        from .错误 import 运行报错
        try:
            if isinstance(对象, dict):
                对象[索引] = 值
            else:
                对象[int(索引)] = 值
            return 值
        except (IndexError, KeyError):
            raise 运行报错(f"索引【{索引}】不存在或越界。", 节点.行号)
        except TypeError:
            raise 运行报错("该对象不支持方括号设值。", 节点.行号)

    def _做_返回语句节点(self, 节点: 返回语句节点, 环境上下文: 环境):
        from .信号 import 返回信号
        if 节点.表达式 is None:
            raise 返回信号(空值())
        else:
            返回值 = self.执行(节点.表达式, 环境上下文)
            raise 返回信号(返回值)

    def _做_输入表达式节点(self, 节点: 输入表达式节点, 环境上下文: 环境):
        提示文 = str(self.执行(节点.提示语句表达式, 环境上下文))
        try:
            return input(提示文)
        except EOFError:
            return ""

    def _做_文本字面量节点(self, 节点: 文本字面量节点, 环境上下文: 环境):
        return 节点.值

    def _做_模板字符串节点(self, 节点: 模板字符串节点, 环境上下文: 环境):
        import re
        from .错误 import 名字找不到报错, 运行报错
        左括号占位 = "\uFFF0"
        右括号占位 = "\uFFF1"

        结果文本 = 节点.原始文本
        # 允许字面量输出【】：支持【【文本】】与 \【文本\】 两种写法
        结果文本 = 结果文本.replace("【【", 左括号占位).replace("】】", 右括号占位)
        结果文本 = 结果文本.replace("\\【", 左括号占位).replace("\\】", 右括号占位)

        找出的变量 = re.findall(r'【([^】]+)】', 结果文本)
        for 变量名 in 找出的变量:
            变量名 = 变量名.strip()
            try:
                值 = 环境上下文.告诉(变量名, 0)
                结果文本 = 结果文本.replace(f"【{变量名}】", self._转为白话文本(值))
            except 名字找不到报错:
                raise 运行报错(f"模板变量【{变量名}】未定义。", 0)

        结果文本 = 结果文本.replace(左括号占位, "【").replace(右括号占位, "】")
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
        
        from .错误 import 类型不匹配报错, 运行报错
        from .语法树 import 文本字面量节点
        # 拼接专门处理
        if 操作符 == "拼接":
            return self._转为白话文本(左边值) + self._转为白话文本(右边值)
        if 操作符 == "+":
            if isinstance(左边值, str) or isinstance(右边值, str):
                return self._转为白话文本(左边值) + self._转为白话文本(右边值)
            
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
            "幂": lambda a, b: a ** b,
            "**": lambda a, b: a ** b,
            "整除": lambda a, b: a // b,
            "//": lambda a, b: a // b,
        }
        
        if 操作符 in 运算函数:
            # 简单类型检查
            if not isinstance(左边值, (int, float)) or not isinstance(右边值, (int, float)):
                raise 类型不匹配报错(f"类型不匹配：{type(左边值).__name__} 与 {type(右边值).__name__} 不能执行【{操作符}】。", 节点.行号)
            if 操作符 in ("除以", "/", "整除", "//", "取余", "%") and 右边值 == 0:
                raise 运行报错("除数不能为 0。", 节点.行号)
            try:
                return 运算函数[操作符](左边值, 右边值)
            except ZeroDivisionError:
                raise 运行报错("除数不能为 0。", 节点.行号)
            
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
