"""Core editor logic helpers extracted from 易码编辑器.py.

These functions are UI-agnostic and can be reused by scripts/tests.
"""

from __future__ import annotations
import importlib.util
import os
import re
import time
from typing import Any, Callable


BUILTIN_WORDS = [
    "新列表",
    "加入",
    "插入",
    "长度",
    "删除",
    "转数字",
    "转文字",
    "取随机数",
    "所有键",
    "所有值",
    "存在",
    "截取",
    "查找",
    "替换",
    "分割",
    "去空格",
    "包含",
    "读文件",
    "写文件",
    "追加文件",
    "文件存在",
    "目录存在",
    "创建目录",
    "列出目录",
    "删除文件",
    "删除目录",
    "复制文件",
    "移动文件",
    "重命名",
    "遍历文件",
    "复制目录",
    "压缩目录",
    "解压缩",
    "哈希文本",
    "哈希文件",
    "下载文件",
    "匹配文件",
    "文件信息",
    "目录大小",
    "格式时间",
    "解析时间",
    "写日志",
    "读日志",
    "睡眠",
    "拼路径",
    "绝对路径",
    "当前目录",
    "读环境变量",
    "写环境变量",
    "执行命令",
    "解析JSON",
    "生成JSON",
    "读JSON",
    "写JSON",
    "读CSV",
    "写CSV",
    "读INI",
    "写INI",
    "发起请求",
    "发GET",
    "发POST",
    "读响应JSON",
    "发GET_JSON",
    "发POST_JSON",
    "打开数据库",
    "执行SQL",
    "查询SQL",
    "开始事务",
    "提交事务",
    "回滚事务",
    "关闭数据库",
    "排序",
    "倒序",
    "去重",
    "合并",
    "最大值",
    "最小值",
    "绝对值",
    "四舍五入",
    "现在时间",
    "时间戳",
    "类型",
    "显示",
    "输入",
    "建窗口",
    "加文字",
    "加输入框",
    "加多行文本框",
    "加组合框",
    "加复选框",
    "加单选按钮",
    "加按钮",
    "读输入",
    "改文字",
    "弹窗",
    "弹窗输入",
    "打开界面",
    "加表格",
    "表格加行",
    "表格清空",
    "表格所有行",
    "表格选中行",
    "表格选中序号",
    "表格删行",
    "表格改行",
    "画布",
    "标题",
    "图标",
    "向前走",
    "向后走",
    "左转",
    "右转",
    "抬笔",
    "落笔",
    "画笔颜色",
    "背景颜色",
    "去",
    "笔粗",
    "画圆",
    "停一下",
    "定格",
    "速度",
    "隐藏画笔",
    "关闭动画",
    "刷新画面",
    "清除",
    "写字",
    "开始监听",
    "绑定按键",
    "计算距离",
    "当前X",
    "当前Y",
]


BUILTIN_MODULE_EXPORTS = {
    "文件管理": ["读文件", "写文件", "追加文件"],
    "系统工具": [
        "文件存在",
        "目录存在",
        "创建目录",
        "列出目录",
        "删除文件",
        "删除目录",
        "复制文件",
        "移动文件",
        "重命名",
        "遍历文件",
        "复制目录",
        "压缩目录",
        "解压缩",
        "哈希文本",
        "哈希文件",
        "下载文件",
        "匹配文件",
        "文件信息",
        "目录大小",
        "格式时间",
        "解析时间",
        "写日志",
        "读日志",
        "睡眠",
        "拼路径",
        "绝对路径",
        "当前目录",
        "读环境变量",
        "写环境变量",
        "执行命令",
    ],
    "数据工具": ["解析JSON", "生成JSON", "读JSON", "写JSON", "读CSV", "写CSV", "读INI", "写INI"],
    "网络请求": ["发起请求", "发GET", "发POST", "读响应JSON", "发GET_JSON", "发POST_JSON"],
    "本地数据库": ["打开数据库", "执行SQL", "查询SQL", "关闭数据库", "开始事务", "提交事务", "回滚事务"],
    "图形界面": [
        "建窗口",
        "加文字",
        "加输入框",
        "加多行文本框",
        "加组合框",
        "加复选框",
        "加单选按钮",
        "读输入",
        "改文字",
        "加按钮",
        "弹窗",
        "弹窗输入",
        "打开界面",
        "加表格",
        "表格加行",
        "表格清空",
        "表格所有行",
        "表格选中行",
        "表格选中序号",
        "表格删行",
        "表格改行",
    ],
    "画板": [
        "画布",
        "标题",
        "图标",
        "向前走",
        "向后走",
        "左转",
        "右转",
        "抬笔",
        "落笔",
        "画笔颜色",
        "背景颜色",
        "去",
        "笔粗",
        "画圆",
        "停一下",
        "定格",
        "速度",
        "隐藏画笔",
        "关闭动画",
        "刷新画面",
        "清除",
        "写字",
        "开始监听",
        "绑定按键",
        "计算距离",
        "当前X",
        "当前Y",
    ],
}


AUTOCOMPLETE_SOURCE_PRIORITY = {
    "function": 0,
    "blueprint": 0,
    "variable": 0,
    "alias": 0,
    "module": 0,
    "member": 1,
    "member_func": 1,
    "member_blueprint": 1,
    "member_class": 1,
    "member_var": 1,
    "member_alias": 1,
    "imported": 1,
    "imported_func": 1,
    "imported_blueprint": 1,
    "imported_class": 1,
    "imported_var": 1,
    "imported_alias": 1,
    "builtin": 2,
    "builtin_func": 2,
    "keyword": 3,
    "snippet": 4,
}


IMPORT_SOURCE_GROUP = {
    "function": ("current", "当前文件"),
    "blueprint": ("current", "当前文件"),
    "variable": ("current", "当前文件"),
    "alias": ("current", "当前文件"),
    "module": ("current", "当前文件"),
    "member": ("imported", "已引入"),
    "member_func": ("imported", "已引入"),
    "member_blueprint": ("imported", "已引入"),
    "member_class": ("imported", "已引入"),
    "member_var": ("imported", "已引入"),
    "member_alias": ("imported", "已引入"),
    "imported": ("imported", "已引入"),
    "imported_func": ("imported", "已引入"),
    "imported_blueprint": ("imported", "已引入"),
    "imported_class": ("imported", "已引入"),
    "imported_var": ("imported", "已引入"),
    "imported_alias": ("imported", "已引入"),
    "builtin": ("builtin", "内置能力"),
    "builtin_func": ("builtin", "内置能力"),
    "keyword": ("keyword", "关键字"),
    "snippet": ("snippet", "模板"),
}


def builtin_word_catalog() -> list[str]:
    return list(BUILTIN_WORDS)


def builtin_module_exports(builtin_words: list[str] | None = None) -> dict[str, list[str]]:
    exports = {name: list(items) for name, items in BUILTIN_MODULE_EXPORTS.items()}
    exports["魔法生态库"] = sorted(list(builtin_words or []))
    return exports


def autocomplete_match(candidate: str, prefix: str, fuzzy_enabled: bool = False) -> bool:
    if not candidate:
        return False
    if not prefix:
        return True
    text = str(candidate or "")
    needle = str(prefix or "")
    if text == needle:
        return True
    if text.startswith(needle):
        return True
    if fuzzy_enabled and len(needle) >= 2:
        return needle in text
    return False


def autocomplete_source_priority(source: str) -> int:
    return AUTOCOMPLETE_SOURCE_PRIORITY.get(str(source or "").strip(), 9)


def autocomplete_source_group(source: str) -> tuple[str, str]:
    return IMPORT_SOURCE_GROUP.get(str(source or "").strip(), ("other", "其他"))



__all__ = [
    "BUILTIN_WORDS",
    "BUILTIN_MODULE_EXPORTS",
    "AUTOCOMPLETE_SOURCE_PRIORITY",
    "IMPORT_SOURCE_GROUP",
    "builtin_word_catalog",
    "builtin_module_exports",
    "autocomplete_match",
    "autocomplete_source_priority",
    "autocomplete_source_group",
]
