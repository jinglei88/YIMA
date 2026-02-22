# d:\易码\易码编辑器.py
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, simpledialog, ttk
from tkinter import font as tkfont
import sys
import io
import shutil
import re
import builtins
import os

# 将当前目录添加到系统路径，确保能找到 yima 包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 易码 import 执行源码

class 易码IDE:
    def __init__(self, root):
        self.root = root
        self.root.title("易码编辑器 (专业版) - 专为中国人设计的编程工具")
        
        # 维护多标签状态数据
        # 格式: { tab_id: { "filepath": str, "editor": ScrolledText, "line_numbers": Text } }
        self.tabs_data = {}
        # 记录默认寻找目录
        self.workspace_dir = os.path.dirname(os.path.abspath(__file__))
        self._highlight_after_id = None
        
        # 计算系统 DPI 缩放比例 (相对于标准的 96 DPI)
        self.dpi_scale = self.root.winfo_fpixels('1i') / 96.0
        if self.dpi_scale < 1.0:
            self.dpi_scale = 1.0
        
        # 加载并设置窗口图标与小图标
        self.icon_file = None
        try:
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            if os.path.exists(logo_path):
                img = tk.PhotoImage(file=logo_path)
                self.root.iconphoto(True, img)
                # 缩小为侧边栏使用的小图标
                # 高分屏下缩小倍数相应减小，使图标稍微变大
                subsample_factor = max(1, int(18 / self.dpi_scale))
                self.icon_file = img.subsample(subsample_factor, subsample_factor)
        except Exception as e:
            print(f"⚠️ 小提示：找不到图标文件 logo.png：{e}")
            
        # 根据系统缩放重设初始窗口大小
        win_w = int(900 * self.dpi_scale)
        win_h = int(700 * self.dpi_scale)
        self.root.geometry(f"{win_w}x{win_h}")
        self.root.configure(bg="#f5f6f7")
        
        # 字体设定（使用大白话、符合国人习惯的微软雅黑）
        self.font_code = ("Microsoft YaHei", 10)
        self.font_ui = ("Microsoft YaHei", 9)
        
        # 现代暗黑专业主题色调 (VS Code 风)
        self.theme_bg = "#1E1E1E"          # 编辑器 & 控制台主背景
        self.theme_sidebar_bg = "#252526"  # 侧边栏文件树背景
        self.theme_toolbar_bg = "#333333"  # 顶部工具栏 & 状态条背景
        self.theme_fg = "#CCCCCC"          # 默认普通文字颜色
        self.theme_line_bg = "#2D2D30"     # 当前行高亮颜色
        self.theme_gutter_bg = "#1E1E1E"   # 行号区背景色与主区融合
        self.theme_gutter_fg = "#858585"   # 行号文字颜色
        self.theme_sash = "#454545"        # 分割线颜色 (稍微提亮使其起分隔作用但不变宽)
        
        # 定义代码片段 (Snippets) 字典
        self.snippets = {
            "如果": "如果 ‹条件› 就\n    ‹代码›",
            "不然": "不然\n    ‹代码›",
            "否则如果": "否则如果 ‹条件› 就\n    ‹代码›",
            "功能": "功能 ‹名字›(‹参数›)\n    ‹代码›",
            "当": "当 ‹条件› 的时候\n    ‹代码›",
            "重复": "重复 ‹次数› 次\n    ‹代码›",
            "遍历": "遍历 ‹列表› 里的每一个 叫做 ‹元素›\n    ‹代码›",
            "尝试": "尝试\n    ‹可能出错的代码›\n如果出错\n    ‹处理错误›",
            "显示": "显示 ‹内容›",
            "定义图纸": "定义图纸 ‹名字›(‹属性›)\n    它的 ‹属性› = ‹属性›\n\n    功能 ‹方法›()\n        ‹代码›",
        }
        
        # 智能联想词库 (合并了所有常用字面量、系统函数和代码片段)
        self.autocomplete_words = sorted(list(set(
            ["功能", "需要", "返回", "叫做", "尝试", "如果出错",
            "如果", "否则如果", "不然", "当", "的时候", "重复", "次", "遍历", "里的每一个", "停下", "略过",
            "引入", "用", "中的", "输入", "定义图纸", "造一个", "它的",
            "对", "错", "空"] +
            ["排列", "新列表", "加入", "插入", "长度", "删除", "转数字", "转文字", "取随机数",
             "所有键", "所有值", "存在", "截取", "查找", "替换", "分割", "去空格", "包含", "读文件", "写文件", "追加文件",
             "显示", "建窗口", "加文字", "加输入框", "加按钮", "读输入", "改文字", "弹窗", "弹窗输入", "打开界面",
             "画布", "向前走", "向后走", "左转", "右转", "抬笔", "落笔", "笔粗", "画圆", "背景颜色", "定格"] +
            list(self.snippets.keys())
        )))

        # 配置 ttk 全局样式以适配字体缩放与暗黑主题
        style = ttk.Style()
        # 统一使用 clam 主题作为基础以获得更好的跨平台扁平化外观
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        
        # 行高也按比例缩放适配大字体
        scaled_rowheight = int(28 * self.dpi_scale)
        
        # 定制 Treeview
        style.configure("Treeview", font=self.font_ui, rowheight=scaled_rowheight, 
                        background=self.theme_sidebar_bg, foreground=self.theme_fg, fieldbackground=self.theme_sidebar_bg, borderwidth=0)
        style.map('Treeview', background=[('selected', '#37373D')], foreground=[('selected', '#FFFFFF')])
        style.configure("Treeview.Heading", font=("Microsoft YaHei", 9, "bold"), background=self.theme_sidebar_bg, foreground="#CCCCCC", borderwidth=0)
        
        # 定制暗黑简约滚动条
        style.configure("Vertical.TScrollbar", background="#3E3E42", troughcolor=self.theme_sidebar_bg, bordercolor=self.theme_sidebar_bg, arrowcolor="#CCCCCC", relief="flat", borderwidth=0)
        style.configure("Horizontal.TScrollbar", background="#3E3E42", troughcolor=self.theme_sidebar_bg, bordercolor=self.theme_sidebar_bg, arrowcolor="#CCCCCC", relief="flat", borderwidth=0)
        style.map("Vertical.TScrollbar", background=[('active', '#555558')])
        style.map("Horizontal.TScrollbar", background=[('active', '#555558')])
        
        # 定制 Notebook 标签页无缝沉浸式外观
        style.configure("TNotebook", background=self.theme_bg, borderwidth=0, padding=0)
        # 未选中的标签
        style.configure("TNotebook.Tab", font=self.font_ui, padding=[15, 6], background="#2D2D30", foreground="#888888", borderwidth=0, focuscolor=self.theme_bg)
        # 选中的标签完美融入背景 (无底边框)
        style.map("TNotebook.Tab", background=[("selected", self.theme_bg)], foreground=[("selected", "#FFFFFF")], expand=[("selected", [0, 1, 0, 0])])
        
        # 彻底干掉 Notebook 原生的客户端框线
        style.layout("TNotebook.client", [("Notebook.client", {"sticky": "nswe"})])

        self.setup_ui()
        self.setup_tags()
        self.bind_events()

    def setup_ui(self):
        # 顶部工具栏 (更窄，更紧凑)
        toolbar = tk.Frame(self.root, bg=self.theme_toolbar_bg, pady=4, padx=10)
        toolbar.pack(fill=tk.X)
        
        def create_tool_btn(parent, text, cmd, bg=self.theme_toolbar_bg, fg=self.theme_fg, font=self.font_ui):
            return tk.Button(parent, text=text, font=font, bg=bg, fg=fg, activebackground="#505050", activeforeground="#FFFFFF", relief="flat", borderwidth=0, cursor="hand2", padx=10, pady=5, command=cmd)
            
        btn_run = create_tool_btn(toolbar, "▶ 运行代码", self.run_code, bg="#3C813F", fg="#FFFFFF", font=("Microsoft YaHei", 11, "bold"))
        btn_run.pack(side=tk.LEFT, padx=10)
        
        btn_new_proj = create_tool_btn(toolbar, "📁 新建项目", self.new_project)
        btn_new_proj.pack(side=tk.LEFT, padx=5)

        btn_open_proj = create_tool_btn(toolbar, "📂 打开项目", self.open_project)
        btn_open_proj.pack(side=tk.LEFT, padx=5)
        
        tk.Label(toolbar, text=" | ", bg=self.theme_toolbar_bg, fg="#555555").pack(side=tk.LEFT)

        btn_new = create_tool_btn(toolbar, "📄 新建代码", self.clear_code)
        btn_new.pack(side=tk.LEFT, padx=5)
        
        btn_open = create_tool_btn(toolbar, "📂 打开代码(单文件)", self.open_file)
        btn_open.pack(side=tk.LEFT, padx=5)
        
        btn_save = create_tool_btn(toolbar, "💾 保存代码", self.save_file)
        btn_save.pack(side=tk.LEFT, padx=5)

        btn_export = create_tool_btn(toolbar, "📦 导出软件(EXE)", self.export_exe, bg="#0E639C", fg="#FFFFFF")
        btn_export.pack(side=tk.RIGHT, padx=5)

        # 主分割区 (外层水平分割：左拉侧边栏，右拉主界面)
        # 将分割线收拢到极致 1px
        self.main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=1, bg=self.theme_sash, borderwidth=0)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # --- 左侧：资源管理器 (Sidebar) ---
        sidebar_frame = tk.Frame(self.main_paned, bg=self.theme_sidebar_bg)
        tk.Label(sidebar_frame, text="资源管理 EXPLORER", font=("Microsoft YaHei", 8, "bold"), bg=self.theme_sidebar_bg, fg="#888888", anchor="w", padx=15).pack(fill=tk.X, pady=(15, 8))
        
        # 文件列表树容器
        tree_container = tk.Frame(sidebar_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(tree_container, selectmode="browse")
        
        # 滚动条 (垂直 + 水平)
        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        
        tree_container.grid_columnconfigure(0, weight=1)
        tree_container.grid_rowconfigure(0, weight=1)
        
        # 初始给左侧多分配一点空间，防止文字被遮挡
        sidebar_default_width = int(250 * self.dpi_scale)
        self.main_paned.add(sidebar_frame, stretch="never", minsize=sidebar_default_width)
        
        # --- 右侧：内层垂直分割（上代码，下输出） ---
        self.right_paned = tk.PanedWindow(self.main_paned, orient=tk.VERTICAL, sashwidth=1, bg=self.theme_sash, borderwidth=0)
        self.main_paned.add(self.right_paned, stretch="always", minsize=600)
        
        # 代码多标签区 (Notebook)
        editor_frame = tk.Frame(self.right_paned, bg=self.theme_bg, borderwidth=0)
        
        self.notebook = ttk.Notebook(editor_frame, padding=0)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<Button-1>", self.on_tab_click)
        
        self.right_paned.add(editor_frame, stretch="always", minsize=400)
        
        # 输出区
        output_frame = tk.Frame(self.right_paned, bg=self.theme_bg)
        
        # 输出区顶栏
        out_top = tk.Frame(output_frame, bg=self.theme_toolbar_bg)
        out_top.pack(fill=tk.X)
        tk.Label(out_top, text="调试控制台", font=("Microsoft YaHei", 9), bg=self.theme_toolbar_bg, fg="#E0E0E0", anchor="w", padx=15, pady=4).pack(side=tk.LEFT)
        
        terminal_font = ("Consolas" if sys.platform == "win32" else "Courier New", 11)
        self.output = scrolledtext.ScrolledText(output_frame, font=terminal_font, height=9, bg=self.theme_bg, fg="#A8C7FA", state=tk.DISABLED, padx=15, pady=5, spacing1=3, borderwidth=0, relief="flat", insertbackground="#CCCCCC")
        self.output.pack(fill=tk.BOTH, expand=True)
        self.right_paned.add(output_frame, stretch="never", minsize=120)
        
        # 树状图右键菜单
        self.tree_menu = tk.Menu(self.root, tearoff=0, font=self.font_ui)
        self.tree_menu.add_command(label="📄 新建代码文件", command=self.create_new_file_in_tree)
        self.tree_menu.add_command(label="📁 新建文件夹", command=self.create_new_folder_in_tree)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="🗑️ 删除", command=self.delete_item_in_tree)
        
        # 智能弹出提示框 (IntelliSense Listbox)
        self.autocomplete_listbox = tk.Listbox(
            self.root, font=self.font_code, bg=self.theme_sidebar_bg, fg=self.theme_fg, 
            selectbackground="#062F4A", selectforeground="#FFFFFF", 
            borderwidth=1, relief="solid", highlightthickness=0, height=8
        )
        self.autocomplete_listbox.place_forget()
        self.autocomplete_listbox.bind("<Double-Button-1>", self._accept_autocomplete)
        
        # 初始化界面后先加载一次文件树，并创建一个默认代码页
        self.refresh_file_tree()
        self._create_editor_tab("未命名代码.ym")

    def setup_tags(self, editor=None):
        target_editor = editor if editor else self._get_current_editor()
        if not target_editor:
            return
            
        # 设定语法高亮颜色 (采用舒适的现代护眼主题)
        target_editor.tag_configure("Keyword", foreground="#C586C0", font=(self.font_code[0], self.font_code[1], "bold"))  # 紫红：控制流
        target_editor.tag_configure("Define", foreground="#569CD6", font=(self.font_code[0], self.font_code[1], "bold"))   # 蓝色：定义类
        target_editor.tag_configure("Operator", foreground="#D4D4D4") # 灰色：操作符 (不再加粗)
        target_editor.tag_configure("String", foreground="#CE9178")                                         # 棕橙：字符串
        target_editor.tag_configure("Number", foreground="#B5CEA8")                                         # 浅绿：数字
        target_editor.tag_configure("Comment", foreground="#6A9955", font=(self.font_code[0], self.font_code[1], "italic"))# 幽绿：注释
        target_editor.tag_configure("Boolean", foreground="#4FC1FF", font=(self.font_code[0], self.font_code[1], "bold"))  # 亮蓝：布尔值
        target_editor.tag_configure("Builtin", foreground="#DCDCAA", font=(self.font_code[0], self.font_code[1], "bold"))  # 浅黄：内置函数
        
        # 控制台专用标签
        self.output.tag_configure("ConsoleError", foreground="#FF6B6B", font=(self.output.cget("font"),))
        
        # 当前行高亮
        target_editor.tag_configure("CurrentLine", background=self.theme_line_bg)
        
    def bind_events(self, editor=None):
        target_editor = editor if editor else self._get_current_editor()
        if not target_editor:
            return
            
        target_editor.bind("<KeyRelease>", self._schedule_highlight)
        target_editor.bind("<KeyRelease>", self._update_line_numbers, add="+")
        target_editor.bind("<KeyRelease>", self._highlight_current_line, add="+")
        target_editor.bind("<ButtonRelease>", self._highlight_current_line, add="+")
        target_editor.bind("<MouseWheel>", self._update_line_numbers, add="+")
        target_editor.bind("<Configure>", self._update_line_numbers, add="+")
        
        # 智能回车换行与自动缩进
        target_editor.bind("<Return>", self._auto_indent)
        
        # Tab 键代码片段补全 / 多行缩进 / 占位符跳转
        target_editor.bind("<Tab>", self._handle_tab)
        target_editor.bind("<Shift-Tab>", self._handle_shift_tab)
        
        # 绑定资源管理器双击事件和右键菜单事件
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<Button-3>", self.popup_tree_menu) 
        
        # 绑定 Tab 切换事件以恢复高亮
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # 智能联想按键绑定
        target_editor.bind("<KeyRelease>", self._check_autocomplete, add="+")
        target_editor.bind("<FocusOut>", lambda e: self.autocomplete_listbox.place_forget())
        target_editor.bind("<Button-1>", lambda e: self.autocomplete_listbox.place_forget())
        target_editor.bind("<Up>", self._handle_autocomplete_nav)
        target_editor.bind("<Down>", self._handle_autocomplete_nav)
        target_editor.bind("<Return>", self._handle_autocomplete_accept)
    # ==========================
    # 编辑器核心组件获取
    # ==========================
    def _get_current_tab_id(self):
        try:
            return self.notebook.select()
        except tk.TclError:
            return None

    def _schedule_highlight(self, event=None):
        """防抖高亮，避免每次按键都做全量扫描。"""
        if self._highlight_after_id:
            try:
                self.root.after_cancel(self._highlight_after_id)
            except tk.TclError:
                pass
        self._highlight_after_id = self.root.after(80, self.highlight)
            
    def _get_current_editor(self):
        tab_id = self._get_current_tab_id()
        if tab_id and tab_id in self.tabs_data:
            return self.tabs_data[tab_id]["editor"]
        return None
        
    def _get_current_line_numbers(self):
        tab_id = self._get_current_tab_id()
        if tab_id and tab_id in self.tabs_data:
            return self.tabs_data[tab_id]["line_numbers"]
        return None

    def _update_line_numbers(self, event=None):
        editor = self._get_current_editor()
        line_numbers = self._get_current_line_numbers()
        if not editor or not line_numbers:
            return
            
        line_numbers.config(state=tk.NORMAL)
        line_numbers.delete("1.0", tk.END)
        line_count = editor.index("end-1c").split(".")[0]
        line_numbers_string = "\n".join(str(i) for i in range(1, int(line_count) + 1))
        line_numbers.insert("1.0", line_numbers_string)
        
        # 靠右对齐
        line_numbers.tag_configure("right", justify="right")
        line_numbers.tag_add("right", "1.0", "end")
        
        line_numbers.config(state=tk.DISABLED)
        # 同步滚动位置
        line_numbers.yview_moveto(editor.yview()[0])
        # 同步更新缩进引导线
        self._update_indent_guides()
        
    def _update_indent_guides(self, event=None):
        tab_id = self._get_current_tab_id()
        if not tab_id or tab_id not in self.tabs_data: return
        
        editor = self.tabs_data[tab_id]["editor"]
        canvas = self.tabs_data[tab_id].get("guide_canvas")
        if not canvas: return
        
        canvas.delete("all")
        
        # 缩进引导线颜色
        guide_colors = ["#333333", "#3B3B5A", "#333333", "#3B3B5A"]
        
        try:
            first_line = int(editor.index("@0,0").split(".")[0])
            last_line = int(editor.index(f"@0,{editor.winfo_height()}").split(".")[0])
        except: return
        
        # 第一次扫描：收集每行的缩进级别和位置
        line_data = []
        for line_num in range(first_line, last_line + 1):
            line_text = editor.get(f"{line_num}.0", f"{line_num}.end")
            bbox = editor.bbox(f"{line_num}.0")
            if not bbox: continue
            
            stripped = line_text.lstrip()
            if stripped:
                indent = len(line_text) - len(stripped)
                levels = indent // 4
            else:
                levels = 0  # 空行继承上下文
            
            line_data.append((line_num, levels, bbox))
        
        # 空行继承上一行的缩进级别（让引导线贯穿空行）
        for i in range(len(line_data)):
            if line_data[i][1] == 0 and i > 0:
                prev_levels = line_data[i-1][1]
                # 检查下一个有内容的行的缩进
                next_levels = 0
                for j in range(i+1, len(line_data)):
                    if line_data[j][1] > 0:
                        next_levels = line_data[j][1]
                        break
                # 取前后缩进的较小值
                inherited = min(prev_levels, next_levels) if next_levels > 0 else 0
                if inherited > 0:
                    line_data[i] = (line_data[i][0], inherited, line_data[i][2])
        
        # 绘制引导线
        canvas_width = int(canvas.cget("width"))
        for line_num, levels, bbox in line_data:
            if levels == 0: continue
            _, y, _, h = bbox
            for lvl in range(levels):
                x = 5 + lvl * 6
                if x >= canvas_width - 2: break
                color = guide_colors[lvl % len(guide_colors)]
                canvas.create_line(x, y, x, y + h, fill=color, width=1)
        
    def _highlight_current_line(self, event=None):
        editor = self._get_current_editor()
        if not editor: return
        editor.tag_remove("CurrentLine", "1.0", "end")
        editor.tag_add("CurrentLine", "insert linestart", "insert lineend+1c")
        
    def _auto_indent(self, event=None):
        editor = self._get_current_editor()
        if not editor: return "break"
        
        line_text = editor.get("insert linestart", "insert lineend")
        
        # 由于拦截了 Return，我们需要手动插入换行符
        editor.insert("insert", "\n")
        
        # 获取原来那行的开头空白保持当前缩进
        indent = ""
        for char in line_text:
            if char in [' ', '\t']:
                indent += char
            else:
                break
                
        # 看看上文需不需要额外再加一层缩进
        stripped_prev = line_text.strip()
        # 这些词结尾或者开头的句子通常表示下一行要缩进
        indent_triggers = ["如果", "否则如果", "不然", "尝试", "如果出错", "重复", "功能", "定义图纸", "当", "遍历"]
        
        for trigger in indent_triggers:
            if stripped_prev.startswith(trigger) or stripped_prev.endswith("的时候") or stripped_prev.endswith("就"):
                indent += "    " # 加四个空格
                break
                
        if indent:
            editor.insert("insert", indent)
            
        editor.see("insert")
        self._highlight_current_line()
        return "break"
        
    def _handle_tab(self, event=None):
        editor = self._get_current_editor()
        if not editor: return "break"
        
        import re
        
        # 0. 如果存在多行选区，则执行多行整体右移缩进
        try:
            sel_start = editor.index(tk.SEL_FIRST)
            sel_end = editor.index(tk.SEL_LAST)
            # 区分：如果只是选中行内的一两个字，走替换还是缩进？VS Code 默认选中文本按 Tab 是替换。
            # 这里按照 VSCode 逻辑：如果选中跨越多行，则是块缩进
            if sel_start.split('.')[0] != sel_end.split('.')[0]:
                start_line = int(sel_start.split('.')[0])
                end_line = int(sel_end.split('.')[0])
                # 如果最后一行只选中了开头第0列，该行不缩进
                if sel_end.split('.')[1] == '0':
                    end_line -= 1
                for i in range(start_line, end_line + 1):
                    editor.insert(f"{i}.0", "    ")
                return "break"
        except tk.TclError:
            pass # 没有选中文本
            
        # 1. 尝试跳向下一个 [占位符]
        search_start = editor.index("insert")
        start_idx = editor.search(r"\u2039.+?\u203a", search_start, stopindex="end", regexp=True)
        
        # 2. 获取光标目前所在行的文本内容
        line_text = editor.get("insert linestart", "insert")
        words = line_text.strip().split()
        
        # 3. 如果前面的词匹配了 Snippet 片段关键字，优先执行 Snippet 展开
        if words:
            last_word = words[-1]
            pure_word_match = re.search(r'([\u4e00-\u9fa5a-zA-Z0-9_]+)$', last_word)
            actual_word = pure_word_match.group(1) if pure_word_match else last_word
            
            if actual_word in self.snippets:
                template = self.snippets[actual_word]
                
                # 删除刚刚输入的那个关键字
                start_index = f"insert - {len(actual_word)}c"
                editor.delete(start_index, "insert")
                
                # 插入模板文本
                insert_pos = editor.index("insert")
                
                # 我们要为后面的换行保持和上文一样的缩进
                base_indent = ""
                for char in line_text:
                    if char in [' ', '\t']: base_indent += char
                    else: break
                
                # 注入时每行增加基础缩进
                lines = template.split('\n')
                indented_template = lines[0] # 第一行不需要加因为光标本来就在那个缩进上
                for line in lines[1:]:
                    indented_template += "\n" + base_indent + line
                
                editor.insert("insert", indented_template)
                
                # 展开后重新搜索后面的第一个占位符进行高亮
                search_start = insert_pos
                start_idx = editor.search(r"\u2039.+?\u203a", search_start, stopindex="end", regexp=True)
                if start_idx:
                    match_content = editor.get(start_idx, f"{start_idx} lineend")
                    match_str = re.search(r"\u2039.+?\u203a", match_content)
                    if match_str:
                        end_idx = f"{start_idx} + {len(match_str.group(0))}c"
                        editor.tag_add("sel", start_idx, end_idx)
                        editor.mark_set("insert", start_idx) # 将光标移过来
                        editor.see("insert")
                
                self.highlight()
                return "break" # 阻止默认的 Tab 键行为
                
        # 4. 如果没有触发 Snippet，但下文有一个占位符，直接跃迁过去 (多占位符支持)
        if start_idx:
            match_content = editor.get(start_idx, f"{start_idx} lineend")
            match_str = re.search(r"\u2039.+?\u203a", match_content)
            if match_str:
                end_idx = f"{start_idx} + {len(match_str.group(0))}c"
                editor.tag_remove("sel", "1.0", "end")
                editor.tag_add("sel", start_idx, end_idx)
                editor.mark_set("insert", start_idx)
                editor.see("insert")
                return "break"
                
        # 如果什么都不是，当做正常的单个或选区文本替换/缩进处理
        try:
            editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError: pass
        
        editor.insert("insert", "    ")
        return "break"

    def _handle_shift_tab(self, event=None):
        editor = self._get_current_editor()
        if not editor: return "break"
        
        # 决定要处理哪些行
        try:
            sel_start = editor.index(tk.SEL_FIRST)
            sel_end = editor.index(tk.SEL_LAST)
            start_line = int(sel_start.split('.')[0])
            end_line = int(sel_end.split('.')[0])
            if sel_end.split('.')[1] == '0' and start_line != end_line:
                end_line -= 1
        except tk.TclError:
            # 没有选区时，只回退当前行
            insert_pos = editor.index("insert")
            start_line = int(insert_pos.split('.')[0])
            end_line = start_line
            
        # 执行回退缩进
        for i in range(start_line, end_line + 1):
            line_text = editor.get(f"{i}.0", f"{i}.end")
            # 找到开头的空白字符数
            space_count = 0
            for char in line_text:
                if char == ' ': space_count += 1
                elif char == '\t': space_count += 4 # 临时将 tab 算成 4 空格的权重
                else: break
            
            # 最多拿掉 4 个空格
            remove_count = min(4, space_count)
            if remove_count > 0:
                editor.delete(f"{i}.0", f"{i}.{remove_count}")
                
        return "break"

    def _check_autocomplete(self, event=None):
        # 排除导航键及控制键
        if event and event.keysym in ('Up', 'Down', 'Left', 'Right', 'Return', 'Tab', 'Escape', 'BackSpace', 'space'):
            if event.keysym == 'Escape':
                self.autocomplete_listbox.place_forget()
            return

        editor = self._get_current_editor()
        if not editor: return

        import re
        
        # === 新增：动态提取局部变量词库 ===
        all_text = editor.get("1.0", "end-1c")
        # 寻找所有长度大于等于 2 的连续中英文数字下划线，作为潜在变量/函数名
        local_words = set(re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9_]{2,}', all_text))

        # 提取光标前当前正在输入的连续中英文字符
        line_text = editor.get("insert linestart", "insert")
        match = re.search(r'([\u4e00-\u9fa5a-zA-Z0-9_]+)$', line_text)
        
        if match:
            current_word = match.group(1)
            
            # 1. 匹配系统内置词库
            system_matches = [w for w in self.autocomplete_words if w.startswith(current_word) and w != current_word]
            
            # 2. 匹配动态变量词库 (过滤掉系统里已经有的词汇，防止重复)
            local_matches = [w for w in local_words if w.startswith(current_word) and w != current_word and w not in self.autocomplete_words]

            if system_matches or local_matches:
                self.autocomplete_listbox.delete(0, tk.END)
                
                # 放入系统关键词与代码片段
                for m in system_matches:
                    display_text = f"⚡ {m}" if m in self.snippets else f"   {m}"
                    self.autocomplete_listbox.insert(tk.END, display_text)
                    
                # 放入当前文档提取出的动态变量
                for m in sorted(local_matches):
                    self.autocomplete_listbox.insert(tk.END, f"📌 {m}")
                
                self.autocomplete_listbox.selection_set(0) # 默认选中第一个
                self.autocomplete_listbox.activate(0)
                
                # 计算光标相对于屏幕的坐标来布置 Listbox
                bbox = editor.bbox("insert")
                if bbox:
                    x, y, width, height = bbox
                    # 把绝对坐标转换为 root 的相对坐标
                    root_x = editor.winfo_rootx() - self.root.winfo_rootx() + x
                    root_y = editor.winfo_rooty() - self.root.winfo_rooty() + y + height
                    
                    self.autocomplete_listbox.place(x=root_x + 5, y=root_y + 5)
                    self.autocomplete_listbox.lift()
                return

        # 隐藏提示框
        self.autocomplete_listbox.place_forget()

    def _handle_autocomplete_nav(self, event):
        if not self.autocomplete_listbox.winfo_ismapped():
            return # 交给系统默认处理
            
        current_selection = self.autocomplete_listbox.curselection()
        if not current_selection: return "break"
        
        idx = current_selection[0]
        self.autocomplete_listbox.selection_clear(idx)
        
        if event.keysym == 'Up':
            idx = max(0, idx - 1)
        elif event.keysym == 'Down':
            idx = min(self.autocomplete_listbox.size() - 1, idx + 1)
            
        self.autocomplete_listbox.selection_set(idx)
        self.autocomplete_listbox.activate(idx)
        self.autocomplete_listbox.see(idx)
        return "break" # 阻止光标移动

    def _handle_autocomplete_accept(self, event):
        if self.autocomplete_listbox.winfo_ismapped():
            self._accept_autocomplete()
            return "break" # 阻止真实回车换行发生

    def _accept_autocomplete(self, event=None):
        if not self.autocomplete_listbox.winfo_ismapped(): return
        
        selection = self.autocomplete_listbox.curselection()
        if not selection: return
        
        # 拿到选中的词 (去掉前面的修饰符)
        raw_text = self.autocomplete_listbox.get(selection[0])
        selected_word = raw_text.split(" ", 1)[-1].strip()
        
        editor = self._get_current_editor()
        if not editor: return
        
        line_text = editor.get("insert linestart", "insert")
        import re
        match = re.search(r'([\u4e00-\u9fa5a-zA-Z0-9_]+)$', line_text)
        
        if match:
            current_word = match.group(1)
            # 删除光标前已敲出的残字
            start_index = f"insert - {len(current_word)}c"
            editor.delete(start_index, "insert")
            # 补入全词
            editor.insert("insert", selected_word)
            
            # 高亮一下当前代码
            self.highlight()
            
        self.autocomplete_listbox.place_forget()

    def highlight(self, event=None):
        editor = self._get_current_editor()
        if not editor: return
        self._highlight_after_id = None
        
        code = editor.get("1.0", "end-1c")
        
        # 先清除所有高亮
        for tag in ["Define", "Keyword", "Operator", "String", "Number", "Comment", "Boolean", "Builtin"]:
            editor.tag_remove(tag, "1.0", "end")
            
        # 1. 高亮数字 (包含小数)
        for match in re.finditer(r'\b\d+(\.\d+)?\b', code):
            start_idx = f"1.0 + {match.start()}c"
            end_idx = f"1.0 + {match.end()}c"
            editor.tag_add("Number", start_idx, end_idx)
            
        # 2. 高亮字符串 (双引号包含的内容)
        for match in re.finditer(r'"[^"]*"', code):
            start_idx = f"1.0 + {match.start()}c"
            end_idx = f"1.0 + {match.end()}c"
            editor.tag_add("String", start_idx, end_idx)

        # 3. 高亮注释 (# 开始到行尾)
        for match in re.finditer(r'#.*', code):
            start_idx = f"1.0 + {match.start()}c"
            end_idx = f"1.0 + {match.end()}c"
            editor.tag_add("Comment", start_idx, end_idx)
            
        # 4. 高亮关键字与操作符
        # Define 控制结构定义
        defines = ["功能", "需要", "返回", "叫做", "尝试", "如果出错", "定义图纸", "造一个", "它的"]
        
        # Keyword 流程控制
        keywords = ["如果", "就", "否则如果", "不然",
                   "当", "的时候", "重复", "次", "遍历", "里的每一个",
                   "停下", "略过", "引入", "用", "中的"]
                   
        operators = ["而且", "并且", "或者", "取反", "!",
                     "+", "-", "*", "/", "%", "**", "//", "==", "!=", ">", "<", ">=", "<="]
        
        booleans = ["对", "错", "空"]
        
        builtins_list = ["排列", "新列表", "加入", "插入", "长度", "删除", 
                         "转数字", "转文字", "取随机数",
                         "所有键", "所有值", "存在",
                         "截取", "查找", "替换", "分割", "去空格", "包含",
                         "读文件", "写文件", "追加文件",
                         "显示", "输入",
                         "建窗口", "加文字", "加输入框", "加按钮", "读输入", "改文字", "弹窗", "弹窗输入", "打开界面"]
        
        def apply_tags(word_list, tag_name):
            # 将单词按长度降序排列，保证长词(如有包含关系)优先被匹配
            for kw in sorted(word_list, key=len, reverse=True):
                start = "1.0"
                while True:
                    # 使用精确字面量匹配
                    start = editor.search(kw, start, stopindex="end")
                    if not start:
                        break
                    
                    end = f"{start} + {len(kw)}c"
                    
                    # ★ 全词边界检测：防止 "长度" 匹配到 "长度值"，"错" 匹配到 "错误信息"
                    is_word = True
                    # 检查前一个字符
                    try:
                        prev_char = editor.get(f"{start} - 1c", start)
                        if prev_char and re.match(r'[\u4e00-\u9fa5a-zA-Z0-9_]', prev_char):
                            is_word = False
                    except tk.TclError:
                        pass
                    # 检查后一个字符
                    if is_word:
                        try:
                            next_char = editor.get(end, f"{end} + 1c")
                            if next_char and re.match(r'[\u4e00-\u9fa5a-zA-Z0-9_]', next_char):
                                # 特殊豁免：操作符后面紧跟中文是允许的（如 "==" 后跟条件）
                                if tag_name != "Operator":
                                    is_word = False
                        except tk.TclError:
                            pass
                    
                    # 防止破坏已经高亮的字符串、注释，或者已经被标记的更高优先级结构
                    existing_tags = editor.tag_names(start)
                    conflict_tags = ["String", "Comment", "Define", "Keyword", "Operator", "Boolean", "Builtin"]
                    
                    if is_word and not any(t in existing_tags for t in conflict_tags):
                        editor.tag_add(tag_name, start, end)
                        
                    start = end

        apply_tags(defines, "Define")
        apply_tags(keywords, "Keyword")
        apply_tags(operators, "Operator")
        apply_tags(booleans, "Boolean")
        apply_tags(builtins_list, "Builtin")

    def print_output(self, text, is_error=False):
        try:
            self.output.config(state=tk.NORMAL)
            if is_error or str(text).startswith("❌"):
                self.output.insert(tk.END, text + "\n", "ConsoleError")
            else:
                self.output.insert(tk.END, text + "\n")
            self.output.see(tk.END)
            self.output.config(state=tk.DISABLED)
        except tk.TclError:
            pass  # 窗口已经关闭了，静默忽略

    # ==========================
    # 多标签与文件树管理
    # ==========================
    def refresh_file_tree(self):
        # 清空现有节点
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 添加根节点
        root_node = self.tree.insert("", "end", text="🚀 易码项目目录", open=True)
        
        longest_text = "🚀 易码项目目录" # 假定初始最长
        
        # 遍历工作目录
        try:
            for item in os.listdir(self.workspace_dir):
                path = os.path.join(self.workspace_dir, item)
                if os.path.isdir(path) and item not in [".venv", "__pycache__", ".git", ".idea", ".vscode"]:
                    # 文件夹
                    folder_name = f"📁 {item}"
                    if len(folder_name) > len(longest_text): longest_text = folder_name
                    folder_node = self.tree.insert(root_node, "end", text=folder_name, values=(path, "dir"), open=True)
                    # 仅深入一层
                    for sub_item in os.listdir(path):
                        sub_path = os.path.join(path, sub_item)
                        if sub_path.endswith(".ym"):
                            file_name = f"📄 {sub_item}"
                            # 带了小图标的，其实宽度更大一些，我们可以多算一点字符兜底
                            if len(file_name) > len(longest_text): longest_text = file_name
                            
                            if self.icon_file:
                                self.tree.insert(folder_node, "end", text=f" {sub_item}", image=self.icon_file, values=(sub_path, "file"))
                            else:
                                self.tree.insert(folder_node, "end", text=file_name, values=(sub_path, "file"))
                elif item.endswith(".ym"):
                    # 根目录下的源文件
                    file_name = f"📄 {item}"
                    if len(file_name) > len(longest_text): longest_text = file_name
                    if self.icon_file:
                        self.tree.insert(root_node, "end", text=f" {item}", image=self.icon_file, values=(path, "file"))
                    else:
                        self.tree.insert(root_node, "end", text=file_name, values=(path, "file"))
                        
            # 根据最长文本自适应调整树形视图的实际宽度
            # 要留点缩进的空隙和图标空间
            try:
                measure_font = tkfont.Font(font=self.font_ui)
                # 留出缩进的像素以及图标大致宽度 (大约 40 像素)
                max_pixel_width = measure_font.measure(longest_text) + int(50 * self.dpi_scale)
                self.tree.column("#0", width=max_pixel_width, minwidth=max_pixel_width, stretch=False)
            except Exception as fe:
                print(f"⚠️ 小提示：字体测量计算失败：{fe}")
                
        except Exception as e:
            self.print_output(f"刷新文件树出错: {e}")

    def _create_editor_tab(self, filename, content=""):
        # 检查是否已经打开
        for tab_id, data in self.tabs_data.items():
            if data["filepath"] == filename:
                self.notebook.select(tab_id)
                return
                
        # 创建新的 Tab 容器 (零边距，完全融合)
        tab_frame = tk.Frame(self.notebook, bg=self.theme_bg, borderwidth=0, highlightthickness=0)
        
        行间距上 = 5
        行间距中 = 0
        行间距下 = 5

        # 行号与编辑器（行距必须与编辑器一致，否则会肉眼错位）
        line_numbers = tk.Text(
            tab_frame,
            width=4,
            padx=4,
            pady=10,
            takefocus=0,
            borderwidth=0,
            highlightthickness=0,
            bg=self.theme_gutter_bg,
            fg=self.theme_gutter_fg,
            font=self.font_code,
            spacing1=行间距上,
            spacing2=行间距中,
            spacing3=行间距下,
            state=tk.DISABLED
        )
        line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # 缩进引导线画布 (窄带垂直线指示器)
        guide_canvas = tk.Canvas(tab_frame, width=30, bg=self.theme_gutter_bg, highlightthickness=0, borderwidth=0)
        guide_canvas.pack(side=tk.LEFT, fill=tk.Y)
        
        editor = scrolledtext.ScrolledText(
            tab_frame,
            font=self.font_code,
            undo=True,
            wrap=tk.NONE,
            bg=self.theme_bg,
            fg=self.theme_fg,
            insertbackground="white",
            padx=10,
            pady=10,
            selectbackground="#264F78",
            spacing1=行间距上,
            spacing2=行间距中,
            spacing3=行间距下,
            borderwidth=0,
            highlightthickness=0
        )
        editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 保证拖动滚动条、滚轮滚动、键盘滚动时行号始终同步
        def 同步纵向滚动(first, last):
            try:
                line_numbers.yview_moveto(float(first))
            except tk.TclError:
                return
            self._update_indent_guides()
            if hasattr(editor, "vbar"):
                editor.vbar.set(first, last)

        editor.configure(yscrollcommand=同步纵向滚动)

        def 左侧滚轮转发到编辑器(event):
            if hasattr(event, "num") and event.num == 4:
                editor.yview_scroll(-1, "units")
                return "break"
            if hasattr(event, "num") and event.num == 5:
                editor.yview_scroll(1, "units")
                return "break"

            delta = getattr(event, "delta", 0)
            if delta != 0:
                # Windows 常见 delta=120 的倍数；其他平台兜底按方向滚动
                步长 = int(-delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
                editor.yview_scroll(步长, "units")
                return "break"
            return None

        for 左侧控件 in (line_numbers, guide_canvas):
            左侧控件.bind("<MouseWheel>", 左侧滚轮转发到编辑器)
            左侧控件.bind("<Button-4>", 左侧滚轮转发到编辑器)
            左侧控件.bind("<Button-5>", 左侧滚轮转发到编辑器)
        
        # 插入内容
        editor.insert("1.0", content)
        
        # 添加到 Notebook
        # 提取文件名作为标签标题，并在末尾加上关闭符号
        tab_title = os.path.basename(filename) if filename != "未命名代码.ym" else filename
        self.notebook.add(tab_frame, text=f" {tab_title}   ✖ ")
        self.notebook.select(tab_frame)
        
        # 记录内部数据
        tab_id = self.notebook.select()
        self.tabs_data[tab_id] = {
            "filepath": filename,
            "editor": editor,
            "line_numbers": line_numbers,
            "guide_canvas": guide_canvas
        }
        
        # 绑定事件并执行初始高亮
        self.bind_events(editor)
        self.setup_tags(editor)
        self.highlight(editor)
        self._update_line_numbers(None)
        
    def on_tree_double_click(self, event):
        item = self.tree.selection()
        if not item: return
        item = item[0]
        values = self.tree.item(item, "values")
        
        if values and values[1] == "file":
            filepath = values[0]
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                self._create_editor_tab(filepath, content)
            except Exception as e:
                messagebox.showerror("打开失败", f"无法读取文件：{e}")
                
    def popup_tree_menu(self, event):
        """在树状图上点击右键弹出菜单"""
        # 可以尝试选中右键点击的项
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            
        self.tree_menu.tk_popup(event.x_root, event.y_root)

    def _get_selected_dir_or_root(self):
        """获取当前选择的文件夹路径，没选或者选了文件就返回它的上级"""
        item = self.tree.selection()
        if not item:
            return self.workspace_dir
            
        item = item[0]
        values = self.tree.item(item, "values")
        if not values:
            return self.workspace_dir
            
        path, node_type = values[0], values[1]
        if node_type == "dir":
            return path
        else:
            return os.path.dirname(path)

    def create_new_file_in_tree(self):
        target_dir = self._get_selected_dir_or_root()
        new_name = simpledialog.askstring("新建代码", "请输入新的易码文件名称（不需要打后缀）：", parent=self.root)
        if not new_name: return
        
        if not new_name.endswith(".ym"):
            new_name += ".ym"
            
        new_path = os.path.join(target_dir, new_name)
        if os.path.exists(new_path):
            messagebox.showerror("冲突", "这个名字已经存在啦，换一个吧！")
            return
            
        try:
            with open(new_path, 'w', encoding='utf-8') as f:
                f.write("") # 创建空文件
            self.refresh_file_tree()
            self._create_editor_tab(new_path, "")
        except Exception as e:
            messagebox.showerror("错误", f"创建文件失败: {e}")
            
    def create_new_folder_in_tree(self):
        target_dir = self._get_selected_dir_or_root()
        new_name = simpledialog.askstring("新建文件夹", "请输入新的文件夹名称：", parent=self.root)
        if not new_name: return
        
        new_path = os.path.join(target_dir, new_name)
        if os.path.exists(new_path):
            messagebox.showerror("冲突", "这个文件夹已经存在啦！")
            return
            
        try:
            os.makedirs(new_path)
            self.refresh_file_tree()
        except Exception as e:
            messagebox.showerror("错误", f"创建文件夹失败: {e}")
            
    def delete_item_in_tree(self):
        item = self.tree.selection()
        if not item: return
        item = item[0]
        values = self.tree.item(item, "values")
        if not values: return
        
        path, node_type = values[0], values[1]
        name = os.path.basename(path)
        
        if not messagebox.askyesno("确认删除", f"你确定要永远删除【{name}】吗？\n删除后不可恢复！"):
            return
            
        try:
            if node_type == "dir":
                shutil.rmtree(path)
            else:
                os.remove(path)
                
            self.refresh_file_tree()
            
            # 检查是否有打开的标签卡是在删除的目录/文件里面，有的话关掉它
            tabs_to_close = []
            for tab_id, data in self.tabs_data.items():
                tab_file = data["filepath"]
                if tab_file == path or tab_file.startswith(path + os.sep):
                    tabs_to_close.append(tab_id)
            
            for tab_id in tabs_to_close:
                # 获取它在 tabs 中的 index 然后触发 close_tab
                tabs_list = self.notebook.tabs()
                if tab_id in tabs_list:
                    idx = tabs_list.index(tab_id)
                    self.close_tab(idx)
                    
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {e}")
                
    def on_tab_click(self, event):
        """处理标签页点击，实现点击 X 关闭标签"""
        try:
            index = self.notebook.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return
            
        # 获取被点击标签的边界框
        x, y, width, height = self.notebook.bbox(index)
        
        # 判断点击位置是否在标签的最右侧（X 的位置）
        # 预留大概 25 * dpi_scale 像素作为关闭按钮区域
        close_area_width = int(25 * self.dpi_scale)
        if event.x > (x + width - close_area_width):
            self.close_tab(index)

    def close_tab(self, index):
        """关闭指定索引的标签页"""
        tab_id = self.notebook.tabs()[index]
        
        current_filepath = self.tabs_data[tab_id]["filepath"]
        # 获取编辑器内容检查是否需要保存等（可扩展）
        
        self.notebook.forget(tab_id)
        
        # 销毁组件释放内存
        if tab_id in self.tabs_data:
            self.tabs_data[tab_id]["editor"].destroy()
            self.tabs_data[tab_id]["line_numbers"].destroy()
            if self.tabs_data[tab_id].get("guide_canvas"):
                self.tabs_data[tab_id]["guide_canvas"].destroy()
            del self.tabs_data[tab_id]
            
        # 如果所有标签都关完了，新建一个空白的
        if not self.notebook.tabs():
            self._create_editor_tab("未命名代码.ym", "")
            
    def on_tab_changed(self, event):
        editor = self._get_current_editor()
        if editor:
            self.highlight()
            self._update_line_numbers()

    # ==========================
    # 顶部工具栏行为
    # ==========================
    def run_code(self):
        editor = self._get_current_editor()
        if not editor: return
        
        # 切换运行目录到当前文件所在位置
        tab_id = self._get_current_tab_id()
        filepath = self.tabs_data[tab_id]["filepath"]
        original_cwd = os.getcwd()
        if filepath and filepath != "未命名代码.ym":
            os.chdir(os.path.dirname(os.path.abspath(filepath)))
            
        # 清空上一次的输出
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.config(state=tk.DISABLED)
        
        code = editor.get("1.0", "end-1c")
        if not code.strip():
            self.print_output("提示：当前标签页为空，无法运行。")
            # 恢复工作目录
            if filepath and filepath != "未命名代码.ym": os.chdir(original_cwd)
            return
            
        # 劫持系统标准输出到内存里
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        # 劫持系统输入，改为弹窗，以支持 `输入` 语句
        old_input = builtins.input
        def gui_input(prompt=""):
            # 弹出一个符合国人审美的输入框
            ans = simpledialog.askstring("易码需要你的回答", prompt, parent=self.root)
            return ans if ans is not None else ""
        builtins.input = gui_input
        
        output_str = ""
        try:
            执行源码(code, interactive=False)
            output_str = sys.stdout.getvalue()
            if not output_str.strip():
                output_str = "代码已执行完成，但没有输出。可使用【显示】语句输出结果。"
        except Exception as e:
            output_str = f"❌ 运行报错了: {e}"
        finally:
            sys.stdout = old_stdout
            builtins.input = old_input
            if filepath and filepath != "未命名代码.ym": os.chdir(original_cwd)
            
        self.print_output(output_str, is_error=output_str.startswith("❌"))

    def open_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("易码源代码", "*.ym"), ("所有文件", "*.*")])
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self._create_editor_tab(filepath, content)
            self.refresh_file_tree()
            
    def save_file(self):
        editor = self._get_current_editor()
        tab_id = self._get_current_tab_id()
        if not editor or not tab_id: return
        
        current_filepath = self.tabs_data[tab_id]["filepath"]
        
        # 如果是未命名或者不存在，则要求另存为
        if current_filepath == "未命名代码.ym" or not os.path.exists(current_filepath):
            filepath = filedialog.asksaveasfilename(defaultextension=".ym", filetypes=[("易码源代码", "*.ym")])
            if not filepath: return
            self.tabs_data[tab_id]["filepath"] = filepath
            # 更新 Tab 名字，补上 ✖
            self.notebook.tab(tab_id, text=f" {os.path.basename(filepath)}   ✖ ")
        else:
            filepath = current_filepath
            
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(editor.get("1.0", "end-1c"))
            messagebox.showinfo("保存成功", f"代码已经稳稳地保存在：\n{filepath}")
            self.refresh_file_tree()
        except Exception as e:
            messagebox.showerror("保存失败", f"无法保存文件：{e}")
            
    def clear_code(self):
        base_name = "未命名代码"
        ext = ".ym"
        idx = ""
        counter = 1
        
        # 寻找一个没有被占用的名字（同时检查磁盘和已打开的标签页）
        while True:
            candidate_name = f"{base_name}{idx}{ext}"
            candidate_path = os.path.join(self.workspace_dir, candidate_name)
            
            # 检查文件是否已在磁盘上存在或者已被打开
            already_exists = os.path.exists(candidate_path)
            already_open = False
            for data in self.tabs_data.values():
                if data["filepath"] == candidate_path or data["filepath"] == candidate_name:
                    already_open = True
                    break
            
            if not already_exists and not already_open:
                # 在磁盘上创建空文件
                try:
                    with open(candidate_path, 'w', encoding='utf-8') as f:
                        f.write("")
                except Exception as e:
                    self.print_output(f"❌ 创建文件失败：{e}")
                    return
                # 打开这个真实文件的标签页
                self._create_editor_tab(candidate_path, "")
                # 刷新左侧文件树
                self.refresh_file_tree()
                break
            idx = f"-{counter}"
            counter += 1

    def _close_all_tabs_silently(self):
        # 默默关掉所有的 tab
        tabs = list(self.notebook.tabs())
        for t in tabs:
            tab_id = t
            self.notebook.forget(tab_id)
            if tab_id in self.tabs_data:
                self.tabs_data[tab_id]["editor"].destroy()
                self.tabs_data[tab_id]["line_numbers"].destroy()
                if self.tabs_data[tab_id].get("guide_canvas"):
                    self.tabs_data[tab_id]["guide_canvas"].destroy()
                del self.tabs_data[tab_id]

    def open_project(self):
        dir_path = filedialog.askdirectory(title="选择易码项目文件夹")
        if dir_path:
            self.workspace_dir = dir_path
            self.refresh_file_tree()
            self._close_all_tabs_silently()
            self.clear_code() # 打开项目后默认给个空页面

    def new_project(self):
        dir_path = filedialog.askdirectory(title="选择一个空文件夹作为新项目")
        if dir_path:
            # 检查文件夹是否为空
            if os.listdir(dir_path):
                if not messagebox.askyesno("提示", "这个文件夹里好像已经有东西了，确定要在这里建易码项目吗？\n（最好选择一个完全空的文件夹哦）"):
                    return
            
            main_file = os.path.join(dir_path, "主程序.ym")
            if not os.path.exists(main_file):
                try:
                    with open(main_file, "w", encoding="utf-8") as f:
                        f.write("# 在这里开始你的易码大作\n显示 \"你好，易码世界！\"\n")
                except Exception as e:
                    messagebox.showerror("创建失败", f"无法创建文件：{e}")
                    return
                    
            self.workspace_dir = dir_path
            self.refresh_file_tree()
            self._close_all_tabs_silently()
            
            with open(main_file, "r", encoding="utf-8") as f:
                content = f.read()
            self._create_editor_tab(main_file, content)

    def export_exe(self):
        editor = self._get_current_editor()
        if not editor: return
        源码内容 = editor.get("1.0", "end-1c")
        if not 源码内容.strip():
            messagebox.showwarning("无法打包", "代码是空的，先写点啥吧！")
            return

        # 创建一个自定义的打包设置对话框
        dlg = tk.Toplevel(self.root)
        dlg.title("📦 导出易码软件")
        # 居中显示
        win_w = int(500 * self.dpi_scale)
        win_h = int(350 * self.dpi_scale)
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (win_w // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (win_h // 2)
        dlg.geometry(f"{win_w}x{win_h}+{x}+{y}")
        dlg.resizable(False, False)
        dlg.configure(bg=self.theme_sidebar_bg)
        dlg.transient(self.root) # 保持在主窗口前
        dlg.grab_set() # 独占焦点

        # 标题区域
        tk.Label(dlg, text="生成独立的 Windows 软件 (EXE)", font=("Microsoft YaHei", 14, "bold"), bg=self.theme_sidebar_bg, fg="#FFFFFF").pack(pady=(20, 10))

        form_frame = tk.Frame(dlg, bg=self.theme_sidebar_bg)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

        # 1. 保存位置
        tk.Label(form_frame, text="存到哪里：", font=self.font_ui, bg=self.theme_sidebar_bg, fg=self.theme_fg).grid(row=0, column=0, sticky="e", pady=10)
        path_var = tk.StringVar()
        path_entry = tk.Entry(form_frame, textvariable=path_var, width=30, font=self.font_ui, bg=self.theme_bg, fg=self.theme_fg, insertbackground="#CCCCCC", relief="flat", highlightthickness=1, highlightbackground=self.theme_sash, highlightcolor="#0E639C")
        path_entry.grid(row=0, column=1, sticky="w", pady=10, ipady=3)
        
        tab_id = self._get_current_tab_id()
        当前文件名 = "我的易码软件"
        if tab_id and self.tabs_data[tab_id]["filepath"] != "未命名代码.ym":
            当前文件名, _ = os.path.splitext(os.path.basename(self.tabs_data[tab_id]["filepath"]))
        path_var.set(os.path.join(os.path.expanduser("~"), "Desktop", f"{当前文件名}.exe")) # 默认放桌面

        def browse_save_path():
            filepath = filedialog.asksaveasfilename(
                title="选择保存位置", defaultextension=".exe", filetypes=[("Windows 软件", "*.exe")], parent=dlg,
                initialfile=f"{当前文件名}.exe"
            )
            if filepath: path_var.set(filepath)
            
        def create_browse_btn(parent, cmd):
            return tk.Button(parent, text="浏览...", command=cmd, bg=self.theme_toolbar_bg, fg=self.theme_fg, activebackground="#505050", activeforeground="#FFFFFF", relief="flat", borderwidth=0, cursor="hand2")

        create_browse_btn(form_frame, browse_save_path).grid(row=0, column=2, padx=(10, 0), pady=10, ipadx=5, ipady=2)

        # 2. 个性图标
        tk.Label(form_frame, text="个性图标：", font=self.font_ui, bg=self.theme_sidebar_bg, fg=self.theme_fg).grid(row=1, column=0, sticky="e", pady=10)
        icon_var = tk.StringVar()
        icon_entry = tk.Entry(form_frame, textvariable=icon_var, width=30, font=self.font_ui, bg=self.theme_bg, fg=self.theme_fg, insertbackground="#CCCCCC", relief="flat", highlightthickness=1, highlightbackground=self.theme_sash, highlightcolor="#0E639C")
        icon_entry.insert(0, "(留空则使用默认易码图标)")
        icon_entry.config(foreground="#666666")
        icon_entry.grid(row=1, column=1, sticky="w", pady=10, ipady=3)
        
        def on_icon_focus_in(e):
            if icon_entry.get() == "(留空则使用默认易码图标)":
                icon_entry.delete(0, "end")
                icon_entry.config(foreground=self.theme_fg)
                
        def on_icon_focus_out(e):
            if not icon_entry.get():
                icon_entry.insert(0, "(留空则使用默认易码图标)")
                icon_entry.config(foreground="#666666")
                
        icon_entry.bind("<FocusIn>", on_icon_focus_in)
        icon_entry.bind("<FocusOut>", on_icon_focus_out)

        def browse_icon():
            filepath = filedialog.askopenfilename(
                title="选择 .ico 图标", filetypes=[("Windows 图标文件", "*.ico")], parent=dlg
            )
            if filepath:
                icon_entry.config(foreground=self.theme_fg)
                icon_var.set(filepath)
                
        create_browse_btn(form_frame, browse_icon).grid(row=1, column=2, padx=(10, 0), pady=10, ipadx=5, ipady=2)

        # 3. 运行模式 (黑框)
        tk.Label(form_frame, text="运行模式：", font=self.font_ui, bg=self.theme_sidebar_bg, fg=self.theme_fg).grid(row=2, column=0, sticky="e", pady=10)
        mode_var = tk.IntVar(value=1) # 默认 1 (显示控制台)
        radio_frame = tk.Frame(form_frame, bg=self.theme_sidebar_bg)
        radio_frame.grid(row=2, column=1, columnspan=2, sticky="w")
        ttk.Radiobutton(radio_frame, text="代码黑框版 (带文字调试口)", variable=mode_var, value=1).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(radio_frame, text="纯净窗口版 (隐藏黑框，适用画板/弹窗)", variable=mode_var, value=2).pack(side=tk.LEFT)

        # Configure custom style for dark ttk radiobuttons
        style = ttk.Style()
        style.configure("Dark.TRadiobutton", background=self.theme_sidebar_bg, foreground=self.theme_fg)
        for child in radio_frame.winfo_children():
            child.configure(style="Dark.TRadiobutton")

        # 底部按钮
        btn_frame = tk.Frame(dlg, bg=self.theme_sidebar_bg)
        btn_frame.pack(fill=tk.X, pady=(10, 20), padx=30)
        
        def start_packing():
            target_path = path_var.get().strip()
            if not target_path:
                messagebox.showerror("抱歉", "得给我一个保存地址呀！", parent=dlg)
                return
                
            icon_path = icon_var.get().strip()
            if icon_path == "(留空则使用默认易码图标)":
                icon_path = None
                
            隐藏黑框 = (mode_var.get() == 2)
            
            dlg.destroy() # 关闭弹窗开始干活
            
            import threading
            import tempfile
            
            self.print_output("=============================\n开始编译并打包 EXE。该过程需要调用底层工具链，可能持续几十秒到几分钟。\n=============================")
            
            def 打印进度(文字):
                self.root.after(0, lambda: self.print_output(文字))

            def 后台打包():
                try:
                    临时目录 = tempfile.gettempdir()
                    临时ym = os.path.join(临时目录, "_易码源码编译缓冲.ym")
                    with open(临时ym, 'w', encoding='utf-8') as f:
                        f.write(源码内容)
                        
                    from 易码打包工具 import 编译并打包
                    最终编译出来的路径 = 编译并打包(临时ym, 图标路径=icon_path, 隐藏黑框=隐藏黑框, 进度打字机=打印进度)
                    
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    shutil.move(最终编译出来的路径, target_path)
                    
                    self.root.after(0, lambda: messagebox.showinfo("打包完成", f"可执行文件已生成：\n{target_path}"))
                except Exception as e:
                    self.root.after(0, lambda msg=str(e): messagebox.showerror("打包失败了", msg))
                    
            t = threading.Thread(target=后台打包)
            t.daemon = True
            t.start()

        create_browse_btn(btn_frame, dlg.destroy).pack(side=tk.RIGHT, padx=(10, 0))
        tk.Button(btn_frame, text="🚀 立即打包", font=("Microsoft YaHei", 10, "bold"), bg="#0E639C", fg="white", activebackground="#1177BB", activeforeground="white", relief="flat", borderwidth=0, cursor="hand2", padx=15, pady=5, command=start_packing).pack(side=tk.RIGHT)

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
    
    root.mainloop()


