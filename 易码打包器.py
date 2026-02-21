# d:\易码\易码打包器.py
import os
import sys
import subprocess
import tempfile
import shutil

# 获取易码引擎所在的绝对目录，方便打包时引入
易码核心路径 = os.path.dirname(os.path.abspath(__file__))

包装器模板 = """# -*- coding: utf-8 -*-
import sys
import os
import base64

# 把易码引擎目录推入环境，确保 Nuitka 能够分析到 yima 库依赖
sys.path.insert(0, r"{引擎路径}")

from yima.词法分析 import 词法分析器
from yima.语法分析 import 语法分析器
from yima.解释器 import 解释器

YIMA_SOURCE_B64 = "{源码B64}"
YIMA_SOURCE_CODE = base64.b64decode(YIMA_SOURCE_B64).decode('utf-8')

def 运行易码():
    try:
        分析员 = 词法分析器(YIMA_SOURCE_CODE)
        tokens = 分析员.分析()
        管家 = 语法分析器(tokens)
        树 = 管家.解析()
        执行狗 = 解释器()
        执行狗.执行代码(树)
    except Exception as e:
        import tkinter.messagebox
        import tkinter
        # 隐藏主窗口
        root = tkinter.Tk()
        root.withdraw()
        tkinter.messagebox.showerror("运行出错了", str(e))

if __name__ == '__main__':
    运行易码()
"""

def 编译并打包(ym文件路径, 隐藏黑框=False, 进度打字机=print):
    if not os.path.exists(ym文件路径):
        raise FileNotFoundError(f"找不到代码文件：{ym文件路径}")
        
    文件名 = os.path.basename(ym文件路径)
    程序名, ext = os.path.splitext(文件名)
    
    with open(ym文件路径, 'r', encoding='utf-8') as f:
        源码内容 = f.read()

    import base64
    源码B64 = base64.b64encode(源码内容.encode('utf-8')).decode('utf-8')

    # 1. 生成隐秘的包装器 python 脚本
    临时文件名 = f"_易码外壳_{程序名}.py"
    当前目录 = os.path.dirname(os.path.abspath(ym文件路径))
    临时文件绝对路径 = os.path.join(当前目录, 临时文件名)
    
    # 替换其中的占位符
    包装代码 = 包装器模板.replace("{引擎路径}", 易码核心路径.replace("\\", "\\\\"))
    包装代码 = 包装代码.replace("{源码B64}", 源码B64)
    
    with open(临时文件绝对路径, 'w', encoding='utf-8') as f:
        f.write(包装代码)
        
    进度打字机(f"🚀 [1/3] 已生成易码启动外壳: {临时文件名}")
    
    # 2. 调用 Nuitka 编译
    进度打字机(f"⚙️ [2/3] 正在下达底层编译指令，请耐心等待（初次使用可能需要几分钟下载C编译器）...")
    
    # 准备 Nuitka 参数
    nuitka_args = [
        sys.executable, "-m", "nuitka",
        "--standalone", 
        "--onefile", 
        "--enable-plugin=tk-inter", # 必须打包 Tkinter 图形界面依赖
        "--assume-yes-for-downloads", # 自动同意下载必要的C编译器
        "--zig", # 强制使用 Zig 编译器，以兼容 Python 3.13/3.14
        "--remove-output", # 编译后自动删除 build 文件夹
    ]
    
    if 隐藏黑框:
        nuitka_args.append("--windows-console-mode=disable")
        
    nuitka_args.append(临时文件绝对路径)
    
    # 运行编译
    # 设置环境变量以防中文路径 utf8 报错
    环境 = os.environ.copy()
    环境["PYTHONIOENCODING"] = "utf-8"
    
    编译过程 = subprocess.Popen(
        nuitka_args, 
        cwd=当前目录,
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    for 每一行 in iter(编译过程.stdout.readline, ''):
        行 = 每一行.strip()
        if 行:
            进度打字机(f"  > {行}")
            
    编译过程.stdout.close()
    退出码 = 编译过程.wait()
    
    # 3. 清理与整理
    try:
        os.remove(临时文件绝对路径)
    except: pass
    
    if 退出码 != 0:
        raise RuntimeError(f"编译失败了，退出码：{退出码}")
        
    # Nuitka 生成的 exe 会保存在当前目录下，名字是: _易码外壳_程序名.exe
    生成exe文件 = os.path.join(当前目录, f"_易码外壳_{程序名}.exe")
    最终exe文件 = os.path.join(当前目录, f"{程序名}.exe")
    
    if os.path.exists(生成exe文件):
        if os.path.exists(最终exe文件):
            try:
                os.remove(最终exe文件)
            except: pass
        os.rename(生成exe文件, 最终exe文件)
        进度打字机(f"✅ [3/3] 恭喜！脱壳编译成功！你现在可以直接双击运行 【{最终exe文件}】")
    else:
        raise RuntimeError(f"虽然编译过程没报错，但没找到生成的 EXE：{生成exe文件}")
    
    return 最终exe文件
