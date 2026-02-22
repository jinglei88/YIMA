# 自动生成的易码打包启动脚本
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
    目标文件 = os.path.join(运行路径, "_易码源码编译缓冲.ym")
    try:
        with open(目标文件, 'r', encoding='utf-8') as f:
            源码 = f.read()
    except Exception as e:
        print(f"加载内部源码出错: {e}")
        input("按回车键退出...")
        sys.exit(1)
        
    try:
        词法结果 = 词法分析器(源码).分析()
        语法树 = 语法分析器(词法结果).解析()
        解释器().执行代码(语法树)
    except Exception as e:
        import traceback
        import tkinter.messagebox
        tkinter.messagebox.showerror("运行报错", f"{e}\n\n{traceback.format_exc()}")
        
    input("\n程序运行结束，按回车键退出...")

if __name__ == '__main__':
    运行()
