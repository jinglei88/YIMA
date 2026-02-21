# -*- coding: utf-8 -*-
import sys
import os
import base64

# 把易码引擎目录推入环境，确保 Nuitka 能够分析到 yima 库依赖
sys.path.insert(0, r"d:\\易码")

from yima.词法分析 import 词法分析器
from yima.语法分析 import 语法分析器
from yima.解释器 import 解释器

YIMA_SOURCE_B64 = "IyDmmJPnoIHlm77lvaLnlYzpnaLlpKfmtYvor5UKCuaKiiDmiJHnmoTnqpflj6Mg6K6+5a6a5Li6IOW7uueql+WPoygi5piT56CB5omT5oub5ZG86L2v5Lu2IiwgNDAwLCAzMDApCgrliqDmloflrZco5oiR55qE56qX5Y+jLCAi5qyi6L+O5p2l5Yiw5piT56CB55qE5Zu+5b2i5LiW55WM77yBIikK5Yqg5paH5a2XKOaIkeeahOeql+WPoywgIuivt+i+k+WFpeS9oOeahOWQjeWtl++8miIpCgrmioog5ZCN5a2X6L6T5YWl5qGGIOiuvuWumuS4uiDliqDovpPlhaXmoYYo5oiR55qE56qX5Y+jKQoKIyDlrprkuYnkuIDkuKrlvZPmjInpkq7mjInkuIvljrvml7bopoHmiafooYznmoTmnKzkuosK5pWZ55S16ISRIOmXruWAmeS4gOS4iyAKICAgIOaKiiDloavlhpnnmoTlkI3lrZcg6K6+5a6a5Li6IOivu+i+k+WFpSjlkI3lrZfovpPlhaXmoYYpCiAgICDlpoLmnpwg5aGr5YaZ55qE5ZCN5a2XIOetieS6jiAiIiDnmoTor50KICAgICAgICDlvLnnqpcoIuitpuWRiiIsICLlkI3lrZfkuI3og73kuLrnqbrlk6bvvIEiKQogICAg5LiN54S255qE6K+dCiAgICAgICAg5oqKIOmXruWAmeivrSDorr7lrprkuLogIuS9oOWlveWRgO+8jCIg5ou85o6lIOWhq+WGmeeahOWQjeWtlyDmi7zmjqUgIu+8gSIKICAgICAgICDlvLnnqpcoIumXruWAmSIsIOmXruWAmeivrSkKICAgIOe7k+adnwrlrablrozkuoYKCuWKoOaWh+WtlyjmiJHnmoTnqpflj6MsICLngrnlh7vkuIvpnaLmjInpkq7or5Xor5XnnIvvvJoiKQrliqDmjInpkq4o5oiR55qE56qX5Y+jLCAi54K55oiR5omT5oub5ZG8IiwgIumXruWAmeS4gOS4iyIpCgojIOacgOWQju+8jOWxleekuuWHuui/meS4queql+WPo++8iOeoi+W6j+S8muWBnOWcqOi/memHjOetieeUqOaIt+aTjeS9nO+8iQrmiZPlvIDnlYzpnaIo5oiR55qE56qX5Y+jKQo="
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
