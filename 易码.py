# 易码.py
# 易码命令行主入口
#
# Ownership Marker (Open Source Prep)
# Author: 景磊 (Jing Lei)
# Copyright (c) 2026 景磊
# Project: 易码 / Yima
# Marker-ID: YIMA-JINGLEI-CORE

__author__ = "景磊"
__copyright__ = "Copyright (c) 2026 景磊"
__marker_id__ = "YIMA-JINGLEI-CORE"

import sys
import os
import argparse
import traceback

from yima.错误 import 易码错误
from yima.词法分析 import 词法分析器
from yima.语法分析 import 语法分析器
from yima.解释器 import 解释器

EXIT_OK = 0
EXIT_CLI_USAGE = 2
EXIT_FILE_ERROR = 3
EXIT_LEX_ERROR = 10
EXIT_PARSE_ERROR = 11
EXIT_RUNTIME_ERROR = 12
EXIT_INTERNAL_ERROR = 20

def 初始化终端编码():
    """尽量避免 Windows 默认编码导致的输出异常。"""
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError):
        pass

def 是否严格局部作用域(覆盖值=None):
    if 覆盖值 is not None:
        return bool(覆盖值)
    值 = os.environ.get("YIMA_STRICT_SCOPE", "").strip().lower()
    return 值 in ("1", "true", "yes", "on")

def 读取版本号():
    版本文件 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "VERSION")
    try:
        with open(版本文件, "r", encoding="utf-8") as f:
            值 = f.read().strip()
        return 值 or "0.0.0"
    except Exception:
        return "0.0.0"

def 错误对应退出码(错误):
    if not isinstance(错误, 易码错误):
        return EXIT_INTERNAL_ERROR
    错误类型 = str(getattr(错误, "错误类型", "") or "")
    if 错误类型 == "词法错误":
        return EXIT_LEX_ERROR
    if 错误类型 == "语法错误":
        return EXIT_PARSE_ERROR
    if 错误类型 == "运行错误":
        return EXIT_RUNTIME_ERROR
    return EXIT_RUNTIME_ERROR

def 执行文件并返回状态(文件路径, strict_scope=None, show_traceback=False):
    try:
        with open(文件路径, 'r', encoding='utf-8') as f:
            代码 = f.read()
            
        return 执行源码并返回状态(
            代码,
            interactive=False,
            源码路径=文件路径,
            strict_scope=strict_scope,
            show_traceback=show_traceback,
        )
        
    except FileNotFoundError:
        print(f"找不到文件：{文件路径}")
        return False, EXIT_FILE_ERROR
    except Exception as e:
        print(f"执行失败：{e}")
        if show_traceback:
            traceback.print_exc()
        return False, EXIT_FILE_ERROR

def 执行文件(文件路径, strict_scope=None, show_traceback=False):
    成功, _退出码 = 执行文件并返回状态(
        文件路径,
        strict_scope=strict_scope,
        show_traceback=show_traceback,
    )
    return 成功

def 执行源码并返回状态(
    代码,
    interactive=True,
    shared_env=None,
    源码路径=None,
    strict_scope=None,
    show_traceback=False,
):
    try:
        分析器 = 词法分析器(代码)
        tokens = 分析器.分析()
        
        语法器 = 语法分析器(tokens)
        语法树 = 语法器.解析()
        
        执行器 = 解释器(严格局部作用域=是否严格局部作用域(strict_scope))
        if 源码路径:
            执行器.设置当前目录(os.path.dirname(os.path.abspath(源码路径)))
        if shared_env:
            执行器.全局环境 = shared_env
        结果 = 执行器.执行(语法树)
        
        if interactive and 结果 is not None:
            print(结果)
        return True, EXIT_OK
        
    except 易码错误 as e:
        if 源码路径 and not getattr(e, "文件路径", None):
            try:
                e.文件路径 = os.path.abspath(源码路径)
            except Exception:
                pass
        print(e)
        return False, 错误对应退出码(e)
    except Exception as e:
        print(f"解释器内部错误：{e}")
        if show_traceback:
            traceback.print_exc()
        return False, EXIT_INTERNAL_ERROR

def 执行源码(
    代码,
    interactive=True,
    shared_env=None,
    源码路径=None,
    strict_scope=None,
    show_traceback=False,
):
    成功, _退出码 = 执行源码并返回状态(
        代码,
        interactive=interactive,
        shared_env=shared_env,
        源码路径=源码路径,
        strict_scope=strict_scope,
        show_traceback=show_traceback,
    )
    return 成功

def 启动交互模式(strict_scope=None, show_traceback=False):
    print("========================================")
    print("欢迎使用 易码 交互模式")
    print("输入代码后回车执行，输入“退出”结束")
    print("========================================\n")
    
    环境上下文 = 解释器(严格局部作用域=是否严格局部作用域(strict_scope)).全局环境
    
    while True:
        try:
            代码 = input("易码 > ")
            if not 代码.strip():
                continue
            if 代码.strip() in ['退出', 'quit', 'exit']:
                print("已退出。")
                break
                
            执行源码(
                代码,
                interactive=True,
                shared_env=环境上下文,
                strict_scope=strict_scope,
                show_traceback=show_traceback,
            )
            
        except KeyboardInterrupt:
            print("\n已退出。")
            break
        except EOFError:
            break

def 解析命令行(argv=None):
    parser = argparse.ArgumentParser(
        description="易码命令行工具",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples / 快速示例：\n"
            "  python 易码.py 示例/欢迎.ym\n"
            "  python 易码.py -c \"显示 1 + 1\"\n"
            "  python 易码.py --strict-scope 示例/M11深度测试.ym\n"
            "  python 易码.py --traceback 示例/欢迎.ym"
        ),
    )
    parser.add_argument("文件", nargs="?", help="要运行的 .ym 文件路径")
    parser.add_argument("-c", "--code", dest="代码", help="直接执行一段易码源码")
    严格组 = parser.add_mutually_exclusive_group()
    严格组.add_argument("--strict-scope", action="store_true", help="强制开启严格局部作用域")
    严格组.add_argument("--no-strict-scope", action="store_true", help="强制关闭严格局部作用域")
    parser.add_argument("--traceback", action="store_true", help="内部异常时显示 Python 调用栈")
    parser.add_argument("-v", "--version", action="store_true", help="显示版本号并退出")
    args = parser.parse_args(argv)
    if args.代码 and args.文件:
        parser.error("不能同时指定 --code 和 文件路径。")
    return args

def 解析严格局部覆盖值(args):
    if getattr(args, "strict_scope", False):
        return True
    if getattr(args, "no_strict_scope", False):
        return False
    return None

def 主程序(argv=None):
    初始化终端编码()
    args = 解析命令行(argv)

    if args.version:
        print(f"易码 {读取版本号()}")
        return 0

    strict_scope = 解析严格局部覆盖值(args)
    if args.代码 is not None:
        成功, 退出码 = 执行源码并返回状态(
            args.代码,
            interactive=False,
            strict_scope=strict_scope,
            show_traceback=args.traceback,
        )
        return EXIT_OK if 成功 else 退出码

    if args.文件:
        成功, 退出码 = 执行文件并返回状态(
            args.文件,
            strict_scope=strict_scope,
            show_traceback=args.traceback,
        )
        return EXIT_OK if 成功 else 退出码

    启动交互模式(strict_scope=strict_scope, show_traceback=args.traceback)
    return 0

if __name__ == "__main__":
    sys.exit(主程序())
