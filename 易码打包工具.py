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

def 显示帮助():
    print("===================================")
    print("         易码 官方打包器            ")
    print("===================================")
    print("用法: python 易码打包工具.py <你的源码.ym> [可选的图标.ico] [可选的软件名]")
    print("例如: python 易码打包工具.py 示例/勇者大冒险.ym 游戏图标.ico 我的勇者传说")
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
    项目根目录 = os.path.dirname(os.path.abspath(__file__))
    当前目录 = os.path.abspath(os.getcwd())
    if not 如果你有图标:
        默认图标路径 = os.path.join(项目根目录, "logo.ico")
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
        解释器().执行代码(语法树)
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
        
    进度打字机(f"✅ 生成启动引导器：{启动器脚本}")
    进度打字机("⏳ 正在检查打包装备 (PyInstaller)...")
    try:
        import PyInstaller
    except ImportError:
        进度打字机("💡 没有找到 PyInstaller，正在为你自动安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        
    进度打字机("开始打包 EXE ...")
    yima核心库路径 = os.path.join(项目根目录, 'yima')
    if not os.path.isdir(yima核心库路径):
        raise FileNotFoundError(f"找不到易码核心库目录：{yima核心库路径}")
    分隔符 = ';' if os.name == 'nt' else ':'
    
    # 先确保当前执行源码本体被打进包里
    额外数据参数 = ["--add-data", f"{绝对源码路径}{分隔符}."]

    # 自动把同目录 .ym 文件一起打包，支持多文件项目
    源码所在目录 = os.path.abspath(源码目录) if 源码目录 else os.path.dirname(绝对源码路径)
    if not os.path.isdir(源码所在目录):
        源码所在目录 = os.path.dirname(绝对源码路径)
    for file in os.listdir(源码所在目录):
        if file.endswith(".ym"):
            完整路径 = os.path.join(源码所在目录, file)
            if os.path.abspath(完整路径) == 绝对源码路径:
                continue
            额外数据参数.extend(["--add-data", f"{完整路径}{分隔符}."])
            
    控制台参数 = "--windowed" if 隐藏黑框 else "--console"
    命令参数 = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--onefile",
    ]
    if 图标绝对路径:
        命令参数.append(f"--icon={图标绝对路径}")
    命令参数.extend([
        控制台参数,
        "--hidden-import=turtle",
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.messagebox",
    ])
    if 图标绝对路径:
        命令参数.extend(["--add-data", f"{图标绝对路径}{分隔符}."])
    命令参数.extend(额外数据参数)
    命令参数.extend(["--add-data", f"{yima核心库路径}{分隔符}yima", 启动器脚本])

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
        print(f"❌ 发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    主程序()
