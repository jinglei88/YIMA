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
        from .错误 import 易码错误

        根环境 = self._获取根环境(环境上下文)
        缓存键 = self._生成模块缓存键(绝对路径, 根环境)
        if 缓存键 in self._模块缓存:
            return self._模块缓存[缓存键]

        try:
            with open(绝对路径, 'r', encoding='utf-8') as f:
                源码 = f.read()

            from .词法分析 import 词法分析器
            from .语法分析 import 语法分析器

            模块Tokens = 词法分析器(源码).分析()
            模块AST = 语法分析器(模块Tokens).解析()

            # 模块执行环境采用“父环境继承 + 本地隔离”：
            # 1) 可直接访问内置能力/主程序全局；
            # 2) 模块内部赋值不回写到主程序全局；
            # 3) 导出符号仅来自模块本地记录本，避免混入父环境。
            模块环境 = 环境(爸爸环境=根环境, 禁止向上赋值=True)

            子解释器 = 解释器(严格局部作用域=self.严格局部作用域)
            子解释器.全局环境 = 模块环境
            子解释器._模块缓存 = self._模块缓存
            子解释器.设置当前目录(os.path.dirname(绝对路径))
            子解释器.执行代码(模块AST)

            模块导出 = dict(模块环境.记录本)

            缓存值 = {
                "导出": 模块导出,
                "全量": dict(模块环境.记录本),
            }
            self._模块缓存[缓存键] = 缓存值
            return 缓存值
        except 易码错误 as e:
            if not getattr(e, "文件路径", None):
                e.文件路径 = os.path.abspath(绝对路径)
            raise

    def _内置模块命名空间(self, 模块名: str, 环境上下文: 环境):
        根环境 = self._获取根环境(环境上下文)
        导出映射 = {
            "文件管理": ["读文件", "写文件", "追加文件"],
            "系统工具": [
                "文件存在", "目录存在", "创建目录", "列出目录", "删除文件", "删除目录",
                "复制文件", "移动文件", "重命名", "遍历文件",
                "复制目录", "压缩目录", "解压缩", "哈希文本", "哈希文件", "下载文件",
                "匹配文件", "文件信息", "目录大小",
                "格式时间", "解析时间", "写日志", "读日志", "睡眠",
                "拼路径", "绝对路径", "当前目录",
                "读环境变量", "写环境变量", "执行命令",
            ],
            "数据工具": ["解析JSON", "生成JSON", "读JSON", "写JSON", "读CSV", "写CSV", "读INI", "写INI"],
            "网络请求": ["发起请求", "发GET", "发POST", "发GET_JSON", "发POST_JSON", "读响应JSON"],
            "本地数据库": ["打开数据库", "执行SQL", "查询SQL", "关闭数据库", "开始事务", "提交事务", "回滚事务"],
            "图形界面": [
                "建窗口", "加文字", "加输入框", "加多行文本框", "加组合框", "加复选框", "加单选按钮",
                "读输入", "改文字", "加按钮", "加卡片", "加双列", "加登录模板", "加列表模板",
                "设位置", "弹窗", "弹窗输入", "打开界面",
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
        def 复制文件(源路径, 目标路径, 覆盖=True):
            import shutil
            源路径文本 = str(源路径)
            目标路径文本 = str(目标路径)
            if not os.path.isfile(源路径文本):
                return False
            if os.path.exists(目标路径文本) and not bool(覆盖):
                return False
            父目录 = os.path.dirname(os.path.abspath(目标路径文本))
            if 父目录:
                os.makedirs(父目录, exist_ok=True)
            shutil.copy2(源路径文本, 目标路径文本)
            return True
        def 移动文件(源路径, 目标路径, 覆盖=True):
            import shutil
            源路径文本 = str(源路径)
            目标路径文本 = str(目标路径)
            if not os.path.exists(源路径文本):
                return False
            if os.path.exists(目标路径文本):
                if not bool(覆盖):
                    return False
                if os.path.isdir(目标路径文本):
                    shutil.rmtree(目标路径文本)
                else:
                    os.remove(目标路径文本)
            父目录 = os.path.dirname(os.path.abspath(目标路径文本))
            if 父目录:
                os.makedirs(父目录, exist_ok=True)
            shutil.move(源路径文本, 目标路径文本)
            return True
        def 重命名(原路径, 新路径, 覆盖=True):
            import shutil
            原路径文本 = str(原路径)
            新路径文本 = str(新路径)
            if not os.path.exists(原路径文本):
                return False
            if os.path.exists(新路径文本):
                if not bool(覆盖):
                    return False
                if os.path.isdir(新路径文本):
                    shutil.rmtree(新路径文本)
                else:
                    os.remove(新路径文本)
            父目录 = os.path.dirname(os.path.abspath(新路径文本))
            if 父目录:
                os.makedirs(父目录, exist_ok=True)
            os.rename(原路径文本, 新路径文本)
            return True
        def 遍历文件(路径, 递归=True):
            路径文本 = str(路径) if 路径 is not None else "."
            if not os.path.isdir(路径文本):
                return []
            结果 = []
            if bool(递归):
                for 当前目录, _, 文件列表 in os.walk(路径文本):
                    for 文件名 in 文件列表:
                        结果.append(os.path.join(当前目录, 文件名))
            else:
                for 名称 in os.listdir(路径文本):
                    候选 = os.path.join(路径文本, 名称)
                    if os.path.isfile(候选):
                        结果.append(候选)
            return sorted(结果)
        def 复制目录(源目录, 目标目录, 覆盖=True):
            import shutil
            源目录文本 = str(源目录)
            目标目录文本 = str(目标目录)
            if not os.path.isdir(源目录文本):
                return False
            if os.path.exists(目标目录文本):
                if not bool(覆盖):
                    return False
                if os.path.isdir(目标目录文本):
                    shutil.rmtree(目标目录文本)
                else:
                    os.remove(目标目录文本)
            父目录 = os.path.dirname(os.path.abspath(目标目录文本))
            if 父目录:
                os.makedirs(父目录, exist_ok=True)
            shutil.copytree(源目录文本, 目标目录文本)
            return True
        def 压缩目录(源目录, 压缩包路径):
            import zipfile
            源目录文本 = str(源目录)
            压缩包文本 = str(压缩包路径)
            if not os.path.isdir(源目录文本):
                return False
            父目录 = os.path.dirname(os.path.abspath(压缩包文本))
            if 父目录:
                os.makedirs(父目录, exist_ok=True)
            with zipfile.ZipFile(压缩包文本, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for 当前目录, _, 文件列表 in os.walk(源目录文本):
                    for 文件名 in 文件列表:
                        完整路径 = os.path.join(当前目录, 文件名)
                        相对路径 = os.path.relpath(完整路径, 源目录文本)
                        zf.write(完整路径, arcname=相对路径)
            return True
        def 解压缩(压缩包路径, 目标目录):
            import zipfile
            压缩包文本 = str(压缩包路径)
            目标目录文本 = str(目标目录)
            if not os.path.isfile(压缩包文本):
                return False
            os.makedirs(目标目录文本, exist_ok=True)
            with zipfile.ZipFile(压缩包文本, "r") as zf:
                zf.extractall(目标目录文本)
            return True
        def 哈希文本(文本, 算法="sha256"):
            import hashlib
            算法名 = str(算法).strip().lower() if 算法 else "sha256"
            if not 算法名:
                算法名 = "sha256"
            if 算法名 not in hashlib.algorithms_available:
                算法名 = "sha256"
            计算器 = hashlib.new(算法名)
            计算器.update(str(文本).encode("utf-8"))
            return 计算器.hexdigest()
        def 哈希文件(路径, 算法="sha256"):
            import hashlib
            路径文本 = str(路径)
            if not os.path.isfile(路径文本):
                return ""
            算法名 = str(算法).strip().lower() if 算法 else "sha256"
            if not 算法名:
                算法名 = "sha256"
            if 算法名 not in hashlib.algorithms_available:
                算法名 = "sha256"
            计算器 = hashlib.new(算法名)
            with open(路径文本, "rb") as f:
                while True:
                    块 = f.read(8192)
                    if not 块:
                        break
                    计算器.update(块)
            return 计算器.hexdigest()
        def 下载文件(网址, 保存路径, 超时秒=30, 断点续传=True, 进度回调=None, 块大小=65536):
            from urllib import request as _req
            from urllib.error import HTTPError, URLError
            import time

            目标网址 = str(网址).strip()
            保存路径文本 = str(保存路径).strip()
            if not 目标网址 or not 保存路径文本:
                return {"成功": False, "状态码": 0, "路径": 保存路径文本, "错误": "网址和保存路径不能为空"}

            try:
                超时值 = max(0.1, float(超时秒))
            except Exception:
                超时值 = 30.0
            try:
                块大小值 = max(4096, int(块大小))
            except Exception:
                块大小值 = 65536

            def 触发进度回调(已下载字节, 总字节):
                if 进度回调 is None:
                    return
                总字节值 = int(总字节) if 总字节 else 0
                if 总字节值 > 0:
                    百分比 = round(float(已下载字节) * 100.0 / float(总字节值), 2)
                else:
                    百分比 = 0.0
                参数候选 = [int(已下载字节), 总字节值, float(百分比)]
                # 兼容 Python 可调用对象
                if hasattr(进度回调, "__call__") and not isinstance(进度回调, 易码函数):
                    for 参数个数 in (3, 2, 1, 0):
                        try:
                            if 参数个数 == 0:
                                进度回调()
                            else:
                                进度回调(*参数候选[:参数个数])
                            return
                        except TypeError:
                            continue
                        except Exception:
                            return
                    return
                # 兼容易码功能对象
                try:
                    回调函数对象 = self._转成易码函数对象(进度回调, self.全局环境)
                    if not 回调函数对象:
                        return
                    参数需求数 = len(getattr(回调函数对象, "参数列表", []) or [])
                    参数需求数 = max(0, min(参数需求数, 3))
                    调用参数 = 参数候选[:参数需求数] if 参数需求数 > 0 else []
                    self._执行易码函数对象(回调函数对象, 调用参数, 0)
                except Exception:
                    return

            try:
                父目录 = os.path.dirname(os.path.abspath(保存路径文本))
                if 父目录:
                    os.makedirs(父目录, exist_ok=True)

                已存在字节 = 0
                准备续传 = bool(断点续传) and os.path.isfile(保存路径文本)
                if 准备续传:
                    try:
                        已存在字节 = max(0, int(os.path.getsize(保存路径文本)))
                    except Exception:
                        已存在字节 = 0

                请求对象 = _req.Request(目标网址)
                if 已存在字节 > 0:
                    请求对象.add_header("Range", f"bytes={已存在字节}-")

                开始时间 = time.time()
                with _req.urlopen(请求对象, timeout=超时值) as resp:
                    状态码 = int(getattr(resp, "status", 200) or 200)
                    续传生效 = (已存在字节 > 0 and 状态码 == 206)
                    if 已存在字节 > 0 and not 续传生效:
                        已存在字节 = 0

                    写入模式 = "ab" if 续传生效 else "wb"
                    内容长度头 = str(resp.headers.get("Content-Length", "") or "").strip()
                    try:
                        本次长度 = int(内容长度头) if 内容长度头 else 0
                    except Exception:
                        本次长度 = 0
                    总字节数 = int(已存在字节 + 本次长度) if 本次长度 > 0 else 0

                    已下载字节 = int(已存在字节)
                    触发进度回调(已下载字节, 总字节数)
                    with open(保存路径文本, 写入模式) as f:
                        while True:
                            块 = resp.read(块大小值)
                            if not 块:
                                break
                            f.write(块)
                            已下载字节 += len(块)
                            触发进度回调(已下载字节, 总字节数)

                    耗时毫秒 = int((time.time() - 开始时间) * 1000)
                    return {
                        "成功": True,
                        "状态码": 状态码,
                        "路径": 保存路径文本,
                        "字节数": int(已下载字节),
                        "总字节数": int(总字节数 if 总字节数 > 0 else 已下载字节),
                        "续传": bool(续传生效),
                        "耗时毫秒": 耗时毫秒,
                    }
            except HTTPError as e:
                错误码 = int(getattr(e, "code", 0) or 0)
                if 错误码 == 416 and bool(断点续传) and os.path.isfile(保存路径文本):
                    try:
                        已有大小 = int(os.path.getsize(保存路径文本))
                    except Exception:
                        已有大小 = 0
                    return {
                        "成功": True,
                        "状态码": 206,
                        "路径": 保存路径文本,
                        "字节数": 已有大小,
                        "总字节数": 已有大小,
                        "续传": True,
                        "耗时毫秒": 0,
                    }
                return {"成功": False, "状态码": 错误码, "路径": 保存路径文本, "错误": str(e)}
            except URLError as e:
                return {"成功": False, "状态码": 0, "路径": 保存路径文本, "错误": str(e)}
            except Exception as e:
                return {"成功": False, "状态码": 0, "路径": 保存路径文本, "错误": str(e)}
        def 匹配文件(模式, 递归=True, 类型="全部", 包含文本="", 排除文本=""):
            import glob
            模式文本 = str(模式).strip()
            if not 模式文本:
                return []
            结果 = sorted(glob.glob(模式文本, recursive=bool(递归)))
            类型文本 = str(类型).strip() if 类型 is not None else "全部"
            if 类型文本 in ("文件", "file", "f"):
                结果 = [路径 for 路径 in 结果 if os.path.isfile(路径)]
            elif 类型文本 in ("目录", "文件夹", "folder", "dir", "d"):
                结果 = [路径 for 路径 in 结果 if os.path.isdir(路径)]

            包含词 = str(包含文本).strip() if 包含文本 is not None else ""
            排除词 = str(排除文本).strip() if 排除文本 is not None else ""
            if 包含词:
                结果 = [路径 for 路径 in 结果 if 包含词 in str(路径)]
            if 排除词:
                结果 = [路径 for 路径 in 结果 if 排除词 not in str(路径)]
            return 结果
        def 文件信息(路径):
            import datetime
            路径文本 = str(路径)
            if not os.path.exists(路径文本):
                return {"存在": False, "路径": os.path.abspath(路径文本)}
            绝对路径文本 = os.path.abspath(路径文本)
            类型文本 = "目录" if os.path.isdir(路径文本) else ("文件" if os.path.isfile(路径文本) else "其他")
            统计 = os.stat(路径文本)
            时间戳值 = float(统计.st_mtime)
            return {
                "存在": True,
                "路径": 绝对路径文本,
                "名称": os.path.basename(绝对路径文本),
                "后缀": os.path.splitext(绝对路径文本)[1],
                "类型": 类型文本,
                "大小": int(统计.st_size),
                "修改时间戳": 时间戳值,
                "修改时间": datetime.datetime.fromtimestamp(时间戳值).strftime("%Y-%m-%d %H:%M:%S"),
            }
        def 目录大小(路径):
            路径文本 = str(路径)
            if not os.path.isdir(路径文本):
                return 0
            总大小 = 0
            for 当前目录, _, 文件列表 in os.walk(路径文本):
                for 文件名 in 文件列表:
                    文件路径 = os.path.join(当前目录, 文件名)
                    if os.path.isfile(文件路径):
                        总大小 += os.path.getsize(文件路径)
            return int(总大小)
        def 格式时间(时间值=None, 格式="%Y-%m-%d %H:%M:%S"):
            import datetime
            时间格式 = str(格式) if 格式 else "%Y-%m-%d %H:%M:%S"
            if 时间值 is None or 时间值 == "":
                时间对象 = datetime.datetime.now()
            else:
                时间对象 = datetime.datetime.fromtimestamp(float(时间值))
            return 时间对象.strftime(时间格式)
        def 解析时间(时间文本, 格式="%Y-%m-%d %H:%M:%S"):
            import datetime
            时间格式 = str(格式) if 格式 else "%Y-%m-%d %H:%M:%S"
            时间对象 = datetime.datetime.strptime(str(时间文本), 时间格式)
            return int(时间对象.timestamp())
        def 写日志(路径, 内容, 级别="信息"):
            import datetime
            路径文本 = str(路径)
            父目录 = os.path.dirname(os.path.abspath(路径文本))
            if 父目录:
                os.makedirs(父目录, exist_ok=True)
            时间文本 = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            级别文本 = str(级别) if 级别 is not None else "信息"
            行文本 = f"[{时间文本}] [{级别文本}] {内容}"
            with open(路径文本, "a", encoding="utf-8") as f:
                f.write(行文本 + "\n")
            return 行文本
        def 读日志(路径, 最大行数=200):
            路径文本 = str(路径)
            if not os.path.isfile(路径文本):
                return []
            行数上限 = int(最大行数) if 最大行数 is not None else 200
            if 行数上限 <= 0:
                return []
            with open(路径文本, "r", encoding="utf-8") as f:
                全部行 = f.readlines()
            return [行.rstrip("\r\n") for 行 in 全部行[-行数上限:]]
        def 睡眠(秒):
            import time
            time.sleep(max(0.0, float(秒)))
            return True
        def 拼路径(*片段):
            return os.path.join(*(str(片) for 片 in 片段))
        def 绝对路径(路径):
            return os.path.abspath(str(路径))
        def 当前目录():
            return os.getcwd()
        def 读环境变量(名称, 默认值=""):
            return os.environ.get(str(名称), 默认值 if 默认值 is not None else "")
        def 写环境变量(名称, 值):
            os.environ[str(名称)] = str(值)
            return os.environ.get(str(名称), "")
        def 执行命令(命令, 超时秒=15, 工作目录=""):
            import subprocess
            命令文本 = str(命令).strip()
            if not 命令文本:
                return {"成功": False, "退出码": -1, "标准输出": "", "标准错误": "命令不能为空", "错误": "命令不能为空"}
            try:
                执行结果 = subprocess.run(
                    命令文本,
                    shell=True,
                    cwd=str(工作目录) if 工作目录 else None,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=float(超时秒),
                )
                return {
                    "成功": 执行结果.returncode == 0,
                    "退出码": int(执行结果.returncode),
                    "标准输出": 执行结果.stdout or "",
                    "标准错误": 执行结果.stderr or "",
                }
            except subprocess.TimeoutExpired as e:
                标准输出 = e.stdout or ""
                标准错误 = e.stderr or ""
                if isinstance(标准输出, (bytes, bytearray)):
                    标准输出 = 标准输出.decode("utf-8", errors="replace")
                if isinstance(标准错误, (bytes, bytearray)):
                    标准错误 = 标准错误.decode("utf-8", errors="replace")
                return {"成功": False, "退出码": -1, "标准输出": str(标准输出), "标准错误": str(标准错误), "错误": "命令执行超时"}
            except Exception as e:
                return {"成功": False, "退出码": -1, "标准输出": "", "标准错误": str(e), "错误": str(e)}
        self.全局环境.记住("文件存在", 文件存在)
        self.全局环境.记住("目录存在", 目录存在)
        self.全局环境.记住("创建目录", 创建目录)
        self.全局环境.记住("列出目录", 列出目录)
        self.全局环境.记住("删除文件", 删除文件)
        self.全局环境.记住("删除目录", 删除目录)
        self.全局环境.记住("复制文件", 复制文件)
        self.全局环境.记住("移动文件", 移动文件)
        self.全局环境.记住("重命名", 重命名)
        self.全局环境.记住("遍历文件", 遍历文件)
        self.全局环境.记住("复制目录", 复制目录)
        self.全局环境.记住("压缩目录", 压缩目录)
        self.全局环境.记住("解压缩", 解压缩)
        self.全局环境.记住("哈希文本", 哈希文本)
        self.全局环境.记住("哈希文件", 哈希文件)
        self.全局环境.记住("下载文件", 下载文件)
        self.全局环境.记住("匹配文件", 匹配文件)
        self.全局环境.记住("文件信息", 文件信息)
        self.全局环境.记住("目录大小", 目录大小)
        self.全局环境.记住("格式时间", 格式时间)
        self.全局环境.记住("解析时间", 解析时间)
        self.全局环境.记住("写日志", 写日志)
        self.全局环境.记住("读日志", 读日志)
        self.全局环境.记住("睡眠", 睡眠)
        self.全局环境.记住("拼路径", 拼路径)
        self.全局环境.记住("绝对路径", 绝对路径)
        self.全局环境.记住("当前目录", 当前目录)
        self.全局环境.记住("读环境变量", 读环境变量)
        self.全局环境.记住("写环境变量", 写环境变量)
        self.全局环境.记住("执行命令", 执行命令)

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
        def 读CSV(路径):
            import csv
            路径文本 = str(路径)
            if not os.path.isfile(路径文本):
                return []
            with open(路径文本, "r", encoding="utf-8", newline="") as f:
                字典读取器 = csv.DictReader(f)
                if 字典读取器.fieldnames:
                    return [dict(行) for 行 in 字典读取器]
                f.seek(0)
                普通读取器 = csv.reader(f)
                return [list(行) for 行 in 普通读取器]
        def 写CSV(路径, 行列表, 表头=None):
            import csv
            路径文本 = str(路径)
            父目录 = os.path.dirname(os.path.abspath(路径文本))
            if 父目录:
                os.makedirs(父目录, exist_ok=True)
            if isinstance(行列表, (list, tuple)):
                数据列表 = list(行列表)
            else:
                数据列表 = []

            with open(路径文本, "w", encoding="utf-8", newline="") as f:
                if 数据列表 and isinstance(数据列表[0], dict):
                    if isinstance(表头, (list, tuple)) and 表头:
                        列名 = [str(列) for 列 in 表头]
                    else:
                        列名 = []
                        for 行 in 数据列表:
                            if isinstance(行, dict):
                                for 键 in 行.keys():
                                    键名 = str(键)
                                    if 键名 not in 列名:
                                        列名.append(键名)
                    写入器 = csv.DictWriter(f, fieldnames=列名)
                    if 列名:
                        写入器.writeheader()
                    for 行 in 数据列表:
                        if isinstance(行, dict):
                            写入器.writerow({列: 行.get(列, "") for 列 in 列名})
                else:
                    写入器 = csv.writer(f)
                    if isinstance(表头, (list, tuple)) and 表头:
                        写入器.writerow([str(列) for 列 in 表头])
                    for 行 in 数据列表:
                        if isinstance(行, (list, tuple)):
                            写入器.writerow(list(行))
                        elif isinstance(行, dict):
                            写入器.writerow(list(行.values()))
                        else:
                            写入器.writerow([行])
            return 路径文本
        def 读INI(路径):
            import configparser
            路径文本 = str(路径)
            if not os.path.isfile(路径文本):
                return {}
            配置 = configparser.ConfigParser()
            配置.read(路径文本, encoding="utf-8")
            结果 = {}
            for 节 in 配置.sections():
                结果[节] = {}
                for 键, 值 in 配置.items(节):
                    结果[节][键] = 值
            return 结果
        def 写INI(路径, 数据):
            import configparser
            路径文本 = str(路径)
            父目录 = os.path.dirname(os.path.abspath(路径文本))
            if 父目录:
                os.makedirs(父目录, exist_ok=True)
            配置 = configparser.ConfigParser()
            if isinstance(数据, dict):
                for 节, 映射 in 数据.items():
                    节名 = str(节)
                    配置[节名] = {}
                    if isinstance(映射, dict):
                        for 键, 值 in 映射.items():
                            配置[节名][str(键)] = str(值)
            with open(路径文本, "w", encoding="utf-8") as f:
                配置.write(f)
            return 路径文本
        self.全局环境.记住("解析JSON", 解析JSON)
        self.全局环境.记住("生成JSON", 生成JSON)
        self.全局环境.记住("读JSON", 读JSON)
        self.全局环境.记住("写JSON", 写JSON)
        self.全局环境.记住("读CSV", 读CSV)
        self.全局环境.记住("写CSV", 写CSV)
        self.全局环境.记住("读INI", 读INI)
        self.全局环境.记住("写INI", 写INI)

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
            原因 = f"图形界面加载失败：{e}"
            self._可选能力告警.append(原因)
            self._植入图形库兜底函数(原因)
            
        # 尝试植入画板引擎 (Turtle)
        try:
            self._植入画图库()
        except Exception as e:
            self._可选能力告警.append(f"画板加载失败：{e}")

    def _植入图形库兜底函数(self, 失败原因: str):
        from .错误 import 运行报错

        图形能力名 = [
            "建窗口", "加文字", "加输入框", "加多行文本框", "加组合框", "加复选框", "加单选按钮",
            "读输入", "改文字", "加按钮", "加卡片", "加双列", "加登录模板", "加列表模板",
            "设位置", "弹窗", "弹窗输入", "打开界面",
            "加表格", "表格加行", "表格清空", "表格所有行", "表格选中行", "表格选中序号", "表格删行", "表格改行",
        ]

        def 生成兜底函数(能力名):
            def _兜底调用(*参数):
                # 兜底函数先尝试“延迟恢复”图形能力，恢复成功后立刻转发。
                try:
                    self._植入图形库()
                    真实函数 = self.全局环境.记录本.get(能力名)
                    if callable(真实函数) and 真实函数 is not _兜底调用:
                        return 真实函数(*参数)
                except Exception as 二次错误:
                    raise 运行报错(f"图形能力【{能力名}】不可用：{二次错误}", 0)
                raise 运行报错(f"图形能力【{能力名}】不可用：{失败原因}", 0)
            return _兜底调用

        for 能力名 in 图形能力名:
            if 能力名 not in self.全局环境.记录本:
                self.全局环境.记住(能力名, 生成兜底函数(能力名))

    def _植入图形库(self):
        import tkinter as tk
        import tkinter.messagebox as messagebox
        import tkinter.font as tkfont
        import tkinter.simpledialog as simpledialog
        try:
            import tkinter.ttk as ttk
        except Exception:
            # 某些打包环境下 `from tkinter import ttk` / `import tkinter.ttk`
            # 其中一种可能失效，做双通道兜底。
            from tkinter import ttk

        界面主题_简洁浅色 = {
            "窗口背景": "#EEF3FA",
            "内容背景": "#F8FBFF",
            "文字颜色": "#1E2A3B",
            "次级文字": "#5C6E83",
            "输入背景": "#FFFFFF",
            "输入文字": "#1E2A3B",
            "边框颜色": "#C8D5E6",
            "强调色": "#2F7FE3",
            "强调悬停色": "#266BC0",
            "按钮文字": "#FFFFFF",
            "表格标题背景": "#E9F1FB",
            "表格标题文字": "#203048",
            "表格背景": "#FFFFFF",
            "表格文字": "#1E2A3B",
            "表格选中背景": "#2F7FE3",
            "表格选中文字": "#FFFFFF",
        }
        界面主题_专业深色 = {
            "窗口背景": "#111827",
            "内容背景": "#162033",
            "文字颜色": "#E6EDF7",
            "次级文字": "#9AA9BE",
            "输入背景": "#0F1726",
            "输入文字": "#E6EDF7",
            "边框颜色": "#2A3B57",
            "强调色": "#2F7FE3",
            "强调悬停色": "#266BC0",
            "按钮文字": "#FFFFFF",
            "表格标题背景": "#1A2A43",
            "表格标题文字": "#DCE8F7",
            "表格背景": "#101A2C",
            "表格文字": "#E6EDF7",
            "表格选中背景": "#2F7FE3",
            "表格选中文字": "#FFFFFF",
        }

        def _解析界面主题(主题名):
            文本 = str(主题名 or "").strip().lower()
            if 文本 in {"深色", "暗色", "夜间", "dark", "专业深色", "dark-pro"}:
                return dict(界面主题_专业深色)
            return dict(界面主题_简洁浅色)

        def _取界面主题(窗口或容器):
            当前 = 窗口或容器
            while 当前 is not None:
                主题 = getattr(当前, "_易码界面主题", None)
                if isinstance(主题, dict):
                    return 主题
                当前 = getattr(当前, "master", None)
            return 界面主题_简洁浅色

        def _取挂载容器(窗口或容器):
            return getattr(窗口或容器, "_易码滚动内容框", 窗口或容器)
        
        def _创建窗口(标题="易码程序", 宽=400, 高=300, 滚动条="自动"):
            现有根窗口 = getattr(tk, "_default_root", None)
            已有根窗口可用 = False
            if 现有根窗口 is not None:
                try:
                    已有根窗口可用 = bool(现有根窗口.winfo_exists())
                except Exception:
                    已有根窗口可用 = False

            嵌入IDE模式 = bool(getattr(现有根窗口, "_易码IDE根窗口", False))
            if 嵌入IDE模式 and 已有根窗口可用:
                窗口 = tk.Toplevel(现有根窗口)
                窗口._易码嵌入窗口 = True
            else:
                窗口 = tk.Tk()
                窗口._易码嵌入窗口 = False
            窗口.title(标题)
            窗口.geometry(f"{宽}x{高}")
            try:
                窗口.minsize(max(360, int(宽 * 0.75)), max(260, int(高 * 0.75)))
            except Exception:
                pass
            # 高清适配
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

            默认主题名 = os.environ.get("YIMA_GUI_THEME", "简洁浅色")
            主题 = _解析界面主题(默认主题名)
            窗口._易码界面主题 = 主题
            try:
                窗口.configure(bg=主题["窗口背景"])
            except Exception:
                pass

            # 为长表单默认启用垂直滚动容器：不改用户代码即可滚动查看底部内容。
            主容器 = tk.Frame(窗口, bg=主题["窗口背景"])
            主容器.pack(fill=tk.BOTH, expand=True)

            滚动画布 = tk.Canvas(
                主容器,
                highlightthickness=0,
                borderwidth=0,
                bg=主题["窗口背景"],
                relief="flat",
            )
            纵向滚动条 = ttk.Scrollbar(主容器, orient="vertical", command=滚动画布.yview)
            滚动画布.configure(yscrollcommand=纵向滚动条.set)

            滚动画布.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            模式文本 = str(滚动条 or "自动").strip().lower()
            if 模式文本 in {"无", "关闭", "off", "none", "no", "false", "0"}:
                滚动模式 = "off"
            elif 模式文本 in {"总是", "始终", "always", "on", "true", "1"}:
                滚动模式 = "always"
            else:
                滚动模式 = "auto"

            滚动条状态 = {"显示": False}

            def _设置滚动条显示(显示):
                需要显示 = bool(显示)
                已显示 = bool(滚动条状态.get("显示", False))
                if 需要显示 and (not 已显示):
                    try:
                        纵向滚动条.pack(side=tk.RIGHT, fill=tk.Y)
                        滚动条状态["显示"] = True
                    except Exception:
                        pass
                elif (not 需要显示) and 已显示:
                    try:
                        纵向滚动条.pack_forget()
                        滚动条状态["显示"] = False
                    except Exception:
                        pass

            内容框 = tk.Frame(滚动画布, bg=主题["内容背景"], padx=16, pady=14)
            内容框._易码绝对布局容器 = True
            内容框窗口 = 滚动画布.create_window((0, 0), window=内容框, anchor="nw")

            def _更新滚动区域(_event=None):
                try:
                    边界 = 滚动画布.bbox("all")
                    if 边界:
                        滚动画布.configure(scrollregion=边界)
                    内容高 = max(0, int((边界[3] - 边界[1]) if 边界 else 0))
                    画布高 = max(0, int(滚动画布.winfo_height() or 0))
                    if 滚动模式 == "always":
                        _设置滚动条显示(True)
                    elif 滚动模式 == "off":
                        _设置滚动条显示(False)
                    else:
                        _设置滚动条显示(内容高 > (画布高 + 2))
                except Exception:
                    pass

            def _同步内容宽度(event):
                try:
                    滚动画布.itemconfigure(内容框窗口, width=event.width)
                except Exception:
                    pass

            def _滚轮滚动(event):
                try:
                    if hasattr(event, "delta") and event.delta:
                        步数 = int(-event.delta / 120)
                    elif getattr(event, "num", None) == 4:
                        步数 = -1
                    elif getattr(event, "num", None) == 5:
                        步数 = 1
                    else:
                        步数 = 0
                    if 步数:
                        滚动画布.yview_scroll(步数, "units")
                        return "break"
                except Exception:
                    return None

            内容框.bind("<Configure>", _更新滚动区域)
            滚动画布.bind("<Configure>", _同步内容宽度)
            窗口.bind("<MouseWheel>", _滚轮滚动, add="+")
            窗口.bind("<Button-4>", _滚轮滚动, add="+")
            窗口.bind("<Button-5>", _滚轮滚动, add="+")

            if 滚动模式 == "always":
                _设置滚动条显示(True)

            窗口._易码滚动画布 = 滚动画布
            窗口._易码滚动内容框 = 内容框
            窗口._易码更新滚动区域 = _更新滚动区域
            return 窗口
            
        def _加上文字(窗口, 内容):
            父容器 = _取挂载容器(窗口)
            主题 = _取界面主题(窗口)
            标签 = tk.Label(
                父容器,
                text=str(内容),
                font=("Microsoft YaHei", 12),
                bg=主题["内容背景"],
                fg=主题["文字颜色"],
                anchor="w",
                justify="left",
            )
            标签.pack(fill=tk.X, pady=(2, 8))
            return 标签
            
        def _加上输入框(窗口):
            父容器 = _取挂载容器(窗口)
            主题 = _取界面主题(窗口)
            输入框 = tk.Entry(
                父容器,
                font=("Microsoft YaHei", 12),
                bg=主题["输入背景"],
                fg=主题["输入文字"],
                insertbackground=主题["输入文字"],
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground=主题["边框颜色"],
                highlightcolor=主题["强调色"],
            )
            输入框.pack(fill=tk.X, pady=(2, 10), ipady=6)
            return 输入框

        def _加上多行文本框(窗口, 默认内容="", 行数=5):
            父容器 = _取挂载容器(窗口)
            主题 = _取界面主题(窗口)
            行数值 = max(3, _转整数(行数, 5))
            文本框 = tk.Text(
                父容器,
                height=行数值,
                wrap="word",
                font=("Microsoft YaHei", 11),
                bg=主题["输入背景"],
                fg=主题["输入文字"],
                insertbackground=主题["输入文字"],
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground=主题["边框颜色"],
                highlightcolor=主题["强调色"],
                padx=8,
                pady=6,
            )
            默认文本 = str(默认内容 or "")
            if 默认文本:
                try:
                    文本框.insert("1.0", 默认文本)
                except Exception:
                    pass
            文本框.pack(fill=tk.X, pady=(2, 10))
            return 文本框

        def _加上组合框(窗口, 选项定义="", 默认值=""):
            父容器 = _取挂载容器(窗口)
            候选项 = _规范列名(选项定义)
            组合框 = ttk.Combobox(
                父容器,
                values=候选项,
                state="readonly",
                font=("Microsoft YaHei", 11),
            )
            默认文本 = str(默认值 or "").strip()
            if 默认文本 and 默认文本 in 候选项:
                组合框.set(默认文本)
            elif 候选项:
                组合框.set(str(候选项[0]))
            组合框.pack(fill=tk.X, pady=(2, 10), ipady=3)
            return 组合框

        def _触发界面函数调用(函数名, 回调环境, 错误标题):
            目标函数名 = str(函数名 or "").strip()
            if not 目标函数名:
                return
            try:
                from .语法树 import 函数调用节点
                虚拟调用 = 函数调用节点(目标函数名, [], 行号=0)
                self._做_函数调用节点(虚拟调用, 回调环境)
            except Exception as e:
                messagebox.showerror(str(错误标题 or "组件执行失败"), f"未找到目标函数或执行失败：{e}")

        def _加上复选框(窗口, 文字="勾选项", 绑定的函数名="", _易码环境=None):
            回调环境 = _易码环境 if _易码环境 is not None else self.全局环境
            父容器 = _取挂载容器(窗口)
            主题 = _取界面主题(窗口)
            勾选变量 = tk.IntVar(value=0)

            def 切换动作():
                _触发界面函数调用(绑定的函数名, 回调环境, "复选框执行失败")

            复选框 = tk.Checkbutton(
                父容器,
                text=str(文字 or "勾选项"),
                variable=勾选变量,
                onvalue=1,
                offvalue=0,
                font=("Microsoft YaHei", 11),
                bg=主题["内容背景"],
                fg=主题["文字颜色"],
                selectcolor=主题["输入背景"],
                activebackground=主题["内容背景"],
                activeforeground=主题["文字颜色"],
                anchor="w",
                relief="flat",
                highlightthickness=0,
                padx=2,
                pady=2,
                command=切换动作,
            )
            复选框._易码值变量 = 勾选变量
            复选框._易码控件类型 = "复选框"
            复选框.pack(fill=tk.X, pady=(2, 8))
            return 复选框
        _加上复选框._易码需要环境 = True

        def _加上单选按钮(窗口, 文字="单选项", 绑定的函数名="", 组名="默认单选组", 值="", _易码环境=None):
            回调环境 = _易码环境 if _易码环境 is not None else self.全局环境
            父容器 = _取挂载容器(窗口)
            主题 = _取界面主题(窗口)

            根容器 = 父容器.winfo_toplevel()
            if not hasattr(根容器, "_易码单选组变量") or not isinstance(getattr(根容器, "_易码单选组变量"), dict):
                根容器._易码单选组变量 = {}
            组字典 = 根容器._易码单选组变量
            组键 = str(组名 or "默认单选组").strip() or "默认单选组"
            单选变量 = 组字典.get(组键)
            if 单选变量 is None:
                单选变量 = tk.StringVar(value="")
                组字典[组键] = 单选变量
            单选值 = str(值 if str(值 or "").strip() else (文字 or "单选项"))

            def 切换动作():
                _触发界面函数调用(绑定的函数名, 回调环境, "单选按钮执行失败")

            单选按钮 = tk.Radiobutton(
                父容器,
                text=str(文字 or "单选项"),
                variable=单选变量,
                value=单选值,
                font=("Microsoft YaHei", 11),
                bg=主题["内容背景"],
                fg=主题["文字颜色"],
                selectcolor=主题["输入背景"],
                activebackground=主题["内容背景"],
                activeforeground=主题["文字颜色"],
                anchor="w",
                relief="flat",
                highlightthickness=0,
                padx=2,
                pady=2,
                command=切换动作,
            )
            单选按钮._易码值变量 = 单选变量
            单选按钮._易码单选值 = 单选值
            单选按钮._易码控件类型 = "单选按钮"
            单选按钮.pack(fill=tk.X, pady=(2, 8))
            return 单选按钮
        _加上单选按钮._易码需要环境 = True
            
        def _读取输入(输入框):
            if 输入框 is None:
                return ""
            值变量 = getattr(输入框, "_易码值变量", None)
            if 值变量 is not None:
                try:
                    值 = 值变量.get()
                    if str(getattr(输入框, "_易码控件类型", "")) == "复选框":
                        return bool(_转整数(值, 0))
                    return 值
                except Exception:
                    pass
            if isinstance(输入框, tk.Text):
                try:
                    return 输入框.get("1.0", "end-1c")
                except Exception:
                    return ""
            try:
                return 输入框.get()
            except Exception:
                return ""

        def _写入输入(输入框, 内容=""):
            if 输入框 is None:
                return ""
            文本 = str(内容 if 内容 is not None else "")
            if isinstance(输入框, tk.Text):
                try:
                    输入框.delete("1.0", "end")
                    if 文本:
                        输入框.insert("1.0", 文本)
                    return 文本
                except Exception:
                    return ""
            try:
                输入框.delete(0, tk.END)
            except Exception:
                pass
            try:
                if 文本:
                    输入框.insert(0, 文本)
            except Exception:
                pass
            return 文本
            
        def _修改文字(标签, 新内容):
            标签.config(text=新内容)

        def _创建主题按钮(父容器, 主题, 文字, 回调=None, 锚点="w", 样式="主按钮"):
            样式文本 = str(样式 or "主按钮").strip().lower()
            主色 = str(主题["强调色"])
            主悬停 = str(主题["强调悬停色"])
            按钮字色 = str(主题["按钮文字"])
            次色 = "#2C3E55"
            次悬停 = "#35506F"
            危险色 = "#C0392B"
            危险悬停 = "#A93226"
            朴素色 = str(主题["内容背景"])
            朴素悬停 = "#22324A"
            朴素字色 = str(主题["文字颜色"])

            背景色 = 主色
            悬停色 = 主悬停
            字色 = 按钮字色
            if 样式文本 in {"次", "次按钮", "secondary", "second"}:
                背景色, 悬停色, 字色 = 次色, 次悬停, "#EAF2FF"
            elif 样式文本 in {"危险", "危险按钮", "danger", "warn", "warning"}:
                背景色, 悬停色, 字色 = 危险色, 危险悬停, "#FFFFFF"
            elif 样式文本 in {"朴素", "朴素按钮", "plain", "ghost", "text"}:
                背景色, 悬停色, 字色 = 朴素色, 朴素悬停, 朴素字色

            按钮 = tk.Button(
                父容器,
                text=str(文字),
                font=("Microsoft YaHei", 11, "bold"),
                bg=背景色,
                fg=字色,
                activebackground=悬停色,
                activeforeground=字色,
                relief="flat",
                bd=0,
                highlightthickness=0,
                padx=16,
                pady=8,
                cursor="hand2",
                command=回调 if callable(回调) else (lambda: None),
            )
            按钮.pack(anchor=str(锚点 or "w"), pady=(2, 10))
            按钮.bind("<Enter>", lambda _e: 按钮.configure(bg=悬停色), add="+")
            按钮.bind("<Leave>", lambda _e: 按钮.configure(bg=背景色), add="+")
            return 按钮
            
        def _加上按钮(窗口, 文字, 绑定的函数名, 样式="主按钮", _易码环境=None):
            回调环境 = _易码环境 if _易码环境 is not None else self.全局环境

            def 点击动作():
                try:
                    from .语法树 import 函数调用节点
                    虚拟调用 = 函数调用节点(绑定的函数名, [], 行号=0)
                    self._做_函数调用节点(虚拟调用, 回调环境)
                except Exception as e:
                    messagebox.showerror("按钮执行失败", f"未找到目标函数或执行失败：{e}")
            
            父容器 = _取挂载容器(窗口)
            主题 = _取界面主题(窗口)
            return _创建主题按钮(父容器, 主题, 文字, 点击动作, 锚点="w", 样式=样式)
        _加上按钮._易码需要环境 = True

        def _转整数(值, 默认值=0):
            try:
                return int(float(值))
            except Exception:
                return int(默认值)

        def _转整数并限制下界(值, 下界=1):
            try:
                整数值 = int(float(值))
            except Exception:
                整数值 = 下界
            return max(int(下界), 整数值)

        def _加上卡片(窗口或容器, 标题="", 显示边框=1):
            父容器 = _取挂载容器(窗口或容器)
            主题 = _取界面主题(窗口或容器)
            边框开 = bool(_转整数(显示边框, 1))

            卡片 = tk.Frame(
                父容器,
                bg=主题["内容背景"],
                highlightthickness=1 if 边框开 else 0,
                highlightbackground=主题["边框颜色"],
                highlightcolor=主题["边框颜色"],
                bd=0,
            )
            卡片.pack(fill=tk.X, pady=(4, 10))

            标题文本 = str(标题 or "").strip()
            if 标题文本:
                头部 = tk.Frame(卡片, bg=主题["内容背景"], padx=12, pady=10)
                头部.pack(fill=tk.X)
                tk.Label(
                    头部,
                    text=标题文本,
                    font=("Microsoft YaHei", 11, "bold"),
                    bg=主题["内容背景"],
                    fg=主题["文字颜色"],
                    anchor="w",
                    justify="left",
                ).pack(fill=tk.X)
                if 边框开:
                    tk.Frame(卡片, bg=主题["边框颜色"], height=1).pack(fill=tk.X, padx=10)

            内容框 = tk.Frame(卡片, bg=主题["内容背景"], padx=12, pady=10)
            内容框.pack(fill=tk.BOTH, expand=True)

            卡片._易码滚动内容框 = 内容框
            卡片._易码界面主题 = 主题
            return 卡片

        def _加上双列(窗口或容器, 左列比例=1, 右列比例=1):
            父容器 = _取挂载容器(窗口或容器)
            主题 = _取界面主题(窗口或容器)

            双列容器 = tk.Frame(父容器, bg=主题["内容背景"])
            双列容器.pack(fill=tk.X, pady=(2, 10))

            左列 = tk.Frame(双列容器, bg=主题["内容背景"])
            右列 = tk.Frame(双列容器, bg=主题["内容背景"])
            左列.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
            右列.grid(row=0, column=1, sticky="nsew")

            双列容器.grid_rowconfigure(0, weight=1)
            双列容器.grid_columnconfigure(0, weight=_转整数并限制下界(左列比例))
            双列容器.grid_columnconfigure(1, weight=_转整数并限制下界(右列比例))

            左列._易码界面主题 = 主题
            右列._易码界面主题 = 主题
            return [左列, 右列]

        def _加登录模板(窗口或容器, 标题="账号登录", 提交文案="登录", 提交函数名="", _易码环境=None):
            回调环境 = _易码环境 if _易码环境 is not None else self.全局环境
            卡片 = _加上卡片(窗口或容器, 标题)
            双列 = _加上双列(卡片, 1, 2)
            左列 = 双列[0]
            右列 = 双列[1]

            _加上文字(左列, "账号")
            账号输入框 = _加上输入框(右列)
            _加上文字(左列, "密码")
            密码输入框 = _加上输入框(右列)
            try:
                密码输入框.configure(show="*")
            except Exception:
                pass

            函数名 = str(提交函数名 or "").strip()

            def 点击动作():
                if not 函数名:
                    return
                try:
                    from .语法树 import 函数调用节点
                    虚拟调用 = 函数调用节点(函数名, [], 行号=0)
                    self._做_函数调用节点(虚拟调用, 回调环境)
                except Exception as e:
                    messagebox.showerror("按钮执行失败", f"未找到目标函数或执行失败：{e}")

            提交按钮 = _创建主题按钮(
                _取挂载容器(卡片),
                _取界面主题(卡片),
                提交文案,
                点击动作,
                锚点="w",
            )
            return {
                "卡片": 卡片,
                "账号输入框": 账号输入框,
                "密码输入框": 密码输入框,
                "提交按钮": 提交按钮,
            }
        _加登录模板._易码需要环境 = True

        def _加列表模板(窗口或容器, 标题="数据列表", 列定义="名称,说明", 高度=10, 查询文案="查询", 查询函数名="", _易码环境=None):
            回调环境 = _易码环境 if _易码环境 is not None else self.全局环境
            卡片 = _加上卡片(窗口或容器, 标题)
            双列 = _加上双列(卡片, 3, 1)
            左列 = 双列[0]
            右列 = 双列[1]

            _加上文字(左列, "关键字")
            关键字输入框 = _加上输入框(左列)

            函数名 = str(查询函数名 or "").strip()

            def 点击动作():
                if not 函数名:
                    return
                try:
                    from .语法树 import 函数调用节点
                    虚拟调用 = 函数调用节点(函数名, [], 行号=0)
                    self._做_函数调用节点(虚拟调用, 回调环境)
                except Exception as e:
                    messagebox.showerror("按钮执行失败", f"未找到目标函数或执行失败：{e}")

            查询按钮 = _创建主题按钮(
                _取挂载容器(右列),
                _取界面主题(右列),
                查询文案,
                点击动作,
                锚点="e",
            )
            表格 = _加上表格(卡片, 列定义, 高度)
            return {
                "卡片": 卡片,
                "关键字输入框": 关键字输入框,
                "查询按钮": 查询按钮,
                "表格": 表格,
            }
        _加列表模板._易码需要环境 = True

        def _设位置(控件, x, y, 宽=0, 高=0):
            x值 = max(0, _转整数(x, 0))
            y值 = max(0, _转整数(y, 0))
            宽值 = _转整数(宽, 0)
            高值 = _转整数(高, 0)

            定位控件 = getattr(控件, "_易码定位控件", 控件)
            if 定位控件 is None:
                定位控件 = 控件

            try:
                定位控件.pack_forget()
            except Exception:
                pass
            try:
                定位控件.grid_forget()
            except Exception:
                pass

            参数 = {"x": x值, "y": y值}
            if 宽值 > 0:
                参数["width"] = 宽值
            if 高值 > 0:
                参数["height"] = 高值
            定位控件.place(**参数)

            try:
                父容器 = getattr(定位控件, "master", None)
                if 父容器 is not None and bool(getattr(父容器, "_易码绝对布局容器", False)):
                    右边 = x值 + (宽值 if 宽值 > 0 else int(定位控件.winfo_reqwidth() or 0))
                    下边 = y值 + (高值 if 高值 > 0 else int(定位控件.winfo_reqheight() or 0))
                    目标宽 = max(int(getattr(父容器, "winfo_reqwidth")() or 0), 右边 + 24)
                    目标高 = max(int(getattr(父容器, "winfo_reqheight")() or 0), 下边 + 24)
                    try:
                        当前宽 = int(getattr(父容器, "winfo_width")() or 0)
                        当前高 = int(getattr(父容器, "winfo_height")() or 0)
                        目标宽 = max(目标宽, 当前宽)
                        目标高 = max(目标高, 当前高)
                    except Exception:
                        pass
                    父容器.configure(width=目标宽, height=目标高)
            except Exception:
                pass

            try:
                顶层 = 定位控件.winfo_toplevel()
                更新滚动 = getattr(顶层, "_易码更新滚动区域", None)
                if callable(更新滚动):
                    更新滚动()
            except Exception:
                pass
            return 控件
            
        def _弹窗提醒(标题, 内容):
            messagebox.showinfo(标题, 内容)
            
        def _弹窗输入(标题, 提示=""):
            结果 = simpledialog.askstring(标题, 提示)
            return 结果 if 结果 is not None else ""
            
        def _展示窗口(窗口):
            更新滚动 = getattr(窗口, "_易码更新滚动区域", None)
            if callable(更新滚动):
                try:
                    更新滚动()
                except Exception:
                    pass
            if bool(getattr(窗口, "_易码嵌入窗口", False)):
                try:
                    窗口.deiconify()
                    窗口.lift()
                    窗口.focus_force()
                except Exception:
                    pass
                return 窗口
            try:
                窗口.mainloop()
            except KeyboardInterrupt:
                try:
                    窗口.destroy()
                except Exception:
                    pass
            return 窗口

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
            主题 = _取界面主题(窗口)

            # 为表格单独设置字体和行高，避免中文在高 DPI 下被裁切
            # Tk 会自己处理系统缩放，这里不要再乘 DPI，避免行距被放大两次
            字号 = 11
            内容字体 = tkfont.Font(family="Microsoft YaHei", size=字号)
            表头字体 = tkfont.Font(family="Microsoft YaHei", size=字号, weight="bold")
            文字行高 = 内容字体.metrics("linespace")
            行高 = max(24, min(34, 文字行高 + 6))

            样式 = ttk.Style(窗口)
            try:
                样式.theme_use("clam")
            except Exception:
                pass
            样式名 = f"Yima{id(窗口)}.Treeview"
            样式.configure(
                样式名,
                font=内容字体,
                rowheight=行高,
                background=主题["表格背景"],
                fieldbackground=主题["表格背景"],
                foreground=主题["表格文字"],
                borderwidth=0,
                relief="flat",
            )
            样式.configure(
                f"{样式名}.Heading",
                font=表头字体,
                background=主题["表格标题背景"],
                foreground=主题["表格标题文字"],
                borderwidth=0,
                relief="flat",
            )
            样式.map(
                样式名,
                background=[("selected", 主题["表格选中背景"])],
                foreground=[("selected", 主题["表格选中文字"])],
            )
            样式.map(
                f"{样式名}.Heading",
                background=[("active", 主题["表格标题背景"])],
                foreground=[("active", 主题["表格标题文字"])],
            )

            父容器 = _取挂载容器(窗口)
            容器 = tk.Frame(
                父容器,
                bg=主题["内容背景"],
                highlightthickness=1,
                highlightbackground=主题["边框颜色"],
                highlightcolor=主题["边框颜色"],
                bd=0,
            )
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

            # 绝对定位时移动外层容器，避免只移动 Treeview 导致显示异常。
            表格._易码定位控件 = 容器
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
        self.全局环境.记住("加多行文本框", _加上多行文本框)
        self.全局环境.记住("加组合框", _加上组合框)
        self.全局环境.记住("加复选框", _加上复选框)
        self.全局环境.记住("加单选按钮", _加上单选按钮)
        self.全局环境.记住("读输入", _读取输入)
        self.全局环境.记住("写输入", _写入输入)
        self.全局环境.记住("改文字", _修改文字)
        self.全局环境.记住("加按钮", _加上按钮)
        self.全局环境.记住("加卡片", _加上卡片)
        self.全局环境.记住("加双列", _加上双列)
        self.全局环境.记住("加登录模板", _加登录模板)
        self.全局环境.记住("加列表模板", _加列表模板)
        self.全局环境.记住("设位置", _设位置)
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
            if getattr(函数定义, "_易码需要环境", False):
                return 函数定义(*传入的参数值, _易码环境=环境上下文)
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
            if getattr(可调用对象, "_易码需要环境", False):
                return 可调用对象(*传入的参数值, _易码环境=环境上下文)
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

        def 按统一引入规则取值(模块容器):
            """
            单一引入机制规则：
            - 引入 "模块" 叫做 名称
            - 若模块中存在同名导出【名称】，直接绑定该导出；
            - 否则绑定整个模块命名空间/模块对象。
            """
            别名 = 节点.别名
            if not 别名:
                return 模块容器
            if isinstance(模块容器, dict) and 别名 in 模块容器:
                return 模块容器[别名]
            if hasattr(模块容器, 别名):
                return getattr(模块容器, 别名)
            return 模块容器
        
        # ========== 第一优先级：内置虚拟模块（它们的函数已经在启动时注入全局环境了）==========
        内置模块集 = {"图形界面", "魔法生态库", "文件管理", "画板", "系统工具", "数据工具", "网络请求", "本地数据库"}
        if 节点.模块名 in 内置模块集:
            if 节点.别名:
                命名空间 = self._内置模块命名空间(节点.模块名, 环境上下文)
                环境上下文.记住(注册名, 按统一引入规则取值(命名空间))
            return 空值()
        
        # ========== 第二优先级：易码源文件模块（.ym 文件）==========
        绝对路径 = self._定位易码模块文件(节点.模块名)
                
        if 绝对路径:
            try:
                模块缓存项 = self._加载易码模块(绝对路径, 环境上下文)
            except 易码错误:
                raise
            except Exception as e:
                raise 运行报错(f"加载模块失败（{绝对路径}）：{e}", 节点.行号)

            环境上下文.记住(注册名, 按统一引入规则取值(模块缓存项["导出"]))
            return 空值()
            
        # ========== 第三优先级：Python 原生库 ==========
        try:
            库模块 = importlib.import_module(节点.模块名)
        except ImportError:
            raise 运行报错(f"找不到模块【{节点.模块名}】。请检查名称或安装状态。", 节点.行号)
            
        环境上下文.记住(注册名, 按统一引入规则取值(库模块))
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
        from .错误 import 名字找不到报错, 运行报错
        try:
            图纸 = 环境上下文.告诉(节点.图纸名, 节点.行号)
        except 名字找不到报错:
            raise 运行报错(
                f"【造一个】找不到图纸【{节点.图纸名}】。",
                节点.行号,
                建议=f"请先定义图纸：定义图纸 {节点.图纸名}(...)，再调用：造一个 {节点.图纸名}(...)。",
            )
        if not isinstance(图纸, 图纸定义节点):
            raise 运行报错(
                f"名称【{节点.图纸名}】不是图纸定义，不能实例化。",
                节点.行号,
                建议=f"【造一个】后面必须是【定义图纸】声明过的名称，例如：造一个 {节点.图纸名}(...)。",
            )
        
        # 检查参数数量
        传入的参数值 = [self.执行(参, 环境上下文) for 参 in 节点.参数列表]
        if len(传入的参数值) != len(图纸.参数列表):
            参数顺序 = "、".join(图纸.参数列表) if 图纸.参数列表 else "无参数"
            raise 运行报错(
                f"【造一个 {节点.图纸名}】参数数量不匹配：需要 {len(图纸.参数列表)} 个，实际传入 {len(传入的参数值)} 个。",
                节点.行号,
                建议=f"图纸【{节点.图纸名}】的参数顺序是：{参数顺序}。请按顺序补齐或删减参数。",
            )
            
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
                                参数顺序 = "、".join(原始函数.参数列表) if 原始函数.参数列表 else "无参数"
                                raise 运行报错(
                                    f"方法【{原始函数.函数名}】参数数量不匹配：需要 {len(原始函数.参数列表)} 个，实际传入 {len(参数值)} 个。",
                                    原始函数.行号,
                                    建议=f"方法【{原始函数.函数名}】参数顺序是：{参数顺序}。",
                                )
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
            raise 运行报错(
                "【它的】只能在图纸内部使用。",
                节点.行号,
                建议="图纸内部写：它的 属性；图纸外请使用：对象.属性。",
            )
        if 节点.属性名 in 实例环境.记录本:
            return 实例环境.记录本[节点.属性名]
        raise 运行报错(
            f"实例上不存在属性【{节点.属性名}】。",
            节点.行号,
            建议=f"请先在图纸中初始化：它的 {节点.属性名} = ...",
        )

    def _做_自身属性设置节点(self, 节点: 自身属性设置节点, 环境上下文: 环境):
        from .错误 import 运行报错
        实例环境 = getattr(self, '_当前实例环境', None)
        if 实例环境 is None:
            raise 运行报错(
                "【它的】只能在图纸内部使用。",
                节点.行号,
                建议="图纸内部写：它的 属性 = 值；图纸外请使用：对象.属性 = 值。",
            )
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
