# d:\易码\易码编辑器.py
#
# Ownership Marker (Open Source Prep)
# Author: 景磊 (Jing Lei)
# Copyright (c) 2026 景磊
# Project: 易码 / Yima
# Marker-ID: YIMA-JINGLEI-CORE

__author__ = "景磊"
__copyright__ = "Copyright (c) 2026 景磊"
__marker_id__ = "YIMA-JINGLEI-CORE"

import tkinter as tk
import sys
import os

# 将当前目录添加到系统路径，确保能找到 yima 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from yima.editor_main_ui import (
    clear_feedback_tab as ui_clear_feedback_tab,
    mark_feedback_tab as ui_mark_feedback_tab,
    on_feedback_tab_changed as ui_on_feedback_tab_changed,
    refresh_feedback_tab_badges as ui_refresh_feedback_tab_badges,
    setup_ui as ui_setup_ui,
)
from yima.editor_project_flow import (
    clear_code as ui_clear_code,
    clear_recent_projects as ui_clear_recent_projects,
    close_all_tabs_silently as ui_close_all_tabs_silently,
    confirm_close_all_dirty_tabs as ui_confirm_close_all_dirty_tabs,
    current_open_file as ui_current_open_file,
    init_standard_project_structure as ui_init_standard_project_structure,
    load_project_state as ui_load_project_state,
    new_project as ui_new_project,
    normalize_file_path as ui_normalize_file_path,
    normalize_project_dir as ui_normalize_project_dir,
    open_file as ui_open_file,
    open_project_from_history as ui_open_project_from_history,
    open_recent_project_menu as ui_open_recent_project_menu,
    open_project as ui_open_project,
    pick_project_entry_file as ui_pick_project_entry_file,
    remember_project as ui_remember_project,
    save_file as ui_save_file,
    save_project_state as ui_save_project_state,
    switch_project as ui_switch_project,
    try_restore_last_project as ui_try_restore_last_project,
)
from yima.editor_runtime_flow import (
    clear_output_console as ui_clear_output_console,
    print_output as ui_print_output,
    run_code as ui_run_code,
    write_output_console_intro as ui_write_output_console_intro,
)
from yima.editor_workspace_flow import (
    close_tab as ui_close_tab,
    confirm_tab_close as ui_confirm_tab_close,
    create_editor_tab as ui_create_editor_tab,
    create_new_file_in_tree as ui_create_new_file_in_tree,
    create_new_folder_in_tree as ui_create_new_folder_in_tree,
    delete_item_in_tree as ui_delete_item_in_tree,
    get_selected_dir_or_root as ui_get_selected_dir_or_root,
    on_app_close as ui_on_app_close,
    on_tab_changed as ui_on_tab_changed,
    on_tab_click as ui_on_tab_click,
    on_tab_middle_click as ui_on_tab_middle_click,
    on_tree_double_click as ui_on_tree_double_click,
    popup_tree_menu as ui_popup_tree_menu,
    refresh_file_tree as ui_refresh_file_tree,
)
from yima.editor_search_flow import (
    clear_find_marks as ui_clear_find_marks,
    find_next as ui_find_next,
    find_prev as ui_find_prev,
    focus_find_result as ui_focus_find_result,
    get_symbol_near_cursor as ui_get_symbol_near_cursor,
    highlight_find_matches as ui_highlight_find_matches,
    is_valid_symbol_name as ui_is_valid_symbol_name,
    open_find_dialog as ui_open_find_dialog,
    rename_symbol as ui_rename_symbol,
    replace_all as ui_replace_all,
    replace_one as ui_replace_one,
    symbol_pattern as ui_symbol_pattern,
)
from yima.editor_shortcuts_flow import (
    bind_global_shortcuts as ui_bind_global_shortcuts,
    shortcut_cheatsheet as ui_shortcut_cheatsheet,
    shortcut_find as ui_shortcut_find,
    shortcut_multi_add_next as ui_shortcut_multi_add_next,
    shortcut_multi_select_all as ui_shortcut_multi_select_all,
    shortcut_new as ui_shortcut_new,
    shortcut_next_tab as ui_shortcut_next_tab,
    shortcut_open as ui_shortcut_open,
    shortcut_prev_tab as ui_shortcut_prev_tab,
    shortcut_quick_view as ui_shortcut_quick_view,
    shortcut_rename_symbol as ui_shortcut_rename_symbol,
    shortcut_replace as ui_shortcut_replace,
    shortcut_run as ui_shortcut_run,
    shortcut_save as ui_shortcut_save,
    shortcut_toggle_fold as ui_shortcut_toggle_fold,
    shortcut_unfold_all as ui_shortcut_unfold_all,
)
from yima.editor_feedback_flow import (
    build_issue_items as ui_build_issue_items,
    collect_block_declarations as ui_collect_block_declarations,
    default_module_alias as ui_default_module_alias,
    format_issue_item as ui_format_issue_item,
    get_selected_issue_item as ui_get_selected_issue_item,
    highlight as ui_highlight,
    issue_update_status as ui_issue_update_status,
    jump_to_diagnostic as ui_jump_to_diagnostic,
    on_editor_modified as ui_on_editor_modified,
    on_issue_activate as ui_on_issue_activate,
    run_live_diagnose as ui_run_live_diagnose,
    refresh_issue_list as ui_refresh_issue_list,
    refresh_quick_view as ui_refresh_quick_view,
    schedule_diagnose as ui_schedule_diagnose,
    semantic_analyze as ui_semantic_analyze,
    semantic_locate_yima_module as ui_semantic_locate_yima_module,
    semantic_module_search_paths as ui_semantic_module_search_paths,
    semantic_read_module_export_details as ui_semantic_read_module_export_details,
    semantic_read_module_export_signatures as ui_semantic_read_module_export_signatures,
    semantic_read_module_exports as ui_semantic_read_module_exports,
    set_diagnostic_status as ui_set_diagnostic_status,
    set_issue_detail_text as ui_set_issue_detail_text,
    set_quick_view_text as ui_set_quick_view_text,
    truncate_issue_message as ui_truncate_issue_message,
    update_cursor_status as ui_update_cursor_status,
    update_issue_detail_wrap as ui_update_issue_detail_wrap,
    update_quick_view_wrap as ui_update_quick_view_wrap,
    update_status_main as ui_update_status_main,
)
from yima.editor_export_flow import export_exe as ui_export_exe
from yima.editor_autocomplete_flow import (
    accept_autocomplete as ui_accept_autocomplete,
    autocomplete_match as ui_autocomplete_match,
    autocomplete_current_index as ui_autocomplete_current_index,
    autocomplete_index_from_event as ui_autocomplete_index_from_event,
    autocomplete_is_visible as ui_autocomplete_is_visible,
    autocomplete_select_index as ui_autocomplete_select_index,
    autocomplete_source_group as ui_autocomplete_source_group,
    autocomplete_source_priority as ui_autocomplete_source_priority,
    builtin_signature_of as ui_builtin_signature_of,
    check_autocomplete as ui_check_autocomplete,
    collect_completion_context as ui_collect_completion_context,
    cross_tab_alias_module as ui_cross_tab_alias_module,
    ensure_runtime_builtin_signatures as ui_ensure_runtime_builtin_signatures,
    flash_calltip as ui_flash_calltip,
    format_param_signature as ui_format_param_signature,
    get_module_completion_member_details as ui_get_module_completion_member_details,
    get_module_completion_member_signatures as ui_get_module_completion_member_signatures,
    get_module_completion_members as ui_get_module_completion_members,
    handle_autocomplete_nav as ui_handle_autocomplete_nav,
    hide_autocomplete as ui_hide_autocomplete,
    hide_autocomplete_if_focus_lost as ui_hide_autocomplete_if_focus_lost,
    hide_calltip as ui_hide_calltip,
    is_autocomplete_widget as ui_is_autocomplete_widget,
    on_autocomplete_mouse_press as ui_on_autocomplete_mouse_press,
    on_editor_focus_out as ui_on_editor_focus_out,
    safe_signature_text as ui_safe_signature_text,
    schedule_calltip_update as ui_schedule_calltip_update,
    show_autocomplete_candidates as ui_show_autocomplete_candidates,
    show_calltip as ui_show_calltip,
    sort_autocomplete_candidates as ui_sort_autocomplete_candidates,
    trigger_autocomplete as ui_trigger_autocomplete,
    update_calltip as ui_update_calltip,
)
from yima.editor_editing_flow import (
    auto_indent as ui_auto_indent,
    expand_snippet_at_cursor as ui_expand_snippet_at_cursor,
    handle_auto_pairs as ui_handle_auto_pairs,
    handle_return as ui_handle_return,
    handle_shift_tab as ui_handle_shift_tab,
    handle_tab as ui_handle_tab,
    remember_edit_cursor as ui_remember_edit_cursor,
    tab_current_word as ui_tab_current_word,
    tab_jump_to_next_placeholder as ui_tab_jump_to_next_placeholder,
    tab_selection_info as ui_tab_selection_info,
)
from yima.editor_multi_cursor_flow import (
    clear_multi_cursor_mode as ui_clear_multi_cursor_mode,
    convert_ranges_to_points as ui_convert_ranges_to_points,
    find_all_symbol_ranges as ui_find_all_symbol_ranges,
    get_multi_state as ui_get_multi_state,
    handle_editor_left_click as ui_handle_editor_left_click,
    handle_multi_cursor_key as ui_handle_multi_cursor_key,
    index_to_abs as ui_index_to_abs,
    multi_apply_backspace as ui_multi_apply_backspace,
    multi_apply_delete as ui_multi_apply_delete,
    multi_apply_insert_char as ui_multi_apply_insert_char,
    multi_cursor_add_next as ui_multi_cursor_add_next,
    multi_cursor_alt_click as ui_multi_cursor_alt_click,
    multi_cursor_select_all as ui_multi_cursor_select_all,
    render_multi_cursor_state as ui_render_multi_cursor_state,
    sort_unique_indices as ui_sort_unique_indices,
    sync_insert_after_click as ui_sync_insert_after_click,
    update_after_multi_edit as ui_update_after_multi_edit,
)
from yima.editor_binding_flow import (
    bind_events as ui_bind_events,
    build_toolbar_icon as ui_build_toolbar_icon,
    setup_tags as ui_setup_tags,
    style_scrolledtext_vbar as ui_style_scrolledtext_vbar,
)
from yima.editor_outline_flow import (
    clear_all_folds as ui_clear_all_folds,
    count_indent_width as ui_count_indent_width,
    extract_fold_line_from_canvas_hit as ui_extract_fold_line_from_canvas_hit,
    get_block_end_line as ui_get_block_end_line,
    get_selected_outline_item as ui_get_selected_outline_item,
    highlight_current_line as ui_highlight_current_line,
    on_guide_canvas_motion as ui_on_guide_canvas_motion,
    on_outline_activate as ui_on_outline_activate,
    outline_update_status as ui_outline_update_status,
    refresh_outline as ui_refresh_outline,
    schedule_outline_update as ui_schedule_outline_update,
    toggle_fold_by_canvas_hit as ui_toggle_fold_by_canvas_hit,
    toggle_fold_by_line as ui_toggle_fold_by_line,
    toggle_fold_current_line as ui_toggle_fold_current_line,
    toggle_fold_from_outline as ui_toggle_fold_from_outline,
    unfold_all_blocks as ui_unfold_all_blocks,
    update_indent_guides as ui_update_indent_guides,
    update_line_numbers as ui_update_line_numbers,
)
from yima.editor_shell_flow import (
    get_current_editor as ui_get_current_editor,
    get_current_line_numbers as ui_get_current_line_numbers,
    get_current_tab_id as ui_get_current_tab_id,
    get_tab_id_by_editor as ui_get_tab_id_by_editor,
    initialize_editor as ui_initialize_editor,
    schedule_highlight as ui_schedule_highlight,
    update_tab_title as ui_update_tab_title,
)
from yima.editor_logic_core import (
    builtin_module_exports as core_builtin_module_exports,
    builtin_word_catalog as core_builtin_word_catalog,
    export_preflight_check as core_export_preflight_check,
    resolve_export_entry as core_resolve_export_entry,
    sanitize_export_name as core_sanitize_export_name,
)
from yima.editor_cheatsheet_flow import (
    insert_selected_cheatsheet_pattern as ui_insert_selected_cheatsheet_pattern,
    on_cheatsheet_quick_query_changed as ui_on_cheatsheet_quick_query_changed,
    on_cheatsheet_quick_select as ui_on_cheatsheet_quick_select,
    open_cheatsheet as ui_open_cheatsheet,
    open_cheatsheet_from_quick as ui_open_cheatsheet_from_quick,
    refresh_cheatsheet as ui_refresh_cheatsheet,
    refresh_cheatsheet_quick_panel as ui_refresh_cheatsheet_quick_panel,
    setup_cheatsheet_quick_section as ui_setup_cheatsheet_quick_section,
)
from yima.editor_examples_flow import open_examples as ui_open_examples

class 易码IDE:
    def __init__(self, root):
        ui_initialize_editor(self, root)

    def _builtin_word_catalog(self):
        return core_builtin_word_catalog()

    def _builtin_module_exports(self):
        return core_builtin_module_exports(self.builtin_words)

    def _style_scrolledtext_vbar(self, text_widget, parent=None):
        return ui_style_scrolledtext_vbar(self, text_widget, parent=parent)

    def _build_toolbar_icon(self, kind="run", size=16, color="#FFFFFF"):
        return ui_build_toolbar_icon(self, kind=kind, size=size, color=color)

    def setup_ui(self):
        return ui_setup_ui(self)

    def _mark_feedback_tab(self, tab_key, active=True):
        return ui_mark_feedback_tab(self, tab_key, active=active)

    def _clear_feedback_tab(self, tab_key=None):
        return ui_clear_feedback_tab(self, tab_key=tab_key)

    def _refresh_feedback_tab_badges(self):
        return ui_refresh_feedback_tab_badges(self)

    def _on_feedback_tab_changed(self, event=None):
        return ui_on_feedback_tab_changed(self, event=event)

    def setup_tags(self, editor=None):
        return ui_setup_tags(self, editor=editor)
        
    def bind_events(self, editor=None):
        return ui_bind_events(self, editor=editor)
    # ==========================
    # 编辑器核心组件获取
    # ==========================
    def _get_current_tab_id(self):
        return ui_get_current_tab_id(self)

    def _schedule_highlight(self, event=None):
        return ui_schedule_highlight(self, event=event)

    def _get_current_editor(self):
        return ui_get_current_editor(self)

    def _get_current_line_numbers(self):
        return ui_get_current_line_numbers(self)

    def _get_tab_id_by_editor(self, editor):
        return ui_get_tab_id_by_editor(self, editor)

    def _update_tab_title(self, tab_id):
        return ui_update_tab_title(self, tab_id)

    def _set_diagnostic_status(self, text, level="ok"):
        return ui_set_diagnostic_status(self, text, level=level)

    def jump_to_diagnostic(self, event=None):
        return ui_jump_to_diagnostic(self, event=event)

    def _构建问题列表(self, tab_id):
        return ui_build_issue_items(self, tab_id)

    def _缩略问题消息(self, 文本, 最大长度=44):
        return ui_truncate_issue_message(self, 文本, 最大长度=最大长度)

    def _格式化问题列表项(self, item):
        return ui_format_issue_item(self, item)

    def _update_issue_detail_wrap(self, event=None):
        return ui_update_issue_detail_wrap(self, event=event)

    def _set_issue_detail_text(self, text):
        return ui_set_issue_detail_text(self, text)

    def _set_quick_view_text(self, text):
        return ui_set_quick_view_text(self, text)

    def _refresh_issue_list(self):
        return ui_refresh_issue_list(self)

    def _refresh_quick_view(self, event=None):
        return ui_refresh_quick_view(self, event=event)

    def _get_selected_issue_item(self):
        return ui_get_selected_issue_item(self)

    def _issue_update_status(self, event=None):
        return ui_issue_update_status(self, event=event)

    def on_issue_activate(self, event=None):
        return ui_on_issue_activate(self, event=event)

    def _update_status_main(self):
        return ui_update_status_main(self)

    def _update_cursor_status(self, event=None):
        return ui_update_cursor_status(self, event=event)

    def _update_quick_view_wrap(self, event=None):
        return ui_update_quick_view_wrap(self, event=event)

    def _on_editor_modified(self, event):
        return ui_on_editor_modified(self, event)

    def _schedule_diagnose(self, event=None):
        return ui_schedule_diagnose(self, event=event)

    def _默认模块别名(self, 模块名):
        return ui_default_module_alias(self, 模块名)

    def _收集块声明(self, 语句列表):
        return ui_collect_block_declarations(self, 语句列表)

    def _语义模块搜索路径(self, tab_id=None):
        return ui_semantic_module_search_paths(self, tab_id=tab_id)

    def _语义定位易码模块(self, 模块名, tab_id=None):
        return ui_semantic_locate_yima_module(self, 模块名, tab_id=tab_id)

    def _语义读取模块导出(self, 模块路径):
        return ui_semantic_read_module_exports(self, 模块路径)

    def _语义读取模块导出详情(self, 模块路径):
        return ui_semantic_read_module_export_details(self, 模块路径)

    def _语义读取模块导出签名(self, 模块路径):
        return ui_semantic_read_module_export_signatures(self, 模块路径)

    def _语义分析(self, 语法树, tab_id=None):
        return ui_semantic_analyze(self, 语法树, tab_id=tab_id)

    def _run_live_diagnose(self):
        return ui_run_live_diagnose(self)

    def _handle_return(self, event=None):
        return ui_handle_return(self, event=event)

    def _tab_current_word(self, editor):
        return ui_tab_current_word(self, editor)

    def _tab_selection_info(self, editor, insert_idx=None):
        return ui_tab_selection_info(self, editor, insert_idx=insert_idx)

    def _remember_edit_cursor(self, event=None):
        return ui_remember_edit_cursor(self, event=event)

    def _tab_jump_to_next_placeholder(self, editor, from_index):
        return ui_tab_jump_to_next_placeholder(self, editor, from_index)

    def _expand_snippet_at_cursor(self, editor, snippet_word, typed_word=''):
        return ui_expand_snippet_at_cursor(self, editor, snippet_word, typed_word=typed_word)


    def _handle_tab(self, event=None):
        return ui_handle_tab(self, event=event)

    def _handle_auto_pairs(self, event):
        return ui_handle_auto_pairs(self, event)

    def _get_multi_state(self, tab_id=None):
        return ui_get_multi_state(self, tab_id=tab_id)

    def _index_to_abs(self, editor, idx):
        return ui_index_to_abs(self, editor, idx)

    def _sort_unique_indices(self, editor, indices):
        return ui_sort_unique_indices(self, editor, indices)

    def _find_all_symbol_ranges(self, editor, symbol_name):
        return ui_find_all_symbol_ranges(self, editor, symbol_name)

    def _convert_ranges_to_points(self, editor, state, use_end=True):
        return ui_convert_ranges_to_points(self, editor, state, use_end=use_end)

    def _handle_editor_left_click(self, event):
        return ui_handle_editor_left_click(self, event)

    def _sync_insert_after_click(self, event=None):
        return ui_sync_insert_after_click(self, event=event)

    def multi_cursor_alt_click(self, event=None):
        return ui_multi_cursor_alt_click(self, event=event)

    def _render_multi_cursor_state(self, tab_id=None):
        return ui_render_multi_cursor_state(self, tab_id=tab_id)

    def _clear_multi_cursor_mode(self, tab_id=None, keep_query=False):
        return ui_clear_multi_cursor_mode(self, tab_id=tab_id, keep_query=keep_query)

    def _update_after_multi_edit(self, tab_id, status_text=""):
        return ui_update_after_multi_edit(self, tab_id, status_text=status_text)

    def multi_cursor_add_next(self, event=None):
        return ui_multi_cursor_add_next(self, event=event)

    def multi_cursor_select_all(self, event=None):
        return ui_multi_cursor_select_all(self, event=event)

    def _multi_apply_insert_char(self, ch):
        return ui_multi_apply_insert_char(self, ch)

    def _multi_apply_backspace(self):
        return ui_multi_apply_backspace(self)

    def _multi_apply_delete(self):
        return ui_multi_apply_delete(self)

    def _handle_multi_cursor_key(self, event):
        return ui_handle_multi_cursor_key(self, event)

    def _count_indent_width(self, line_text):
        return ui_count_indent_width(self, line_text)

    def _get_block_end_line(self, editor, start_line):
        return ui_get_block_end_line(self, editor, start_line)

    def _schedule_outline_update(self, event=None):
        return ui_schedule_outline_update(self, event=event)

    def _refresh_outline(self):
        return ui_refresh_outline(self)

    def _get_selected_outline_item(self):
        return ui_get_selected_outline_item(self)

    def _outline_update_status(self, event=None):
        return ui_outline_update_status(self, event=event)

    def on_outline_activate(self, event=None):
        return ui_on_outline_activate(self, event=event)

    def _toggle_fold_by_line(self, line_no):
        return ui_toggle_fold_by_line(self, line_no)

    def _clear_all_folds(self, tab_id=None):
        return ui_clear_all_folds(self, tab_id=tab_id)

    def toggle_fold_from_outline(self, event=None):
        return ui_toggle_fold_from_outline(self, event=event)

    def toggle_fold_current_line(self, event=None):
        return ui_toggle_fold_current_line(self, event=event)

    def unfold_all_blocks(self, event=None):
        return ui_unfold_all_blocks(self, event=event)

    def _extract_fold_line_from_canvas_hit(self, canvas, x, y):
        return ui_extract_fold_line_from_canvas_hit(self, canvas, x, y)

    def _toggle_fold_by_canvas_hit(self, event):
        return ui_toggle_fold_by_canvas_hit(self, event)

    def _on_guide_canvas_motion(self, event):
        return ui_on_guide_canvas_motion(self, event)

    def _update_line_numbers(self, event=None):
        return ui_update_line_numbers(self, event=event)

    def _update_indent_guides(self, event=None):
        return ui_update_indent_guides(self, event=event)

    def _highlight_current_line(self, event=None):
        return ui_highlight_current_line(self, event=event)
        
    def _auto_indent(self, event=None):
        return ui_auto_indent(self, event=event)
        
    def _handle_shift_tab(self, event=None):
        return ui_handle_shift_tab(self, event=event)

    def _trigger_autocomplete(self, event=None):
        return ui_trigger_autocomplete(self, event=event)

    def _schedule_calltip_update(self, event=None):
        return ui_schedule_calltip_update(self, event=event)

    def _autocomplete_is_visible(self):
        return ui_autocomplete_is_visible(self)

    def _is_autocomplete_widget(self, 控件):
        return ui_is_autocomplete_widget(self, 控件)

    def _autocomplete_select_index(self, 索引):
        return ui_autocomplete_select_index(self, 索引)

    def _autocomplete_current_index(self):
        return ui_autocomplete_current_index(self)

    def _autocomplete_index_from_event(self, event=None):
        return ui_autocomplete_index_from_event(self, event=event)

    def _on_autocomplete_mouse_press(self, event=None):
        return ui_on_autocomplete_mouse_press(self, event=event)

    def _on_editor_focus_out(self, event=None):
        return ui_on_editor_focus_out(self, event=event)

    def _hide_autocomplete_if_focus_lost(self):
        return ui_hide_autocomplete_if_focus_lost(self)

    def _hide_autocomplete(self):
        return ui_hide_autocomplete(self)

    def _hide_calltip(self):
        return ui_hide_calltip(self)

    def _导出前置检查(self, 源码入口, 打包配置, 输出路径):
        return core_export_preflight_check(
            source_entry=源码入口,
            package_config=打包配置,
            output_path=输出路径,
            workspace_dir=self.workspace_dir,
            tool_root_dir=os.path.dirname(os.path.abspath(__file__)),
            sanitize_export_name_func=self._sanitize_export_name,
            builtin_module_names=set(self._builtin_module_exports().keys()),
            module_locator=lambda 模块名: self._语义定位易码模块(模块名),
        )

    def _flash_calltip(self):
        return ui_flash_calltip(self)

    def _show_calltip(self, editor, 文本, emphasize=False):
        return ui_show_calltip(self, editor, 文本, emphasize=emphasize)

    def _ensure_runtime_builtin_signatures(self):
        return ui_ensure_runtime_builtin_signatures(self)

    def _builtin_signature_of(self, 名称):
        return ui_builtin_signature_of(self, 名称)

    def _update_calltip(self, editor=None, tab_id=None, 全文=None, 行前文本=None, 上下文=None, emphasize=False):
        return ui_update_calltip(
            self,
            editor=editor,
            tab_id=tab_id,
            全文=全文,
            行前文本=行前文本,
            上下文=上下文,
            emphasize=emphasize,
        )

    def _autocomplete_match(self, 候选词, 前缀):
        return ui_autocomplete_match(self, 候选词, 前缀)

    def _autocomplete_source_priority(self, 来源):
        return ui_autocomplete_source_priority(self, 来源)

    def _autocomplete_source_group(self, 来源):
        return ui_autocomplete_source_group(self, 来源)

    def _sort_autocomplete_candidates(self, 候选列表):
        return ui_sort_autocomplete_candidates(self, 候选列表)

    def _格式化参数签名(self, 参数列表):
        return ui_format_param_signature(self, 参数列表)

    def _安全签名文本(self, 可调用对象):
        return ui_safe_signature_text(self, 可调用对象)

    def _跨标签查别名模块(self, 别名, 当前tab_id=None):
        return ui_cross_tab_alias_module(self, 别名, 当前tab_id=当前tab_id)

    def _获取模块补全成员(self, 模块名, tab_id=None):
        return ui_get_module_completion_members(self, 模块名, tab_id=tab_id)

    def _获取模块补全成员详情(self, 模块名, tab_id=None):
        return ui_get_module_completion_member_details(self, 模块名, tab_id=tab_id)

    def _获取模块补全成员签名(self, 模块名, tab_id=None):
        return ui_get_module_completion_member_signatures(self, 模块名, tab_id=tab_id)

    def _收集补全上下文(self, 全文, tab_id=None, 光标行=None):
        return ui_collect_completion_context(self, 全文, tab_id=tab_id, 光标行=光标行)

    def _展示自动补全候选(self, editor, 排序候选):
        return ui_show_autocomplete_candidates(self, editor, 排序候选)

    def _check_autocomplete(self, event=None):
        return ui_check_autocomplete(self, event=event)

    def _handle_autocomplete_nav(self, event):
        return ui_handle_autocomplete_nav(self, event)

    def _accept_autocomplete(self, event=None):
        return ui_accept_autocomplete(self, event=event)

    def bind_global_shortcuts(self):
        return ui_bind_global_shortcuts(self)

    def _shortcut_save(self, event=None):
        return ui_shortcut_save(self, event=event)

    def _shortcut_open(self, event=None):
        return ui_shortcut_open(self, event=event)

    def _shortcut_new(self, event=None):
        return ui_shortcut_new(self, event=event)

    def _shortcut_cheatsheet(self, event=None):
        return ui_shortcut_cheatsheet(self, event=event)

    def _shortcut_run(self, event=None):
        return ui_shortcut_run(self, event=event)

    def _shortcut_multi_add_next(self, event=None):
        return ui_shortcut_multi_add_next(self, event=event)

    def _shortcut_multi_select_all(self, event=None):
        return ui_shortcut_multi_select_all(self, event=event)

    def _shortcut_find(self, event=None):
        return ui_shortcut_find(self, event=event)

    def _shortcut_replace(self, event=None):
        return ui_shortcut_replace(self, event=event)

    def _shortcut_rename_symbol(self, event=None):
        return ui_shortcut_rename_symbol(self, event=event)

    def _shortcut_quick_view(self, event=None):
        return ui_shortcut_quick_view(self, event=event)

    def _shortcut_next_tab(self, event=None):
        return ui_shortcut_next_tab(self, event=event)

    def _shortcut_prev_tab(self, event=None):
        return ui_shortcut_prev_tab(self, event=event)

    def _shortcut_toggle_fold(self, event=None):
        return ui_shortcut_toggle_fold(self, event=event)

    def _shortcut_unfold_all(self, event=None):
        return ui_shortcut_unfold_all(self, event=event)

    def _symbol_pattern(self, name):
        return ui_symbol_pattern(self, name)

    def _is_valid_symbol_name(self, name):
        return ui_is_valid_symbol_name(self, name)

    def _get_symbol_near_cursor(self, editor):
        return ui_get_symbol_near_cursor(self, editor)

    def rename_symbol(self, event=None):
        return ui_rename_symbol(self, event=event)

    def _clear_find_marks(self, editor=None):
        return ui_clear_find_marks(self, editor=editor)

    def _highlight_find_matches(self, event=None):
        return ui_highlight_find_matches(self, event=event)

    def _focus_find_result(self, start_idx, end_idx, query):
        return ui_focus_find_result(self, start_idx, end_idx, query)

    def _find_next(self, event=None):
        return ui_find_next(self, event=event)

    def _find_prev(self, event=None):
        return ui_find_prev(self, event=event)

    def _replace_one(self, event=None):
        return ui_replace_one(self, event=event)

    def _replace_all(self, event=None):
        return ui_replace_all(self, event=event)

    def open_find_dialog(self, event=None, focus_replace=False):
        return ui_open_find_dialog(self, event=event, focus_replace=focus_replace)

    def highlight(self, event=None):
        return ui_highlight(self, event=event)

    def print_output(self, text, is_error=False):
        return ui_print_output(self, text, is_error=is_error)

    def _write_output_console_intro(self):
        return ui_write_output_console_intro(self)

    def _clear_output_console(self, keep_intro=True):
        return ui_clear_output_console(self, keep_intro=keep_intro)

    # ==========================
    # 项目记录（上次项目 / 历史项目）
    # ==========================
    def _normalize_project_dir(self, path):
        return ui_normalize_project_dir(self, path)

    def _normalize_file_path(self, path):
        return ui_normalize_file_path(self, path)

    def _load_project_state(self):
        return ui_load_project_state(self)

    def _save_project_state(self):
        return ui_save_project_state(self)

    def _remember_project(self, dir_path, active_file=None):
        return ui_remember_project(self, dir_path, active_file=active_file)

    def _current_open_file(self):
        return ui_current_open_file(self)

    def _pick_project_entry_file(self, project_dir, preferred_file=None):
        return ui_pick_project_entry_file(self, project_dir, preferred_file=preferred_file)

    def _初始化标准项目结构(self, project_dir):
        return ui_init_standard_project_structure(self, project_dir)

    def _switch_project(self, dir_path, preferred_file=None, create_blank_if_empty=True):
        return ui_switch_project(self, dir_path, preferred_file=preferred_file, create_blank_if_empty=create_blank_if_empty)

    def _try_restore_last_project(self):
        return ui_try_restore_last_project(self)

    def open_recent_project_menu(self):
        return ui_open_recent_project_menu(self)

    def _open_project_from_history(self, project_dir):
        return ui_open_project_from_history(self, project_dir)

    def clear_recent_projects(self):
        return ui_clear_recent_projects(self)

    # ==========================
    # 多标签与文件树管理
    # ==========================
    def refresh_file_tree(self):
        return ui_refresh_file_tree(self)

    def _create_editor_tab(self, filename, content=""):
        return ui_create_editor_tab(self, filename, content)
        
    def on_tree_double_click(self, event):
        return ui_on_tree_double_click(self, event)
                
    def popup_tree_menu(self, event):
        return ui_popup_tree_menu(self, event)

    def _get_selected_dir_or_root(self):
        return ui_get_selected_dir_or_root(self)

    def create_new_file_in_tree(self):
        return ui_create_new_file_in_tree(self)
            
    def create_new_folder_in_tree(self):
        return ui_create_new_folder_in_tree(self)
            
    def delete_item_in_tree(self):
        return ui_delete_item_in_tree(self)
                
    def on_tab_click(self, event):
        return ui_on_tab_click(self, event)

    def on_tab_middle_click(self, event):
        return ui_on_tab_middle_click(self, event)

    def close_tab(self, index):
        return ui_close_tab(self, index)

    def _confirm_tab_close(self, tab_id):
        return ui_confirm_tab_close(self, tab_id)

    def on_app_close(self):
        return ui_on_app_close(self)
            
    def on_tab_changed(self, event):
        return ui_on_tab_changed(self, event)

    # ==========================
    # 顶部工具栏行为
    # ==========================
    def run_code(self):
        return ui_run_code(self)

    def open_file(self):
        return ui_open_file(self)
            
    def save_file(self, event=None, show_message=True):
        return ui_save_file(self, event=event, show_message=show_message)
            
    def clear_code(self):
        return ui_clear_code(self)

    def _close_all_tabs_silently(self):
        return ui_close_all_tabs_silently(self)

    def _confirm_close_all_dirty_tabs(self):
        return ui_confirm_close_all_dirty_tabs(self)

    def open_project(self):
        return ui_open_project(self)

    def new_project(self):
        return ui_new_project(self)

    def _setup_cheatsheet_quick_section(self, sidebar_frame, create_tool_btn):
        return ui_setup_cheatsheet_quick_section(self, sidebar_frame, create_tool_btn)

    def _refresh_cheatsheet_quick_panel(self, event=None):
        return ui_refresh_cheatsheet_quick_panel(self, event=event)

    def _on_cheatsheet_quick_query_changed(self, event=None):
        return ui_on_cheatsheet_quick_query_changed(self, event=event)

    def _on_cheatsheet_quick_select(self, event=None):
        return ui_on_cheatsheet_quick_select(self, event=event)

    def _insert_selected_cheatsheet_pattern(self, event=None):
        return ui_insert_selected_cheatsheet_pattern(self, event=event)

    def _open_cheatsheet_from_quick(self, event=None):
        return ui_open_cheatsheet_from_quick(self, event=event)

    def open_cheatsheet(self, event=None):
        return ui_open_cheatsheet(self, event=event)

    def open_examples(self, event=None):
        return ui_open_examples(self, event=event)

    def _refresh_cheatsheet(self, event=None):
        return ui_refresh_cheatsheet(self, event=event)

    def _sanitize_export_name(self, 名称):
        return core_sanitize_export_name(名称)

    def _解析导出入口(self, 当前文件路径):
        return core_resolve_export_entry(当前文件路径, self.workspace_dir)

    def export_exe(self):
        return ui_export_exe(self)
if __name__ == "__main__":
    # 必须在初始化 Tk 之前宣告 DPI 感知，否则即使点数(pt)字体缩放了，Tkinter本身也会按照低分屏映射引发排版错乱
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    root = tk.Tk()

    app = 易码IDE(root)
    # 不再需要外部强行插入欢迎代码，逻辑已在 init 默认建 tab
    
    # 窗口居中
    root.update_idletasks()
    w = root.winfo_screenwidth()
    h = root.winfo_screenheight()
    size = tuple(int(_) for _ in root.geometry().split('+')[0].split('x'))
    x = w/2 - size[0]/2
    y = h/2 - size[1]/2
    root.geometry("%dx%d+%d+%d" % (size[0], size[1], x, y))
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        # 允许在终端用 Ctrl+C 结束，不打印 traceback。
        try:
            root.destroy()
        except Exception:
            pass
