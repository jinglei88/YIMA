#!/usr/bin/env python3
"""生成内置示例清单（精写版）。"""

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
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from yima import editor_examples_flow as flow  # noqa: E402


DOMAIN_OBJECTIVE = {
    "语法基础": "变量、分支、循环、函数与异常处理",
    "模块组织": "模块拆分、统一引入与命名空间调用",
    "图纸对象": "图纸定义、对象实例化、属性读写与方法调用",
    "图形界面": "窗口布局、控件事件与界面状态刷新",
    "文件系统": "路径处理、文件读写与 JSON 落盘",
    "网络通信": "HTTP 请求、响应解析与失败重试提示",
    "本地数据库": "SQLite 建表、增删改查与事务边界",
    "综合实战": "多模块协作、数据持久化与可运行交付",
}

RUN_EXPECTATION = {
    "自动可跑": "直接运行后应完整执行示例流程并输出关键结果，过程中不出现异常。",
    "手动交互": "运行后会打开交互界面；按提示完成至少一次操作且无异常即为通过。",
    "需要网络": "运行前请确保联网；请求成功时应返回数据/状态，失败时应有可读错误提示。",
    "本地数据库": "运行会创建或复用本地数据库文件，并输出至少一轮增删改查或事务结果。",
}

# 少量高价值示例使用专门说明，其他由通用规则生成。
EXACT_TEXT = {
    "_测试列表.ym": (
        "用最小样例验证列表与字典的创建、索引、遍历和更新行为，作为容器语义基线。",
        "运行后应看到容器操作结果输出，读写行为与注释一致且无异常。",
    ),
    "欢迎.ym": (
        "面向新手的第一份示例，覆盖输入、输出、判断和循环，帮助快速跑通完整开发闭环。",
        "点击运行后应按步骤输出欢迎与练习结果，界面无报错即可视为通过。",
    ),
    "官方写法总览.ym": (
        "集中展示官方推荐写法，便于在一个文件内快速对照常用语法和模块能力。",
        "运行后应分段输出各语法块结果，可作为语法回归与学习速查基准。",
    ),
    "测试中文引号.ym": (
        "验证中文标点和字符串解析兼容性，避免因输入法差异导致的脚本误判。",
        "运行后字符串应被正确解析并输出，不应出现词法或语法报错。",
    ),
    "点语法测试.ym": (
        "验证点语法在字典/对象场景中的读取与调用语义，确认可读性写法稳定可用。",
        "运行后应输出点语法访问结果，属性读取与方法调用行为符合预期。",
    ),
    "M8猜数字游戏.ym": (
        "通过小游戏练习条件判断、循环与状态更新，理解交互式脚本的控制流组织。",
        "运行后应可反复输入数字并得到提示，猜中后流程结束且无异常。",
    ),
    "经典案例_九九乘法表.ym": (
        "使用双层循环生成标准 9x9 乘法表，练习循环嵌套与文本拼接格式化。",
        "运行后应按行输出乘法表，末行包含 9x9=81 且排版可读。",
    ),
    "经典案例_冒泡排序.ym": (
        "通过冒泡排序示例掌握比较、交换和双重循环，理解基础排序算法实现方式。",
        "运行后应输出排序前后序列，结果需满足升序且元素数量不变。",
    ),
    "经典案例_学生成绩统计.ym": (
        "围绕成绩数据练习列表遍历、条件分段与统计汇总，形成数据分析基础范式。",
        "运行后应输出每段统计和总体结果，计算口径与样例注释一致。",
    ),
    "经典案例_词频统计.ym": (
        "演示文本清洗、分词计数与结果排序流程，构建可复用的文本处理模板。",
        "运行后应输出高频词及次数，词频排序与输入文本相匹配。",
    ),
    "经典案例_图纸对象入门.ym": (
        "聚焦图纸对象的定义、造对象、属性读写与方法调用，建立易码面向对象直觉。",
        "运行后应看到对象属性和方法输出，字段更新前后差异可被验证。",
    ),
    "经典案例_本地数据库增删改查.ym": (
        "以 SQLite 为载体演示建表与增删改查全流程，帮助形成持久化开发基本功。",
        "运行后应输出增删改查各步骤结果，并在本地生成或复用数据库文件。",
    ),
    "经典案例_事务与网络JSON.ym": (
        "把数据库事务和网络 JSON 请求放在同一流程中，展示提交/回滚与接口调用协同。",
        "运行时应看到事务执行与网络请求结果；异常分支需给出明确错误提示。",
    ),
    "经典案例_真实网络请求实战.ym": (
        "演示 GET/POST/JSON 的真实联网调用流程，覆盖请求参数、响应解析和异常处理。",
        "联网运行后应输出状态码与关键返回字段；失败时需展示可诊断的错误信息。",
    ),
    "经典案例_网图下载器.ym": (
        "通过图形界面封装网络下载流程，练习输入校验、下载进度与文件落盘。",
        "运行后输入图片地址应能完成下载并保存到本地，失败场景给出原因提示。",
    ),
    "经典案例_网图下载器_自动测试.ym": (
        "为网图下载器提供自动化验证脚本，确保核心下载链路在改动后仍可回归。",
        "直接运行应自动给出通过/失败结论，无需人工点击界面。",
    ),
    "经典案例_注册登录_GUI数据库.ym": (
        "构建带界面的注册登录流程，覆盖账号校验、密码存储与数据库交互。",
        "运行后应可完成注册与登录操作，界面提示与数据库结果保持一致。",
    ),
    "经典案例_注册登录_自动测试.ym": (
        "对注册登录核心逻辑做自动化回归，确保改动后账号流程仍然稳定。",
        "直接运行应自动执行用例并打印结果，不依赖手工交互。",
    ),
    "经典案例_全模块总览自测.ym": (
        "以一份脚本串联常见模块能力，适合在版本发布前做快速全局自检。",
        "运行后应逐段输出模块检查结果，任一模块异常都应被显式提示。",
    ),
    "经典案例_常用内置能力总测.ym": (
        "集中验证高频内置能力，作为解释器升级后的稳定性回归样本。",
        "运行后应输出每项内置能力的测试结果，并给出总体通过结论。",
    ),
}


CLASSIFY_OVERRIDE: dict[str, tuple[str | None, str | None, str | None]] = {
    "M7图形界面测试.ym": ("进阶", "图形界面", "手动交互"),
    "待办事项本.ym": (None, "图形界面", "手动交互"),
    "M13实战_密码管家.ym": ("实战", "图形界面", "手动交互"),
    "M15网格账号密码本.ym": ("实战", "图形界面", "手动交互"),
    "M14记账本项目/记账本_界面层.ym": ("实战", "图形界面", "手动交互"),
    "M17任务协作台项目/任务协作_界面层.ym": ("实战", "图形界面", "手动交互"),
    "经典案例_注册登录_GUI数据库.ym": ("实战", "图形界面", "手动交互"),
    "M16全量能力测试项目/03_文件系统与JSON.ym": ("实战", "文件系统", "自动可跑"),
    "M16全量能力测试项目/07_GUI手动交互验证.ym": ("实战", "图形界面", "手动交互"),
    "M16全量能力测试项目/08_画板手动交互验证.ym": ("实战", "图形界面", "手动交互"),
}


def _first_hint(path: Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return ""
    for raw in lines[:30]:
        s = raw.strip()
        if not s.startswith("#"):
            continue
        s = s.lstrip("#").strip()
        if not s:
            continue
        if re.fullmatch(r"[=+\-_* ]+", s):
            continue
        if len(s) <= 2:
            continue
        return s
    return ""


def _title_from_rel(rel: str) -> str:
    display = rel[:-3] if rel.lower().endswith(".ym") else rel
    return display.replace("/", " / ")


def _infer_classification(rel: str, name: str) -> tuple[str, str, str]:
    difficulty = flow._infer_difficulty(rel, name)
    domain = flow._infer_domain(rel)
    run_mode = flow._infer_run_mode(rel)
    if difficulty not in flow.DIFFICULTY_VALUES:
        difficulty = "进阶"
    if domain not in flow.DOMAIN_VALUES:
        domain = "语法基础"
    if run_mode not in flow.RUN_MODE_VALUES:
        run_mode = "自动可跑"

    override = CLASSIFY_OVERRIDE.get(rel)
    if override:
        d0, d1, d2 = override
        if d0 in flow.DIFFICULTY_VALUES:
            difficulty = d0
        if d1 in flow.DOMAIN_VALUES:
            domain = d1
        if d2 in flow.RUN_MODE_VALUES:
            run_mode = d2
    return difficulty, domain, run_mode


def _special_text(rel: str) -> tuple[str, str] | None:
    if rel in EXACT_TEXT:
        return EXACT_TEXT[rel]

    if rel.startswith("M16全量能力测试项目/01_"):
        return (
            "全量套件的语法入口，聚焦条件、循环、函数和异常处理的稳定行为。",
            "运行后应输出语法分组结果，核心控制流分支可被逐条验证。",
        )
    if rel.startswith("M16全量能力测试项目/02_"):
        return (
            "全量套件的内置函数与容器文本测试，验证字符串、列表和字典的常见操作。",
            "运行后应输出内置函数执行结果，容器与文本处理行为需与注释一致。",
        )
    if rel.startswith("M16全量能力测试项目/03_"):
        return (
            "全量套件的文件与 JSON 流程测试，覆盖路径、读写和序列化回读。",
            "运行后应生成测试文件并输出 JSON 处理结果，读回内容与写入一致。",
        )
    if rel.startswith("M16全量能力测试项目/04_"):
        return (
            "全量套件的联网与数据库测试，验证接口调用与数据落库在同一流程中的可靠性。",
            "联网运行后应输出请求和数据库结果，异常分支需可读且不中断主流程。",
        )
    if rel.startswith("M16全量能力测试项目/05_"):
        return (
            "全量套件的模块导入与图纸对象测试，验证跨文件调用和对象模型能力。",
            "运行后应输出模块函数与对象方法结果，命名空间访问保持稳定。",
        )
    if rel.startswith("M16全量能力测试项目/06_"):
        return (
            "全量套件的 GUI/画板自动检查，确保界面构建逻辑在非阻塞模式下可回归。",
            "运行后应输出界面检查结果并自动结束，不需要人工点击。",
        )
    if rel.startswith("M16全量能力测试项目/07_"):
        return (
            "全量套件的 GUI 手动验证场景，用于确认按钮事件与状态变化链路正确。",
            "运行后会打开窗口，手工触发操作后应得到对应提示且无异常。",
        )
    if rel.startswith("M16全量能力测试项目/08_"):
        return (
            "全量套件的画板手动验证场景，重点检查绘制交互与窗口生命周期。",
            "运行后会打开画板窗口，完成交互后应看到预期反馈并可正常结束。",
        )
    if rel == "M16全量能力测试项目/主程序.ym":
        return (
            "全量能力测试的统一入口脚本，负责调度各子套件并汇总结果。",
            "运行后应依次触发各套件输出，并给出整体通过/失败信息。",
        )
    if rel == "M16全量能力测试项目/模块_数学工具.ym":
        return (
            "全量项目的本地工具模块示例，演示被主程序统一引入与复用的写法。",
            "该文件被引入后应返回可调用函数；主流程中调用结果需正确。",
        )
    if rel == "M16全量能力测试项目/测试工具.ym":
        return (
            "全量项目的测试辅助模块，封装断言与结果汇总逻辑，提升脚本可维护性。",
            "运行主流程时应看到该工具输出的测试结论，失败项可被定位。",
        )

    if rel.startswith("M14记账本项目/主程序"):
        return (
            "记账本项目入口，负责组织数据层与界面层，演示分层项目的启动流程。",
            "运行后应正常加载账本界面并可进入记账流程，初始化阶段无异常。",
        )
    if rel.startswith("M14记账本项目/记账本_数据层"):
        return (
            "记账本数据层实现，聚焦账单读写、查询与持久化结构约定。",
            "运行相关业务后应正确保存与读取账单数据，字段结构保持一致。",
        )
    if rel.startswith("M14记账本项目/记账本_界面层"):
        return (
            "记账本界面层实现，负责窗口布局、输入交互和账单展示。",
            "运行后应打开界面并可完成至少一次新增/查看操作。",
        )

    if rel.startswith("M17任务协作台项目/主程序"):
        return (
            "任务协作台项目入口，调度数据层、业务层和界面层并完成启动编排。",
            "运行后应完成模块装配并进入主界面，控制台无初始化错误。",
        )
    if rel.startswith("M17任务协作台项目/任务协作_数据层"):
        return (
            "任务协作台数据层，负责任务记录持久化与查询接口。",
            "运行后应可读写任务数据并返回稳定的数据结构。",
        )
    if rel.startswith("M17任务协作台项目/任务协作_业务层"):
        return (
            "任务协作台业务层，封装任务状态流转与规则校验逻辑。",
            "运行相关流程后应输出业务校验结果，非法输入有明确提示。",
        )
    if rel.startswith("M17任务协作台项目/任务协作_界面层"):
        return (
            "任务协作台界面层，负责任务列表展示、操作触发和状态刷新。",
            "运行后应可在界面上完成新增或更新任务并即时看到变化。",
        )
    if rel.startswith("M17任务协作台项目/自动测试"):
        return (
            "任务协作台自动化回归入口，用于批量验证项目核心功能。",
            "直接运行应输出自动测试结论，不需要手工操作窗口。",
        )

    if rel in {"M10综合测试.ym", "M10完善测试.ym"}:
        return (
            "阶段性综合回归脚本，覆盖语法、内置能力和常见边界行为。",
            "运行后应分段输出测试结果，关键场景均通过且无异常。",
        )
    if rel == "M11模块化测试.ym":
        return (
            "聚焦模块拆分、引入与跨文件调用，验证工程化组织方式是否稳定。",
            "运行后应能成功引入模块并输出组合结果，导入链路无报错。",
        )
    if rel == "M11深度测试.ym":
        return (
            "覆盖字符串转义、空容器等边界语义，验证解释器在细节场景下的稳定性。",
            "运行后边界样例应按预期输出，异常场景有明确提示。",
        )
    if rel == "M12容错测试.ym":
        return (
            "专门验证异常处理与容错分支，确保错误不会破坏主执行流程。",
            "运行后应看到 try/catch 分支输出，异常被正确捕获并继续执行。",
        )

    return None


def _build_summary_expected(rel: str, title: str, domain: str, run_mode: str, hint: str) -> tuple[str, str]:
    special = _special_text(rel)
    if special is not None:
        return special

    objective = DOMAIN_OBJECTIVE.get(domain, "核心语法与模块能力")
    scene = hint if hint else title
    summary = f"以「{scene}」为场景，练习{objective}，并形成可迁移到真实项目的实现方式。"

    if "自动测试" in rel:
        expected = "运行后应自动执行断言并输出通过/失败结论，无需人工干预。"
    else:
        expected = RUN_EXPECTATION.get(run_mode, RUN_EXPECTATION["自动可跑"])
    return summary, expected


def build_manifest() -> dict:
    examples: dict[str, dict[str, str]] = {}
    base = flow.BUILTIN_EXAMPLES_DIR
    for path in sorted(base.rglob("*.ym"), key=lambda p: p.as_posix().lower()):
        rel = path.relative_to(base).as_posix()
        title = _title_from_rel(rel)
        difficulty, domain, run_mode = _infer_classification(rel, path.name)
        hint = _first_hint(path)
        summary, expected = _build_summary_expected(rel, title, domain, run_mode, hint)

        examples[rel] = {
            "title": title,
            "summary": summary,
            "expected": expected,
            "difficulty": difficulty,
            "domain": domain,
            "run_mode": run_mode,
        }

    return {
        "version": 3,
        "description": "易码内置示例清单（精写学习目标、预期输出、难度与分类）",
        "examples": examples,
    }


def main() -> int:
    manifest = build_manifest()
    flow.MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] 已生成清单：{flow.MANIFEST_PATH}")
    print(f"[OK] 示例条目数：{len(manifest.get('examples', {}))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
