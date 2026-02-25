"""Visual UI designer flow: free drag layout + code export."""

from __future__ import annotations

#
# Ownership Marker (Open Source Prep)
# Author: 景磊 (Jing Lei)
# Copyright (c) 2026 景磊
# Project: 易码 / Yima
# Marker-ID: YIMA-JINGLEI-CORE

__author__ = "景磊"
__copyright__ = "Copyright (c) 2026 景磊"
__marker_id__ = "YIMA-JINGLEI-CORE"

import json
import re
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont


CANVAS_REGION_W = 2200
CANVAS_REGION_H = 1400
CANVAS_GRID = 20
CANVAS_RESIZE_HANDLE = 8


COMPONENT_CATALOG = [
    ("窗口", {"x": 48, "y": 40, "w": 960, "h": 640, "text": "我的窗口", "scroll_mode": "自动", "singleton": True}),
    ("文字", {"w": 180, "h": 34, "text": "文字内容"}),
    ("输入框", {"w": 240, "h": 36, "text": "输入内容"}),
    ("多行文本框", {"w": 320, "h": 120, "text": "请输入多行内容"}),
    ("按钮", {"w": 150, "h": 40, "text": "按钮", "event": "处理点击", "button_style": "主按钮"}),
    ("复选框", {"w": 160, "h": 34, "text": "勾选项", "event": "处理勾选"}),
    ("单选按钮", {"w": 160, "h": 34, "text": "单选项", "event": "处理选择"}),
    ("组合框", {"w": 240, "h": 36, "text": "选项1,选项2"}),
    ("数值框", {"w": 180, "h": 36, "text": "0"}),
    ("数值滑块", {"w": 260, "h": 36, "text": "0~100"}),
    ("进度条", {"w": 260, "h": 28, "text": "进度 50%"}),
    ("日期选择器", {"w": 220, "h": 36, "text": "2026-01-01"}),
    ("图片框", {"w": 240, "h": 160, "text": "图片占位"}),
    ("列表框", {"w": 260, "h": 200, "text": "列表数据", "columns": "项目", "rows": 8}),
    ("树形视图", {"w": 320, "h": 220, "text": "树形数据", "columns": "节点,值", "rows": 8}),
    ("表格", {"w": 420, "h": 220, "text": "数据表", "columns": "列1,列2,列3", "rows": 8}),
    ("卡片", {"w": 420, "h": 260, "text": "卡片标题", "card_border": "显示"}),
    ("分组框", {"w": 360, "h": 240, "text": "分组容器"}),
    ("选项卡", {"w": 420, "h": 280, "text": "选项卡容器"}),
    ("分割容器", {"w": 420, "h": 260, "text": "分割布局"}),
    ("表格布局面板", {"w": 420, "h": 260, "text": "网格布局"}),
    ("流式布局面板", {"w": 420, "h": 260, "text": "流式布局"}),
    ("菜单栏", {"w": 460, "h": 34, "text": "文件 编辑 视图"}),
    ("工具栏", {"w": 460, "h": 38, "text": "新建 保存 导出"}),
    ("状态栏", {"w": 460, "h": 30, "text": "就绪"}),
    ("登录模板", {"w": 420, "h": 240, "text": "账号登录", "action_text": "登录", "event": "处理登录"}),
    ("列表模板", {"w": 560, "h": 320, "text": "数据列表", "action_text": "查询", "event": "执行查询", "columns": "名称,说明", "rows": 10}),
]
COMPONENT_KIND_SET = {item[0] for item in COMPONENT_CATALOG}
WINDOW_COMPONENT_KIND = "窗口"
COMPONENT_SINGLETON_KINDS = {
    kind for kind, config in COMPONENT_CATALOG if bool(config.get("singleton"))
}
TEXT_COMPONENT_KINDS = {"文字", "菜单栏", "工具栏", "状态栏"}
INPUT_COMPONENT_KINDS = {"输入框", "多行文本框", "组合框", "数值框", "数值滑块", "日期选择器"}
BUTTON_COMPONENT_KINDS = {"按钮", "复选框", "单选按钮"}
TABLE_COMPONENT_KINDS = {"表格", "列表框", "树形视图"}
CARD_COMPONENT_KINDS = {"卡片", "图片框", "分组框", "选项卡", "分割容器", "表格布局面板", "流式布局面板", "进度条"}
COMPONENT_PALETTE_GROUPS = [
    ("容器", [WINDOW_COMPONENT_KIND, "卡片", "分组框", "选项卡", "分割容器", "表格布局面板", "流式布局面板"]),
    ("常用控件", ["文字", "输入框", "多行文本框", "按钮", "复选框", "单选按钮", "组合框", "数值框", "数值滑块", "日期选择器"]),
    ("数据控件", ["表格", "列表框", "树形视图", "进度条", "图片框"]),
    ("菜单与状态", ["菜单栏", "工具栏", "状态栏"]),
    ("模板", ["登录模板", "列表模板"]),
]
DATA_BACKEND_CHOICES = [
    ("sqlite", "SQLite"),
    ("json", "JSON文件"),
]
DATA_BACKEND_KEY_TO_LABEL = {key: label for key, label in DATA_BACKEND_CHOICES}
DATA_BACKEND_LABEL_TO_KEY = {label: key for key, label in DATA_BACKEND_CHOICES}
WINDOW_SCROLL_MODE_CHOICES = ["自动", "无", "总是"]
BUTTON_STYLE_CHOICES = ["主按钮", "次按钮", "危险按钮", "朴素按钮"]
CARD_BORDER_CHOICES = ["显示", "隐藏"]

PROPERTY_EDITABLE_KEYS_BY_KIND = {
    "default": {
        "text", "event", "action_text", "columns", "column_count", "rows",
        "scroll_mode", "button_style", "card_border", "x", "y", "w", "h",
    },
    WINDOW_COMPONENT_KIND: {"text", "scroll_mode", "x", "y", "w", "h"},
    "文字": {"text", "x", "y", "w", "h"},
    "菜单栏": {"text", "x", "y", "w", "h"},
    "工具栏": {"text", "x", "y", "w", "h"},
    "状态栏": {"text", "x", "y", "w", "h"},
    "输入框": {"text", "x", "y", "w", "h"},
    "多行文本框": {"text", "x", "y", "w", "h"},
    "组合框": {"text", "x", "y", "w", "h"},
    "数值框": {"text", "x", "y", "w", "h"},
    "数值滑块": {"text", "x", "y", "w", "h"},
    "日期选择器": {"text", "x", "y", "w", "h"},
    "按钮": {"text", "event", "button_style", "x", "y", "w", "h"},
    "复选框": {"text", "event", "x", "y", "w", "h"},
    "单选按钮": {"text", "event", "x", "y", "w", "h"},
    "表格": {"text", "columns", "column_count", "rows", "x", "y", "w", "h"},
    "列表框": {"text", "columns", "column_count", "rows", "x", "y", "w", "h"},
    "树形视图": {"text", "columns", "column_count", "rows", "x", "y", "w", "h"},
    "卡片": {"text", "card_border", "x", "y", "w", "h"},
    "图片框": {"text", "card_border", "x", "y", "w", "h"},
    "分组框": {"text", "card_border", "x", "y", "w", "h"},
    "选项卡": {"text", "card_border", "x", "y", "w", "h"},
    "分割容器": {"text", "card_border", "x", "y", "w", "h"},
    "表格布局面板": {"text", "card_border", "x", "y", "w", "h"},
    "流式布局面板": {"text", "card_border", "x", "y", "w", "h"},
    "进度条": {"text", "x", "y", "w", "h"},
    "登录模板": {"text", "action_text", "event", "x", "y", "w", "h"},
    "列表模板": {"text", "action_text", "event", "columns", "rows", "x", "y", "w", "h"},
}
PROPERTY_HINT_BY_KIND = {
    "default": "按顺序调整：文本、位置(X/Y)、尺寸(宽/高)。函数名只给有点击行为的组件填写。",
    WINDOW_COMPONENT_KIND: "窗口可配置：标题、滚动条(自动/无/总是)、宽高和位置。",
    "文字": "文字组件只需要文本和位置尺寸，通常用于标题或说明。",
    "菜单栏": "菜单栏可先写菜单项文字，后续再补菜单事件逻辑。",
    "工具栏": "工具栏适合放常用动作说明，先完成布局和文字。",
    "状态栏": "状态栏通常位于底部，建议宽度拉满。",
    "输入框": "输入框建议先改文本(占位提示)，再调整位置尺寸。",
    "多行文本框": "多行文本框建议设置较高高度，便于输入备注。",
    "组合框": "组合框文本可先写候选项提示，后续在逻辑中填真实选项。",
    "数值框": "数值框建议默认值写数字文本，业务层再做校验。",
    "数值滑块": "滑块可先放占位，导出后可替换为具体控件逻辑。",
    "日期选择器": "日期选择器先以输入框形式导出，业务层可补日期校验。",
    "按钮": "按钮可设置样式（主/次/危险/朴素），并填写函数名。",
    "复选框": "复选框会按可点击控件导出，建议填写函数名处理状态变化。",
    "单选按钮": "单选按钮会按可点击控件导出，建议填写函数名处理选择。",
    "表格": "表格可直接填列定义，或先填列数自动生成列1..列N。",
    "列表框": "列表框可填列数自动生成列名，也可手动改列定义。",
    "树形视图": "树形视图可填列数自动生成列名，后续可再手动微调。",
    "卡片": "卡片可配置边框显示与否，适合信息分组展示。",
    "图片框": "图片框当前按卡片导出，可控制边框显示并先做图片占位。",
    "分组框": "分组框适合作为一组控件的视觉容器。",
    "选项卡": "选项卡当前按容器占位导出，先确定区域尺寸。",
    "分割容器": "分割容器当前按容器占位导出，先确定布局比例。",
    "表格布局面板": "表格布局面板用于网格布局占位，后续可升级自动布局逻辑。",
    "流式布局面板": "流式布局面板用于流式排版占位，后续可升级自动换行逻辑。",
    "进度条": "进度条当前按容器占位导出，可在业务层更新文本进度。",
    "登录模板": "登录模板建议填写按钮文案和函数名，导出后自动串联业务层与数据层。",
    "列表模板": "列表模板建议同时配置列定义、按钮文案和函数名。",
}
QUICK_START_SCENES = [
    {"key": "blank", "title": "空白窗口", "desc": "只保留窗口，适合从零手动搭建", "category": "基础", "tags": ["起步", "空白"]},
    {"key": "form", "title": "录入表单", "desc": "标题 + 两个输入框 + 提交按钮", "category": "基础", "tags": ["表单", "录入"]},
    {"key": "query", "title": "查询表格", "desc": "关键词输入 + 查询按钮 + 数据表格", "category": "基础", "tags": ["查询", "表格"]},
    {"key": "login", "title": "登录页面", "desc": "账号/密码 + 登录按钮 + 记住我", "category": "用户", "tags": ["登录", "认证"]},
    {"key": "crud", "title": "列表增删改查", "desc": "查询区 + 表格 + 新增/编辑/删除按钮", "category": "业务", "tags": ["CRUD", "管理"]},
    {"key": "dashboard", "title": "运营看板", "desc": "状态卡片 + 快捷操作 + 数据列表", "category": "运营", "tags": ["看板", "统计"]},
    {"key": "settings", "title": "系统设置", "desc": "分组配置 + 保存按钮", "category": "系统", "tags": ["设置", "配置"]},
    {"key": "report", "title": "报表筛选", "desc": "时间筛选 + 统计区 + 报表表格", "category": "运营", "tags": ["报表", "筛选"]},
    {"key": "approval", "title": "审批工作台", "desc": "待办列表 + 操作区 + 备注", "category": "流程", "tags": ["审批", "流程"]},
    {"key": "wizard", "title": "向导页面", "desc": "步骤提示 + 表单 + 上一步/下一步", "category": "流程", "tags": ["向导", "步骤"]},
    {"key": "profile", "title": "个人中心", "desc": "头像区 + 信息卡 + 操作按钮", "category": "用户", "tags": ["个人", "资料"]},
]

QUICK_START_CATEGORY_ORDER = ["全部", "基础", "业务", "运营", "系统", "流程", "用户"]

TEMPLATE_RECOMMENDED_KINDS = {
    "default": ["文字", "输入框", "按钮", "表格", "卡片", "分组框", "复选框"],
    "blank": ["文字", "输入框", "按钮", "表格", "卡片"],
    "form": ["文字", "输入框", "多行文本框", "按钮", "分组框"],
    "query": ["输入框", "按钮", "表格", "组合框", "日期选择器"],
    "login": ["文字", "输入框", "按钮", "复选框"],
    "crud": ["输入框", "按钮", "表格", "组合框", "卡片"],
    "dashboard": ["卡片", "表格", "按钮", "进度条", "文字"],
    "settings": ["分组框", "文字", "输入框", "按钮", "复选框"],
    "report": ["日期选择器", "组合框", "按钮", "表格", "卡片"],
    "approval": ["表格", "多行文本框", "按钮", "文字"],
    "wizard": ["进度条", "卡片", "按钮", "输入框"],
    "profile": ["图片框", "卡片", "按钮", "文字", "输入框"],
}

QUICK_START_SCENE_SPECS = {
    "blank": {
        "key": "blank",
        "title": "空白窗口",
        "window": {"text": "我的窗口", "w": 960, "h": 640},
        "components": [],
    },
    "form": {
        "key": "form",
        "title": "录入表单",
        "window": {"text": "信息录入", "w": 900, "h": 620},
        "components": [
            {"kind": "文字", "name": "姓名标签", "text": "姓名", "x": 140, "y": 140, "w": 100, "h": 34},
            {"kind": "输入框", "name": "姓名输入", "text": "请输入姓名", "x": 240, "y": 138, "w": 300, "h": 36},
            {"kind": "文字", "name": "手机标签", "text": "手机号", "x": 140, "y": 196, "w": 100, "h": 34},
            {"kind": "输入框", "name": "手机输入", "text": "请输入手机号", "x": 240, "y": 194, "w": 300, "h": 36},
            {"kind": "按钮", "name": "提交按钮", "text": "提交", "event": "提交表单", "x": 240, "y": 260, "w": 140, "h": 42},
        ],
    },
    "query": {
        "key": "query",
        "title": "查询表格",
        "window": {"text": "数据查询", "w": 980, "h": 660},
        "components": [
            {"kind": "文字", "name": "关键词标签", "text": "关键词", "x": 120, "y": 120, "w": 100, "h": 34},
            {"kind": "输入框", "name": "关键词输入", "text": "请输入关键词", "x": 220, "y": 118, "w": 300, "h": 36},
            {"kind": "按钮", "name": "查询按钮", "text": "查询", "event": "执行查询", "x": 540, "y": 116, "w": 120, "h": 40},
            {"kind": "表格", "name": "结果表格", "text": "查询结果", "columns": "编号,名称,说明", "rows": 10, "x": 120, "y": 180, "w": 780, "h": 360},
        ],
    },
    "login": {
        "key": "login",
        "title": "登录页面",
        "window": {"text": "用户登录", "w": 860, "h": 560},
        "components": [
            {"kind": "文字", "name": "标题", "text": "欢迎登录", "x": 320, "y": 110, "w": 200, "h": 36},
            {"kind": "输入框", "name": "账号输入", "text": "请输入账号", "x": 270, "y": 180, "w": 320, "h": 36},
            {"kind": "输入框", "name": "密码输入", "text": "请输入密码", "x": 270, "y": 230, "w": 320, "h": 36},
            {"kind": "复选框", "name": "记住我", "text": "记住我", "event": "切换记住我", "x": 270, "y": 280, "w": 120, "h": 34},
            {"kind": "按钮", "name": "登录按钮", "text": "登录", "event": "处理登录", "x": 270, "y": 324, "w": 320, "h": 42},
        ],
    },
    "crud": {
        "key": "crud",
        "title": "列表增删改查",
        "window": {"text": "数据管理", "w": 1080, "h": 700},
        "components": [
            {"kind": "输入框", "name": "关键词输入", "text": "输入关键词", "x": 90, "y": 90, "w": 280, "h": 36},
            {"kind": "按钮", "name": "查询按钮", "text": "查询", "event": "执行查询", "x": 390, "y": 88, "w": 100, "h": 38},
            {"kind": "按钮", "name": "新增按钮", "text": "新增", "event": "打开新增", "x": 510, "y": 88, "w": 100, "h": 38},
            {"kind": "按钮", "name": "编辑按钮", "text": "编辑", "event": "打开编辑", "x": 620, "y": 88, "w": 100, "h": 38},
            {"kind": "按钮", "name": "删除按钮", "text": "删除", "event": "执行删除", "x": 730, "y": 88, "w": 100, "h": 38},
            {"kind": "表格", "name": "主表格", "text": "列表", "columns": "编号,名称,状态,更新时间", "rows": 12, "x": 90, "y": 150, "w": 900, "h": 440},
        ],
    },
    "dashboard": {
        "key": "dashboard",
        "title": "运营看板",
        "window": {"text": "运营看板", "w": 1140, "h": 720},
        "components": [
            {"kind": "卡片", "name": "今日订单", "text": "今日订单", "x": 80, "y": 90, "w": 240, "h": 130},
            {"kind": "卡片", "name": "今日营收", "text": "今日营收", "x": 340, "y": 90, "w": 240, "h": 130},
            {"kind": "卡片", "name": "新增用户", "text": "新增用户", "x": 600, "y": 90, "w": 240, "h": 130},
            {"kind": "按钮", "name": "刷新按钮", "text": "刷新数据", "event": "刷新看板", "x": 860, "y": 90, "w": 180, "h": 42},
            {"kind": "表格", "name": "动态列表", "text": "最近动态", "columns": "时间,事件,负责人", "rows": 10, "x": 80, "y": 250, "w": 960, "h": 370},
        ],
    },
    "settings": {
        "key": "settings",
        "title": "系统设置",
        "window": {"text": "系统设置", "w": 980, "h": 680},
        "components": [
            {"kind": "分组框", "name": "基础设置区", "text": "基础设置", "x": 80, "y": 90, "w": 820, "h": 220},
            {"kind": "文字", "name": "系统名称标签", "text": "系统名称", "x": 110, "y": 130, "w": 120, "h": 34},
            {"kind": "输入框", "name": "系统名称输入", "text": "请输入系统名称", "x": 230, "y": 128, "w": 320, "h": 36},
            {"kind": "文字", "name": "管理员邮箱标签", "text": "管理员邮箱", "x": 110, "y": 180, "w": 120, "h": 34},
            {"kind": "输入框", "name": "管理员邮箱输入", "text": "请输入邮箱", "x": 230, "y": 178, "w": 320, "h": 36},
            {"kind": "按钮", "name": "保存设置按钮", "text": "保存设置", "event": "保存设置", "x": 730, "y": 560, "w": 170, "h": 42},
        ],
    },
    "report": {
        "key": "report",
        "title": "报表筛选",
        "window": {"text": "经营报表", "w": 1080, "h": 700},
        "components": [
            {"kind": "日期选择器", "name": "开始日期", "text": "开始日期", "x": 90, "y": 96, "w": 200, "h": 36},
            {"kind": "日期选择器", "name": "结束日期", "text": "结束日期", "x": 310, "y": 96, "w": 200, "h": 36},
            {"kind": "组合框", "name": "维度选择", "text": "日,周,月", "x": 530, "y": 96, "w": 180, "h": 36},
            {"kind": "按钮", "name": "生成报表按钮", "text": "生成报表", "event": "生成报表", "x": 730, "y": 94, "w": 140, "h": 40},
            {"kind": "卡片", "name": "汇总卡", "text": "汇总数据", "x": 90, "y": 154, "w": 780, "h": 120},
            {"kind": "表格", "name": "报表明细", "text": "报表明细", "columns": "日期,指标,数值,环比", "rows": 11, "x": 90, "y": 290, "w": 900, "h": 340},
        ],
    },
    "approval": {
        "key": "approval",
        "title": "审批工作台",
        "window": {"text": "审批中心", "w": 1100, "h": 720},
        "components": [
            {"kind": "表格", "name": "待审列表", "text": "待审任务", "columns": "单号,申请人,类型,状态", "rows": 10, "x": 80, "y": 100, "w": 620, "h": 460},
            {"kind": "多行文本框", "name": "审批备注", "text": "请输入审批备注", "x": 730, "y": 100, "w": 280, "h": 180},
            {"kind": "按钮", "name": "通过按钮", "text": "通过", "event": "审批通过", "x": 730, "y": 300, "w": 130, "h": 40},
            {"kind": "按钮", "name": "驳回按钮", "text": "驳回", "event": "审批驳回", "x": 880, "y": 300, "w": 130, "h": 40},
        ],
    },
    "wizard": {
        "key": "wizard",
        "title": "向导页面",
        "window": {"text": "创建向导", "w": 980, "h": 680},
        "components": [
            {"kind": "进度条", "name": "步骤进度", "text": "步骤 1/3", "x": 110, "y": 90, "w": 760, "h": 30},
            {"kind": "卡片", "name": "步骤内容区", "text": "步骤内容", "x": 110, "y": 140, "w": 760, "h": 400},
            {"kind": "按钮", "name": "上一步按钮", "text": "上一步", "event": "向导上一步", "x": 590, "y": 570, "w": 120, "h": 40},
            {"kind": "按钮", "name": "下一步按钮", "text": "下一步", "event": "向导下一步", "x": 730, "y": 570, "w": 140, "h": 40},
        ],
    },
    "profile": {
        "key": "profile",
        "title": "个人中心",
        "window": {"text": "个人中心", "w": 960, "h": 660},
        "components": [
            {"kind": "图片框", "name": "头像区", "text": "头像", "x": 100, "y": 110, "w": 180, "h": 180},
            {"kind": "卡片", "name": "信息卡", "text": "个人信息", "x": 310, "y": 110, "w": 520, "h": 260},
            {"kind": "按钮", "name": "编辑资料按钮", "text": "编辑资料", "event": "编辑资料", "x": 310, "y": 390, "w": 160, "h": 40},
            {"kind": "按钮", "name": "退出登录按钮", "text": "退出登录", "event": "退出登录", "x": 490, "y": 390, "w": 160, "h": 40},
        ],
    },
}

NOVICE_STEP_LABELS = [
    "1 选模板",
    "2 放组件",
    "3 绑动作",
    "4 运行导出",
]

NOVICE_BASIC_PROP_KEYS = {
    "text",
    "button_style",
    "card_border",
    "action_text",
    "event",
    "columns",
    "column_count",
    "rows",
    "x",
    "y",
    "w",
    "h",
}

NOVICE_VISIBLE_PROP_KEYS = {
    "text", "scroll_mode", "event", "button_style", "card_border",
    "columns", "column_count", "rows", "x", "y", "w", "h",
}


def _catalog_map():
    return {kind: dict(config) for kind, config in COMPONENT_CATALOG}


def _normalize_data_backend(value):
    text = str(value or "").strip().lower()
    if text in {"json", "json文件", "json file", "json-file"}:
        return "json"
    return "sqlite"


def _backend_label_of(key):
    backend_key = _normalize_data_backend(key)
    return DATA_BACKEND_KEY_TO_LABEL.get(backend_key, DATA_BACKEND_KEY_TO_LABEL["sqlite"])


def _backend_key_from_label(text):
    raw = str(text or "").strip()
    if raw in DATA_BACKEND_LABEL_TO_KEY:
        return _normalize_data_backend(DATA_BACKEND_LABEL_TO_KEY[raw])
    return _normalize_data_backend(raw)


def _normalize_layer_export_prefix(text, fallback="界面设计"):
    value = str(text or "").strip()
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value)
    value = re.sub(r"\s+", "_", value)
    value = value.strip("._")
    if not value:
        return str(fallback or "界面设计")
    return value[:60]


def _set_data_backend(owner, backend, sync_vars=True):
    _ensure_state(owner)
    key = _normalize_data_backend(backend)
    owner._ui_designer_data_backend = key
    if not sync_vars:
        return key
    label = _backend_label_of(key)
    keep_vars = []
    for var in list(getattr(owner, "_ui_designer_backend_vars", []) or []):
        if var is None:
            continue
        try:
            if str(var.get()) != label:
                var.set(label)
            keep_vars.append(var)
        except Exception:
            continue
    owner._ui_designer_backend_vars = keep_vars
    return key


def _create_data_backend_selector(owner, parent):
    _ensure_state(owner)
    wrap = tk.Frame(parent, bg=owner.theme_toolbar_bg)
    wrap.pack(side=tk.LEFT, padx=(14, 0))
    tk.Label(
        wrap,
        text="数据层：",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_toolbar_muted,
    ).pack(side=tk.LEFT)
    backend_var = tk.StringVar(value=_backend_label_of(getattr(owner, "_ui_designer_data_backend", "sqlite")))
    combo = ttk.Combobox(
        wrap,
        textvariable=backend_var,
        values=[label for _key, label in DATA_BACKEND_CHOICES],
        state="readonly",
        width=9,
    )
    combo.pack(side=tk.LEFT, padx=(4, 0))

    def _on_backend_change(_event=None):
        selected_key = _backend_key_from_label(backend_var.get())
        _set_data_backend(owner, selected_key)
        saver = getattr(owner, "_save_project_state", None)
        if callable(saver):
            try:
                saver()
            except Exception:
                pass
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set(f"界面设计器：数据层后端已切换为 {_backend_label_of(selected_key)}")

    combo.bind("<<ComboboxSelected>>", _on_backend_change, add="+")
    owner._ui_designer_backend_vars.append(backend_var)
    return wrap


def _prompt_layer_export_backend(owner):
    _ensure_state(owner)
    default_backend = _normalize_data_backend(getattr(owner, "_ui_designer_data_backend", "sqlite"))
    default_prefix = _normalize_layer_export_prefix(getattr(owner, "_ui_designer_layer_export_prefix", "界面设计"))
    result = {
        "ok": False,
        "backend": default_backend,
        "remember": True,
        "prefix": default_prefix,
        "remember_prefix": True,
    }

    dialog = tk.Toplevel(owner.root)
    dialog.title("导出三层代码")
    dialog.transient(owner.root)
    dialog.configure(bg=owner.theme_bg)
    try:
        dialog.resizable(False, False)
    except tk.TclError:
        pass
    try:
        dialog.grab_set()
    except tk.TclError:
        pass

    try:
        owner.root.update_idletasks()
        # 先给一个安全初始尺寸，避免构建内容时被压缩裁剪。
        w = 460
        h = 320
        x = int(owner.root.winfo_x() + max(0, (owner.root.winfo_width() - w) / 2))
        y = int(owner.root.winfo_y() + max(0, (owner.root.winfo_height() - h) / 2))
        dialog.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        pass

    body = tk.Frame(dialog, bg=owner.theme_bg, padx=14, pady=12)
    body.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        body,
        text="选择本次三层导出的数据层后端",
        font=("Microsoft YaHei", 9, "bold"),
        bg=owner.theme_bg,
        fg="#DFE6EE",
        anchor="w",
    ).pack(fill=tk.X, pady=(0, 8))

    row = tk.Frame(body, bg=owner.theme_bg)
    row.pack(fill=tk.X)
    tk.Label(
        row,
        text="后端：",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_bg,
        fg=owner.theme_toolbar_muted,
    ).pack(side=tk.LEFT)
    backend_var = tk.StringVar(value=_backend_label_of(default_backend))
    combo = ttk.Combobox(
        row,
        textvariable=backend_var,
        values=[label for _key, label in DATA_BACKEND_CHOICES],
        state="readonly",
        width=10,
    )
    combo.pack(side=tk.LEFT, padx=(4, 0))
    try:
        combo.focus_set()
    except tk.TclError:
        pass

    prefix_row = tk.Frame(body, bg=owner.theme_bg)
    prefix_row.pack(fill=tk.X, pady=(10, 0))
    tk.Label(
        prefix_row,
        text="前缀：",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_bg,
        fg=owner.theme_toolbar_muted,
    ).pack(side=tk.LEFT)
    prefix_var = tk.StringVar(value=default_prefix)
    prefix_entry = tk.Entry(
        prefix_row,
        textvariable=prefix_var,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_inner_bg,
        fg=owner.theme_fg,
        insertbackground=owner.theme_fg,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=owner.theme_toolbar_border,
        highlightcolor=owner.theme_accent,
    )
    prefix_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0), ipady=2)

    remember_var = tk.BooleanVar(value=True)
    tk.Checkbutton(
        body,
        text="记住为当前项目默认后端",
        variable=remember_var,
        onvalue=True,
        offvalue=False,
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        activebackground=owner.theme_bg,
        activeforeground="#FFFFFF",
        selectcolor=owner.theme_panel_inner_bg,
        font=("Microsoft YaHei", 8),
        anchor="w",
    ).pack(fill=tk.X, pady=(10, 0))
    remember_prefix_var = tk.BooleanVar(value=True)
    tk.Checkbutton(
        body,
        text="记住为默认导出前缀",
        variable=remember_prefix_var,
        onvalue=True,
        offvalue=False,
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        activebackground=owner.theme_bg,
        activeforeground="#FFFFFF",
        selectcolor=owner.theme_panel_inner_bg,
        font=("Microsoft YaHei", 8),
        anchor="w",
    ).pack(fill=tk.X, pady=(4, 0))

    action = tk.Frame(body, bg=owner.theme_bg)
    action.pack(fill=tk.X, pady=(14, 0))

    def _close(ok):
        result["ok"] = bool(ok)
        result["backend"] = _backend_key_from_label(backend_var.get())
        result["remember"] = bool(remember_var.get())
        result["prefix"] = _normalize_layer_export_prefix(prefix_var.get(), fallback=default_prefix)
        result["remember_prefix"] = bool(remember_prefix_var.get())
        try:
            dialog.destroy()
        except tk.TclError:
            pass

    tk.Button(
        action,
        text="取消",
        command=lambda: _close(False),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=10,
        pady=3,
        cursor="hand2",
    ).pack(side=tk.RIGHT)
    tk.Button(
        action,
        text="开始导出",
        command=lambda: _close(True),
        font=("Microsoft YaHei", 8),
        bg="#0E639C",
        fg="#FFFFFF",
        activebackground="#1577B8",
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=12,
        pady=3,
        cursor="hand2",
    ).pack(side=tk.RIGHT, padx=(0, 6))

    # 按内容自动计算弹窗尺寸，解决高 DPI/大字体时按钮看不见的问题。
    try:
        owner.root.update_idletasks()
        dialog.update_idletasks()
        req_w = max(500, int(dialog.winfo_reqwidth()) + 24)
        req_h = max(350, int(dialog.winfo_reqheight()) + 24)
        max_w = max(480, int(dialog.winfo_screenwidth()) - 80)
        max_h = max(320, int(dialog.winfo_screenheight()) - 120)
        final_w = min(req_w, max_w)
        final_h = min(req_h, max_h)
        x = int(owner.root.winfo_x() + max(0, (owner.root.winfo_width() - final_w) / 2))
        y = int(owner.root.winfo_y() + max(0, (owner.root.winfo_height() - final_h) / 2))
        dialog.geometry(f"{final_w}x{final_h}+{x}+{y}")
    except Exception:
        pass

    dialog.bind("<Return>", lambda _e: _close(True), add="+")
    dialog.bind("<Escape>", lambda _e: _close(False), add="+")
    dialog.protocol("WM_DELETE_WINDOW", lambda: _close(False))
    owner.root.wait_window(dialog)
    if not result["ok"]:
        return None
    return {
        "backend": _normalize_data_backend(result["backend"]),
        "remember": bool(result["remember"]),
        "prefix": _normalize_layer_export_prefix(result.get("prefix"), fallback=default_prefix),
        "remember_prefix": bool(result.get("remember_prefix")),
    }


def _editable_property_keys(kind):
    key = str(kind or "")
    default_keys = PROPERTY_EDITABLE_KEYS_BY_KIND.get("default", set())
    custom_keys = PROPERTY_EDITABLE_KEYS_BY_KIND.get(key)
    if custom_keys is None:
        return set(default_keys)
    return set(custom_keys)


def _set_property_hint_text(owner, text):
    hint_var = getattr(owner, "_ui_designer_prop_hint_var", None)
    if hint_var is None:
        return
    try:
        hint_var.set(str(text or ""))
    except Exception:
        pass


def _refresh_designer_step_ui(owner):
    labels = list(getattr(owner, "_ui_designer_step_labels", []) or [])
    step = int(getattr(owner, "_ui_designer_step", 1) or 1)
    for idx, lbl in enumerate(labels, start=1):
        if lbl is None:
            continue
        active = idx == step
        try:
            lbl.configure(
                bg="#0E639C" if active else owner.theme_panel_bg,
                fg="#FFFFFF" if active else owner.theme_toolbar_fg,
                highlightbackground="#2D82BC" if active else owner.theme_toolbar_border,
            )
        except tk.TclError:
            continue


def _set_designer_step(owner, step: int, hint_text: str = ""):
    owner._ui_designer_step = _clamp(_to_int(step, 1), 1, 4)
    if hint_text and hasattr(owner, "_ui_designer_step_hint_var") and owner._ui_designer_step_hint_var is not None:
        try:
            owner._ui_designer_step_hint_var.set(str(hint_text))
        except Exception:
            pass
    _refresh_designer_step_ui(owner)
    _refresh_novice_action_buttons(owner)
    _refresh_property_visibility(owner)


def _refresh_novice_action_buttons(owner):
    buttons = getattr(owner, "_ui_designer_novice_buttons", {}) or {}
    if not isinstance(buttons, dict):
        return
    step = int(getattr(owner, "_ui_designer_step", 1) or 1)
    mode = str(getattr(owner, "_ui_designer_mode", "novice"))
    if mode != "novice":
        for btn in buttons.values():
            if btn is None:
                continue
            try:
                btn.configure(state="normal")
            except tk.TclError:
                pass
        return

    states = {
        "template": "normal",
        "add": "normal" if step >= 2 else "disabled",
        "bind": "normal" if step >= 2 else "disabled",
        "export": "normal" if step >= 3 else "disabled",
    }
    for key, btn in buttons.items():
        if btn is None:
            continue
        try:
            btn.configure(state=states.get(str(key), "normal"))
        except tk.TclError:
            pass


def _recommended_kinds_for_owner(owner):
    scene_key = str(getattr(owner, "_ui_designer_last_scene_key", "") or "").strip().lower()
    kinds = list(TEMPLATE_RECOMMENDED_KINDS.get(scene_key, TEMPLATE_RECOMMENDED_KINDS.get("default", [])))
    result = [k for k in kinds if k in COMPONENT_KIND_SET]
    if not result:
        result = ["文字", "输入框", "按钮"]
    return result


def _refresh_recommended_palette(owner):
    lst = getattr(owner, "_ui_designer_palette_recommended", None)
    if lst is None:
        return
    kinds = _recommended_kinds_for_owner(owner)
    owner._ui_designer_palette_list_kinds = list(kinds)
    try:
        lst.delete(0, tk.END)
        for kind in kinds:
            lst.insert(tk.END, kind)
        if kinds:
            lst.selection_clear(0, tk.END)
            lst.selection_set(0)
            lst.see(0)
    except Exception:
        pass


def _refresh_property_visibility(owner):
    widgets = getattr(owner, "_ui_designer_prop_widgets", None)
    if not isinstance(widgets, dict):
        return
    mode = str(getattr(owner, "_ui_designer_mode", "novice"))
    show_advanced = bool(getattr(owner, "_ui_designer_show_advanced", False))
    selected = _selected_component(owner)
    selected_kind = str(selected.get("kind", "")) if isinstance(selected, dict) else ""
    editable = _editable_property_keys(selected_kind) if selected_kind else set()

    has_novice_advanced = False
    for key, meta in widgets.items():
        if not isinstance(meta, dict):
            continue
        if bool(meta.get("readonly")):
            continue
        if key in editable and key not in NOVICE_VISIBLE_PROP_KEYS:
            has_novice_advanced = True
            break

    for key, meta in widgets.items():
        if not isinstance(meta, dict):
            continue
        row = meta.get("row")
        if row is None:
            continue
        readonly = bool(meta.get("readonly"))
        visible = True
        if readonly:
            visible = True
        elif key not in editable:
            visible = False
        elif mode == "novice":
            visible = (key in NOVICE_VISIBLE_PROP_KEYS) or show_advanced
        else:
            visible = True
        try:
            mapped = bool(row.winfo_manager())
        except Exception:
            mapped = False
        if visible and not mapped:
            try:
                row.pack(fill=tk.X, pady=(0, 6))
            except tk.TclError:
                pass
        elif (not visible) and mapped:
            try:
                row.pack_forget()
            except tk.TclError:
                pass

    toggle_btn = getattr(owner, "_ui_designer_prop_toggle_btn", None)
    if toggle_btn is not None:
        if mode == "novice" and has_novice_advanced:
            try:
                toggle_btn.configure(text=("收起高级属性" if show_advanced else "展开高级属性"))
            except tk.TclError:
                pass
            try:
                if not bool(toggle_btn.winfo_manager()):
                    toggle_btn.pack(anchor="w", pady=(0, 6))
            except Exception:
                pass
        else:
            try:
                toggle_btn.pack_forget()
            except tk.TclError:
                pass


def _toggle_novice_advanced_props(owner):
    owner._ui_designer_show_advanced = not bool(getattr(owner, "_ui_designer_show_advanced", False))
    _refresh_property_visibility(owner)
    return "break"


def _set_designer_mode(owner, mode: str, announce: bool = False):
    target = str(mode or "novice").strip().lower()
    if target not in {"novice", "pro"}:
        target = "novice"
    owner._ui_designer_mode = target

    mode_btns = getattr(owner, "_ui_designer_mode_buttons", {}) or {}
    for key, btn in mode_btns.items():
        if btn is None:
            continue
        active = str(key) == target
        try:
            btn.configure(
                bg="#0E639C" if active else owner.theme_panel_bg,
                fg="#FFFFFF" if active else owner.theme_toolbar_fg,
            )
        except tk.TclError:
            pass

    show_novice = target == "novice"
    controls = getattr(owner, "_ui_designer_top_controls", {}) or {}
    pro_only_keys = {"copy", "export_layers", "clear", "delete"}
    for key in pro_only_keys:
        widget = controls.get(key)
        if widget is None:
            continue
        shown = bool(getattr(widget, "_ui_shown", True))
        need_show = not show_novice
        if need_show and not shown:
            try:
                widget.pack(side=tk.RIGHT, padx=(6, 0))
                widget._ui_shown = True
            except tk.TclError:
                pass
        elif (not need_show) and shown:
            try:
                widget.pack_forget()
                widget._ui_shown = False
            except tk.TclError:
                pass

    novice_guide = getattr(owner, "_ui_designer_novice_guide", None)
    if novice_guide is not None:
        shown = bool(getattr(novice_guide, "_ui_shown", True))
        if show_novice and not shown:
            try:
                pack_fn = getattr(novice_guide, "pack", None)
                if callable(pack_fn):
                    pack_fn(fill=tk.X, pady=(0, 6), before=getattr(owner, "_ui_designer_body_paned", None))
                setattr(novice_guide, "_ui_shown", True)
            except tk.TclError:
                pass
        elif (not show_novice) and shown:
            try:
                forget_fn = getattr(novice_guide, "pack_forget", None)
                if callable(forget_fn):
                    forget_fn()
                setattr(novice_guide, "_ui_shown", False)
            except tk.TclError:
                pass

    novice_palette = getattr(owner, "_ui_designer_palette_novice_wrap", None)
    pro_palette = getattr(owner, "_ui_designer_palette_pro_wrap", None)
    if novice_palette is not None and pro_palette is not None:
        novice_shown = bool(getattr(novice_palette, "_ui_shown", True))
        pro_shown = bool(getattr(pro_palette, "_ui_shown", True))
        if show_novice:
            if not novice_shown:
                try:
                    novice_palette.pack(fill=tk.BOTH, expand=True)
                    novice_palette._ui_shown = True
                except tk.TclError:
                    pass
            if pro_shown:
                try:
                    pro_palette.pack_forget()
                    pro_palette._ui_shown = False
                except tk.TclError:
                    pass
            owner._ui_designer_palette = getattr(owner, "_ui_designer_palette_recommended", getattr(owner, "_ui_designer_palette", None))
            _refresh_recommended_palette(owner)
        else:
            if novice_shown:
                try:
                    novice_palette.pack_forget()
                    novice_palette._ui_shown = False
                except tk.TclError:
                    pass
            if not pro_shown:
                try:
                    pro_palette.pack(fill=tk.BOTH, expand=True)
                    pro_palette._ui_shown = True
                except tk.TclError:
                    pass
            owner._ui_designer_palette = getattr(owner, "_ui_designer_palette_pro", getattr(owner, "_ui_designer_palette", None))

    _refresh_novice_action_buttons(owner)

    if announce and hasattr(owner, "status_main_var"):
        mode_text = "新手模式" if target == "novice" else "专业模式"
        owner.status_main_var.set(f"界面设计器：已切换到{mode_text}")


def _apply_property_field_state(owner, kind):
    widgets = getattr(owner, "_ui_designer_prop_widgets", None)
    if not isinstance(widgets, dict):
        return
    editable = set() if kind is None else _editable_property_keys(kind)
    if str(getattr(owner, "_ui_designer_mode", "novice")) == "novice":
        editable = editable & set(NOVICE_BASIC_PROP_KEYS)
    for key, meta in widgets.items():
        if not isinstance(meta, dict):
            continue
        entry = meta.get("entry")
        if entry is None:
            continue
        readonly = bool(meta.get("readonly"))
        choice = bool(meta.get("choice"))
        if readonly:
            next_state = "readonly"
        elif key in editable:
            next_state = "readonly" if choice else "normal"
        else:
            next_state = "disabled"
        try:
            entry.configure(state=next_state)
        except tk.TclError:
            continue


def _resolve_quick_start_scene(scene_key):
    key = str(scene_key or "").strip().lower()
    scene = QUICK_START_SCENE_SPECS.get(key)
    if scene is None:
        scene = QUICK_START_SCENE_SPECS.get("blank", {})
    return json.loads(json.dumps(scene, ensure_ascii=False)) if scene else {
        "key": "blank",
        "title": "空白窗口",
        "window": {"text": "我的窗口", "w": 960, "h": 640},
        "components": [],
    }


def _new_component_from_scene_spec(owner, spec):
    kind = str(spec.get("kind", "文字"))
    if kind not in COMPONENT_KIND_SET:
        kind = "文字"
    comp = _new_component(
        owner,
        kind,
        x=_to_int(spec.get("x", 120), 120),
        y=_to_int(spec.get("y", 90), 90),
    )
    for key in ("text", "event", "action_text", "columns"):
        if key in spec:
            comp[key] = str(spec.get(key, comp.get(key, "")))
    if "column_count" in spec:
        comp["column_count"] = _clamp(_to_int(spec.get("column_count", comp.get("column_count", 3)), 3), 1, 32)
    if "name" in spec:
        wanted_name = _sanitize_identifier(spec.get("name", ""), comp.get("name", ""))
        if wanted_name:
            existing = {
                str(item.get("name", ""))
                for item in list(getattr(owner, "_ui_designer_components", []) or [])
            }
            name = wanted_name
            seq = 2
            while name in existing:
                name = f"{wanted_name}_{seq}"
                seq += 1
            comp["name"] = name
    if "rows" in spec:
        comp["rows"] = max(3, _to_int(spec.get("rows", comp.get("rows", 8)), comp.get("rows", 8)))
    min_w = 360 if kind == WINDOW_COMPONENT_KIND else 60
    min_h = 240 if kind == WINDOW_COMPONENT_KIND else 24
    comp["w"] = _clamp(_to_int(spec.get("w", comp.get("w", 180)), comp.get("w", 180)), min_w, CANVAS_REGION_W)
    comp["h"] = _clamp(_to_int(spec.get("h", comp.get("h", 36)), comp.get("h", 36)), min_h, CANVAS_REGION_H)
    max_x = max(0, CANVAS_REGION_W - _to_int(comp.get("w", 180), 180))
    max_y = max(0, CANVAS_REGION_H - _to_int(comp.get("h", 36), 36))
    comp["x"] = _clamp(_to_int(spec.get("x", comp.get("x", 0)), comp.get("x", 0)), 0, max_x)
    comp["y"] = _clamp(_to_int(spec.get("y", comp.get("y", 0)), comp.get("y", 0)), 0, max_y)
    return comp


def _apply_quick_start_scene(owner, scene_key, clear_existing=True):
    _ensure_component_baseline(owner)
    scene = _resolve_quick_start_scene(scene_key)
    window_comp = _ensure_window_component(owner)
    if clear_existing:
        owner._ui_designer_components = [window_comp]
    window_cfg = scene.get("window", {}) or {}
    window_comp["text"] = str(window_cfg.get("text", window_comp.get("text", "我的窗口"))).strip() or "我的窗口"
    window_comp["scroll_mode"] = _normalize_window_scroll_mode(window_cfg.get("scroll_mode", window_comp.get("scroll_mode", "自动")))
    window_comp["w"] = _clamp(_to_int(window_cfg.get("w", window_comp.get("w", 960)), 960), 360, CANVAS_REGION_W)
    window_comp["h"] = _clamp(_to_int(window_cfg.get("h", window_comp.get("h", 640)), 640), 240, CANVAS_REGION_H)

    created = []
    for spec in list(scene.get("components", []) or []):
        comp = _new_component_from_scene_spec(owner, spec)
        owner._ui_designer_components.append(comp)
        created.append(comp)

    owner._ui_designer_selected_uid = int((created[0] if created else window_comp).get("uid", 0))
    _render_canvas(owner)
    _refresh_property_panel(owner)
    if hasattr(owner, "status_main_var"):
        suffix = "并清空旧组件" if clear_existing else "并保留已有组件"
        owner.status_main_var.set(f"界面设计器：已应用一键起步 - {scene.get('title', '空白窗口')}（{suffix}）")
    owner._ui_designer_last_scene_key = str(scene.get("key", scene_key)).strip().lower()
    _remember_recent_quick_start_scene(owner, str(scene.get("key", scene_key)))
    owner._ui_designer_name_suggest_prefix = _sanitize_identifier(scene.get("title", ""), "界面")
    _refresh_recommended_palette(owner)
    _set_designer_step(owner, 2, "下一步：继续添加/调整组件，完成基础页面布局。")
    return "break"


def _remember_recent_quick_start_scene(owner, scene_key: str):
    _ensure_state(owner)
    key = str(scene_key or "").strip().lower()
    if not key:
        return
    scenes = [str(x).strip().lower() for x in list(getattr(owner, "_ui_designer_recent_scenes", []) or []) if str(x).strip()]
    scenes = [x for x in scenes if x != key]
    scenes.insert(0, key)
    owner._ui_designer_recent_scenes = scenes[:6]
    saver = getattr(owner, "_save_project_state", None)
    if callable(saver):
        try:
            saver()
        except Exception:
            pass


def _prompt_quick_start_scene(owner):
    _ensure_state(owner)
    result = {"ok": False, "scene": "form", "clear": True}

    dialog = tk.Toplevel(owner.root)
    dialog.title("一键起步")
    dialog.transient(owner.root)
    dialog.configure(bg=owner.theme_bg)
    try:
        dialog.resizable(False, False)
    except tk.TclError:
        pass
    try:
        dialog.grab_set()
    except tk.TclError:
        pass

    body = tk.Frame(dialog, bg=owner.theme_bg, padx=14, pady=12)
    body.pack(fill=tk.BOTH, expand=True)
    tk.Label(
        body,
        text="选择一个基础场景，先生成可运行页面骨架，再改细节。",
        font=("Microsoft YaHei", 9, "bold"),
        bg=owner.theme_bg,
        fg="#DFE6EE",
        anchor="w",
    ).pack(fill=tk.X, pady=(0, 8))

    scene_items = list(QUICK_START_SCENES)
    scene_keys = {str(item.get("key", "")) for item in scene_items}
    recent_scene_keys = [str(x).strip().lower() for x in list(getattr(owner, "_ui_designer_recent_scenes", []) or []) if str(x).strip()]
    if recent_scene_keys and recent_scene_keys[0] in scene_keys:
        default_scene = recent_scene_keys[0]
    else:
        default_scene = "form" if "form" in scene_keys else (scene_items[0]["key"] if scene_items else "blank")
    scene_var = tk.StringVar(value=str(default_scene))
    category_var = tk.StringVar(value="全部")
    query_var = tk.StringVar(value="")
    visible_scene_items = []

    filter_row = tk.Frame(body, bg=owner.theme_bg)
    filter_row.pack(fill=tk.X, pady=(0, 8))
    tk.Label(
        filter_row,
        text="分类：",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_bg,
        fg=owner.theme_toolbar_muted,
    ).pack(side=tk.LEFT)
    category_values = list(QUICK_START_CATEGORY_ORDER)
    for scene in scene_items:
        c = str(scene.get("category", "基础"))
        if c and c not in category_values:
            category_values.append(c)
    category_combo = ttk.Combobox(filter_row, textvariable=category_var, values=category_values, state="readonly", width=8)
    category_combo.pack(side=tk.LEFT, padx=(4, 0))
    tk.Label(
        filter_row,
        text="搜索：",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_bg,
        fg=owner.theme_toolbar_muted,
    ).pack(side=tk.LEFT, padx=(10, 0))
    query_entry = tk.Entry(
        filter_row,
        textvariable=query_var,
        width=20,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_inner_bg,
        fg=owner.theme_fg,
        insertbackground=owner.theme_fg,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=owner.theme_toolbar_border,
        highlightcolor=owner.theme_accent,
    )
    query_entry.pack(side=tk.LEFT, padx=(4, 0), ipady=2)
    result_count_var = tk.StringVar(value="")
    tk.Label(
        filter_row,
        textvariable=result_count_var,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_bg,
        fg=owner.theme_toolbar_muted,
    ).pack(side=tk.RIGHT)

    selector = tk.Frame(body, bg=owner.theme_bg)
    selector.pack(fill=tk.BOTH, expand=True)

    left = tk.Frame(selector, bg=owner.theme_bg)
    left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    right = tk.Frame(selector, bg=owner.theme_panel_bg, padx=10, pady=8)
    right.pack(side=tk.LEFT, fill=tk.BOTH, padx=(10, 0))

    list_wrap = tk.Frame(left, bg=owner.theme_bg)
    list_wrap.pack(fill=tk.BOTH, expand=True)
    scene_list = tk.Listbox(
        list_wrap,
        height=10,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_inner_bg,
        fg=owner.theme_fg,
        selectbackground=owner.theme_accent,
        selectforeground="#FFFFFF",
        relief="flat",
        borderwidth=0,
        highlightthickness=1,
        highlightbackground=owner.theme_toolbar_border,
        highlightcolor=owner.theme_accent,
        activestyle="none",
    )
    scene_scroll = ttk.Scrollbar(list_wrap, orient="vertical", command=scene_list.yview)
    scene_list.configure(yscrollcommand=scene_scroll.set)
    scene_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scene_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    scene_detail_var = tk.StringVar(value="")
    tk.Label(
        right,
        text="模板说明",
        font=("Microsoft YaHei", 8, "bold"),
        bg=owner.theme_panel_bg,
        fg="#DFE6EE",
        anchor="w",
    ).pack(fill=tk.X)
    tk.Label(
        right,
        textvariable=scene_detail_var,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg="#B8C7D8",
        justify="left",
        anchor="nw",
        wraplength=250,
        pady=6,
    ).pack(fill=tk.BOTH, expand=True)

    preview_canvas = tk.Canvas(
        right,
        width=260,
        height=160,
        bg=owner.theme_panel_inner_bg,
        highlightthickness=1,
        highlightbackground=owner.theme_toolbar_border,
        highlightcolor=owner.theme_toolbar_border,
        relief="flat",
        borderwidth=0,
    )
    preview_canvas.pack(fill=tk.X, pady=(6, 0))

    def _draw_scene_preview(scene_key: str):
        scene = _resolve_quick_start_scene(scene_key)
        preview_canvas.delete("all")
        cw = int(preview_canvas.winfo_width() or 260)
        ch = int(preview_canvas.winfo_height() or 160)
        pad = 10
        win = dict(scene.get("window", {}) or {})
        ww = max(360, _to_int(win.get("w", 960), 960))
        wh = max(240, _to_int(win.get("h", 640), 640))
        scale = min((cw - pad * 2) / float(ww), (ch - pad * 2) / float(wh))
        scale = max(0.08, min(1.0, scale))
        view_w = int(ww * scale)
        view_h = int(wh * scale)
        ox = int((cw - view_w) / 2)
        oy = int((ch - view_h) / 2)

        preview_canvas.create_rectangle(ox, oy, ox + view_w, oy + view_h, outline="#4CA8FF", width=1)
        kinds_color = {
            "按钮": "#2E7D32",
            "输入框": "#3A4A5E",
            "多行文本框": "#3A4A5E",
            "表格": "#0E639C",
            "卡片": "#374861",
            "复选框": "#2E7D32",
            "单选按钮": "#2E7D32",
            "文字": "#5A6D84",
        }
        for comp in list(scene.get("components", []) or [])[:30]:
            cx = _to_int(comp.get("x", 0), 0)
            cy = _to_int(comp.get("y", 0), 0)
            cw_i = max(40, _to_int(comp.get("w", 120), 120))
            ch_i = max(20, _to_int(comp.get("h", 30), 30))
            px1 = ox + int(cx * scale)
            py1 = oy + int(cy * scale)
            px2 = ox + int((cx + cw_i) * scale)
            py2 = oy + int((cy + ch_i) * scale)
            fill = kinds_color.get(str(comp.get("kind", "")), "#455B74")
            preview_canvas.create_rectangle(px1, py1, px2, py2, fill=fill, outline="")

    def _filtered_scene_items():
        selected_category = str(category_var.get() or "全部")
        query_text = str(query_var.get() or "").strip().lower()

        def _match_query(scene):
            if not query_text:
                return True
            title = str(scene.get("title", "")).lower()
            desc = str(scene.get("desc", "")).lower()
            key = str(scene.get("key", "")).lower()
            tags = " ".join(str(x).lower() for x in list(scene.get("tags", []) or []))
            bucket = f"{title} {desc} {key} {tags}"
            return query_text in bucket

        if selected_category == "全部":
            rows = [s for s in scene_items if _match_query(s)]
        else:
            rows = [s for s in scene_items if str(s.get("category", "基础")) == selected_category and _match_query(s)]

        def _sort_key(scene):
            key = str(scene.get("key", "")).lower()
            if key in recent_scene_keys:
                return (0, recent_scene_keys.index(key), str(scene.get("title", "")))
            return (1, 999, str(scene.get("title", "")))

        rows.sort(key=_sort_key)
        return rows

    def _refresh_scene_list(prefer_key: str = ""):
        nonlocal visible_scene_items
        visible_scene_items = _filtered_scene_items()
        scene_list.delete(0, tk.END)
        for scene in visible_scene_items:
            title = str(scene.get("title", ""))
            desc = str(scene.get("desc", ""))
            cat = str(scene.get("category", "基础"))
            key = str(scene.get("key", "")).lower()
            prefix = "★ " if key in recent_scene_keys else ""
            scene_list.insert(tk.END, f"{prefix}[{cat}] {title}  ·  {desc}")
        result_count_var.set(f"{len(visible_scene_items)} 个模板")

        selected_key = str(prefer_key or scene_var.get() or "")
        sel_index = -1
        for idx, scene in enumerate(visible_scene_items):
            if str(scene.get("key", "")) == selected_key:
                sel_index = idx
                break
        if sel_index < 0 and visible_scene_items:
            sel_index = 0

        if sel_index >= 0:
            scene_list.selection_set(sel_index)
            scene_list.see(sel_index)
            scene_var.set(str(visible_scene_items[sel_index].get("key", default_scene)))
            _refresh_scene_detail(scene_var.get())
        else:
            scene_detail_var.set("当前分类没有模板。")
            preview_canvas.delete("all")

    def _refresh_scene_detail(scene_key: str):
        scene = _resolve_quick_start_scene(scene_key)
        components = list(scene.get("components", []) or [])
        action_names = []
        for comp in components:
            if str(comp.get("kind", "")) in BUTTON_COMPONENT_KINDS or str(comp.get("kind", "")) in {"登录模板", "列表模板"}:
                event_name = str(comp.get("event", "")).strip()
                if event_name:
                    action_names.append(event_name)
        action_names = action_names[:4]
        detail_lines = [
            f"模板：{scene.get('title', '')}",
            f"窗口：{scene.get('window', {}).get('text', '我的窗口')}",
            f"组件数：{len(components)}",
        ]
        if action_names:
            detail_lines.append("关键动作：" + "、".join(action_names))
        else:
            detail_lines.append("关键动作：需后续手动配置")
        tags = list(scene.get("tags", []) or [])
        if tags:
            detail_lines.append("标签：" + " / ".join(str(t) for t in tags[:5]))
        scene_detail_var.set("\n".join(detail_lines))
        _draw_scene_preview(scene_key)

    def _sync_scene_from_list(_event=None):
        sel = scene_list.curselection()
        if not sel:
            return
        idx = int(sel[0])
        if 0 <= idx < len(visible_scene_items):
            key = str(visible_scene_items[idx].get("key", "blank"))
            scene_var.set(key)
            _refresh_scene_detail(key)

    scene_list.bind("<<ListboxSelect>>", _sync_scene_from_list, add="+")
    category_combo.bind("<<ComboboxSelected>>", lambda _e: _refresh_scene_list(prefer_key=scene_var.get()), add="+")
    query_var.trace_add("write", lambda *_args: _refresh_scene_list(prefer_key=scene_var.get()))

    clear_var = tk.BooleanVar(value=True)
    tk.Checkbutton(
        body,
        text="应用前清空当前组件（窗口保留）",
        variable=clear_var,
        onvalue=True,
        offvalue=False,
        bg=owner.theme_bg,
        fg=owner.theme_fg,
        activebackground=owner.theme_bg,
        activeforeground="#FFFFFF",
        selectcolor=owner.theme_panel_inner_bg,
        font=("Microsoft YaHei", 8),
        anchor="w",
    ).pack(fill=tk.X, pady=(8, 0))

    _refresh_scene_list(prefer_key=str(default_scene))
    try:
        query_entry.focus_set()
    except tk.TclError:
        pass

    action = tk.Frame(body, bg=owner.theme_bg)
    action.pack(fill=tk.X, pady=(14, 0))

    def _close(ok):
        result["ok"] = bool(ok)
        result["scene"] = str(scene_var.get() or default_scene)
        result["clear"] = bool(clear_var.get())
        try:
            dialog.destroy()
        except tk.TclError:
            pass

    tk.Button(
        action,
        text="取消",
        command=lambda: _close(False),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=10,
        pady=3,
        cursor="hand2",
    ).pack(side=tk.RIGHT)
    tk.Button(
        action,
        text="开始生成",
        command=lambda: _close(True),
        font=("Microsoft YaHei", 8),
        bg="#0E639C",
        fg="#FFFFFF",
        activebackground="#1577B8",
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=12,
        pady=3,
        cursor="hand2",
    ).pack(side=tk.RIGHT, padx=(0, 6))

    # 依据内容自动计算弹窗大小，避免高 DPI 或大字体时按钮被截断。
    try:
        owner.root.update_idletasks()
        dialog.update_idletasks()
        req_w = max(760, int(dialog.winfo_reqwidth()) + 24)
        req_h = max(460, int(dialog.winfo_reqheight()) + 24)
        x = int(owner.root.winfo_x() + max(0, (owner.root.winfo_width() - req_w) / 2))
        y = int(owner.root.winfo_y() + max(0, (owner.root.winfo_height() - req_h) / 2))
        dialog.geometry(f"{req_w}x{req_h}+{x}+{y}")
    except Exception:
        pass

    dialog.bind("<Return>", lambda _e: _close(True), add="+")
    dialog.bind("<Escape>", lambda _e: _close(False), add="+")
    dialog.protocol("WM_DELETE_WINDOW", lambda: _close(False))
    owner.root.wait_window(dialog)
    if not result["ok"]:
        return None
    return {"scene": result["scene"], "clear": bool(result["clear"])}


def run_ui_designer_quick_start(owner, event=None):
    del event
    choice = _prompt_quick_start_scene(owner)
    if not choice:
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("界面设计器：已取消一键起步")
        return "break"
    return _apply_quick_start_scene(owner, choice.get("scene"), clear_existing=bool(choice.get("clear", True)))


def _tool_button(owner, parent, text, cmd):
    btn = tk.Button(
        parent,
        text=text,
        command=cmd,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=2,
        cursor="hand2",
    )
    btn.pack(side=tk.RIGHT, padx=(6, 0))
    return btn


def _center_window(owner, win, width=1320, height=820):
    try:
        owner.root.update_idletasks()
        x = int(owner.root.winfo_x() + max(0, (owner.root.winfo_width() - width) / 2))
        y = int(owner.root.winfo_y() + max(0, (owner.root.winfo_height() - height) / 2))
        win.geometry(f"{width}x{height}+{x}+{y}")
    except Exception:
        try:
            win.geometry(f"{width}x{height}")
        except Exception:
            pass


def _ensure_state(owner):
    if not hasattr(owner, "_ui_designer_components"):
        owner._ui_designer_components = []
    if not hasattr(owner, "_ui_designer_next_uid"):
        owner._ui_designer_next_uid = 1
    if not hasattr(owner, "_ui_designer_selected_uid"):
        owner._ui_designer_selected_uid = None
    if not hasattr(owner, "_ui_designer_drag"):
        owner._ui_designer_drag = {"uid": None, "start_x": 0, "start_y": 0}
    if not hasattr(owner, "_ui_designer_resize"):
        owner._ui_designer_resize = {
            "uid": None,
            "anchor": "",
            "start_x": 0,
            "start_y": 0,
            "x": 0,
            "y": 0,
            "w": 0,
            "h": 0,
        }
    if not hasattr(owner, "_ui_designer_data_backend"):
        owner._ui_designer_data_backend = "sqlite"
    owner._ui_designer_data_backend = _normalize_data_backend(getattr(owner, "_ui_designer_data_backend", "sqlite"))
    if not hasattr(owner, "_ui_designer_backend_vars"):
        owner._ui_designer_backend_vars = []
    if not hasattr(owner, "_ui_designer_layer_export_prefix"):
        owner._ui_designer_layer_export_prefix = "界面设计"
    if not hasattr(owner, "_ui_designer_prop_widgets"):
        owner._ui_designer_prop_widgets = {}
    if not hasattr(owner, "_ui_designer_prop_hint_var"):
        owner._ui_designer_prop_hint_var = None
    if not hasattr(owner, "_ui_designer_palette_kind_map"):
        owner._ui_designer_palette_kind_map = {}
    if not hasattr(owner, "_ui_designer_mode"):
        owner._ui_designer_mode = "novice"
    if not hasattr(owner, "_ui_designer_step"):
        owner._ui_designer_step = 1
    if not hasattr(owner, "_ui_designer_step_labels"):
        owner._ui_designer_step_labels = []
    if not hasattr(owner, "_ui_designer_mode_buttons"):
        owner._ui_designer_mode_buttons = {}
    if not hasattr(owner, "_ui_designer_top_controls"):
        owner._ui_designer_top_controls = {}
    if not hasattr(owner, "_ui_designer_novice_guide"):
        owner._ui_designer_novice_guide = None
    if not hasattr(owner, "_ui_designer_step_hint_var"):
        owner._ui_designer_step_hint_var = None
    if not hasattr(owner, "_ui_designer_body_paned"):
        owner._ui_designer_body_paned = None
    if not hasattr(owner, "_ui_designer_recent_scenes"):
        owner._ui_designer_recent_scenes = []
    if not hasattr(owner, "_ui_designer_name_suggest_prefix"):
        owner._ui_designer_name_suggest_prefix = "界面"
    if not hasattr(owner, "_ui_designer_novice_buttons"):
        owner._ui_designer_novice_buttons = {}
    if not hasattr(owner, "_ui_designer_palette_list_kinds"):
        owner._ui_designer_palette_list_kinds = []
    if not hasattr(owner, "_ui_designer_last_scene_key"):
        owner._ui_designer_last_scene_key = ""
    if not hasattr(owner, "_ui_designer_opened_once"):
        owner._ui_designer_opened_once = False
    if not hasattr(owner, "_ui_designer_show_advanced"):
        owner._ui_designer_show_advanced = False
    if not hasattr(owner, "_ui_designer_prop_toggle_btn"):
        owner._ui_designer_prop_toggle_btn = None
    if not hasattr(owner, "_ui_designer_pro_palette_query_var"):
        owner._ui_designer_pro_palette_query_var = None
    if not hasattr(owner, "_ui_designer_pro_palette_query_entry"):
        owner._ui_designer_pro_palette_query_entry = None
    if not hasattr(owner, "_ui_designer_professional_clean_render"):
        # 专业模式默认也启用清爽渲染，减少双层文字和视觉噪音。
        owner._ui_designer_professional_clean_render = True
    owner._ui_designer_layer_export_prefix = _normalize_layer_export_prefix(
        getattr(owner, "_ui_designer_layer_export_prefix", "界面设计")
    )


def _find_first_component_by_kind(owner, kind):
    _ensure_state(owner)
    target = str(kind or "")
    for item in owner._ui_designer_components:
        if str(item.get("kind", "")) == target:
            return item
    return None


def _ensure_window_component(owner):
    exists = _find_first_component_by_kind(owner, WINDOW_COMPONENT_KIND)
    if exists is not None:
        return exists
    comp = _new_component(owner, WINDOW_COMPONENT_KIND)
    owner._ui_designer_components.insert(0, comp)
    return comp


def _ensure_component_baseline(owner):
    _ensure_state(owner)
    window_comp = _ensure_window_component(owner)
    if str(window_comp.get("kind", "")) == WINDOW_COMPONENT_KIND:
        window_comp["scroll_mode"] = _normalize_window_scroll_mode(window_comp.get("scroll_mode", "自动"))
    if getattr(owner, "_ui_designer_selected_uid", None) is None:
        owner._ui_designer_selected_uid = int(window_comp.get("uid", 0))


def _next_uid(owner):
    _ensure_state(owner)
    uid = int(getattr(owner, "_ui_designer_next_uid", 1) or 1)
    owner._ui_designer_next_uid = uid + 1
    return uid


def _kind_name_token(kind: str) -> str:
    mapping = {
        WINDOW_COMPONENT_KIND: "窗口",
        "文字": "标题",
        "输入框": "输入",
        "多行文本框": "多行输入",
        "按钮": "按钮",
        "复选框": "勾选",
        "单选按钮": "单选",
        "组合框": "组合",
        "数值框": "数值",
        "数值滑块": "滑块",
        "日期选择器": "日期",
        "列表框": "列表",
        "树形视图": "树形",
        "表格": "表格",
        "卡片": "卡片",
        "分组框": "分组",
        "选项卡": "选项卡",
        "分割容器": "分割",
        "表格布局面板": "网格",
        "流式布局面板": "流式",
        "菜单栏": "菜单",
        "工具栏": "工具栏",
        "状态栏": "状态栏",
        "登录模板": "登录模板",
        "列表模板": "列表模板",
        "进度条": "进度",
        "图片框": "图片",
    }
    return str(mapping.get(str(kind or ""), str(kind or "控件")))


def _calc_palette_width(owner) -> tuple[int, int, int]:
    """Estimate palette panel and tree column width from text metrics.

    Returns: (panel_width, panel_minsize, tree_col_width)
    """
    dpi_scale = float(getattr(owner, "dpi_scale", 1.0) or 1.0)
    try:
        f = tkfont.Font(family="Microsoft YaHei", size=9)
    except Exception:
        f = None

    def _measure(text: str) -> int:
        s = str(text or "")
        if f is None:
            return int(len(s) * 9)
        try:
            return int(f.measure(s))
        except Exception:
            return int(len(s) * 9)

    max_w = 0
    for group_name, kind_list in COMPONENT_PALETTE_GROUPS:
        valid = [k for k in kind_list if k in COMPONENT_KIND_SET]
        title = f"{group_name} ({len(valid)})"
        max_w = max(max_w, _measure(title))
        for kind in valid:
            max_w = max(max_w, _measure(kind))

    # paddings: tree indent + scrollbar + panel margins + safety gap
    # 左侧组件栏默认保持紧凑，避免挤占画布可视区。
    tree_col_width = max(210, int(max_w + 64), int(228 * dpi_scale))
    panel_width = max(236, int(tree_col_width + 26), int(248 * dpi_scale))
    panel_minsize = max(210, int(panel_width - 18), int(220 * dpi_scale))
    return panel_width, panel_minsize, tree_col_width


def _suggest_component_name(owner, kind: str, uid: int, preferred: str = "") -> str:
    _ensure_state(owner)
    raw_prefix = str(getattr(owner, "_ui_designer_name_suggest_prefix", "界面") or "界面")
    prefix = _sanitize_identifier(raw_prefix, "界面")
    token = _sanitize_identifier(preferred, "") if str(preferred or "").strip() else _sanitize_identifier(_kind_name_token(kind), "控件")
    base = _sanitize_identifier(f"{prefix}_{token}", f"{token}{uid}")
    existing = {str(item.get("name", "")) for item in list(getattr(owner, "_ui_designer_components", []) or [])}
    name = base
    seq = 2
    while name in existing:
        name = f"{base}_{seq}"
        seq += 1
    return name


def _clamp(value, low, high):
    return max(low, min(high, value))


def _to_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return int(default)


def _normalize_window_scroll_mode(value, fallback="自动"):
    text = str(value or "").strip().lower()
    if text in {"无", "关闭", "off", "none", "no", "false", "0"}:
        return "无"
    if text in {"总是", "始终", "always", "on", "true", "1"}:
        return "总是"
    if text in {"自动", "auto", "default", ""}:
        return "自动"
    return str(fallback or "自动")


def _normalize_button_style(value, fallback="主按钮"):
    text = str(value or "").strip().lower()
    if text in {"主", "主按钮", "primary", "main", "默认"}:
        return "主按钮"
    if text in {"次", "次按钮", "secondary", "second"}:
        return "次按钮"
    if text in {"危险", "危险按钮", "danger", "warn", "warning"}:
        return "危险按钮"
    if text in {"朴素", "朴素按钮", "plain", "ghost", "text"}:
        return "朴素按钮"
    return str(fallback or "主按钮")


def _normalize_card_border(value, fallback="显示"):
    text = str(value or "").strip().lower()
    if text in {"隐藏", "无", "关", "off", "none", "false", "0"}:
        return "隐藏"
    if text in {"显示", "开", "on", "true", "1", ""}:
        return "显示"
    return str(fallback or "显示")


def _new_component(owner, kind, x=120, y=90):
    if kind not in COMPONENT_KIND_SET:
        kind = "文字"
    catalog_map = _catalog_map()
    base = catalog_map.get(kind, {"w": 180, "h": 34, "text": kind})
    uid = _next_uid(owner)
    name = _suggest_component_name(owner, kind, uid)
    default_x = _to_int(base.get("x", x), x)
    default_y = _to_int(base.get("y", y), y)
    return {
        "uid": uid,
        "kind": kind,
        "name": name,
        "text": str(base.get("text", kind)),
        "scroll_mode": _normalize_window_scroll_mode(base.get("scroll_mode", "自动")),
        "button_style": _normalize_button_style(base.get("button_style", "主按钮")),
        "card_border": _normalize_card_border(base.get("card_border", "显示")),
        "x": default_x,
        "y": default_y,
        "w": max(80, _to_int(base.get("w", 180), 180)),
        "h": max(28, _to_int(base.get("h", 34), 34)),
        "event": str(base.get("event", "")),
        "action_text": str(base.get("action_text", "")),
        "columns": str(base.get("columns", "列1,列2")),
        "column_count": max(1, len(_normalize_columns(base.get("columns", "列1,列2")))),
        "rows": max(3, _to_int(base.get("rows", 8), 8)),
    }


def _find_component(owner, uid):
    _ensure_state(owner)
    target_uid = _to_int(uid, -1)
    if target_uid < 0:
        return None
    for item in owner._ui_designer_components:
        if _to_int(item.get("uid", -1), -1) == target_uid:
            return item
    return None


def _selected_component(owner):
    uid = getattr(owner, "_ui_designer_selected_uid", None)
    if uid is None:
        return None
    return _find_component(owner, uid)


def _draw_grid(owner):
    canvas = getattr(owner, "_ui_designer_canvas", None)
    if canvas is None:
        return
    canvas.delete("grid")
    try:
        for x in range(0, CANVAS_REGION_W + 1, CANVAS_GRID):
            color = "#283547" if x % (CANVAS_GRID * 5) == 0 else "#1B2533"
            canvas.create_line(x, 0, x, CANVAS_REGION_H, fill=color, width=1, tags=("grid",))
        for y in range(0, CANVAS_REGION_H + 1, CANVAS_GRID):
            color = "#283547" if y % (CANVAS_GRID * 5) == 0 else "#1B2533"
            canvas.create_line(0, y, CANVAS_REGION_W, y, fill=color, width=1, tags=("grid",))
    except tk.TclError:
        return
    canvas.lower("grid")


def _component_colors(kind):
    if kind == WINDOW_COMPONENT_KIND:
        return {"fill": "#0F1726", "text": "#DCE8F7"}
    if kind in BUTTON_COMPONENT_KINDS:
        return {"fill": "#154E7A", "text": "#FFFFFF"}
    if kind in INPUT_COMPONENT_KINDS:
        return {"fill": "#1A2433", "text": "#D8E0EA"}
    if kind in TABLE_COMPONENT_KINDS:
        return {"fill": "#1D2A3C", "text": "#DCE7F5"}
    if kind in CARD_COMPONENT_KINDS:
        return {"fill": "#1A2230", "text": "#DCE7F5"}
    if kind in {"登录模板", "列表模板"}:
        return {"fill": "#1D2738", "text": "#DCE7F5"}
    if kind in TEXT_COMPONENT_KINDS:
        return {"fill": "#223144", "text": "#DCE7F5"}
    return {"fill": "#223144", "text": "#DCE7F5"}


def _preview_text(raw, fallback="", limit=18):
    text = str(raw or "").strip().replace("\n", " ")
    if not text:
        text = str(fallback or "")
    if len(text) > max(4, int(limit)):
        return text[: max(3, int(limit) - 1)] + "…"
    return text


def _draw_component_preview(canvas, kind, x, y, x2, y2, text, colors, tag, simplify=False):
    tags = ("component", tag)
    items = []
    w = max(1, x2 - x)
    h = max(1, y2 - y)
    label = _preview_text(text, fallback=kind, limit=22)

    if simplify:
        if kind == WINDOW_COMPONENT_KIND:
            items.append(
                canvas.create_text(
                    x + 12,
                    y + 14,
                    text=label,
                    fill="#E8F2FF",
                    anchor="nw",
                    font=("Microsoft YaHei", 10, "bold"),
                    tags=tags,
                )
            )
            return items
        items.append(
            canvas.create_text(
                x + int(w / 2),
                y + int(h / 2),
                text=label,
                fill=colors["text"],
                anchor="c",
                font=("Microsoft YaHei", 10 if kind in BUTTON_COMPONENT_KINDS else 9),
                tags=tags,
            )
        )
        return items

    if w < 36 or h < 24:
        items.append(
            canvas.create_text(
                x + 6,
                y + 6,
                text=label,
                fill=colors["text"],
                anchor="nw",
                font=("Microsoft YaHei", 8),
                tags=tags,
            )
        )
        return items

    left = x + 8
    top = y + 26
    right = x2 - 8
    bottom = y2 - 8
    if right <= left or bottom <= top:
        items.append(
            canvas.create_text(
                x + 8,
                y + max(20, int(h / 2)),
                text=label,
                fill=colors["text"],
                anchor="w",
                font=("Microsoft YaHei", 9),
                tags=tags,
            )
        )
        return items

    if kind == WINDOW_COMPONENT_KIND:
        title_h = min(32, max(24, int(h * 0.12)))
        items.append(
            canvas.create_rectangle(
                left,
                top,
                right,
                top + title_h,
                fill="#1E2C43",
                outline="#304766",
                width=1,
                tags=tags,
            )
        )
        items.append(
            canvas.create_rectangle(
                left,
                top + title_h,
                right,
                bottom,
                fill="#0A1930",
                outline="#304766",
                width=1,
                tags=tags,
            )
        )
        items.append(
            canvas.create_text(
                left + 8,
                top + int(title_h / 2),
                text=label,
                fill="#E8F2FF",
                anchor="w",
                font=("Microsoft YaHei", 9, "bold"),
                tags=tags,
            )
        )
        return items

    if kind == "登录模板":
        items.append(canvas.create_rectangle(left, top, right, bottom, fill="#1A2538", outline="#354D70", width=1, tags=tags))
        line_h = max(16, int((bottom - top) * 0.18))
        items.append(canvas.create_rectangle(left + 10, top + 28, right - 10, top + 28 + line_h, fill="#0E1726", outline="#48658C", width=1, tags=tags))
        items.append(canvas.create_rectangle(left + 10, top + 28 + line_h + 8, right - 10, top + 28 + line_h * 2 + 8, fill="#0E1726", outline="#48658C", width=1, tags=tags))
        items.append(canvas.create_rectangle(left + 10, bottom - line_h - 10, right - 10, bottom - 10, fill="#1E71B8", outline="#5FB2FF", width=1, tags=tags))
        items.append(canvas.create_text(left + 12, top + 10, text=label, fill="#DCE8F7", anchor="nw", font=("Microsoft YaHei", 9, "bold"), tags=tags))
        return items

    if kind == "列表模板":
        items.append(canvas.create_rectangle(left, top, right, bottom, fill="#1A2538", outline="#354D70", width=1, tags=tags))
        head_h = max(20, int((bottom - top) * 0.18))
        items.append(canvas.create_rectangle(left + 10, top + 8, right - 86, top + 8 + head_h, fill="#0E1726", outline="#48658C", width=1, tags=tags))
        items.append(canvas.create_rectangle(right - 74, top + 8, right - 10, top + 8 + head_h, fill="#1E71B8", outline="#5FB2FF", width=1, tags=tags))
        table_top = top + head_h + 18
        items.append(canvas.create_rectangle(left + 10, table_top, right - 10, bottom - 10, fill="#111B2A", outline="#48658C", width=1, tags=tags))
        for row in range(1, 4):
            ly = table_top + int((bottom - 10 - table_top) * row / 4)
            items.append(canvas.create_line(left + 10, ly, right - 10, ly, fill="#344A67", width=1, tags=tags))
        items.append(canvas.create_text(left + 12, top + 10, text=label, fill="#DCE8F7", anchor="nw", font=("Microsoft YaHei", 9, "bold"), tags=tags))
        return items

    if kind in BUTTON_COMPONENT_KINDS:
        center_y = top + int((bottom - top) / 2)
        if kind == "复选框":
            box = max(12, min(18, bottom - top - 6))
            bx = left + 6
            by = center_y - int(box / 2)
            items.append(canvas.create_rectangle(bx, by, bx + box, by + box, fill="#0F1726", outline="#7FB1E8", width=1, tags=tags))
            items.append(canvas.create_line(bx + 3, by + int(box * 0.55), bx + int(box * 0.45), by + box - 3, fill="#8FD4FF", width=2, tags=tags))
            items.append(canvas.create_line(bx + int(box * 0.45), by + box - 3, bx + box - 2, by + 3, fill="#8FD4FF", width=2, tags=tags))
            items.append(canvas.create_text(bx + box + 8, center_y, text=label, fill="#E4F0FF", anchor="w", font=("Microsoft YaHei", 9), tags=tags))
            return items
        if kind == "单选按钮":
            r = max(6, min(9, int((bottom - top) / 3)))
            cx = left + 10 + r
            cy = center_y
            items.append(canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#0F1726", outline="#7FB1E8", width=1, tags=tags))
            items.append(canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill="#8FD4FF", outline="#8FD4FF", width=1, tags=tags))
            items.append(canvas.create_text(cx + r + 8, center_y, text=label, fill="#E4F0FF", anchor="w", font=("Microsoft YaHei", 9), tags=tags))
            return items
        items.append(canvas.create_rectangle(left + 6, top + 6, right - 6, bottom - 6, fill="#1E71B8", outline="#67B9FF", width=1, tags=tags))
        items.append(canvas.create_text((left + right) / 2, (top + bottom) / 2, text=label, fill="#FFFFFF", anchor="c", font=("Microsoft YaHei", 9, "bold"), tags=tags))
        return items

    if kind in INPUT_COMPONENT_KINDS:
        if kind == "数值滑块":
            ly = top + int((bottom - top) / 2)
            items.append(canvas.create_line(left + 10, ly, right - 10, ly, fill="#84A7CF", width=3, tags=tags))
            knob_x = left + int((right - left) * 0.62)
            items.append(canvas.create_oval(knob_x - 6, ly - 6, knob_x + 6, ly + 6, fill="#5FB2FF", outline="#BCE4FF", width=1, tags=tags))
            items.append(canvas.create_text(left + 4, top + 2, text=label, fill="#CFDFF3", anchor="nw", font=("Microsoft YaHei", 8), tags=tags))
            return items

        if kind == "多行文本框":
            items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, bottom - 4, fill="#0E1726", outline="#4E6C93", width=1, tags=tags))
            for row in range(1, 4):
                ly = top + 8 + row * max(12, int((bottom - top - 16) / 4))
                items.append(canvas.create_line(left + 10, ly, right - 10, ly, fill="#2C3F5A", width=1, tags=tags))
            items.append(canvas.create_text(left + 10, top + 10, text=label, fill="#AFC4DD", anchor="nw", font=("Microsoft YaHei", 8), tags=tags))
            return items

        entry_h = max(18, min(28, bottom - top - 8))
        entry_y = top + int((bottom - top - entry_h) / 2)
        items.append(canvas.create_rectangle(left + 4, entry_y, right - 4, entry_y + entry_h, fill="#0E1726", outline="#4E6C93", width=1, tags=tags))
        items.append(canvas.create_text(left + 10, entry_y + int(entry_h / 2), text=label, fill="#AFC4DD", anchor="w", font=("Microsoft YaHei", 8), tags=tags))

        if kind == "组合框":
            arrow_w = max(18, min(24, int((right - left) * 0.18)))
            items.append(canvas.create_rectangle(right - 4 - arrow_w, entry_y, right - 4, entry_y + entry_h, fill="#1E2F47", outline="#4E6C93", width=1, tags=tags))
            cx = right - 4 - int(arrow_w / 2)
            cy = entry_y + int(entry_h / 2)
            items.append(canvas.create_polygon(cx - 4, cy - 2, cx + 4, cy - 2, cx, cy + 3, fill="#9DC8F5", outline="", tags=tags))
        elif kind == "日期选择器":
            icon_w = max(18, min(24, int((right - left) * 0.2)))
            items.append(canvas.create_rectangle(right - 4 - icon_w, entry_y, right - 4, entry_y + entry_h, fill="#1E2F47", outline="#4E6C93", width=1, tags=tags))
            ix = right - 4 - icon_w + 4
            iy = entry_y + 4
            items.append(canvas.create_rectangle(ix, iy, right - 8, entry_y + entry_h - 4, fill="#2A3C58", outline="#87B8EF", width=1, tags=tags))
            items.append(canvas.create_line(ix, iy + 5, right - 8, iy + 5, fill="#87B8EF", width=1, tags=tags))
        elif kind == "数值框":
            ctl_w = max(16, min(22, int((right - left) * 0.16)))
            items.append(canvas.create_rectangle(right - 4 - ctl_w, entry_y, right - 4, entry_y + int(entry_h / 2), fill="#1E2F47", outline="#4E6C93", width=1, tags=tags))
            items.append(canvas.create_rectangle(right - 4 - ctl_w, entry_y + int(entry_h / 2), right - 4, entry_y + entry_h, fill="#1E2F47", outline="#4E6C93", width=1, tags=tags))
            cx = right - 4 - int(ctl_w / 2)
            items.append(canvas.create_polygon(cx - 3, entry_y + int(entry_h / 4) + 2, cx + 3, entry_y + int(entry_h / 4) + 2, cx, entry_y + int(entry_h / 4) - 2, fill="#9DC8F5", outline="", tags=tags))
            items.append(canvas.create_polygon(cx - 3, entry_y + int(entry_h * 3 / 4) - 2, cx + 3, entry_y + int(entry_h * 3 / 4) - 2, cx, entry_y + int(entry_h * 3 / 4) + 2, fill="#9DC8F5", outline="", tags=tags))
        return items

    if kind in TABLE_COMPONENT_KINDS:
        table_left = left + 4
        table_top = top + 4
        table_right = right - 4
        table_bottom = bottom - 4
        header_h = max(18, min(24, int((table_bottom - table_top) * 0.2)))
        items.append(canvas.create_rectangle(table_left, table_top, table_right, table_bottom, fill="#111B2A", outline="#48658C", width=1, tags=tags))
        items.append(canvas.create_rectangle(table_left, table_top, table_right, table_top + header_h, fill="#24384F", outline="#48658C", width=1, tags=tags))
        col_count = 1 if kind == "列表框" else 3
        for c in range(1, col_count):
            lx = table_left + int((table_right - table_left) * c / col_count)
            items.append(canvas.create_line(lx, table_top, lx, table_bottom, fill="#35506F", width=1, tags=tags))
        row_count = 4
        for r in range(1, row_count):
            ly = table_top + header_h + int((table_bottom - table_top - header_h) * r / row_count)
            items.append(canvas.create_line(table_left, ly, table_right, ly, fill="#2E445F", width=1, tags=tags))
        if kind == "树形视图":
            base_y = table_top + header_h + 8
            items.append(canvas.create_line(table_left + 12, base_y, table_left + 12, min(table_bottom - 8, base_y + 36), fill="#7AA9D6", width=1, tags=tags))
            items.append(canvas.create_line(table_left + 12, base_y + 12, table_left + 24, base_y + 12, fill="#7AA9D6", width=1, tags=tags))
            items.append(canvas.create_line(table_left + 12, base_y + 24, table_left + 24, base_y + 24, fill="#7AA9D6", width=1, tags=tags))
        return items

    if kind in CARD_COMPONENT_KINDS:
        if kind == "进度条":
            track_h = max(12, min(16, int((bottom - top) * 0.28)))
            ly = top + int((bottom - top - track_h) / 2)
            items.append(canvas.create_rectangle(left + 4, ly, right - 4, ly + track_h, fill="#0F1726", outline="#55779F", width=1, tags=tags))
            fill_w = max(20, int((right - left - 10) * 0.55))
            items.append(canvas.create_rectangle(left + 5, ly + 1, left + 5 + fill_w, ly + track_h - 1, fill="#2F7FE3", outline="#2F7FE3", width=1, tags=tags))
            items.append(canvas.create_text((left + right) / 2, ly + int(track_h / 2), text=label, fill="#E4F0FF", anchor="c", font=("Microsoft YaHei", 8), tags=tags))
            return items

        if kind == "图片框":
            items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, bottom - 4, fill="#0E1726", outline="#4E6C93", width=1, tags=tags))
            items.append(canvas.create_line(left + 8, bottom - 8, right - 8, top + 8, fill="#8AB8E8", width=1, tags=tags))
            items.append(canvas.create_line(left + 8, top + 8, right - 8, bottom - 8, fill="#8AB8E8", width=1, tags=tags))
            items.append(canvas.create_text((left + right) / 2, bottom - 14, text=label, fill="#AFC4DD", anchor="c", font=("Microsoft YaHei", 8), tags=tags))
            return items

        if kind == "分组框":
            group_top = top + 10
            items.append(canvas.create_rectangle(left + 4, group_top, right - 4, bottom - 4, fill="#142236", outline="#4E6C93", width=1, tags=tags))
            items.append(canvas.create_text(left + 12, top + 6, text=label, fill="#9FC7F3", anchor="w", font=("Microsoft YaHei", 8, "bold"), tags=tags))
            return items

        if kind == "选项卡":
            tab_h = max(16, min(22, int((bottom - top) * 0.22)))
            items.append(canvas.create_rectangle(left + 4, top + tab_h + 2, right - 4, bottom - 4, fill="#111B2A", outline="#4E6C93", width=1, tags=tags))
            items.append(canvas.create_rectangle(left + 8, top + 4, left + 70, top + tab_h, fill="#2B4362", outline="#6DAEE8", width=1, tags=tags))
            items.append(canvas.create_rectangle(left + 72, top + 6, left + 132, top + tab_h, fill="#1A2A40", outline="#4E6C93", width=1, tags=tags))
            items.append(canvas.create_text(left + 14, top + int(tab_h / 2) + 1, text="选项1", fill="#E4F0FF", anchor="w", font=("Microsoft YaHei", 8), tags=tags))
            items.append(canvas.create_text(left + 78, top + int(tab_h / 2) + 1, text="选项2", fill="#9FB4CF", anchor="w", font=("Microsoft YaHei", 8), tags=tags))
            return items

        if kind == "分割容器":
            items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, bottom - 4, fill="#111B2A", outline="#4E6C93", width=1, tags=tags))
            mid = left + int((right - left) / 2)
            items.append(canvas.create_line(mid, top + 8, mid, bottom - 8, fill="#6DAEE8", width=2, tags=tags))
            items.append(canvas.create_text(left + 12, top + 10, text=label, fill="#AFC4DD", anchor="nw", font=("Microsoft YaHei", 8), tags=tags))
            return items

        if kind == "表格布局面板":
            items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, bottom - 4, fill="#111B2A", outline="#4E6C93", width=1, tags=tags))
            for c in range(1, 4):
                lx = left + 4 + int((right - left - 8) * c / 4)
                items.append(canvas.create_line(lx, top + 4, lx, bottom - 4, fill="#38516F", width=1, tags=tags))
            for r in range(1, 3):
                ly = top + 4 + int((bottom - top - 8) * r / 3)
                items.append(canvas.create_line(left + 4, ly, right - 4, ly, fill="#38516F", width=1, tags=tags))
            items.append(canvas.create_text(left + 10, top + 10, text=label, fill="#AFC4DD", anchor="nw", font=("Microsoft YaHei", 8), tags=tags))
            return items

        if kind == "流式布局面板":
            items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, bottom - 4, fill="#111B2A", outline="#4E6C93", width=1, tags=tags))
            chip_top = top + 10
            chip_x = left + 10
            for idx in range(4):
                chip_w = 40 + (idx % 2) * 16
                if chip_x + chip_w > right - 10:
                    chip_x = left + 10
                    chip_top += 20
                items.append(canvas.create_rectangle(chip_x, chip_top, chip_x + chip_w, chip_top + 14, fill="#2A4361", outline="#6FAEE6", width=1, tags=tags))
                chip_x += chip_w + 8
            items.append(canvas.create_text(left + 10, top + 10, text=label, fill="#AFC4DD", anchor="nw", font=("Microsoft YaHei", 8), tags=tags))
            return items

        items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, bottom - 4, fill="#162338", outline="#4E6C93", width=1, tags=tags))
        items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, top + 24, fill="#23374F", outline="#4E6C93", width=1, tags=tags))
        items.append(canvas.create_text(left + 10, top + 14, text=label, fill="#DCE8F7", anchor="w", font=("Microsoft YaHei", 8, "bold"), tags=tags))
        return items

    if kind in TEXT_COMPONENT_KINDS:
        if kind == "菜单栏":
            items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, top + 24, fill="#203247", outline="#48658C", width=1, tags=tags))
            items.append(canvas.create_text(left + 10, top + 14, text=label, fill="#E4F0FF", anchor="w", font=("Microsoft YaHei", 8), tags=tags))
            return items
        if kind == "工具栏":
            items.append(canvas.create_rectangle(left + 4, top + 4, right - 4, top + 26, fill="#1D2D44", outline="#48658C", width=1, tags=tags))
            ix = left + 10
            for _ in range(5):
                items.append(canvas.create_rectangle(ix, top + 9, ix + 10, top + 19, fill="#7FAEDA", outline="#9DCAEF", width=1, tags=tags))
                ix += 16
            return items
        if kind == "状态栏":
            bar_h = max(16, min(22, int((bottom - top) * 0.4)))
            items.append(canvas.create_rectangle(left + 4, bottom - bar_h - 4, right - 4, bottom - 4, fill="#1D2D44", outline="#48658C", width=1, tags=tags))
            items.append(canvas.create_text(left + 10, bottom - int(bar_h / 2) - 4, text=label, fill="#BBD4EF", anchor="w", font=("Microsoft YaHei", 8), tags=tags))
            return items
        items.append(canvas.create_text(left + 4, top + int((bottom - top) / 2), text=label, fill=colors["text"], anchor="w", font=("Microsoft YaHei", 10), tags=tags))
        return items

    items.append(canvas.create_text(left + 4, top + int((bottom - top) / 2), text=label, fill=colors["text"], anchor="w", font=("Microsoft YaHei", 9), tags=tags))
    return items


def _render_canvas(owner):
    _ensure_component_baseline(owner)
    canvas = getattr(owner, "_ui_designer_canvas", None)
    if canvas is None:
        return
    _draw_grid(owner)
    canvas.delete("component")
    selected_uid = getattr(owner, "_ui_designer_selected_uid", None)

    components = list(getattr(owner, "_ui_designer_components", []) or [])
    mode = str(getattr(owner, "_ui_designer_mode", "novice"))
    pro_clean = bool(getattr(owner, "_ui_designer_professional_clean_render", True))
    simplify = (mode == "novice") or (mode == "pro" and pro_clean)
    components.sort(
        key=lambda item: (
            0 if str(item.get("kind", "")) == WINDOW_COMPONENT_KIND else 1,
            _to_int(item.get("y", 0), 0),
            _to_int(item.get("x", 0), 0),
            _to_int(item.get("uid", 0), 0),
        )
    )

    for comp in components:
        uid = int(comp.get("uid", 0))
        tag = f"comp_{uid}"
        x = _clamp(_to_int(comp.get("x", 0), 0), 0, CANVAS_REGION_W - 20)
        y = _clamp(_to_int(comp.get("y", 0), 0), 0, CANVAS_REGION_H - 20)
        kind = str(comp.get("kind", "文字"))
        min_w = 360 if kind == WINDOW_COMPONENT_KIND else 60
        min_h = 240 if kind == WINDOW_COMPONENT_KIND else 24
        w = _clamp(_to_int(comp.get("w", 180), 180), min_w, CANVAS_REGION_W)
        h = _clamp(_to_int(comp.get("h", 36), 36), min_h, CANVAS_REGION_H)
        x2 = min(CANVAS_REGION_W, x + w)
        y2 = min(CANVAS_REGION_H, y + h)
        text = str(comp.get("text", "")).strip() or kind
        colors = _component_colors(kind)
        selected = uid == selected_uid
        outline = "#4CA8FF" if selected else "#3B4C62"
        border_w = 2 if selected else 1

        rect_id = canvas.create_rectangle(
            x,
            y,
            x2,
            y2,
            fill=colors["fill"],
            outline=outline,
            width=border_w,
            tags=("component", tag),
        )
        preview_item_ids = _draw_component_preview(canvas, kind, x, y, x2, y2, text, colors, tag, simplify=simplify)
        bind_item_ids = [rect_id]
        if selected and (not simplify):
            badge_text = f"{kind} · {str(comp.get('name', f'控件{uid}'))}"
            chip_y = max(8, y - 10)
            chip = canvas.create_text(
                x + 8,
                chip_y,
                text=badge_text,
                fill="#8FC5FF",
                anchor="nw",
                font=("Microsoft YaHei", 8, "bold"),
                tags=("component", tag),
            )
            bind_item_ids.append(chip)
        bind_item_ids.extend(list(preview_item_ids or []))
        for item_id in bind_item_ids:
            canvas.tag_bind(item_id, "<ButtonPress-1>", lambda e, target_uid=uid: _on_canvas_press(owner, e, target_uid))
            canvas.tag_bind(item_id, "<B1-Motion>", lambda e, target_uid=uid: _on_canvas_drag(owner, e, target_uid))
            canvas.tag_bind(item_id, "<ButtonRelease-1>", lambda e: _on_canvas_release(owner, e))

        # 选中组件显示缩放手柄：拖拽手柄可直接改宽高。
        if selected:
            hs = CANVAS_RESIZE_HANDLE
            handles = [
                ("nw", x, y),
                ("ne", x2, y),
                ("sw", x, y2),
                ("se", x2, y2),
            ]
            for anchor, hx, hy in handles:
                handle_id = canvas.create_rectangle(
                    hx - hs,
                    hy - hs,
                    hx + hs,
                    hy + hs,
                    fill="#4CA8FF",
                    outline="#BFE3FF",
                    width=1,
                    tags=("component", tag, "resize_handle"),
                )
                canvas.tag_bind(
                    handle_id,
                    "<ButtonPress-1>",
                    lambda e, target_uid=uid, target_anchor=anchor: _on_resize_press(owner, e, target_uid, target_anchor),
                )
                canvas.tag_bind(handle_id, "<B1-Motion>", lambda e, target_uid=uid: _on_resize_drag(owner, e, target_uid))
                canvas.tag_bind(handle_id, "<ButtonRelease-1>", lambda e: _on_canvas_release(owner, e))


def _refresh_property_panel(owner):
    _ensure_component_baseline(owner)
    comp = _selected_component(owner)
    info_var = getattr(owner, "_ui_designer_info_var", None)
    vars_map = getattr(owner, "_ui_designer_prop_vars", None)
    if info_var is None or not isinstance(vars_map, dict):
        return
    if comp is None:
        info_var.set("未选中组件")
        for key in (
            "name", "kind", "text", "scroll_mode", "button_style", "card_border",
            "event", "action_text", "columns", "column_count", "rows", "x", "y", "w", "h",
        ):
            if key in vars_map:
                vars_map[key].set("")
        _set_property_hint_text(owner, "先选中组件，再填写高亮字段。灰色字段表示当前组件不需要。")
        _apply_property_field_state(owner, None)
        return

    kind = str(comp.get("kind", ""))
    info_var.set(f"已选中：{comp.get('name', '')} ({kind})")
    vars_map["name"].set(str(comp.get("name", "")))
    vars_map["kind"].set(kind)
    vars_map["text"].set(str(comp.get("text", "")))
    if "scroll_mode" in vars_map:
        vars_map["scroll_mode"].set(_normalize_window_scroll_mode(comp.get("scroll_mode", "自动")))
    if "button_style" in vars_map:
        vars_map["button_style"].set(_normalize_button_style(comp.get("button_style", "主按钮")))
    if "card_border" in vars_map:
        vars_map["card_border"].set(_normalize_card_border(comp.get("card_border", "显示")))
    vars_map["event"].set(str(comp.get("event", "")))
    if "action_text" in vars_map:
        vars_map["action_text"].set(str(comp.get("action_text", "")))
    normalized_cols = _normalize_columns(comp.get("columns", ""))
    vars_map["columns"].set(",".join(normalized_cols))
    if "column_count" in vars_map:
        vars_map["column_count"].set(str(max(1, _to_int(comp.get("column_count", len(normalized_cols)), len(normalized_cols) or 1))))
    vars_map["rows"].set(str(comp.get("rows", 8)))
    vars_map["x"].set(str(comp.get("x", 0)))
    vars_map["y"].set(str(comp.get("y", 0)))
    vars_map["w"].set(str(comp.get("w", 180)))
    vars_map["h"].set(str(comp.get("h", 36)))
    _set_property_hint_text(owner, PROPERTY_HINT_BY_KIND.get(kind, PROPERTY_HINT_BY_KIND["default"]))
    _apply_property_field_state(owner, kind)


def _select_component(owner, uid):
    selected_uid = _to_int(uid, -1)
    if selected_uid < 0:
        return
    owner._ui_designer_selected_uid = selected_uid
    _render_canvas(owner)
    _refresh_property_panel(owner)


def _on_canvas_press(owner, event, uid):
    canvas = getattr(owner, "_ui_designer_canvas", None)
    if canvas is None:
        return "break"
    target_uid = _to_int(uid, -1)
    if target_uid < 0:
        return "break"
    cx = _to_int(canvas.canvasx(event.x), 0)
    cy = _to_int(canvas.canvasy(event.y), 0)
    owner._ui_designer_resize = {
        "uid": None,
        "anchor": "",
        "start_x": 0,
        "start_y": 0,
        "x": 0,
        "y": 0,
        "w": 0,
        "h": 0,
    }
    owner._ui_designer_drag = {"uid": target_uid, "start_x": cx, "start_y": cy}
    owner._ui_designer_selected_uid = target_uid
    _refresh_property_panel(owner)
    return "break"


def _component_min_size(kind):
    if str(kind or "") == WINDOW_COMPONENT_KIND:
        return 360, 240
    return 60, 24


def _on_resize_press(owner, event, uid, anchor):
    canvas = getattr(owner, "_ui_designer_canvas", None)
    comp = _find_component(owner, uid)
    if canvas is None or comp is None:
        return "break"
    target_uid = _to_int(uid, -1)
    if target_uid < 0:
        return "break"
    cx = _to_int(canvas.canvasx(event.x), 0)
    cy = _to_int(canvas.canvasy(event.y), 0)
    owner._ui_designer_drag = {"uid": None, "start_x": 0, "start_y": 0}
    owner._ui_designer_resize = {
        "uid": target_uid,
        "anchor": str(anchor or "se"),
        "start_x": cx,
        "start_y": cy,
        "x": _to_int(comp.get("x", 0), 0),
        "y": _to_int(comp.get("y", 0), 0),
        "w": _to_int(comp.get("w", 180), 180),
        "h": _to_int(comp.get("h", 36), 36),
    }
    owner._ui_designer_selected_uid = target_uid
    _refresh_property_panel(owner)
    return "break"


def _on_resize_drag(owner, event, uid):
    canvas = getattr(owner, "_ui_designer_canvas", None)
    comp = _find_component(owner, uid)
    resize = getattr(owner, "_ui_designer_resize", {}) or {}
    target_uid = _to_int(uid, -1)
    resize_uid = _to_int(resize.get("uid", -1), -1)
    if canvas is None or comp is None or target_uid < 0 or resize_uid != target_uid:
        return "break"

    cx = _to_int(canvas.canvasx(event.x), resize.get("start_x", 0))
    cy = _to_int(canvas.canvasy(event.y), resize.get("start_y", 0))
    dx = cx - _to_int(resize.get("start_x", cx), cx)
    dy = cy - _to_int(resize.get("start_y", cy), cy)

    left0 = _to_int(resize.get("x", 0), 0)
    top0 = _to_int(resize.get("y", 0), 0)
    right0 = left0 + max(20, _to_int(resize.get("w", 180), 180))
    bottom0 = top0 + max(20, _to_int(resize.get("h", 36), 36))
    min_w, min_h = _component_min_size(comp.get("kind", ""))
    anchor = str(resize.get("anchor", "se") or "se")

    left = left0
    right = right0
    top = top0
    bottom = bottom0
    if "w" in anchor:
        left = _clamp(left0 + dx, 0, right0 - min_w)
    if "e" in anchor:
        right = _clamp(right0 + dx, left + min_w, CANVAS_REGION_W)
    if "n" in anchor:
        top = _clamp(top0 + dy, 0, bottom0 - min_h)
    if "s" in anchor:
        bottom = _clamp(bottom0 + dy, top + min_h, CANVAS_REGION_H)

    comp["x"] = _clamp(left, 0, CANVAS_REGION_W - min_w)
    comp["y"] = _clamp(top, 0, CANVAS_REGION_H - min_h)
    comp["w"] = _clamp(right - left, min_w, CANVAS_REGION_W)
    comp["h"] = _clamp(bottom - top, min_h, CANVAS_REGION_H)

    max_x = max(0, CANVAS_REGION_W - _to_int(comp.get("w", min_w), min_w))
    max_y = max(0, CANVAS_REGION_H - _to_int(comp.get("h", min_h), min_h))
    comp["x"] = _clamp(_to_int(comp.get("x", 0), 0), 0, max_x)
    comp["y"] = _clamp(_to_int(comp.get("y", 0), 0), 0, max_y)

    _render_canvas(owner)
    _refresh_property_panel(owner)
    return "break"


def _on_canvas_drag(owner, event, uid):
    canvas = getattr(owner, "_ui_designer_canvas", None)
    comp = _find_component(owner, uid)
    drag = getattr(owner, "_ui_designer_drag", {}) or {}
    resize = getattr(owner, "_ui_designer_resize", {}) or {}
    target_uid = _to_int(uid, -1)
    drag_uid = _to_int(drag.get("uid", -1), -1)
    resize_uid = _to_int(resize.get("uid", -1), -1)
    if canvas is None or comp is None or target_uid < 0 or drag_uid != target_uid or resize_uid == target_uid:
        return "break"
    cx = _to_int(canvas.canvasx(event.x), comp.get("x", 0))
    cy = _to_int(canvas.canvasy(event.y), comp.get("y", 0))
    dx = cx - _to_int(drag.get("start_x", cx), cx)
    dy = cy - _to_int(drag.get("start_y", cy), cy)
    comp_w = max(20, _to_int(comp.get("w", 180), 180))
    comp_h = max(20, _to_int(comp.get("h", 36), 36))
    max_x = max(0, CANVAS_REGION_W - comp_w)
    max_y = max(0, CANVAS_REGION_H - comp_h)
    comp["x"] = _clamp(_to_int(comp.get("x", 0)) + dx, 0, max_x)
    comp["y"] = _clamp(_to_int(comp.get("y", 0)) + dy, 0, max_y)
    owner._ui_designer_drag = {"uid": target_uid, "start_x": cx, "start_y": cy}
    _render_canvas(owner)
    _refresh_property_panel(owner)
    return "break"


def _on_canvas_background_press(owner, event=None):
    canvas = getattr(owner, "_ui_designer_canvas", None)
    if canvas is None:
        return None
    drag = getattr(owner, "_ui_designer_drag", {}) or {}
    resize = getattr(owner, "_ui_designer_resize", {}) or {}
    if _to_int(drag.get("uid", -1), -1) >= 0 or _to_int(resize.get("uid", -1), -1) >= 0:
        return None
    if event is not None:
        current = canvas.find_withtag("current")
        if current:
            try:
                tags = set(canvas.gettags(current[0]))
            except tk.TclError:
                tags = set()
            if "component" in tags or "resize_handle" in tags:
                # 让组件自身的按下/拖拽绑定继续处理，不在这里拦截。
                return None
    _on_canvas_release(owner, event)
    return None


def _focus_first_action_component(owner):
    _ensure_component_baseline(owner)
    for comp in list(getattr(owner, "_ui_designer_components", []) or []):
        kind = str(comp.get("kind", ""))
        if kind in BUTTON_COMPONENT_KINDS or kind in {"登录模板", "列表模板"}:
            _select_component(owner, comp.get("uid"))
            return True
    return False


def _novice_focus_action_step(owner):
    step = int(getattr(owner, "_ui_designer_step", 1) or 1)
    if step < 2:
        _set_designer_step(owner, 1, "请先选择模板或添加按钮组件，再进行动作绑定。")
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("界面设计器：请先完成第 1 步（选择模板）")
        return "break"

    ok = _focus_first_action_component(owner)
    if ok:
        comp = _selected_component(owner)
        _set_designer_step(owner, 3, "请在右侧填写函数名，再点应用属性。")
        widgets = getattr(owner, "_ui_designer_prop_widgets", {}) or {}
        event_entry = None
        if isinstance(widgets, dict):
            meta = widgets.get("event")
            if isinstance(meta, dict):
                event_entry = meta.get("entry")
        if event_entry is not None:
            try:
                event_entry.focus_set()
                event_entry.selection_range(0, tk.END)
                event_entry.icursor(tk.END)
            except tk.TclError:
                pass
        if hasattr(owner, "status_main_var"):
            name = str((comp or {}).get("name", "按钮"))
            owner.status_main_var.set(f"界面设计器：已定位到 {name}，请在右侧“函数”中填写动作名")
    elif hasattr(owner, "status_main_var"):
        owner.status_main_var.set("界面设计器：当前页面还没有可绑定动作的按钮，已为你自动添加一个按钮")
        _add_component(owner, "按钮")
        _set_designer_step(owner, 3, "请在右侧填写函数名，再点应用属性。")
    return "break"


def _novice_add_component(owner):
    step = int(getattr(owner, "_ui_designer_step", 1) or 1)
    if step < 2:
        _set_designer_step(owner, 1, "请先选择模板，再继续添加组件。")
        return "break"
    return _add_component(owner)


def _novice_export(owner):
    step = int(getattr(owner, "_ui_designer_step", 1) or 1)
    if step < 3:
        _set_designer_step(owner, 3, "请先绑定关键动作，再导出到编辑区。")
        return "break"
    return export_ui_design_to_editor(owner)


def _run_preview_from_designer(owner):
    if str(getattr(owner, "_ui_designer_mode", "novice")) == "novice":
        step = int(getattr(owner, "_ui_designer_step", 1) or 1)
        if step < 3:
            _set_designer_step(owner, 3, "请先绑定关键动作，再运行预览。")
            return "break"
    export_ui_design_to_editor(owner)
    selected = _select_code_tab_by_filename(owner, "界面设计导出.ym")
    runner = getattr(owner, "run_code", None)
    if callable(runner) and selected:
        return runner()
    # 兜底：当编辑区标签无法被选中时，直接运行设计器导出的代码，避免“无输出且无窗口组件”的静默失败。
    return _run_preview_direct_from_designer(owner)


def _run_preview_direct_from_designer(owner):
    code = _generate_ym_code(owner)
    clear_console = getattr(owner, "_clear_output_console", None)
    if callable(clear_console):
        try:
            clear_console(keep_intro=True)
        except Exception:
            pass

    output_str = ""
    try:
        import io
        import sys
        from 易码 import 执行源码

        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            执行源码(code, interactive=False, 源码路径=None)
            output_str = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
    except Exception as e:
        output_str = f"❌ 运行报错了: {e}"

    if not str(output_str).strip():
        output_str = "代码已执行完成，但没有输出。可使用【显示】语句输出结果。"
    printer = getattr(owner, "print_output", None)
    if callable(printer):
        try:
            printer(output_str, is_error=str(output_str).startswith("❌"))
        except Exception:
            pass
    if hasattr(owner, "status_main_var"):
        try:
            owner.status_main_var.set("运行完成" if not str(output_str).startswith("❌") else "运行失败")
        except Exception:
            pass
    return "break"


def _export_software_from_designer(owner):
    if str(getattr(owner, "_ui_designer_mode", "novice")) == "novice":
        step = int(getattr(owner, "_ui_designer_step", 1) or 1)
        if step < 3:
            _set_designer_step(owner, 3, "请先绑定关键动作，再导出软件。")
            return "break"
    export_ui_design_to_editor(owner)
    exporter = getattr(owner, "export_exe", None)
    if callable(exporter):
        return exporter()
    return "break"


def _on_canvas_motion(owner, event=None):
    drag = getattr(owner, "_ui_designer_drag", {}) or {}
    resize = getattr(owner, "_ui_designer_resize", {}) or {}
    resize_uid = _to_int(resize.get("uid", -1), -1)
    if resize_uid >= 0:
        return _on_resize_drag(owner, event, resize_uid)
    drag_uid = _to_int(drag.get("uid", -1), -1)
    if drag_uid >= 0:
        return _on_canvas_drag(owner, event, drag_uid)
    return None


def _on_canvas_release(owner, event=None):
    del event
    owner._ui_designer_drag = {"uid": None, "start_x": 0, "start_y": 0}
    owner._ui_designer_resize = {
        "uid": None,
        "anchor": "",
        "start_x": 0,
        "start_y": 0,
        "x": 0,
        "y": 0,
        "w": 0,
        "h": 0,
    }
    return "break"


def _selected_palette_kind(owner, fallback="文字"):
    palette = getattr(owner, "_ui_designer_palette", None)
    if palette is None:
        return str(fallback or "文字")

    if isinstance(palette, tk.Listbox):
        try:
            selection = palette.curselection()
            if selection:
                idx = int(selection[0])
                list_kinds = list(getattr(owner, "_ui_designer_palette_list_kinds", []) or [])
                if 0 <= idx < len(list_kinds):
                    kind = str(list_kinds[idx])
                    if kind in COMPONENT_KIND_SET:
                        return kind
        except Exception:
            pass
        return str(fallback or "文字")

    kind_map = getattr(owner, "_ui_designer_palette_kind_map", {}) or {}
    if isinstance(palette, ttk.Treeview):
        for item_id in list(palette.selection()):
            kind = str(kind_map.get(item_id, ""))
            if kind in COMPONENT_KIND_SET:
                return kind
            for child_id in palette.get_children(item_id):
                child_kind = str(kind_map.get(child_id, ""))
                if child_kind in COMPONENT_KIND_SET:
                    return child_kind
        for group_id in palette.get_children(""):
            for child_id in palette.get_children(group_id):
                child_kind = str(kind_map.get(child_id, ""))
                if child_kind in COMPONENT_KIND_SET:
                    return child_kind
    return str(fallback or "文字")


def _build_palette_tree(owner, parent):
    theme_bg = getattr(owner, "theme_panel_inner_bg", "#18212F")
    theme_fg = getattr(owner, "theme_fg", "#DCE7F5")
    theme_muted = getattr(owner, "theme_toolbar_muted", "#8FA1B8")
    theme_accent = getattr(owner, "theme_accent", "#2F7FE3")
    theme_border = getattr(owner, "theme_toolbar_border", "#2A3A4F")
    style_name = f"YimaUiPalette{id(parent)}.Treeview"
    style = ttk.Style(parent)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    dpi_scale = float(getattr(owner, "dpi_scale", 1.0) or 1.0)
    _panel_w, _panel_min, tree_col_width = _calc_palette_width(owner)
    ui_font = tkfont.Font(family="Microsoft YaHei", size=9)
    row_h = max(28, int(ui_font.metrics("linespace") + 10), int(26 * dpi_scale))
    style.configure(
        style_name,
        background=theme_bg,
        fieldbackground=theme_bg,
        foreground=theme_fg,
        borderwidth=0,
        rowheight=row_h,
        relief="flat",
        font=ui_font,
    )
    style.map(
        style_name,
        background=[("selected", theme_accent)],
        foreground=[("selected", "#FFFFFF")],
    )

    search_row = tk.Frame(parent, bg=owner.theme_panel_bg)
    search_row.pack(fill=tk.X, pady=(0, 6))
    tk.Label(
        search_row,
        text="搜索",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg=theme_muted,
        anchor="w",
    ).pack(side=tk.LEFT)
    query_var = tk.StringVar(value="")
    query_entry = tk.Entry(
        search_row,
        textvariable=query_var,
        font=("Microsoft YaHei", 8),
        bg=theme_bg,
        fg=theme_fg,
        insertbackground=theme_fg,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground=theme_border,
        highlightcolor=theme_accent,
        width=16,
    )
    query_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0), ipady=3)

    palette_wrap = tk.Frame(parent, bg=owner.theme_panel_bg)
    palette_wrap.pack(fill=tk.BOTH, expand=True, pady=(2, 0))

    palette = ttk.Treeview(
        palette_wrap,
        show="tree",
        selectmode="browse",
        style=style_name,
        height=10,
    )
    try:
        min_col = max(260, int(tree_col_width * 0.8))
        palette.column("#0", width=tree_col_width, minwidth=min_col, stretch=True)
    except Exception:
        pass
    palette_vsb = ttk.Scrollbar(palette_wrap, orient="vertical", command=palette.yview)
    palette.configure(yscrollcommand=palette_vsb.set)
    palette.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    palette_vsb.pack(side=tk.RIGHT, fill=tk.Y)

    kind_map = {}

    def _populate(filter_text: str = ""):
        nonlocal kind_map
        kind_map = {}
        for node in palette.get_children(""):
            palette.delete(node)

        needle = str(filter_text or "").strip().lower()
        first_child = None
        for group_name, kind_list in COMPONENT_PALETTE_GROUPS:
            valid_kinds = [kind for kind in kind_list if kind in COMPONENT_KIND_SET]
            if needle:
                valid_kinds = [k for k in valid_kinds if needle in str(k).lower()]
            if not valid_kinds:
                continue
            group_id = palette.insert("", tk.END, text=f"{group_name} ({len(valid_kinds)})", open=bool(needle))
            for kind in valid_kinds:
                child_id = palette.insert(group_id, tk.END, text=str(kind))
                kind_map[child_id] = kind
                if first_child is None:
                    first_child = child_id

        owner._ui_designer_palette_kind_map = dict(kind_map)

        if first_child is not None:
            try:
                palette.selection_set(first_child)
                palette.focus(first_child)
            except tk.TclError:
                pass

    _populate("")

    def _on_tree_double_click(event=None):
        del event
        focus_id = palette.focus()
        if focus_id and focus_id not in kind_map:
            try:
                is_open = bool(palette.item(focus_id, "open"))
                palette.item(focus_id, open=not is_open)
                return "break"
            except tk.TclError:
                return "break"
        selected_kind = _selected_palette_kind(owner)
        if selected_kind in COMPONENT_KIND_SET:
            return _add_component(owner, selected_kind)
        return "break"

    def _on_tree_return(event=None):
        del event
        selected_kind = _selected_palette_kind(owner)
        if selected_kind in COMPONENT_KIND_SET:
            return _add_component(owner, selected_kind)
        return "break"

    palette.bind("<Double-Button-1>", _on_tree_double_click, add="+")
    palette.bind("<Return>", _on_tree_return, add="+")
    palette.bind("<KP_Enter>", _on_tree_return, add="+")

    try:
        # 避免某些主题下分组项文字过淡，附加轻量颜色标签。
        for group_id in palette.get_children(""):
            palette.item(group_id, tags=("group",))
        palette.tag_configure("group", foreground=theme_muted)
    except Exception:
        pass

    def _on_query_change(*_args):
        _populate(query_var.get())
        try:
            for group_id in palette.get_children(""):
                palette.item(group_id, tags=("group",))
        except Exception:
            pass

    query_var.trace_add("write", _on_query_change)
    owner._ui_designer_pro_palette_query_var = query_var
    owner._ui_designer_pro_palette_query_entry = query_entry

    return palette


def _build_recommended_palette(owner, parent):
    wrap = tk.Frame(parent, bg=owner.theme_panel_bg)
    wrap.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        wrap,
        text="推荐组件",
        font=("Microsoft YaHei", 8, "bold"),
        bg=owner.theme_panel_bg,
        fg="#9FB0C5",
        anchor="w",
        padx=2,
        pady=4,
    ).pack(fill=tk.X)

    list_wrap = tk.Frame(wrap, bg=owner.theme_panel_bg)
    list_wrap.pack(fill=tk.BOTH, expand=True)
    lst = tk.Listbox(
        list_wrap,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_inner_bg,
        fg=owner.theme_fg,
        selectbackground=owner.theme_accent,
        selectforeground="#FFFFFF",
        activestyle="none",
        relief="flat",
        borderwidth=0,
        highlightthickness=1,
        highlightbackground=owner.theme_toolbar_border,
        highlightcolor=owner.theme_accent,
    )
    sb = ttk.Scrollbar(list_wrap, orient="vertical", command=lst.yview)
    lst.configure(yscrollcommand=sb.set)
    lst.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)

    def _on_double(_event=None):
        kind = _selected_palette_kind(owner)
        if kind in COMPONENT_KIND_SET:
            return _add_component(owner, kind)
        return "break"

    lst.bind("<Double-Button-1>", _on_double, add="+")
    lst.bind("<Return>", _on_double, add="+")
    lst.bind("<KP_Enter>", _on_double, add="+")

    owner._ui_designer_palette_recommended = lst
    owner._ui_designer_palette_list_kinds = []
    _refresh_recommended_palette(owner)
    return wrap, lst


def _add_component(owner, kind=None):
    _ensure_component_baseline(owner)
    if kind not in COMPONENT_KIND_SET:
        kind = _selected_palette_kind(owner, fallback="文字")

    if kind in COMPONENT_SINGLETON_KINDS:
        exists = _find_first_component_by_kind(owner, kind)
        if exists is not None:
            _select_component(owner, exists.get("uid", 0))
            if hasattr(owner, "status_main_var"):
                owner.status_main_var.set(f"界面设计器：{kind} 组件只允许一个，已定位到现有组件")
            return "break"

    offset = len(owner._ui_designer_components) * 16
    if kind == WINDOW_COMPONENT_KIND:
        comp = _new_component(owner, kind, x=48, y=40)
    else:
        comp = _new_component(owner, kind, x=120 + offset, y=90 + offset)
    owner._ui_designer_components.append(comp)
    _select_component(owner, comp["uid"])
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set(f"界面设计器：已添加组件 {kind}")
    _set_designer_step(owner, 2, "继续拖拽和微调组件位置，完成页面结构。")
    return "break"


def _delete_selected_component(owner):
    _ensure_component_baseline(owner)
    comp = _selected_component(owner)
    if comp is None:
        return "break"
    if str(comp.get("kind", "")) == WINDOW_COMPONENT_KIND:
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("界面设计器：窗口是必选组件，不能删除")
        return "break"
    owner._ui_designer_components = [item for item in owner._ui_designer_components if int(item.get("uid", -1)) != int(comp["uid"])]
    owner._ui_designer_selected_uid = None
    _ensure_window_component(owner)
    _render_canvas(owner)
    _refresh_property_panel(owner)
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set("界面设计器：已删除选中组件")
    return "break"


def _clear_components(owner):
    _ensure_component_baseline(owner)
    win_uid = None
    for item in list(owner._ui_designer_components):
        if str(item.get("kind", "")) == WINDOW_COMPONENT_KIND:
            win_uid = int(item.get("uid", 0))
            break
    owner._ui_designer_components = [item for item in owner._ui_designer_components if str(item.get("kind", "")) == WINDOW_COMPONENT_KIND]
    if not owner._ui_designer_components:
        win = _ensure_window_component(owner)
        win_uid = int(win.get("uid", 0))
    owner._ui_designer_selected_uid = win_uid
    _render_canvas(owner)
    _refresh_property_panel(owner)
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set("界面设计器：已清空页面组件，保留窗口")
    return "break"


def _apply_properties(owner):
    _ensure_component_baseline(owner)
    comp = _selected_component(owner)
    vars_map = getattr(owner, "_ui_designer_prop_vars", None)
    if comp is None or not isinstance(vars_map, dict):
        return "break"

    kind = str(comp.get("kind", ""))
    editable = _editable_property_keys(kind)

    if "text" in editable:
        comp["text"] = str(vars_map["text"].get() or "").strip()
    if "event" in editable:
        comp["event"] = str(vars_map["event"].get() or "").strip()
    if "scroll_mode" in editable and vars_map.get("scroll_mode") is not None:
        comp["scroll_mode"] = _normalize_window_scroll_mode(vars_map["scroll_mode"].get(), comp.get("scroll_mode", "自动"))
    if "button_style" in editable and vars_map.get("button_style") is not None:
        comp["button_style"] = _normalize_button_style(vars_map["button_style"].get(), comp.get("button_style", "主按钮"))
    if "card_border" in editable and vars_map.get("card_border") is not None:
        comp["card_border"] = _normalize_card_border(vars_map["card_border"].get(), comp.get("card_border", "显示"))
    if "action_text" in editable and vars_map.get("action_text") is not None:
        comp["action_text"] = str(vars_map["action_text"].get() or "").strip()
    if "columns" in editable:
        comp["columns"] = str(vars_map["columns"].get() or "").strip()
    if "column_count" in editable and vars_map.get("column_count") is not None:
        col_count = _clamp(_to_int(vars_map["column_count"].get(), comp.get("column_count", 3)), 1, 32)
        comp["column_count"] = col_count
        if ("columns" in editable) and not str(vars_map["columns"].get() or "").strip():
            comp["columns"] = ",".join(_columns_by_count(col_count))
    if "rows" in editable:
        comp["rows"] = max(3, _to_int(vars_map["rows"].get(), comp.get("rows", 8)))

    if kind in TABLE_COMPONENT_KINDS:
        cols = _normalize_columns(comp.get("columns", ""))
        col_count = _clamp(_to_int(comp.get("column_count", len(cols)), len(cols)), 1, 32)
        if col_count != len(cols):
            comp["columns"] = ",".join(_columns_by_count(col_count))
        else:
            comp["columns"] = ",".join(cols)
        comp["column_count"] = len(_normalize_columns(comp.get("columns", "")))

    if kind == WINDOW_COMPONENT_KIND:
        if "w" in editable:
            comp["w"] = _clamp(_to_int(vars_map["w"].get(), comp.get("w", 960)), 360, CANVAS_REGION_W)
        if "h" in editable:
            comp["h"] = _clamp(_to_int(vars_map["h"].get(), comp.get("h", 640)), 240, CANVAS_REGION_H)
    else:
        if "w" in editable:
            comp["w"] = _clamp(_to_int(vars_map["w"].get(), comp.get("w", 180)), 60, CANVAS_REGION_W)
        if "h" in editable:
            comp["h"] = _clamp(_to_int(vars_map["h"].get(), comp.get("h", 36)), 24, CANVAS_REGION_H)

    max_x = max(0, CANVAS_REGION_W - _to_int(comp.get("w", 180), 180))
    max_y = max(0, CANVAS_REGION_H - _to_int(comp.get("h", 36), 36))
    if "x" in editable:
        comp["x"] = _clamp(_to_int(vars_map["x"].get(), comp.get("x", 0)), 0, max_x)
    if "y" in editable:
        comp["y"] = _clamp(_to_int(vars_map["y"].get(), comp.get("y", 0)), 0, max_y)

    # 防止组件因尺寸变化后跑出画布边界。
    comp["x"] = _clamp(_to_int(comp.get("x", 0), 0), 0, max_x)
    comp["y"] = _clamp(_to_int(comp.get("y", 0), 0), 0, max_y)

    _render_canvas(owner)
    _refresh_property_panel(owner)
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set(f"界面设计器：已更新 {comp.get('name', '')}")
    has_action = bool(str(comp.get("event", "")).strip()) and str(comp.get("kind", "")) in (BUTTON_COMPONENT_KINDS | {"登录模板", "列表模板"})
    if has_action:
        _set_designer_step(owner, 4, "下一步：点击运行预览或导出到编辑区。")
    else:
        _set_designer_step(owner, 3, "建议给关键按钮填写函数名，再进入导出。")
    return "break"


def _sanitize_identifier(text, fallback):
    value = re.sub(r"[^\u4e00-\u9fa5A-Za-z0-9_]", "", str(text or ""))
    if not value:
        value = fallback
    if value[0].isdigit():
        value = f"控件_{value}"
    return value


def _sanitize_function_name(text, fallback):
    name = _sanitize_identifier(text, fallback)
    if not name.startswith("功能") and name in {"显示", "输入", "如果", "功能", "返回"}:
        return f"{fallback}"
    return name


def _normalize_columns(raw_columns):
    text = str(raw_columns or "").strip()
    if not text:
        return ["列1", "列2"]
    sep = None
    for candidate in [",", "，", "|", "｜", ";", "；"]:
        if candidate in text:
            sep = candidate
            break
    if sep is None:
        return [text]
    cols = [item.strip() for item in text.split(sep) if item.strip()]
    return cols or ["列1", "列2"]


def _columns_by_count(count):
    n = _clamp(_to_int(count, 3), 1, 32)
    return [f"列{i}" for i in range(1, n + 1)]


def _guess_param_name_from_input(component_name, index, used_names):
    base = _sanitize_identifier(component_name, f"参数{index}")
    base = re.sub(r"(输入框|输入)\d*$", "", base)
    base = re.sub(r"_?\d+$", "", base).strip("_")
    if not base:
        base = f"参数{index}"
    if base[0].isdigit():
        base = f"参数_{base}"
    name = base
    seq = 2
    while name in used_names:
        name = f"{base}_{seq}"
        seq += 1
    used_names.add(name)
    return name


def _infer_button_bindings(export_items):
    items = list(export_items or [])
    input_items = [item for item in items if str(item.get("kind", "")) in INPUT_COMPONENT_KINDS]
    table_items = [item for item in items if str(item.get("kind", "")) in TABLE_COMPONENT_KINDS]
    query_keywords = ("查", "查询", "搜索", "检索", "筛选")
    bindings = {}

    for button in items:
        if str(button.get("kind", "")) not in BUTTON_COMPONENT_KINDS:
            continue
        fn_name = str(button.get("event_fn", "") or "")
        if not fn_name or fn_name in bindings:
            continue

        bx = _to_int(button.get("x", 0), 0)
        by = _to_int(button.get("y", 0), 0)
        bw = _to_int(button.get("w", 120), 120)
        text = str(button.get("text", "") or "")
        fn_text = str(fn_name)

        nearby_inputs = []
        for inp in input_items:
            ix = _to_int(inp.get("x", 0), 0)
            iy = _to_int(inp.get("y", 0), 0)
            iw = _to_int(inp.get("w", 200), 200)
            vertical_delta = abs(iy - by)
            if vertical_delta > 180:
                continue
            if ix > bx + bw + 420:
                continue
            score = vertical_delta * 3 + abs((ix + int(iw / 2)) - (bx + int(bw / 2)))
            nearby_inputs.append((score, inp))
        nearby_inputs.sort(key=lambda pair: pair[0])
        selected_inputs = [pair[1] for pair in nearby_inputs[:2]]
        selected_inputs.sort(key=lambda inp: (_to_int(inp.get("y", 0), 0), _to_int(inp.get("x", 0), 0)))

        used_params = set()
        param_names = []
        input_names = []
        for idx, inp in enumerate(selected_inputs, start=1):
            input_names.append(str(inp.get("name", "")))
            param_names.append(_guess_param_name_from_input(inp.get("name", ""), idx, used_params))

        table_name = ""
        table_score = None
        for table in table_items:
            tx = _to_int(table.get("x", 0), 0)
            ty = _to_int(table.get("y", 0), 0)
            delta_y = ty - by
            if delta_y < -220:
                continue
            score = abs(delta_y) * 2 + abs(tx - bx)
            if table_score is None or score < table_score:
                table_score = score
                table_name = str(table.get("name", ""))

        query_mode = bool(table_name) and any(keyword in (text + fn_text) for keyword in query_keywords)
        bindings[fn_name] = {
            "input_components": input_names,
            "param_names": param_names,
            "table_component": table_name,
            "query_mode": query_mode,
        }
    return bindings


def _collect_design_export_context(owner):
    _ensure_component_baseline(owner)
    all_components = list(getattr(owner, "_ui_designer_components", []) or [])

    window_component = None
    for item in all_components:
        if str(item.get("kind", "")) == WINDOW_COMPONENT_KIND:
            window_component = item
            break

    win_title = "可视化界面"
    win_w = 960
    win_h = 640
    win_x = 0
    win_y = 0
    win_scroll_mode = "自动"
    if window_component is not None:
        title = str(window_component.get("text", "")).strip()
        win_title = title or win_title
        win_w = max(360, _to_int(window_component.get("w", win_w), win_w))
        win_h = max(240, _to_int(window_component.get("h", win_h), win_h))
        win_x = max(0, _to_int(window_component.get("x", 0), 0))
        win_y = max(0, _to_int(window_component.get("y", 0), 0))
        win_scroll_mode = _normalize_window_scroll_mode(window_component.get("scroll_mode", "自动"))

    comps = [item for item in all_components if str(item.get("kind", "")) != WINDOW_COMPONENT_KIND]
    comps.sort(key=lambda item: (_to_int(item.get("y", 0)), _to_int(item.get("x", 0)), _to_int(item.get("uid", 0))))

    def _position_score(items):
        score = 0
        for item in list(items or []):
            x = _to_int(item.get("x", 0), 0)
            y = _to_int(item.get("y", 0), 0)
            w = max(20, _to_int(item.get("w", 60), 60))
            h = max(20, _to_int(item.get("h", 24), 24))
            if (-w < x < win_w) and (-h < y < win_h):
                score += 1
        return score

    used_names = set()
    export_items = []
    raw_points = []
    for index, comp in enumerate(comps, start=1):
        kind = str(comp.get("kind", "文字"))
        base_name = _sanitize_identifier(comp.get("name", ""), f"控件{index}")
        name = base_name
        n = 2
        while name in used_names:
            name = f"{base_name}_{n}"
            n += 1
        used_names.add(name)

        raw_x = _to_int(comp.get("x", 0), 0)
        raw_y = _to_int(comp.get("y", 0), 0)
        raw_points.append((raw_x, raw_y))
        item = {
            "index": index,
            "kind": kind,
            "name": name,
            # 设计器是全局画布坐标；导出运行时需要窗口内相对坐标。
            "x": raw_x - win_x,
            "y": raw_y - win_y,
            "w": max(60, _to_int(comp.get("w", 160), 160)),
            "h": max(24, _to_int(comp.get("h", 34), 34)),
            "text": str(comp.get("text", "")).strip() or kind,
            "button_style": _normalize_button_style(comp.get("button_style", "主按钮")),
            "card_border": _normalize_card_border(comp.get("card_border", "显示")),
            "action_text": str(comp.get("action_text", "")).strip(),
            "event_fn": "",
            "columns": _normalize_columns(comp.get("columns", "列1,列2")),
            "column_count": _clamp(_to_int(comp.get("column_count", 0), 0), 0, 32),
            "rows": max(3, _to_int(comp.get("rows", 8), 8)),
        }
        if kind in BUTTON_COMPONENT_KINDS:
            if kind == "复选框":
                default_event = f"处理勾选_{index}"
            elif kind == "单选按钮":
                default_event = f"处理选择_{index}"
            else:
                default_event = f"处理点击_{index}"
            item["event_fn"] = _sanitize_function_name(comp.get("event", ""), default_event)
        elif kind == "登录模板":
            item["action_text"] = item["action_text"] or "登录"
            item["event_fn"] = _sanitize_function_name(comp.get("event", ""), f"处理登录_{index}")
        elif kind == "列表模板":
            item["action_text"] = item["action_text"] or "查询"
            item["event_fn"] = _sanitize_function_name(comp.get("event", ""), f"执行查询_{index}")
            item["rows"] = max(3, _to_int(comp.get("rows", 10), 10))
        if kind in TABLE_COMPONENT_KINDS and int(item.get("column_count", 0)) > 0:
            target_count = _clamp(_to_int(item.get("column_count", len(item["columns"])), len(item["columns"])), 1, 32)
            if target_count != len(item["columns"]):
                item["columns"] = _columns_by_count(target_count)
        export_items.append(item)

    # 兼容异常坐标场景：若窗口坐标基准异常，尝试按组件最小坐标重建相对位置。
    # 采用命中分数更高的方案，确保运行预览至少能稳定看到组件。
    if export_items and raw_points:
        base_score = _position_score(export_items)
        min_x = min(p[0] for p in raw_points)
        min_y = min(p[1] for p in raw_points)
        rebased = []
        for item in export_items:
            clone = dict(item)
            src_x = _to_int(clone.get("x", 0), 0) + win_x
            src_y = _to_int(clone.get("y", 0), 0) + win_y
            clone["x"] = max(0, src_x - min_x + 24)
            clone["y"] = max(0, src_y - min_y + 24)
            rebased.append(clone)
        rebased_score = _position_score(rebased)
        if rebased_score > base_score:
            export_items = rebased

    for item in export_items:
        w = int(item.get("w", 120))
        h = int(item.get("h", 36))
        max_x = max(0, win_w - max(20, w))
        max_y = max(0, win_h - max(20, h))
        item["x"] = _clamp(_to_int(item.get("x", 0), 0), 0, max_x)
        item["y"] = _clamp(_to_int(item.get("y", 0), 0), 0, max_y)

    return {
        "window_title": win_title,
        "window_w": win_w,
        "window_h": win_h,
        "window_scroll_mode": win_scroll_mode,
        "items": export_items,
    }


def _auto_fix_design_components_for_export(owner):
    _ensure_component_baseline(owner)
    fixes = []
    used_events = set()
    for comp in list(getattr(owner, "_ui_designer_components", []) or []):
        if str(comp.get("kind", "")) == WINDOW_COMPONENT_KIND:
            continue
        event_name = str(comp.get("event", "")).strip()
        if event_name:
            used_events.add(event_name)

    def _next_unique_event(base_name: str):
        base = _sanitize_function_name(base_name, "处理事件")
        candidate = base
        seq = 2
        while candidate in used_events:
            candidate = f"{base}_{seq}"
            seq += 1
        used_events.add(candidate)
        return candidate

    for idx, comp in enumerate(list(getattr(owner, "_ui_designer_components", []) or []), start=1):
        kind = str(comp.get("kind", ""))
        if kind == WINDOW_COMPONENT_KIND:
            title = str(comp.get("text", "")).strip()
            if not title:
                comp["text"] = "我的窗口"
                fixes.append("窗口标题为空，已自动填充为“我的窗口”")
            comp["scroll_mode"] = _normalize_window_scroll_mode(comp.get("scroll_mode", "自动"))
            continue

        if kind in BUTTON_COMPONENT_KINDS or kind in {"登录模板", "列表模板"}:
            current = str(comp.get("event", "")).strip()
            if not current:
                if kind == "登录模板":
                    base = "处理登录"
                elif kind == "列表模板":
                    base = "执行查询"
                elif kind == "复选框":
                    base = "处理勾选"
                elif kind == "单选按钮":
                    base = "处理选择"
                else:
                    base = "处理点击"
                name_hint = _sanitize_identifier(comp.get("name", ""), f"控件{idx}")
                comp["event"] = _next_unique_event(f"{base}_{name_hint}")
                fixes.append(f"{comp.get('name', kind)} 未设置函数名，已自动生成")
            else:
                normalized = _sanitize_function_name(current, f"处理事件_{idx}")
                if normalized != current:
                    comp["event"] = _next_unique_event(normalized)
                    fixes.append(f"{comp.get('name', kind)} 函数名已自动规范化")

        if kind == "按钮":
            comp["button_style"] = _normalize_button_style(comp.get("button_style", "主按钮"))

        if kind in CARD_COMPONENT_KINDS:
            comp["card_border"] = _normalize_card_border(comp.get("card_border", "显示"))

        if kind in TABLE_COMPONENT_KINDS or kind == "列表模板":
            old_columns = str(comp.get("columns", "")).strip()
            normalized_columns = _normalize_columns(old_columns)
            target_count = _clamp(_to_int(comp.get("column_count", len(normalized_columns)), len(normalized_columns)), 1, 32)
            if kind in TABLE_COMPONENT_KINDS and target_count != len(normalized_columns):
                normalized_columns = _columns_by_count(target_count)
                fixes.append(f"{comp.get('name', kind)} 列数已同步为 {target_count}")
            comp["column_count"] = target_count
            new_columns = ",".join(normalized_columns)
            if old_columns != new_columns:
                comp["columns"] = new_columns
                fixes.append(f"{comp.get('name', kind)} 列定义已自动规范化")
            old_rows = _to_int(comp.get("rows", 8), 8)
            new_rows = max(3, old_rows)
            if new_rows != old_rows:
                comp["rows"] = new_rows
                fixes.append(f"{comp.get('name', kind)} 行数过小，已修正为 {new_rows}")

    if fixes:
        try:
            _render_canvas(owner)
            _refresh_property_panel(owner)
        except Exception:
            pass
    return fixes


def _find_missing_logic_functions(ui_code: str, logic_code: str):
    ui_calls = set(re.findall(r"业务\.([\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*)\s*\(", str(ui_code or "")))
    logic_defs = set(re.findall(r"^\s*功能\s+([\u4e00-\u9fa5A-Za-z_][\u4e00-\u9fa5A-Za-z0-9_]*)", str(logic_code or ""), flags=re.MULTILINE))
    return sorted(name for name in ui_calls if name and name not in logic_defs)


def _append_logic_function_stubs(logic_code: str, fn_names):
    missing = [str(x).strip() for x in list(fn_names or []) if str(x).strip()]
    if not missing:
        return str(logic_code or "")
    lines = [str(logic_code or "").rstrip(), "", "# --- 自动补齐：缺失业务函数 ---"]
    for name in missing:
        lines.append(f"功能 {name}()")
        lines.append(f"    返回 \"请实现业务函数：{name}\"")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _build_window_create_line(context):
    title = json.dumps(context.get("window_title", "可视化界面"), ensure_ascii=False)
    win_w = int(context.get("window_w", 960))
    win_h = int(context.get("window_h", 640))
    scroll_mode = _normalize_window_scroll_mode(context.get("window_scroll_mode", "自动"))
    return f"窗口 = 建窗口({title}, {win_w}, {win_h}, {json.dumps(scroll_mode, ensure_ascii=False)})"


def _generate_ym_code(owner):
    context = _collect_design_export_context(owner)

    lines = [
        "# --- 可视化界面设计器导出 ---",
        _build_window_create_line(context),
        "",
    ]
    generated_events = []

    for item in context["items"]:
        index = int(item["index"])
        kind = str(item["kind"])
        name = str(item["name"])
        x = int(item["x"])
        y = int(item["y"])
        w = int(item["w"])
        h = int(item["h"])
        text = str(item["text"])

        if kind == "多行文本框":
            lines.append(f"{name} = 加多行文本框(窗口, {json.dumps(text, ensure_ascii=False)})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind == "组合框":
            combo_options = _normalize_columns(text)
            default_value = str(combo_options[0] if combo_options else "")
            lines.append(
                f"{name} = 加组合框(窗口, {json.dumps(combo_options, ensure_ascii=False)}, "
                f"{json.dumps(default_value, ensure_ascii=False)})"
            )
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind == "复选框":
            fn_name = str(item["event_fn"])
            lines.append(f"{name} = 加复选框(窗口, {json.dumps(text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
            generated_events.append(fn_name)
        elif kind == "单选按钮":
            fn_name = str(item["event_fn"])
            group_name = "默认单选组"
            option_value = str(text or name)
            lines.append(
                f"{name} = 加单选按钮(窗口, {json.dumps(text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)}, "
                f"{json.dumps(group_name, ensure_ascii=False)}, {json.dumps(option_value, ensure_ascii=False)})"
            )
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
            generated_events.append(fn_name)
        elif kind in TEXT_COMPONENT_KINDS:
            lines.append(f"{name} = 加文字(窗口, {json.dumps(text, ensure_ascii=False)})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind in INPUT_COMPONENT_KINDS:
            lines.append(f"{name} = 加输入框(窗口)")
            if text:
                lines.append(f"写输入({name}, {json.dumps(text, ensure_ascii=False)})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind in BUTTON_COMPONENT_KINDS:
            fn_name = str(item["event_fn"])
            btn_style = _normalize_button_style(item.get("button_style", "主按钮"))
            lines.append(
                f"{name} = 加按钮(窗口, {json.dumps(text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)}, "
                f"{json.dumps(btn_style, ensure_ascii=False)})"
            )
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
            generated_events.append(fn_name)
        elif kind in TABLE_COMPONENT_KINDS:
            columns = list(item["columns"])
            rows = int(item["rows"])
            lines.append(f"{name} = 加表格(窗口, {json.dumps(columns, ensure_ascii=False)}, {rows})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind in CARD_COMPONENT_KINDS:
            border_on = 1 if _normalize_card_border(item.get("card_border", "显示")) == "显示" else 0
            lines.append(f"{name} = 加卡片(窗口, {json.dumps(text, ensure_ascii=False)}, {border_on})")
            lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind == "登录模板":
            action_text = str(item["action_text"])
            fn_name = str(item["event_fn"])
            lines.append(
                f"{name} = 加登录模板(窗口, {json.dumps(text, ensure_ascii=False)}, "
                f"{json.dumps(action_text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)})"
            )
            lines.append(f"设位置({name}[\"卡片\"], {x}, {y}, {w}, {h})")
            generated_events.append(fn_name)
        elif kind == "列表模板":
            action_text = str(item["action_text"])
            fn_name = str(item["event_fn"])
            columns = list(item["columns"])
            rows = int(item["rows"])
            lines.append(
                f"{name} = 加列表模板(窗口, {json.dumps(text, ensure_ascii=False)}, "
                f"{json.dumps(columns, ensure_ascii=False)}, {rows}, "
                f"{json.dumps(action_text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)})"
            )
            lines.append(f"设位置({name}[\"卡片\"], {x}, {y}, {w}, {h})")
            generated_events.append(fn_name)
        else:
            lines.append(f"# 未识别组件：{json.dumps(kind, ensure_ascii=False)}")
        lines.append("")

    generated_events = sorted(set(generated_events))
    for fn_name in generated_events:
        lines.append(f"功能 {fn_name}")
        lines.append("    # TODO: 在这里填写业务逻辑")
        lines.append(f"    弹窗(\"提示\", \"触发：{fn_name}\")")
        lines.append("")

    lines.append("打开界面(窗口)")
    return "\n".join(lines).rstrip() + "\n"


def _generate_layered_ym_codes(owner, data_backend=None):
    context = _collect_design_export_context(owner)
    button_bindings = _infer_button_bindings(context["items"])
    ui_lines = [
        "# --- 可视化界面设计器导出：界面层 ---",
        "引入 \"界面设计_业务层\" 叫做 业务",
        "",
        _build_window_create_line(context),
        "",
    ]
    event_map = {}
    list_template_specs = []
    login_template_specs = []

    for item in context["items"]:
        index = int(item["index"])
        kind = str(item["kind"])
        name = str(item["name"])
        x = int(item["x"])
        y = int(item["y"])
        w = int(item["w"])
        h = int(item["h"])
        text = str(item["text"])
        fn_name = str(item.get("event_fn", "") or "")

        if kind == "多行文本框":
            ui_lines.append(f"{name} = 加多行文本框(窗口, {json.dumps(text, ensure_ascii=False)})")
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind == "组合框":
            combo_options = _normalize_columns(text)
            default_value = str(combo_options[0] if combo_options else "")
            ui_lines.append(
                f"{name} = 加组合框(窗口, {json.dumps(combo_options, ensure_ascii=False)}, "
                f"{json.dumps(default_value, ensure_ascii=False)})"
            )
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind == "复选框":
            ui_lines.append(f"{name} = 加复选框(窗口, {json.dumps(text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)})")
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
            if fn_name and fn_name not in event_map:
                event_map[fn_name] = {
                    "kind": kind,
                    "component_name": name,
                    **dict(button_bindings.get(fn_name, {})),
                }
        elif kind == "单选按钮":
            group_name = "默认单选组"
            option_value = str(text or name)
            ui_lines.append(
                f"{name} = 加单选按钮(窗口, {json.dumps(text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)}, "
                f"{json.dumps(group_name, ensure_ascii=False)}, {json.dumps(option_value, ensure_ascii=False)})"
            )
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
            if fn_name and fn_name not in event_map:
                event_map[fn_name] = {
                    "kind": kind,
                    "component_name": name,
                    **dict(button_bindings.get(fn_name, {})),
                }
        elif kind in TEXT_COMPONENT_KINDS:
            ui_lines.append(f"{name} = 加文字(窗口, {json.dumps(text, ensure_ascii=False)})")
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind in INPUT_COMPONENT_KINDS:
            ui_lines.append(f"{name} = 加输入框(窗口)")
            if text:
                ui_lines.append(f"写输入({name}, {json.dumps(text, ensure_ascii=False)})")
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind in BUTTON_COMPONENT_KINDS:
            btn_style = _normalize_button_style(item.get("button_style", "主按钮"))
            ui_lines.append(
                f"{name} = 加按钮(窗口, {json.dumps(text, ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)}, "
                f"{json.dumps(btn_style, ensure_ascii=False)})"
            )
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
            if fn_name and fn_name not in event_map:
                event_map[fn_name] = {
                    "kind": kind,
                    "component_name": name,
                    **dict(button_bindings.get(fn_name, {})),
                }
        elif kind in TABLE_COMPONENT_KINDS:
            ui_lines.append(f"{name} = 加表格(窗口, {json.dumps(item['columns'], ensure_ascii=False)}, {int(item['rows'])})")
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind in CARD_COMPONENT_KINDS:
            border_on = 1 if _normalize_card_border(item.get("card_border", "显示")) == "显示" else 0
            ui_lines.append(f"{name} = 加卡片(窗口, {json.dumps(text, ensure_ascii=False)}, {border_on})")
            ui_lines.append(f"设位置({name}, {x}, {y}, {w}, {h})")
        elif kind == "登录模板":
            ui_lines.append(
                f"{name} = 加登录模板(窗口, {json.dumps(text, ensure_ascii=False)}, "
                f"{json.dumps(item['action_text'], ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)})"
            )
            ui_lines.append(f"设位置({name}[\"卡片\"], {x}, {y}, {w}, {h})")
            if fn_name and fn_name not in event_map:
                prefix = _sanitize_identifier(name, f"登录模板{index}")
                data_auth_fn = f"{prefix}_登录校验"
                event_map[fn_name] = {"kind": kind, "component_name": name, "data_auth_fn": data_auth_fn}
                login_template_specs.append({"prefix": prefix, "event_fn": fn_name, "data_auth_fn": data_auth_fn})
        elif kind == "列表模板":
            ui_lines.append(
                f"{name} = 加列表模板(窗口, {json.dumps(text, ensure_ascii=False)}, "
                f"{json.dumps(item['columns'], ensure_ascii=False)}, {int(item['rows'])}, "
                f"{json.dumps(item['action_text'], ensure_ascii=False)}, {json.dumps(fn_name, ensure_ascii=False)})"
            )
            ui_lines.append(f"设位置({name}[\"卡片\"], {x}, {y}, {w}, {h})")
            if fn_name and fn_name not in event_map:
                prefix = _sanitize_identifier(name, f"列表模板{index}")
                query_fn = f"{prefix}_查询"
                create_fn = f"{prefix}_新增"
                update_fn = f"{prefix}_更新"
                delete_fn = f"{prefix}_删除"
                event_map[fn_name] = {
                    "kind": kind,
                    "component_name": name,
                    "query_fn": query_fn,
                    "create_fn": create_fn,
                    "update_fn": update_fn,
                    "delete_fn": delete_fn,
                }
                list_template_specs.append(
                    {
                        "index": index,
                        "prefix": prefix,
                        "event_fn": fn_name,
                        "query_fn": query_fn,
                        "create_fn": create_fn,
                        "update_fn": update_fn,
                        "delete_fn": delete_fn,
                    }
                )
        else:
            ui_lines.append(f"# 未识别组件：{json.dumps(kind, ensure_ascii=False)}")
        ui_lines.append("")

    for fn_name, meta in event_map.items():
        source_kind = str(meta.get("kind", ""))
        comp_name = str(meta.get("component_name", ""))
        ui_lines.append(f"功能 {fn_name}")
        if source_kind == "登录模板":
            ui_lines.append(f"    账号 = 读输入({comp_name}[\"账号输入框\"])")
            ui_lines.append(f"    密码 = 读输入({comp_name}[\"密码输入框\"])")
            ui_lines.append(f"    结果 = 业务.{fn_name}(账号, 密码)")
            ui_lines.append("    弹窗(\"提示\", 转文字(结果))")
        elif source_kind == "列表模板":
            ui_lines.append(f"    关键字 = 读输入({comp_name}[\"关键字输入框\"])")
            ui_lines.append(f"    行列表 = 业务.{fn_name}(关键字)")
            ui_lines.append(f"    表格清空({comp_name}[\"表格\"])")
            ui_lines.append("    重复 长度(行列表) 次 叫做 序号")
            ui_lines.append("        行 = 行列表[序号]")
            ui_lines.append(f"        表格加行({comp_name}[\"表格\"], 行)")
        elif source_kind in BUTTON_COMPONENT_KINDS:
            param_names = list(meta.get("param_names", []) or [])
            input_components = list(meta.get("input_components", []) or [])
            table_component = str(meta.get("table_component", "") or "")
            query_mode = bool(meta.get("query_mode")) and bool(table_component)
            for idx, input_name in enumerate(input_components):
                if idx >= len(param_names):
                    break
                ui_lines.append(f"    {param_names[idx]} = 读输入({input_name})")
            call_args = ", ".join(param_names)
            if query_mode:
                if call_args:
                    ui_lines.append(f"    行列表 = 业务.{fn_name}({call_args})")
                else:
                    ui_lines.append(f"    行列表 = 业务.{fn_name}()")
                ui_lines.append(f"    表格清空({table_component})")
                ui_lines.append("    重复 长度(行列表) 次 叫做 序号")
                ui_lines.append("        行 = 行列表[序号]")
                ui_lines.append(f"        表格加行({table_component}, 行)")
            else:
                if call_args:
                    ui_lines.append(f"    结果 = 业务.{fn_name}({call_args})")
                else:
                    ui_lines.append(f"    结果 = 业务.{fn_name}()")
                ui_lines.append("    弹窗(\"提示\", 转文字(结果))")
        else:
            ui_lines.append(f"    结果 = 业务.{fn_name}()")
            ui_lines.append("    弹窗(\"提示\", 转文字(结果))")
        ui_lines.append("")

    if list_template_specs:
        ui_lines.append("# --- 列表模板默认操作示例（可选调用）---")
        for spec in list_template_specs:
            prefix = str(spec["prefix"])
            create_fn = str(spec["create_fn"])
            update_fn = str(spec["update_fn"])
            delete_fn = str(spec["delete_fn"])
            ui_lines.append(f"功能 {prefix}_新增示例")
            ui_lines.append(f"    结果 = 业务.{create_fn}(\"示例标题\", \"示例说明\")")
            ui_lines.append("    弹窗(\"新增\", 转文字(结果))")
            ui_lines.append("")
            ui_lines.append(f"功能 {prefix}_更新示例")
            ui_lines.append(f"    结果 = 业务.{update_fn}(\"1\", \"示例标题-更新\", \"示例说明-更新\")")
            ui_lines.append("    弹窗(\"更新\", 转文字(结果))")
            ui_lines.append("")
            ui_lines.append(f"功能 {prefix}_删除示例")
            ui_lines.append(f"    结果 = 业务.{delete_fn}(\"1\")")
            ui_lines.append("    弹窗(\"删除\", 转文字(结果))")
            ui_lines.append("")

    ui_lines.append("打开界面(窗口)")
    ui_code = "\n".join(ui_lines).rstrip() + "\n"

    logic_lines = [
        "# --- 可视化界面设计器导出：业务层 ---",
        "引入 \"界面设计_数据层\" 叫做 数据",
        "# 这里写业务逻辑，界面层会调用同名函数。",
        "",
        "功能 初始化()",
        "    数据.初始化()",
        "    返回 {\"成功\": 对, \"消息\": \"业务层初始化完成\"}",
        "",
    ]
    for fn_name, meta in event_map.items():
        source_kind = str(meta.get("kind", ""))
        if source_kind == "登录模板":
            logic_lines.append(f"功能 {fn_name}(账号, 密码)")
            logic_lines.append("    如果 去空格(账号) == \"\" 或者 去空格(密码) == \"\" 就")
            logic_lines.append("        返回 {\"成功\": 错, \"消息\": \"账号或密码不能为空\"}")
            data_auth_fn = str(meta.get("data_auth_fn", ""))
            if data_auth_fn:
                logic_lines.append(f"    返回 数据.{data_auth_fn}(账号, 密码)")
            else:
                logic_lines.append("    返回 {\"成功\": 对, \"消息\": \"登录校验通过：\" + 账号}")
        elif source_kind == "列表模板":
            query_fn = str(meta.get("query_fn", fn_name))
            if fn_name != query_fn:
                logic_lines.append(f"功能 {fn_name}(关键字)")
                logic_lines.append(f"    返回 {query_fn}(关键字)")
                logic_lines.append("")
        elif source_kind in BUTTON_COMPONENT_KINDS:
            param_names = list(meta.get("param_names", []) or [])
            table_component = str(meta.get("table_component", "") or "")
            query_mode = bool(meta.get("query_mode")) and bool(table_component)
            signature = ", ".join(param_names)
            if signature:
                logic_lines.append(f"功能 {fn_name}({signature})")
            else:
                logic_lines.append(f"功能 {fn_name}()")
            if query_mode:
                logic_lines.append("    # TODO: 返回二维列表，每一行对应表格一行")
                if param_names:
                    logic_lines.append(f"    关键字 = 去空格({param_names[0]})")
                    logic_lines.append("    如果 关键字 == \"\" 就")
                    logic_lines.append("        返回 新列表()")
                logic_lines.append("    返回 [[\"示例\", \"请替换为真实数据\"]]")
            else:
                logic_lines.append(f"    返回 \"请实现业务函数：{fn_name}\"")
        else:
            logic_lines.append(f"功能 {fn_name}()")
            logic_lines.append(f"    返回 \"请实现业务函数：{fn_name}\"")
        logic_lines.append("")

    if list_template_specs:
        logic_lines.append("# --- 列表模板：标准 CRUD 占位函数 ---")
        for spec in list_template_specs:
            query_fn = str(spec["query_fn"])
            create_fn = str(spec["create_fn"])
            update_fn = str(spec["update_fn"])
            delete_fn = str(spec["delete_fn"])
            logic_lines.append(f"功能 {query_fn}(关键字)")
            logic_lines.append(f"    返回 数据.{query_fn}(关键字)")
            logic_lines.append("")
            logic_lines.append(f"功能 {create_fn}(标题, 说明)")
            logic_lines.append("    如果 去空格(标题) == \"\" 就")
            logic_lines.append("        返回 {\"成功\": 错, \"消息\": \"标题不能为空\"}")
            logic_lines.append(f"    返回 数据.{create_fn}(标题, 说明)")
            logic_lines.append("")
            logic_lines.append(f"功能 {update_fn}(编号文本, 标题, 说明)")
            logic_lines.append("    如果 去空格(编号文本) == \"\" 就")
            logic_lines.append("        返回 {\"成功\": 错, \"消息\": \"编号不能为空\"}")
            logic_lines.append("    编号 = 转数字(编号文本)")
            logic_lines.append(f"    返回 数据.{update_fn}(编号, 标题, 说明)")
            logic_lines.append("")
            logic_lines.append(f"功能 {delete_fn}(编号文本)")
            logic_lines.append("    如果 去空格(编号文本) == \"\" 就")
            logic_lines.append("        返回 {\"成功\": 错, \"消息\": \"编号不能为空\"}")
            logic_lines.append("    编号 = 转数字(编号文本)")
            logic_lines.append(f"    返回 数据.{delete_fn}(编号)")
            logic_lines.append("")

    logic_code = "\n".join(logic_lines).rstrip() + "\n"

    data_backend = _normalize_data_backend(
        data_backend if data_backend is not None else getattr(owner, "_ui_designer_data_backend", "sqlite")
    )
    if data_backend == "json":
        data_lines = [
            "# --- 可视化界面设计器导出：数据层（JSON文件） ---",
            "引入 \"数据工具\" 叫做 数据",
            "引入 \"系统工具\" 叫做 系统",
            "",
            "数据文件 = \"界面设计_数据.json\"",
            "数据仓库 = {\"用户\": 新列表()}",
            "",
            "功能 确保仓库结构()",
            "    如果 取反 存在(数据仓库, \"用户\") 就",
            "        数据仓库[\"用户\"] = 新列表()",
            "",
            "功能 保存仓库()",
            "    确保仓库结构()",
            "    数据.写JSON(数据文件, 数据仓库, 对)",
            "    返回 对",
            "",
            "功能 初始化()",
            "    如果 系统.文件存在(数据文件) 就",
            "        读回 = 数据.读JSON(数据文件)",
            "        如果 读回 != 空 就",
            "            数据仓库 = 读回",
            "    确保仓库结构()",
            "    如果 长度(数据仓库[\"用户\"]) == 0 就",
            "        加入(数据仓库[\"用户\"], {\"账号\": \"admin\", \"密码\": \"123456\"})",
            "    保存仓库()",
            "    返回 对",
            "",
        ]
        if login_template_specs:
            data_lines.append("# --- 登录模板数据函数（JSON）---")
            for spec in login_template_specs:
                auth_fn = str(spec["data_auth_fn"])
                data_lines.append(f"功能 {auth_fn}(账号, 密码)")
                data_lines.append("    确保仓库结构()")
                data_lines.append("    账号值 = 去空格(账号)")
                data_lines.append("    密码值 = 去空格(密码)")
                data_lines.append("    重复 长度(数据仓库[\"用户\"]) 次 叫做 序号")
                data_lines.append("        用户 = 数据仓库[\"用户\"][序号]")
                data_lines.append("        如果 转文字(用户[\"账号\"]) == 账号值 并且 转文字(用户[\"密码\"]) == 密码值 就")
                data_lines.append("            返回 {\"成功\": 对, \"消息\": \"登录成功\"}")
                data_lines.append("    返回 {\"成功\": 错, \"消息\": \"账号或密码错误\"}")
                data_lines.append("")
        if list_template_specs:
            data_lines.append("# --- 列表模板数据函数（JSON + CRUD）---")
            for spec in list_template_specs:
                index = int(spec.get("index", 1))
                list_key = f"列表_{index}"
                query_fn = str(spec["query_fn"])
                create_fn = str(spec["create_fn"])
                update_fn = str(spec["update_fn"])
                delete_fn = str(spec["delete_fn"])
                data_lines.append(f"功能 {query_fn}(关键字)")
                data_lines.append("    确保仓库结构()")
                data_lines.append(f"    如果 取反 存在(数据仓库, \"{list_key}\") 就")
                data_lines.append(f"        数据仓库[\"{list_key}\"] = 新列表()")
                data_lines.append("    词 = 去空格(关键字)")
                data_lines.append("    结果 = 新列表()")
                data_lines.append(f"    重复 长度(数据仓库[\"{list_key}\"]) 次 叫做 序号")
                data_lines.append(f"        项 = 数据仓库[\"{list_key}\"][序号]")
                data_lines.append("        编号 = 转文字(项[\"编号\"])")
                data_lines.append("        标题 = 转文字(项[\"标题\"])")
                data_lines.append("        说明 = 转文字(项[\"说明\"])")
                data_lines.append("        如果 词 == \"\" 或者 包含(标题, 词) 或者 包含(说明, 词) 就")
                data_lines.append("            加入(结果, [编号, 标题, 说明])")
                data_lines.append("    返回 结果")
                data_lines.append("")
                data_lines.append(f"功能 {create_fn}(标题, 说明)")
                data_lines.append("    确保仓库结构()")
                data_lines.append(f"    如果 取反 存在(数据仓库, \"{list_key}\") 就")
                data_lines.append(f"        数据仓库[\"{list_key}\"] = 新列表()")
                data_lines.append(f"    新编号 = 长度(数据仓库[\"{list_key}\"]) + 1")
                data_lines.append(f"    加入(数据仓库[\"{list_key}\"], {{\"编号\": 新编号, \"标题\": 标题, \"说明\": 说明}})")
                data_lines.append("    保存仓库()")
                data_lines.append("    返回 {\"成功\": 对, \"消息\": \"新增成功\"}")
                data_lines.append("")
                data_lines.append(f"功能 {update_fn}(编号, 标题, 说明)")
                data_lines.append("    确保仓库结构()")
                data_lines.append(f"    如果 取反 存在(数据仓库, \"{list_key}\") 就")
                data_lines.append("        返回 {\"成功\": 错, \"消息\": \"记录不存在\"}")
                data_lines.append("    目标编号 = 转文字(编号)")
                data_lines.append("    命中 = 错")
                data_lines.append(f"    重复 长度(数据仓库[\"{list_key}\"]) 次 叫做 序号")
                data_lines.append(f"        项 = 数据仓库[\"{list_key}\"][序号]")
                data_lines.append("        如果 转文字(项[\"编号\"]) == 目标编号 就")
                data_lines.append("            项[\"标题\"] = 标题")
                data_lines.append("            项[\"说明\"] = 说明")
                data_lines.append("            命中 = 对")
                data_lines.append("            停下")
                data_lines.append("    如果 取反 命中 就")
                data_lines.append("        返回 {\"成功\": 错, \"消息\": \"未找到要更新的记录\"}")
                data_lines.append("    保存仓库()")
                data_lines.append("    返回 {\"成功\": 对, \"消息\": \"更新成功\"}")
                data_lines.append("")
                data_lines.append(f"功能 {delete_fn}(编号)")
                data_lines.append("    确保仓库结构()")
                data_lines.append(f"    如果 取反 存在(数据仓库, \"{list_key}\") 就")
                data_lines.append("        返回 {\"成功\": 错, \"消息\": \"记录不存在\"}")
                data_lines.append("    目标编号 = 转文字(编号)")
                data_lines.append("    命中 = 错")
                data_lines.append(f"    重复 长度(数据仓库[\"{list_key}\"]) 次 叫做 序号")
                data_lines.append(f"        项 = 数据仓库[\"{list_key}\"][序号]")
                data_lines.append("        如果 转文字(项[\"编号\"]) == 目标编号 就")
                data_lines.append(f"            删除(数据仓库[\"{list_key}\"], 序号)")
                data_lines.append("            命中 = 对")
                data_lines.append("            停下")
                data_lines.append("    如果 取反 命中 就")
                data_lines.append("        返回 {\"成功\": 错, \"消息\": \"未找到要删除的记录\"}")
                data_lines.append("    保存仓库()")
                data_lines.append("    返回 {\"成功\": 对, \"消息\": \"删除成功\"}")
                data_lines.append("")
    else:
        data_lines = [
            "# --- 可视化界面设计器导出：数据层（SQLite） ---",
            "引入 \"本地数据库\" 叫做 库",
            "",
            "数据库文件 = \"界面设计_数据.db\"",
            "连接 = 空",
            "",
            "功能 取连接()",
            "    如果 连接 == 空 就",
            "        连接 = 库.打开数据库(数据库文件)",
            "    返回 连接",
            "",
            "功能 初始化()",
            "    本地连接 = 取连接()",
        ]
        if login_template_specs:
            data_lines.append("    库.执行SQL(本地连接, \"CREATE TABLE IF NOT EXISTS 用户(账号 TEXT PRIMARY KEY, 密码 TEXT)\")")
            data_lines.append("    库.执行SQL(本地连接, \"INSERT OR IGNORE INTO 用户(账号, 密码) VALUES(?, ?)\", [\"admin\", \"123456\"])")
        for spec in list_template_specs:
            index = int(spec.get("index", 1))
            table_name = f"列表数据_{index}"
            data_lines.append(
                f"    库.执行SQL(本地连接, \"CREATE TABLE IF NOT EXISTS {table_name}(编号 INTEGER PRIMARY KEY AUTOINCREMENT, 标题 TEXT, 说明 TEXT)\")"
            )
        data_lines.append("    返回 对")
        data_lines.append("")
        if login_template_specs:
            data_lines.append("# --- 登录模板数据函数（SQLite）---")
            for spec in login_template_specs:
                auth_fn = str(spec["data_auth_fn"])
                data_lines.append(f"功能 {auth_fn}(账号, 密码)")
                data_lines.append("    本地连接 = 取连接()")
                data_lines.append("    结果 = 库.查询SQL(本地连接, \"SELECT 账号 FROM 用户 WHERE 账号 = ? AND 密码 = ? LIMIT 1\", [账号, 密码])")
                data_lines.append("    如果 长度(结果) > 0 就")
                data_lines.append("        返回 {\"成功\": 对, \"消息\": \"登录成功\"}")
                data_lines.append("    返回 {\"成功\": 错, \"消息\": \"账号或密码错误\"}")
                data_lines.append("")
        if list_template_specs:
            data_lines.append("# --- 列表模板数据函数（SQLite + CRUD）---")
            for spec in list_template_specs:
                index = int(spec.get("index", 1))
                table_name = f"列表数据_{index}"
                query_fn = str(spec["query_fn"])
                create_fn = str(spec["create_fn"])
                update_fn = str(spec["update_fn"])
                delete_fn = str(spec["delete_fn"])
                data_lines.append(f"功能 {query_fn}(关键字)")
                data_lines.append("    本地连接 = 取连接()")
                data_lines.append("    词 = 去空格(关键字)")
                data_lines.append("    如果 词 == \"\" 就")
                data_lines.append(
                    f"        原始结果 = 库.查询SQL(本地连接, \"SELECT 编号, 标题, 说明 FROM {table_name} ORDER BY 编号 DESC\")"
                )
                data_lines.append("    不然")
                data_lines.append("        模式 = \"%\" + 词 + \"%\"")
                data_lines.append(
                    f"        原始结果 = 库.查询SQL(本地连接, \"SELECT 编号, 标题, 说明 FROM {table_name} WHERE 标题 LIKE ? OR 说明 LIKE ? ORDER BY 编号 DESC\", [模式, 模式])"
                )
                data_lines.append("    结果 = 新列表()")
                data_lines.append("    重复 长度(原始结果) 次 叫做 序号")
                data_lines.append("        项 = 原始结果[序号]")
                data_lines.append("        加入(结果, [转文字(项[\"编号\"]), 转文字(项[\"标题\"]), 转文字(项[\"说明\"])])")
                data_lines.append("    返回 结果")
                data_lines.append("")
                data_lines.append(f"功能 {create_fn}(标题, 说明)")
                data_lines.append("    本地连接 = 取连接()")
                data_lines.append(
                    f"    库.执行SQL(本地连接, \"INSERT INTO {table_name}(标题, 说明) VALUES(?, ?)\", [标题, 说明])"
                )
                data_lines.append("    返回 {\"成功\": 对, \"消息\": \"新增成功\"}")
                data_lines.append("")
                data_lines.append(f"功能 {update_fn}(编号, 标题, 说明)")
                data_lines.append("    本地连接 = 取连接()")
                data_lines.append(
                    f"    库.执行SQL(本地连接, \"UPDATE {table_name} SET 标题 = ?, 说明 = ? WHERE 编号 = ?\", [标题, 说明, 编号])"
                )
                data_lines.append("    返回 {\"成功\": 对, \"消息\": \"更新成功\"}")
                data_lines.append("")
                data_lines.append(f"功能 {delete_fn}(编号)")
                data_lines.append("    本地连接 = 取连接()")
                data_lines.append(f"    库.执行SQL(本地连接, \"DELETE FROM {table_name} WHERE 编号 = ?\", [编号])")
                data_lines.append("    返回 {\"成功\": 对, \"消息\": \"删除成功\"}")
                data_lines.append("")

    data_code = "\n".join(data_lines).rstrip() + "\n"
    return ui_code, logic_code, data_code


def _insert_code_to_editor(owner, code):
    editor = owner._get_current_editor()
    if editor is None:
        try:
            owner._create_editor_tab("界面设计导出.ym", "")
            editor = owner._get_current_editor()
        except Exception:
            editor = None
    if editor is None:
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("界面设计器：没有可写入的编辑区")
        return False
    try:
        editor.delete("1.0", tk.END)
        editor.insert("1.0", code)
        try:
            editor.mark_set("insert", "1.0")
        except tk.TclError:
            pass
        editor.focus_set()
        owner._schedule_highlight()
        owner._update_line_numbers()
        owner._update_cursor_status()
        owner._schedule_diagnose()
        return True
    except tk.TclError:
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("界面设计器：插入代码失败")
        return False


def _upsert_code_to_named_tab(owner, filename, code):
    target_tab_id = None
    for tab_id, data in list(getattr(owner, "tabs_data", {}).items()):
        if str(data.get("filepath", "")) == str(filename):
            target_tab_id = tab_id
            break

    editor = None
    try:
        if target_tab_id is None:
            owner._create_editor_tab(str(filename), str(code))
            target_tab_id = owner._get_current_tab_id()
            if target_tab_id and target_tab_id in owner.tabs_data:
                editor = owner.tabs_data[target_tab_id].get("editor")
        else:
            owner.notebook.select(target_tab_id)
            editor = owner.tabs_data[target_tab_id].get("editor")
            if editor is None:
                return False
            editor.delete("1.0", tk.END)
            editor.insert("1.0", str(code))
    except tk.TclError:
        return False
    except Exception:
        return False

    if target_tab_id and target_tab_id in owner.tabs_data:
        owner.tabs_data[target_tab_id]["dirty"] = True
        try:
            owner._update_tab_title(target_tab_id)
        except Exception:
            pass

    if editor is not None:
        try:
            editor.focus_set()
        except tk.TclError:
            pass
    try:
        owner._schedule_highlight()
        owner._update_line_numbers()
        owner._update_cursor_status()
        owner._schedule_diagnose()
        owner._refresh_outline()
    except Exception:
        pass
    if target_tab_id and target_tab_id in owner.tabs_data:
        try:
            owner.notebook.select(target_tab_id)
        except Exception:
            pass
    return bool(target_tab_id and target_tab_id in owner.tabs_data)


def _select_code_tab_by_filename(owner, filename):
    target = str(filename or "")
    if not target:
        return False
    for tab_id, data in list(getattr(owner, "tabs_data", {}).items()):
        if str(data.get("filepath", "")) != target:
            continue
        try:
            owner.notebook.select(tab_id)
            return True
        except Exception:
            return False
    return False


def export_ui_design_to_editor(owner):
    fixes = _auto_fix_design_components_for_export(owner)
    code = _generate_ym_code(owner)
    ok = _upsert_code_to_named_tab(owner, "界面设计导出.ym", code)
    if not ok:
        ok = _insert_code_to_editor(owner, code)
    else:
        _select_code_tab_by_filename(owner, "界面设计导出.ym")
    if ok and hasattr(owner, "status_main_var"):
        if fixes:
            owner.status_main_var.set(f"界面设计器：已导出到编辑区（自动修复 {len(fixes)} 项）")
        else:
            owner.status_main_var.set("界面设计器：已导出到编辑区")
    if ok:
        _set_designer_step(owner, 4, "已完成导出，可返回编辑区运行或继续优化界面。")
    return "break"


def export_ui_design_to_layered_editors(owner, event=None, choose_backend=False):
    del event
    fixes = _auto_fix_design_components_for_export(owner)
    backend = _normalize_data_backend(getattr(owner, "_ui_designer_data_backend", "sqlite"))
    prefix = _normalize_layer_export_prefix(getattr(owner, "_ui_designer_layer_export_prefix", "界面设计"))
    remembered = True
    remember_prefix = True
    if choose_backend:
        choice = _prompt_layer_export_backend(owner)
        if not choice:
            if hasattr(owner, "status_main_var"):
                owner.status_main_var.set("界面设计器：已取消导出三层代码")
            return "break"
        backend = _normalize_data_backend(choice.get("backend"))
        remembered = bool(choice.get("remember"))
        prefix = _normalize_layer_export_prefix(choice.get("prefix"), fallback=prefix)
        remember_prefix = bool(choice.get("remember_prefix"))
        if remembered:
            _set_data_backend(owner, backend)
        if remember_prefix:
            owner._ui_designer_layer_export_prefix = prefix
            if hasattr(owner, "_ui_designer_layer_export_prefix"):
                owner._ui_designer_layer_export_prefix = _normalize_layer_export_prefix(owner._ui_designer_layer_export_prefix)
        else:
            # 仅本次导出时，保持当前默认前缀不变。
            pass
        if remembered or remember_prefix:
            saver = getattr(owner, "_save_project_state", None)
            if callable(saver):
                try:
                    saver()
                except Exception:
                    pass

    ui_code, logic_code, data_code = _generate_layered_ym_codes(owner, data_backend=backend)
    missing_logic = _find_missing_logic_functions(ui_code, logic_code)
    if missing_logic:
        logic_code = _append_logic_function_stubs(logic_code, missing_logic)
    data_filename = f"{prefix}_数据层.ym"
    logic_filename = f"{prefix}_业务层.ym"
    ui_filename = f"{prefix}_界面层.ym"
    ok_data = _upsert_code_to_named_tab(owner, data_filename, data_code)
    ok_logic = _upsert_code_to_named_tab(owner, logic_filename, logic_code)
    ok_ui = _upsert_code_to_named_tab(owner, ui_filename, ui_code)
    backend_label = _backend_label_of(backend)
    if ok_data and ok_logic and ok_ui and hasattr(owner, "status_main_var"):
        backend_suffix = "，并记住当前项目后端" if remembered else "，后端仅用于本次导出"
        prefix_suffix = "，并记住导出前缀" if remember_prefix else "，前缀仅用于本次导出"
        fix_suffix = f"，自动修复 {len(fixes)} 项" if fixes else ""
        missing_suffix = f"，补齐业务函数 {len(missing_logic)} 个" if missing_logic else ""
        owner.status_main_var.set(
            f"界面设计器：已导出三层代码（前缀：{prefix}，后端：{backend_label}{backend_suffix}{prefix_suffix}{fix_suffix}{missing_suffix}）"
        )
        _set_designer_step(owner, 4, "已导出三层代码，可直接运行主程序验证。")
    elif hasattr(owner, "status_main_var"):
        owner.status_main_var.set("界面设计器：导出三层代码失败")
    return "break"


def copy_ui_design_code(owner):
    code = _generate_ym_code(owner)
    try:
        owner.root.clipboard_clear()
        owner.root.clipboard_append(code)
        owner.root.update_idletasks()
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("界面设计器：代码已复制到剪贴板")
    except tk.TclError:
        if hasattr(owner, "status_main_var"):
            owner.status_main_var.set("界面设计器：复制失败")
    return "break"


def _ensure_window(owner):
    _ensure_component_baseline(owner)
    win = getattr(owner, "_ui_designer_window", None)
    if win is not None:
        try:
            if win.winfo_exists():
                return win
        except tk.TclError:
            pass

    win = tk.Toplevel(owner.root)
    win.title("易码界面设计器")
    _center_window(owner, win, 1320, 820)
    try:
        win.minsize(1080, 680)
    except tk.TclError:
        pass
    win.configure(bg=owner.theme_bg)
    win.protocol("WM_DELETE_WINDOW", win.withdraw)
    panel = _build_designer_panel(owner, win, title_text="界面设计器 UI DESIGNER")
    panel.pack(fill=tk.BOTH, expand=True)
    owner._ui_designer_window = win
    _render_canvas(owner)
    _refresh_property_panel(owner)
    return win


def _build_designer_panel(owner, parent, title_text="可视化界面设计 UI DESIGNER"):
    _ensure_component_baseline(owner)
    panel = tk.Frame(parent, bg=owner.theme_bg)

    top = tk.Frame(panel, bg=owner.theme_toolbar_bg, padx=10, pady=8)
    top.pack(fill=tk.X)
    tk.Label(
        top,
        text=title_text,
        font=("Microsoft YaHei", 10, "bold"),
        bg=owner.theme_toolbar_bg,
        fg="#DFE6EE",
    ).pack(side=tk.LEFT)

    mode_wrap = tk.Frame(top, bg=owner.theme_toolbar_bg)
    mode_wrap.pack(side=tk.LEFT, padx=(12, 0))
    tk.Label(
        mode_wrap,
        text="模式：",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_bg,
        fg=owner.theme_toolbar_muted,
    ).pack(side=tk.LEFT)
    mode_novice_btn = tk.Button(
        mode_wrap,
        text="新手",
        command=lambda: _set_designer_mode(owner, "novice", announce=True),
        font=("Microsoft YaHei", 8),
        relief="flat",
        bd=0,
        padx=8,
        pady=2,
        cursor="hand2",
    )
    mode_novice_btn.pack(side=tk.LEFT, padx=(4, 0))
    mode_pro_btn = tk.Button(
        mode_wrap,
        text="专业",
        command=lambda: _set_designer_mode(owner, "pro", announce=True),
        font=("Microsoft YaHei", 8),
        relief="flat",
        bd=0,
        padx=8,
        pady=2,
        cursor="hand2",
    )
    mode_pro_btn.pack(side=tk.LEFT, padx=(4, 0))
    owner._ui_designer_mode_buttons = {"novice": mode_novice_btn, "pro": mode_pro_btn}

    _create_data_backend_selector(owner, top)

    btn_delete = _tool_button(owner, top, "删除选中", lambda: _delete_selected_component(owner))
    btn_clear = _tool_button(owner, top, "清空画布", lambda: _clear_components(owner))
    btn_export_editor = _tool_button(owner, top, "导出到编辑区", lambda: export_ui_design_to_editor(owner))
    btn_export_layers = _tool_button(owner, top, "导出三层代码...", lambda: export_ui_design_to_layered_editors(owner, choose_backend=True))
    btn_copy = _tool_button(owner, top, "复制代码", lambda: copy_ui_design_code(owner))
    btn_quickstart = _tool_button(owner, top, "一键起步", lambda: run_ui_designer_quick_start(owner))
    owner._ui_designer_top_controls = {
        "delete": btn_delete,
        "clear": btn_clear,
        "export_editor": btn_export_editor,
        "export_layers": btn_export_layers,
        "copy": btn_copy,
        "quickstart": btn_quickstart,
    }

    novice_guide = tk.Frame(panel, bg=owner.theme_panel_bg, padx=10, pady=8)
    novice_guide.pack(fill=tk.X, pady=(0, 6))
    owner._ui_designer_novice_guide = novice_guide
    step_row = tk.Frame(novice_guide, bg=owner.theme_panel_bg)
    step_row.pack(fill=tk.X)
    step_labels = []
    for idx, text in enumerate(NOVICE_STEP_LABELS):
        lbl = tk.Label(
            step_row,
            text=text,
            font=("Microsoft YaHei", 8, "bold"),
            bg=owner.theme_panel_bg,
            fg=owner.theme_toolbar_fg,
            padx=8,
            pady=3,
            highlightthickness=1,
            highlightbackground=owner.theme_toolbar_border,
            anchor="w",
        )
        lbl.pack(side=tk.LEFT)
        step_labels.append(lbl)
        if idx < len(NOVICE_STEP_LABELS) - 1:
            tk.Label(step_row, text="→", bg=owner.theme_panel_bg, fg=owner.theme_toolbar_muted, padx=5).pack(side=tk.LEFT)
    owner._ui_designer_step_labels = step_labels

    owner._ui_designer_step_hint_var = tk.StringVar(value="先点击“选择模板”，快速生成可编辑页面。")
    tk.Label(
        novice_guide,
        textvariable=owner._ui_designer_step_hint_var,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg="#8FA1B8",
        anchor="w",
        pady=4,
    ).pack(fill=tk.X)

    act_row = tk.Frame(novice_guide, bg=owner.theme_panel_bg)
    act_row.pack(fill=tk.X)
    btn_export_novice = _tool_button(owner, act_row, "导出到编辑区", lambda: _novice_export(owner))
    btn_bind_novice = _tool_button(owner, act_row, "绑定动作", lambda: _novice_focus_action_step(owner))
    btn_add_novice = _tool_button(owner, act_row, "添加组件", lambda: _novice_add_component(owner))
    btn_template_novice = _tool_button(owner, act_row, "选择模板", lambda: run_ui_designer_quick_start(owner))
    owner._ui_designer_novice_buttons = {
        "template": btn_template_novice,
        "add": btn_add_novice,
        "bind": btn_bind_novice,
        "export": btn_export_novice,
    }

    body = tk.PanedWindow(panel, orient=tk.HORIZONTAL, sashwidth=4, bg=owner.theme_sash, borderwidth=0)
    body.pack(fill=tk.BOTH, expand=True)
    owner._ui_designer_body_paned = body

    palette_panel_w, palette_panel_min, _tree_col_w = _calc_palette_width(owner)
    left = tk.Frame(body, bg=owner.theme_panel_bg, width=palette_panel_w)
    body.add(left, stretch="never", minsize=palette_panel_min)
    tk.Label(
        left,
        text="组件列表",
        font=("Microsoft YaHei", 9, "bold"),
        bg=owner.theme_panel_bg,
        fg="#9FB0C5",
        anchor="w",
        padx=10,
        pady=8,
    ).pack(fill=tk.X)

    palette_novice_wrap = tk.Frame(left, bg=owner.theme_panel_bg, padx=8, pady=0)
    palette_novice_wrap.pack(fill=tk.BOTH, expand=True)
    novice_palette_wrap, novice_palette = _build_recommended_palette(owner, palette_novice_wrap)
    owner._ui_designer_palette_novice_wrap = palette_novice_wrap
    owner._ui_designer_palette_recommended = novice_palette
    owner._ui_designer_palette = novice_palette

    palette_pro_wrap = tk.Frame(left, bg=owner.theme_panel_bg, padx=8, pady=0)
    palette_pro_wrap.pack(fill=tk.BOTH, expand=True)
    pro_palette = _build_palette_tree(owner, palette_pro_wrap)
    owner._ui_designer_palette_pro_wrap = palette_pro_wrap
    owner._ui_designer_palette_pro = pro_palette

    action_left = tk.Frame(left, bg=owner.theme_panel_bg, padx=10, pady=10)
    action_left.pack(fill=tk.X)
    add_btn = tk.Button(
        action_left,
        text="添加组件",
        command=lambda: _novice_add_component(owner) if str(getattr(owner, "_ui_designer_mode", "novice")) == "novice" else _add_component(owner),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=3,
        cursor="hand2",
    )
    add_btn.pack(side=tk.LEFT, padx=(0, 8), pady=(0, 2))
    quick_btn = tk.Button(
        action_left,
        text="一键起步",
        command=lambda: run_ui_designer_quick_start(owner),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=3,
        cursor="hand2",
    )
    quick_btn.pack(side=tk.LEFT, pady=(0, 2))

    center = tk.Frame(body, bg=owner.theme_panel_bg)
    body.add(center, stretch="always", minsize=520)
    center_top = tk.Frame(center, bg=owner.theme_panel_bg, padx=10, pady=6)
    center_top.pack(fill=tk.X)
    tk.Label(
        center_top,
        text="自由画布（拖拽组件自由排版，支持绝对布局代码导出）",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg="#8FA1B8",
        anchor="w",
    ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    tk.Button(
        center_top,
        text="导出软件",
        command=lambda: _export_software_from_designer(owner),
        font=("Microsoft YaHei", 8),
        bg="#0E639C",
        fg="#FFFFFF",
        activebackground="#1577B8",
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=2,
        cursor="hand2",
    ).pack(side=tk.RIGHT)
    tk.Button(
        center_top,
        text="运行预览",
        command=lambda: _run_preview_from_designer(owner),
        font=("Microsoft YaHei", 8),
        bg="#2E7D32",
        fg="#FFFFFF",
        activebackground="#3D9742",
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=2,
        cursor="hand2",
    ).pack(side=tk.RIGHT, padx=(0, 6))

    canvas_wrap = tk.Frame(center, bg=owner.theme_panel_bg, padx=8, pady=0)
    canvas_wrap.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
    canvas = tk.Canvas(
        canvas_wrap,
        bg="#101723",
        highlightthickness=0,
        borderwidth=0,
        relief="flat",
        scrollregion=(0, 0, CANVAS_REGION_W, CANVAS_REGION_H),
    )
    canvas_x = ttk.Scrollbar(canvas_wrap, orient="horizontal", command=canvas.xview)
    canvas_y = ttk.Scrollbar(canvas_wrap, orient="vertical", command=canvas.yview)
    canvas.configure(xscrollcommand=canvas_x.set, yscrollcommand=canvas_y.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    canvas_y.grid(row=0, column=1, sticky="ns")
    canvas_x.grid(row=1, column=0, sticky="ew")
    canvas_wrap.grid_rowconfigure(0, weight=1)
    canvas_wrap.grid_columnconfigure(0, weight=1)
    owner._ui_designer_canvas = canvas
    canvas.bind("<ButtonPress-1>", lambda e: _on_canvas_background_press(owner, e), add="+")
    canvas.bind("<B1-Motion>", lambda e: _on_canvas_motion(owner, e), add="+")
    canvas.bind("<ButtonRelease-1>", lambda e: _on_canvas_release(owner, e), add="+")

    right = tk.Frame(body, bg=owner.theme_panel_bg, width=300)
    body.add(right, stretch="never", minsize=260)
    tk.Label(
        right,
        text="属性",
        font=("Microsoft YaHei", 9, "bold"),
        bg=owner.theme_panel_bg,
        fg="#9FB0C5",
        anchor="w",
        padx=10,
        pady=8,
    ).pack(fill=tk.X)

    owner._ui_designer_info_var = tk.StringVar(value="未选中组件")
    tk.Label(
        right,
        textvariable=owner._ui_designer_info_var,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg="#D1DDEA",
        anchor="w",
        padx=10,
        pady=2,
    ).pack(fill=tk.X)
    owner._ui_designer_prop_hint_var = tk.StringVar(value="先选组件再编辑。灰色字段可忽略。")
    tk.Label(
        right,
        textvariable=owner._ui_designer_prop_hint_var,
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg="#8FA1B8",
        justify="left",
        anchor="w",
        padx=10,
        pady=0,
    ).pack(fill=tk.X, pady=(0, 4))

    prop_body = tk.Frame(right, bg=owner.theme_panel_bg, padx=10, pady=8)
    prop_body.pack(fill=tk.BOTH, expand=True)

    owner._ui_designer_prop_vars = {
        "name": tk.StringVar(value=""),
        "kind": tk.StringVar(value=""),
        "text": tk.StringVar(value=""),
        "scroll_mode": tk.StringVar(value="自动"),
        "button_style": tk.StringVar(value="主按钮"),
        "card_border": tk.StringVar(value="显示"),
        "event": tk.StringVar(value=""),
        "action_text": tk.StringVar(value=""),
        "columns": tk.StringVar(value=""),
        "column_count": tk.StringVar(value="3"),
        "rows": tk.StringVar(value=""),
        "x": tk.StringVar(value=""),
        "y": tk.StringVar(value=""),
        "w": tk.StringVar(value=""),
        "h": tk.StringVar(value=""),
    }
    prop_widgets = {}

    basic_prop_keys = set(NOVICE_BASIC_PROP_KEYS)

    def _row(label, key, readonly=False):
        row = tk.Frame(prop_body, bg=owner.theme_panel_bg)
        row.pack(fill=tk.X, pady=(0, 6))
        tk.Label(
            row,
            text=label,
            width=8,
            font=("Microsoft YaHei", 8),
            bg=owner.theme_panel_bg,
            fg="#8FA1B8",
            anchor="w",
        ).pack(side=tk.LEFT)
        entry = tk.Entry(
            row,
            textvariable=owner._ui_designer_prop_vars[key],
            font=("Microsoft YaHei", 8),
            bg=owner.theme_panel_inner_bg,
            fg=owner.theme_fg,
            insertbackground=owner.theme_fg,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=owner.theme_toolbar_border,
            highlightcolor=owner.theme_accent,
        )
        if readonly:
            entry.configure(state="readonly")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if not readonly:
            entry.bind("<Return>", lambda e: _apply_properties(owner), add="+")
            entry.bind("<FocusOut>", lambda e: _apply_properties(owner), add="+")
        prop_widgets[key] = {
            "entry": entry,
            "row": row,
            "readonly": bool(readonly),
            "basic": bool(key in basic_prop_keys),
        }
        return entry

    def _row_choice(label, key, values):
        row = tk.Frame(prop_body, bg=owner.theme_panel_bg)
        row.pack(fill=tk.X, pady=(0, 6))
        tk.Label(
            row,
            text=label,
            width=8,
            font=("Microsoft YaHei", 8),
            bg=owner.theme_panel_bg,
            fg="#8FA1B8",
            anchor="w",
        ).pack(side=tk.LEFT)
        combo = ttk.Combobox(
            row,
            textvariable=owner._ui_designer_prop_vars[key],
            values=list(values),
            state="readonly",
            font=("Microsoft YaHei", 8),
            width=12,
        )
        combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        combo.bind("<<ComboboxSelected>>", lambda e: _apply_properties(owner), add="+")
        prop_widgets[key] = {
            "entry": combo,
            "row": row,
            "readonly": False,
            "choice": True,
            "basic": bool(key in basic_prop_keys),
        }
        return combo

    _row("标识", "name", readonly=True)
    _row("类型", "kind", readonly=True)
    _row("文本", "text")
    _row_choice("滚动条", "scroll_mode", WINDOW_SCROLL_MODE_CHOICES)
    _row_choice("按钮样式", "button_style", BUTTON_STYLE_CHOICES)
    _row_choice("卡片边框", "card_border", CARD_BORDER_CHOICES)
    _row("按钮文案", "action_text")
    _row("函数", "event")
    _row("列定义", "columns")
    _row("列数", "column_count")
    _row("行数", "rows")
    _row("X", "x")
    _row("Y", "y")
    _row("宽", "w")
    _row("高", "h")
    owner._ui_designer_prop_widgets = prop_widgets

    toggle_btn = tk.Button(
        prop_body,
        text="展开高级属性",
        command=lambda: _toggle_novice_advanced_props(owner),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=3,
        cursor="hand2",
    )
    owner._ui_designer_prop_toggle_btn = toggle_btn

    tk.Button(
        prop_body,
        text="应用属性",
        command=lambda: _apply_properties(owner),
        font=("Microsoft YaHei", 8),
        bg=owner.theme_toolbar_group_bg,
        fg=owner.theme_toolbar_fg,
        activebackground=owner.theme_toolbar_hover,
        activeforeground="#FFFFFF",
        relief="flat",
        bd=0,
        padx=8,
        pady=3,
        cursor="hand2",
    ).pack(anchor="w", pady=(4, 0))

    tk.Label(
        right,
        text="提示:\n1. 先点“一键起步”生成基础页面\n2. 左侧继续添加组件微调布局\n3. 右侧优先填写高亮属性\n4. 再导出到编辑区或导出三层代码",
        font=("Microsoft YaHei", 8),
        bg=owner.theme_panel_bg,
        fg="#8FA1B8",
        justify="left",
        anchor="w",
        padx=10,
        pady=8,
    ).pack(fill=tk.X, side=tk.BOTTOM)
    _set_designer_mode(owner, getattr(owner, "_ui_designer_mode", "novice"), announce=False)
    _set_designer_step(owner, getattr(owner, "_ui_designer_step", 1), hint_text="先点击“选择模板”，快速生成可编辑页面。")
    return panel


def ensure_embedded_ui_designer(owner, parent):
    _ensure_state(owner)
    panel = getattr(owner, "_ui_designer_embedded_panel", None)
    if panel is not None:
        try:
            if panel.winfo_exists() and panel.master is parent:
                return panel
        except tk.TclError:
            pass
        try:
            panel.destroy()
        except tk.TclError:
            pass

    panel = _build_designer_panel(owner, parent, title_text="可视化界面设计 UI DESIGNER")
    owner._ui_designer_embedded_panel = panel
    _render_canvas(owner)
    _refresh_property_panel(owner)
    return panel


def open_ui_designer(owner, event=None):
    del event
    switcher = getattr(owner, "_switch_workspace_mode", None)
    if callable(switcher):
        try:
            switcher("designer")
            if hasattr(owner, "status_main_var"):
                owner.status_main_var.set("已切换到可视化界面设计模式")
            return "break"
        except Exception:
            pass

    _ensure_state(owner)
    win = _ensure_window(owner)
    try:
        win.deiconify()
        win.lift()
        win.focus_force()
    except tk.TclError:
        pass
    if hasattr(owner, "status_main_var"):
        owner.status_main_var.set("界面设计器已打开（组件化 + 自由拖拽 + 代码导出）")

    try:
        _ensure_state(owner)
        first_hint = not bool(getattr(owner, "_ui_designer_opened_once", False))
        only_window = len(list(getattr(owner, "_ui_designer_components", []) or [])) <= 1
        if first_hint and str(getattr(owner, "_ui_designer_mode", "novice")) == "novice" and only_window:
            owner._ui_designer_opened_once = True
            run_ui_designer_quick_start(owner)
    except Exception:
        pass
    return "break"
