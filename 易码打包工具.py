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
import sys
import subprocess
import shutil
import re
import importlib.util
import json

def 显示帮助():
    print("===================================")
    print("         易码 官方打包器            ")
    print("===================================")
    print("用法: python 易码打包工具.py <你的源码.ym> [可选的图标.ico] [可选的软件名]")
    print("例如: python 易码打包工具.py 示例/勇者大冒险.ym 游戏图标.ico 我的勇者传说")
    print("可选：在项目根目录放 易码打包清单.json（或 yima_pack.json）补充 hidden-import / datas")
    print("会在当前目录生成可直接运行的 .exe 文件。")

def 命令转文本(参数列表):
    """把命令参数列表转成可读文本，便于在日志中展示。"""
    if os.name == "nt":
        return subprocess.list2cmdline(参数列表)
    try:
        import shlex
        return " ".join(shlex.quote(x) for x in 参数列表)
    except Exception:
        return " ".join(str(x) for x in 参数列表)

def 清理软件名(名称, 默认值="易码生成软件"):
    名称文本 = str(名称 or "").strip()
    if not 名称文本:
        名称文本 = 默认值
    for 坏字符 in '<>:"/\\|?*\n\r\t':
        名称文本 = 名称文本.replace(坏字符, "_")
    名称文本 = 名称文本.strip(" .")
    if not 名称文本:
        名称文本 = 默认值
    系统保留名 = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}
    if 名称文本.upper() in 系统保留名:
        名称文本 = f"{名称文本}_app"
    return 名称文本

def _提取引入模块名(源码文本):
    """
    从易码源码中提取模块引用：
      - 引入 "模块名" ...
      - 用 "模块名" 中的 ...
    """
    结果 = []
    引入模式 = re.compile(r'^\s*(引入|用)\s*["“]([^"”]+)["”]')
    for 原始行 in str(源码文本 or "").splitlines():
        去注释 = 原始行.split("#", 1)[0].strip()
        if not 去注释:
            continue
        匹配 = 引入模式.match(去注释)
        if 匹配:
            模块名 = 匹配.group(2).strip()
            if 模块名:
                结果.append(模块名)
    return 结果

def _内置模块集合():
    return {
        "图形界面", "魔法生态库", "文件管理", "画板",
        "系统工具", "数据工具", "网络请求", "本地数据库",
    }

def _定位本地易码模块(模块名, 当前目录, 项目根目录):
    名称 = str(模块名 or "").strip().replace("\\", "/")
    if not 名称:
        return None

    候选文件名 = [名称]
    if not 名称.endswith(".ym"):
        候选文件名.append(f"{名称}.ym")

    候选路径 = []
    if os.path.isabs(名称):
        候选路径.extend(候选文件名)
    else:
        搜索基目录 = [当前目录, 项目根目录, os.path.join(项目根目录, "示例")]
        for 基目录 in 搜索基目录:
            if not 基目录:
                continue
            for 文件名 in 候选文件名:
                候选路径.append(os.path.join(基目录, 文件名))

    for 路径 in 候选路径:
        if os.path.isfile(路径):
            return os.path.abspath(路径)
    return None

def _推断可打包Python模块(模块名):
    """
    将易码里的模块名映射为可用于 PyInstaller hidden-import 的 Python 模块。
    仅返回当前环境可解析的模块，避免无效 hidden-import。
    """
    名称 = str(模块名 or "").strip()
    if not 名称:
        return set()
    if "/" in 名称 or "\\" in 名称:
        return set()
    if 名称.endswith(".ym"):
        return set()

    候选 = {名称}
    if "." in 名称:
        候选.add(名称.split(".")[0])

    结果 = set()
    for 项 in 候选:
        try:
            if importlib.util.find_spec(项) is not None:
                结果.add(项)
        except Exception:
            pass
    return 结果

def _收集项目源码文件(项目根目录):
    结果 = []
    if not 项目根目录 or not os.path.isdir(项目根目录):
        return 结果
    for 根目录, _, 文件名列表 in os.walk(项目根目录):
        for 文件名 in 文件名列表:
            if 文件名.lower().endswith(".ym"):
                结果.append(os.path.abspath(os.path.join(根目录, 文件名)))
    return sorted(set(结果))

def _读取打包清单(项目根目录, 进度打字机=print):
    """
    可选清单文件（放在项目根目录）：
      - 易码打包清单.json
      - yima_pack.json

    字段：
      {
        "hidden_imports": ["requests", "PIL.Image"],
        "datas": [
          "assets/logo.png",
          {"src": "assets", "dest": "assets"}
        ]
      }
    """
    候选名 = ["易码打包清单.json", "yima_pack.json"]
    清单路径 = None
    for 文件名 in 候选名:
        路径 = os.path.join(项目根目录, 文件名)
        if os.path.isfile(路径):
            清单路径 = 路径
            break

    if not 清单路径:
        return {"path": None, "hidden_imports": [], "datas": []}

    try:
        with open(清单路径, "r", encoding="utf-8") as f:
            数据 = json.load(f)
    except Exception as e:
        raise RuntimeError(f"打包清单读取失败：{清单路径}，原因：{e}")

    if not isinstance(数据, dict):
        raise RuntimeError(f"打包清单格式错误：{清单路径}，根节点必须是对象。")

    原始隐藏导入 = 数据.get("hidden_imports", []) or []
    if not isinstance(原始隐藏导入, list):
        raise RuntimeError(f"打包清单格式错误：{清单路径}，hidden_imports 必须是数组。")

    清单隐藏导入 = []
    for 项 in 原始隐藏导入:
        名称 = str(项 or "").strip()
        if 名称:
            清单隐藏导入.append(名称)

    原始数据项 = 数据.get("datas", []) or []
    if not isinstance(原始数据项, list):
        raise RuntimeError(f"打包清单格式错误：{清单路径}，datas 必须是数组。")

    清单数据项 = []
    for 项 in 原始数据项:
        if isinstance(项, str):
            源 = 项.strip()
            if not 源:
                continue
            目标 = "."
        elif isinstance(项, dict):
            源 = str(项.get("src", "")).strip()
            目标 = str(项.get("dest", ".")).strip() or "."
            if not 源:
                continue
        else:
            continue

        绝对源 = os.path.abspath(os.path.join(项目根目录, os.path.expanduser(源)))
        if not os.path.exists(绝对源):
            进度打字机(f"[提示] 清单资源不存在，已跳过：{绝对源}")
            continue
        清单数据项.append((绝对源, 目标.replace("\\", "/")))

    进度打字机(f"[OK] 发现打包清单：{清单路径}")
    return {"path": 清单路径, "hidden_imports": 清单隐藏导入, "datas": 清单数据项}

def _分析隐式Python依赖(源码文件列表, 项目根目录):
    Python模块集合 = set()
    内置模块 = _内置模块集合()

    for 源码文件 in 源码文件列表:
        try:
            with open(源码文件, "r", encoding="utf-8") as f:
                源码 = f.read()
        except Exception:
            continue

        当前目录 = os.path.dirname(os.path.abspath(源码文件))
        for 模块名 in _提取引入模块名(源码):
            if 模块名 in 内置模块:
                continue
            if _定位本地易码模块(模块名, 当前目录, 项目根目录):
                continue
            Python模块集合.update(_推断可打包Python模块(模块名))
    return Python模块集合

def 编译并打包(源码路径, 图标路径=None, 隐藏黑框=False, 进度打字机=print, 软件名称=None, 源码目录=None):
    if not os.path.exists(源码路径):
        raise FileNotFoundError(f"找不到文件：{源码路径}")

    绝对源码路径 = os.path.abspath(源码路径)
    文件名 = os.path.basename(源码路径)
    默认应用名, ext = os.path.splitext(文件名)
    if 默认应用名.startswith("_易码源码编译缓冲"):
        默认应用名 = "易码生成软件"
    应用名 = 清理软件名(软件名称, 默认值=默认应用名)

    如果你有图标 = 图标路径
    工具根目录 = os.path.dirname(os.path.abspath(__file__))
    当前目录 = os.path.abspath(os.getcwd())
    if not 如果你有图标:
        默认图标路径 = os.path.join(工具根目录, "logo.ico")
        if os.path.exists(默认图标路径):
            如果你有图标 = 默认图标路径

    图标绝对路径 = None
    if 如果你有图标:
        if not os.path.exists(如果你有图标):
            raise FileNotFoundError(f"找不到指定的图标文件：{如果你有图标}")
        图标绝对路径 = os.path.abspath(如果你有图标)

    打包临时目录 = os.path.join(当前目录, "打包缓存文件夹")
    if not os.path.exists(打包临时目录):
        os.makedirs(打包临时目录)

    启动器脚本 = os.path.join(打包临时目录, f"_启动器_{应用名}.py")
    代码 = f"""# 自动生成的易码打包启动脚本
import os
import sys

当前路径 = os.path.dirname(os.path.abspath(__file__))
if hasattr(sys, '_MEIPASS'):
    运行路径 = sys._MEIPASS
else:
    运行路径 = 当前路径

sys.path.insert(0, 运行路径)

from yima.解释器 import 解释器
from yima.语法分析 import 语法分析器
from yima.词法分析 import 词法分析器

def 运行():
    目标文件 = os.path.join(运行路径, "{文件名}")
    try:
        with open(目标文件, 'r', encoding='utf-8') as f:
            源码 = f.read()
    except Exception as e:
        print(f"加载内部源码出错: {{e}}")
        input("按回车键退出...")
        sys.exit(1)
        
    try:
        词法结果 = 词法分析器(源码).分析()
        语法树 = 语法分析器(词法结果).解析()
        执行器 = 解释器()
        执行器.设置当前目录(运行路径)
        执行器.执行代码(语法树)
    except Exception as e:
        import traceback
        import tkinter.messagebox
        tkinter.messagebox.showerror("运行报错", f"{{e}}\\n\\n{{traceback.format_exc()}}")
        
    {'pass' if 隐藏黑框 else 'input("\\n程序运行结束，按回车键退出...")'}

if __name__ == '__main__':
    运行()
"""
    with open(启动器脚本, 'w', encoding='utf-8') as f:
        f.write(代码)
        
    进度打字机(f"[OK] 生成启动引导器：{启动器脚本}")
    进度打字机("[..] 正在检查打包装备 (PyInstaller)...")
    try:
        import PyInstaller
    except ImportError:
        进度打字机("[提示] 没有找到 PyInstaller，正在为你自动安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        
    进度打字机("开始打包 EXE ...")
    yima核心库路径 = os.path.join(工具根目录, 'yima')
    if not os.path.isdir(yima核心库路径):
        raise FileNotFoundError(f"找不到易码核心库目录：{yima核心库路径}")
    分隔符 = ';' if os.name == 'nt' else ':'
    
    # 先确保当前执行源码本体被打进包里（运行入口）
    额外数据参数 = ["--add-data", f"{绝对源码路径}{分隔符}."]

    # 自动递归打包项目目录中的 .ym 文件，并保留相对目录结构
    源码所在目录 = os.path.abspath(源码目录) if 源码目录 else os.path.dirname(绝对源码路径)
    if not os.path.isdir(源码所在目录):
        源码所在目录 = os.path.dirname(绝对源码路径)
    项目源码文件 = _收集项目源码文件(源码所在目录)
    for 完整路径 in 项目源码文件:
        if os.path.abspath(完整路径) == 绝对源码路径:
            continue
        try:
            相对路径 = os.path.relpath(完整路径, 源码所在目录)
            目标目录 = os.path.dirname(相对路径).replace("\\", "/")
            if not 目标目录 or 目标目录 == ".":
                目标目录 = "."
        except Exception:
            目标目录 = "."
        额外数据参数.extend(["--add-data", f"{完整路径}{分隔符}{目标目录}"])

    # 读取可选清单：手动补充依赖/资源（无需修改解释器与编辑器）
    打包清单 = _读取打包清单(源码所在目录, 进度打字机=进度打字机)
    for 资源源路径, 资源目标目录 in 打包清单["datas"]:
        额外数据参数.extend(["--add-data", f"{资源源路径}{分隔符}{资源目标目录}"])

    # 扫描 .ym 源码里的 引入/用，自动补充 Python hidden-import，减少“写了代码但打包后缺依赖”
    分析样本 = [绝对源码路径] + [p for p in 项目源码文件 if os.path.abspath(p) != 绝对源码路径]
    自动隐藏导入 = {"turtle", "tkinter", "tkinter.messagebox"}
    自动隐藏导入.update(_分析隐式Python依赖(分析样本, 源码所在目录))
    自动隐藏导入.update(打包清单["hidden_imports"])
    自动隐藏导入 = sorted(自动隐藏导入)
            
    控制台参数 = "--windowed" if 隐藏黑框 else "--console"
    命令参数 = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--onefile",
    ]
    if 图标绝对路径:
        命令参数.append(f"--icon={图标绝对路径}")
    命令参数.append(控制台参数)
    for 模块名 in 自动隐藏导入:
        命令参数.append(f"--hidden-import={模块名}")
    if 图标绝对路径:
        命令参数.extend(["--add-data", f"{图标绝对路径}{分隔符}."])
    命令参数.extend(额外数据参数)
    命令参数.extend(["--add-data", f"{yima核心库路径}{分隔符}yima", 启动器脚本])

    进度打字机(f"自动识别 Python 依赖：{', '.join(自动隐藏导入)}")
    if 打包清单["datas"]:
        进度打字机(f"清单附加资源数量：{len(打包清单['datas'])}")
    if 打包清单["hidden_imports"]:
        进度打字机(f"清单附加 hidden-import：{', '.join(打包清单['hidden_imports'])}")
    进度打字机(f"执行命令: {命令转文本(命令参数)}")
    
    # Run the command and capture output to pass to 进度打字机
    import locale
    sys_encoding = locale.getpreferredencoding()
    process = subprocess.Popen(
        命令参数,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding=sys_encoding,
        errors='replace'
    )
    for line in iter(process.stdout.readline, ''):
        if line.strip():
            进度打字机(line.strip())
    process.wait()
    if process.returncode != 0:
        raise RuntimeError("PyInstaller 打包失败了，请查看上方日志。")
    
    进度打字机("清理中间文件...")
    输出目录 = os.path.join(当前目录, "易码_成品软件")
    if not os.path.exists(输出目录):
        os.makedirs(输出目录)

    当前Exe = os.path.join("dist", f"_启动器_{应用名}.exe")
    目标Exe = os.path.join(输出目录, f"{应用名}.exe")
    
    if os.path.exists(当前Exe):
        if os.path.exists(目标Exe):
            os.remove(目标Exe)
        shutil.move(当前Exe, 目标Exe)
        
        打包渣渣 = ["build", "dist", "打包缓存文件夹"]
        for 渣 in 打包渣渣:
            渣路径 = os.path.join(当前目录, 渣)
            if os.path.exists(渣路径):
                shutil.rmtree(渣路径, ignore_errors=True)
                
        spec遗留 = os.path.join(当前目录, f"_启动器_{应用名}.spec")
        if os.path.exists(spec遗留):
            os.remove(spec遗留)
            
        进度打字机(f"打包成功：{目标Exe}")
        return 目标Exe
    else:
        raise RuntimeError("打包过程中似乎出了点毛病，找不到产出的 EXE。")

def 主程序():
    if len(sys.argv) < 2:
        显示帮助()
        sys.exit(0)
    源码路径 = sys.argv[1]
    图标路径 = sys.argv[2] if len(sys.argv) > 2 else None
    软件名称 = sys.argv[3] if len(sys.argv) > 3 else None
    try:
        编译并打包(源码路径, 图标路径, 软件名称=软件名称)
    except Exception as e:
        print(f"[错误] 发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    主程序()
