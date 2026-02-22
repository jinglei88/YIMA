# 易码.py
# 易码命令行主入口

import sys
import os

from yima.错误 import 易码错误
from yima.词法分析 import 词法分析器
from yima.语法分析 import 语法分析器
from yima.解释器 import 解释器


def 初始化终端编码():
    """尽量避免 Windows 默认编码导致的输出异常。"""
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError):
        pass

def 是否严格局部作用域():
    值 = os.environ.get("YIMA_STRICT_SCOPE", "").strip().lower()
    return 值 in ("1", "true", "yes", "on")

def 执行文件(文件路径):
    try:
        with open(文件路径, 'r', encoding='utf-8') as f:
            代码 = f.read()
            
        return 执行源码(代码, interactive=False, 源码路径=文件路径)
        
    except FileNotFoundError:
        print(f"找不到文件：{文件路径}")
        return False
    except Exception as e:
        print(f"执行失败：{e}")
        return False

def 执行源码(代码, interactive=True, shared_env=None, 源码路径=None):
    try:
        分析器 = 词法分析器(代码)
        tokens = 分析器.分析()
        
        语法器 = 语法分析器(tokens)
        语法树 = 语法器.解析()
        
        执行器 = 解释器(严格局部作用域=是否严格局部作用域())
        if 源码路径:
            执行器.设置当前目录(os.path.dirname(os.path.abspath(源码路径)))
        if shared_env:
            执行器.全局环境 = shared_env
        结果 = 执行器.执行(语法树)
        
        if interactive and 结果 is not None:
            print(结果)
        return True
        
    except 易码错误 as e:
        print(e)
        return False
    except Exception as e:
        print(f"解释器内部错误：{e}")
        return False

def 启动交互模式():
    print("========================================")
    print("欢迎使用 易码 交互模式")
    print("输入代码后回车执行，输入“退出”结束")
    print("========================================\n")
    
    环境上下文 = 解释器(严格局部作用域=是否严格局部作用域()).全局环境
    
    while True:
        try:
            代码 = input("易码 > ")
            if not 代码.strip():
                continue
            if 代码.strip() in ['退出', 'quit', 'exit']:
                print("已退出。")
                break
                
            执行源码(代码, interactive=True, shared_env=环境上下文)
            
        except KeyboardInterrupt:
            print("\n已退出。")
            break
        except EOFError:
            break

# 兼容旧接口（后续版本将移除）
玩弄代码 = 执行源码
读文件并玩弄 = 执行文件
启动聊天模式 = 启动交互模式

if __name__ == "__main__":
    初始化终端编码()
    if len(sys.argv) > 1:
        目标文件 = sys.argv[1]
        成功 = 执行文件(目标文件)
        sys.exit(0 if 成功 else 1)
    else:
        启动交互模式()
