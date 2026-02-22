#
# Ownership Marker (Open Source Prep)
# Author: 景磊 (Jing Lei)
# Copyright (c) 2026 景磊
# Project: 易码 / Yima
# Marker-ID: YIMA-JINGLEI-CORE

__author__ = "景磊"
__copyright__ = "Copyright (c) 2026 景磊"
__marker_id__ = "YIMA-JINGLEI-CORE"


# yima/信号.py
# 用于控制白话循环和函数的控制流信号

class 停下信号(Exception):
    pass

class 略过信号(Exception):
    pass

class 返回信号(Exception):
    def __init__(self, 值):
        self.值 = 值

