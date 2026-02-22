# yima/信号.py
# 用于控制白话循环和函数的控制流信号

class 停下信号(Exception):
    pass

class 略过信号(Exception):
    pass

class 返回信号(Exception):
    def __init__(self, 值):
        self.值 = 值
