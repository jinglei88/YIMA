# 易码.py
# 🇨🇳 易码大白话编程主入口

import sys
import os

from yima.错误 import 易码错误
from yima.词法分析 import 词法分析器
from yima.语法分析 import 语法分析器
from yima.解释器 import 解释器

def 读文件并玩弄(文件路径):
    try:
        with open(文件路径, 'r', encoding='utf-8') as f:
            代码 = f.read()
            
        玩弄代码(代码, interactive=False)
        
    except FileNotFoundError:
        print(f"❌ 找不到你说的文件：{文件路径}")
    except Exception as e:
        print(f"❌ 程序奔溃了：{e}")

def 玩弄代码(代码, interactive=True, shared_env=None):
    try:
        # 1. 切分为词
        分析员 = 词法分析器(代码)
        tokens = 分析员.分析()
        
        # 2. 组成句式树
        管家 = 语法分析器(tokens)
        树 = 管家.解析()
        
        # 3. 按照树行动
        执行狗 = 解释器()
        if shared_env:
            执行狗.全局环境 = shared_env
        结果 = 执行狗.执行(树)
        
        if interactive and 结果 is not None:
            print(f"👉 {结果}")
        
    except 易码错误 as e:
        print(e)
    except Exception as e:
        print(f"❌ 易码引擎故障了 (Bug)：{e}")

def 启动聊天模式():
    print("========================================")
    print("🌟 欢迎来到 易码大白话 编程世界 🌟")
    print("输入代码即可运行，输入 '退出' 结束")
    print("========================================\n")
    
    环境上下文 = 解释器().全局环境
    
    while True:
        try:
            代码 = input("易码 > ")
            if not 代码.strip():
                continue
            if 代码.strip() in ['退出', 'quit', 'exit']:
                print("拜拜！")
                break
                
            玩弄代码(代码, interactive=True, shared_env=环境上下文)
            
        except KeyboardInterrupt:
            print("\n拜拜！")
            break
        except EOFError:
            break

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 如果带了参数，第一参数就是文件名
        执行文件 = sys.argv[1]
        读文件并玩弄(执行文件)
    else:
        # 不带参数进入互动模式
        启动聊天模式()
