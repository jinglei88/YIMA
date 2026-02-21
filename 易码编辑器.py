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
from 易码 import 玩弄代码

class 易码IDE:
    def __init__(self, root):
        self.root = root
        self.root.title("易码编辑器 (专业版) - 专为中国人设计的编程工具")
        
        # 维护多标签状态数据
        # 格式: { tab_id: { "filepath": str, "editor": ScrolledText, "line_numbers": Text } }
        self.tabs_data = {}
        # 记录默认寻找目录
        self.workspace_dir = os.path.dirname(os.path.abspath(__file__))
        
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
            print(f"Warning: Could not load logo.png: {e}")
            
        # 根据系统缩放重设初始窗口大小
        win_w = int(900 * self.dpi_scale)
        win_h = int(700 * self.dpi_scale)
        self.root.geometry(f"{win_w}x{win_h}")
        self.root.configure(bg="#f5f6f7")
        
        # 字体设定（使用大白话、符合国人习惯的微软雅黑）
        self.font_code = ("Microsoft YaHei", 12)
        self.font_ui = ("Microsoft YaHei", 9)
        
        # 现代暗色主题色调
        self.theme_bg = "#1E1E1E"          # 编辑器背景色
        self.theme_fg = "#D4D4D4"          # 默认文字颜色
        self.theme_line_bg = "#2D2D30"     # 当前行高亮颜色
        self.theme_gutter_bg = "#252526"   # 行号区背景色
        self.theme_gutter_fg = "#858585"   # 行号文字颜色
        
        # 配置 ttk 全局样式以适配字体缩放
        style = ttk.Style()
        # 统一使用 clam 主题作为基础以获得更好的跨平台扁平化外观
        try: style.theme_use("clam")
        except: pass
        
        # 行高也按比例缩放适配大字体
        scaled_rowheight = int(28 * self.dpi_scale)
        style.configure("Treeview", font=self.font_ui, rowheight=scaled_rowheight) 
        style.configure("Treeview.Heading", font=("Microsoft YaHei", 11, "bold"))
        style.configure("TNotebook.Tab", font=self.font_ui, padding=[8, 4])
        
        self.setup_ui()
        self.setup_tags()
        self.bind_events()

    def setup_ui(self):
        # 顶部工具栏
        toolbar = tk.Frame(self.root, bg="#e0e0e0", pady=8, padx=10)
        toolbar.pack(fill=tk.X)
        
        btn_run = tk.Button(toolbar, text="▶ 运行代码", font=("Microsoft YaHei", 12, "bold"), bg="#4CAF50", fg="white", relief="flat", padx=15, pady=5, command=self.run_code)
        btn_run.pack(side=tk.LEFT, padx=10)
        
        btn_new = tk.Button(toolbar, text="📄 新建代码", font=self.font_ui, relief="flat", padx=10, pady=5, command=self.clear_code)
        btn_new.pack(side=tk.LEFT, padx=5)
        
        btn_open = tk.Button(toolbar, text="📂 打开代码", font=self.font_ui, relief="flat", padx=10, pady=5, command=self.open_file)
        btn_open.pack(side=tk.LEFT, padx=5)
        
        btn_save = tk.Button(toolbar, text="💾 保存代码", font=self.font_ui, relief="flat", padx=10, pady=5, command=self.save_file)
        btn_save.pack(side=tk.LEFT, padx=5)

        btn_export = tk.Button(toolbar, text="📦 导出软件(EXE)", font=self.font_ui, bg="#2196F3", fg="white", relief="flat", padx=10, pady=5, command=self.export_exe)
        btn_export.pack(side=tk.RIGHT, padx=5)

        # 主分割区 (外层水平分割：左拉侧边栏，右拉主界面)
        self.main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=8, bg="#cccccc")
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- 左侧：资源管理器 (Sidebar) ---
        sidebar_frame = tk.Frame(self.main_paned, bg="#f5f6f7")
        tk.Label(sidebar_frame, text="📁 资源管理", font=("Microsoft YaHei", 12, "bold"), bg="#f5f6f7", fg="#333333", anchor="w").pack(fill=tk.X, pady=(0, 5))
        
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
        self.right_paned = tk.PanedWindow(self.main_paned, orient=tk.VERTICAL, sashwidth=8, bg="#cccccc")
        self.main_paned.add(self.right_paned, stretch="always", minsize=600)
        
        # 代码多标签区 (Notebook)
        editor_frame = tk.Frame(self.right_paned, bg="#f5f6f7")
        # tk.Label(editor_frame, text="✏️ 在这里用大白话写代码：", font=("Microsoft YaHei", 12, "bold"), bg="#f5f6f7", fg="#333333", anchor="w").pack(fill=tk.X, pady=(0, 5))
        
        self.notebook = ttk.Notebook(editor_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<Button-1>", self.on_tab_click)
        
        self.right_paned.add(editor_frame, stretch="always", minsize=400)
        
        # 输出区
        output_frame = tk.Frame(self.right_paned, bg="#f5f6f7")
        tk.Label(output_frame, text="📺 电脑运行的结果：", font=("Microsoft YaHei", 12, "bold"), bg="#f5f6f7", fg="#333333", anchor="w").pack(fill=tk.X, pady=(5, 5))
        self.output = scrolledtext.ScrolledText(output_frame, font=self.font_code, height=10, bg="#000000", fg="#4CAF50", state=tk.DISABLED, padx=10, pady=10, spacing1=2)
        self.output.pack(fill=tk.BOTH, expand=True)
        self.right_paned.add(output_frame, stretch="never", minsize=150)
        
        # 树状图右键菜单
        self.tree_menu = tk.Menu(self.root, tearoff=0, font=self.font_ui)
        self.tree_menu.add_command(label="📄 新建代码文件", command=self.create_new_file_in_tree)
        self.tree_menu.add_command(label="📁 新建文件夹", command=self.create_new_folder_in_tree)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="🗑️ 删除", command=self.delete_item_in_tree)
        
        # 初始化界面后先加载一次文件树，并创建一个默认代码页
        self.refresh_file_tree()
        self._create_editor_tab("未命名代码.ym")

    def setup_tags(self, editor=None):
        target_editor = editor if editor else self._get_current_editor()
        if not target_editor:
            return
            
        # 设定语法高亮颜色 (采用舒适的现代护眼主题)
        target_editor.tag_configure("Keyword", foreground="#C586C0", font=("Microsoft YaHei", 15, "bold"))  # 紫红：控制流
        target_editor.tag_configure("Define", foreground="#569CD6", font=("Microsoft YaHei", 15, "bold"))   # 蓝色：定义类
        target_editor.tag_configure("Operator", foreground="#D4D4D4", font=("Microsoft YaHei", 15, "bold")) # 灰色：操作符
        target_editor.tag_configure("String", foreground="#CE9178")                                         # 棕橙：字符串
        target_editor.tag_configure("Number", foreground="#B5CEA8")                                         # 浅绿：数字
        target_editor.tag_configure("Comment", foreground="#6A9955", font=("Microsoft YaHei", 15, "italic"))# 幽绿：注释
        target_editor.tag_configure("Boolean", foreground="#4FC1FF", font=("Microsoft YaHei", 15, "bold"))  # 亮蓝：布尔值
        target_editor.tag_configure("Builtin", foreground="#DCDCAA", font=("Microsoft YaHei", 15, "bold"))  # 浅黄：内置函数
        
        # 当前行高亮
        target_editor.tag_configure("CurrentLine", background=self.theme_line_bg)
        
    def bind_events(self, editor=None):
        target_editor = editor if editor else self._get_current_editor()
        if not target_editor:
            return
            
        target_editor.bind("<KeyRelease>", self.highlight)
        target_editor.bind("<KeyRelease>", self._update_line_numbers, add="+")
        target_editor.bind("<KeyRelease>", self._highlight_current_line, add="+")
        target_editor.bind("<ButtonRelease>", self._highlight_current_line, add="+")
        target_editor.bind("<MouseWheel>", self._update_line_numbers, add="+")
        target_editor.bind("<Configure>", self._update_line_numbers, add="+")
        
        # 智能回车换行与自动缩进
        target_editor.bind("<Return>", self._auto_indent)
        
        # 绑定资源管理器双击事件和右键菜单事件
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<Button-3>", self.popup_tree_menu) 
        
        # 绑定 Tab 切换事件以恢复高亮
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    # ==========================
    # 编辑器核心组件获取
    # ==========================
    def _get_current_tab_id(self):
        try:
            return self.notebook.select()
        except:
            return None
            
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
        indent_triggers = ["如果", "否则如果", "不然的话", "不然", "尝试", "如果出错", "重复", "功能"]
        
        for trigger in indent_triggers:
            if stripped_prev.startswith(trigger) or stripped_prev.endswith("的时候") or stripped_prev.endswith("的话"):
                indent += "    " # 加四个空格
                break
                
        if indent:
            editor.insert("insert", indent)
            
        editor.see("insert")
        self._highlight_current_line()
        return "break"
        
    def highlight(self, event=None):
        editor = self._get_current_editor()
        if not editor: return
        
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
        defines = ["功能", "需要", "学完了", "交出", "叫做", "把", "设定为", "让", "尝试", "如果出错", "结束"]
        
        # Keyword 流程控制
        keywords = ["如果", "的话", "不然的话", "否则如果", "不然",
                   "当", "的时候", "只要", "重复", "次", "取出", "里的每一个",
                   "停下", "略过", "引入"]
                   
        operators = ["加上", "减去", "乘以", "除以", "取余", "拼接", 
                     "大于", "小于", "等于", "不等于", "至少是", "最多是", "是", "不是", 
                     "而且", "并且", "或者", "取反", "反过来说",
                     "+", "-", "*", "/", "%", "===", "==", "!=", ">", "<", ">=", "<="]
        
        booleans = ["对", "错", "无", "空的"]
        
        builtins_list = ["提取", "取第", "排列", "新列表", "加入", "长度", "删除", 
                         "变数字", "转数字", "变文字", "转文字", "取随机数",
                         "所有键", "所有值", "有没有", 
                         "截取", "查找", "替换", "分割", "去空格", "包含",
                         "读文件", "写文件", "追加文件",
                         "显示", "说", "询问", "问",
                         "建窗口", "加文字", "加输入框", "加按钮", "读输入", "改文字", "弹窗", "打开界面"]
        
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
                    
                    # 防止破坏已经高亮的字符串、注释，或者已经被标记的更高优先级结构
                    existing_tags = editor.tag_names(start)
                    conflict_tags = ["String", "Comment", "Define", "Keyword", "Operator", "Boolean", "Builtin"]
                    
                    if not any(t in existing_tags for t in conflict_tags):
                        editor.tag_add(tag_name, start, end)
                        
                    start = end

        apply_tags(defines, "Define")
        apply_tags(keywords, "Keyword")
        apply_tags(operators, "Operator")
        apply_tags(booleans, "Boolean")
        apply_tags(builtins_list, "Builtin")

    def print_output(self, text):
        try:
            self.output.config(state=tk.NORMAL)
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
                print(f"Font measurement failed: {fe}")
                
        except Exception as e:
            self.print_output(f"刷新文件树出错: {e}")

    def _create_editor_tab(self, filename, content=""):
        # 检查是否已经打开
        for tab_id, data in self.tabs_data.items():
            if data["filepath"] == filename:
                self.notebook.select(tab_id)
                return
                
        # 创建新的 Tab 容器
        tab_frame = tk.Frame(self.notebook, bg=self.theme_bg)
        
        # 行号与编辑器
        line_numbers = tk.Text(tab_frame, width=4, padx=4, pady=10, takefocus=0, border=0, bg=self.theme_gutter_bg, fg=self.theme_gutter_fg, font=self.font_code, state=tk.DISABLED)
        line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        editor = scrolledtext.ScrolledText(tab_frame, font=self.font_code, undo=True, wrap=tk.NONE, bg=self.theme_bg, fg=self.theme_fg, insertbackground="white", padx=10, pady=10, selectbackground="#264F78", spacing1=2, spacing3=2)
        editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
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
            "line_numbers": line_numbers
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
            self.print_output("提示：当前标签页是空的，没法运行哦！")
            # 恢复工作目录
            if filepath and filepath != "未命名代码.ym": os.chdir(original_cwd)
            return
            
        # 劫持系统标准输出到内存里
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        # 劫持系统输入，变成弹窗，这样`询问`功能就能在界面里用了
        old_input = builtins.input
        def gui_input(prompt=""):
            # 弹出一个符合国人审美的输入框
            ans = simpledialog.askstring("易码需要你的回答", prompt, parent=self.root)
            return ans if ans is not None else ""
        builtins.input = gui_input
        
        output_str = ""
        try:
            玩弄代码(code, interactive=False)
            output_str = sys.stdout.getvalue()
            if not output_str.strip():
                output_str = "👉 代码顺利跑完了，但没有任何输出。（提示：可以用【显示】把结果打在屏幕上哦）"
        except Exception as e:
            output_str = f"❌ 运行报错了: {e}"
        finally:
            sys.stdout = old_stdout
            builtins.input = old_input
            if filepath and filepath != "未命名代码.ym": os.chdir(original_cwd)
            
        self.print_output(output_str)

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
        self._create_editor_tab("未命名代码.ym", "")

    def export_exe(self):
        import threading
        import tempfile
        import os
        # (shutil is now imported globally)
        
        # 直接询问用户想要把最终的 exe 保存到哪里
        filepath = filedialog.asksaveasfilename(
            title="请选择你生成的 EXE 软件想要存放在哪里",
            defaultextension=".exe", 
            filetypes=[("Windows 独立软件", "*.exe")]
        )
        if not filepath:
            return
        editor = self._get_current_editor()
        if not editor: return
        
        源码内容 = editor.get("1.0", "end-1c")
            
        隐藏黑框 = messagebox.askyesno("打包选项", "这是一个带【自定义图形界面】的程序吗？\n\n- 如果是专门画了窗口的程序，选【是】（运行时隐藏黑色控制台）。\n- 如果是只在黑框框打文字的程序，选【否】。")
        
        self.print_output(f"=============================\n起锅烧油！准备编译生成独立的 EXE 程序（需要调用原生 C 语言等底层工具链重铸你的程序，这可能需要几十秒到几分钟，请耐心等待直到弹窗成功~）\n=============================")
        
        def 打印进度(文字):
            def 更新UI():
                self.print_output(文字)
            self.root.after(0, 更新UI)

        def 后台打包():
            try:
                # 后台偷梁换柱：先保存成临时 ym 给我的编译器用
                临时目录 = tempfile.gettempdir()
                临时ym = os.path.join(临时目录, "_易码源码编译缓冲.ym")
                with open(临时ym, 'w', encoding='utf-8') as f:
                    f.write(源码内容)
                    
                from 易码打包器 import 编译并打包
                最终编译出来的路径 = 编译并打包(临时ym, 隐藏黑框=隐藏黑框, 进度打字机=打印进度)
                
                # 把编译好的文件悄悄移动到用户刚才指定的路径
                if os.path.exists(filepath):
                    os.remove(filepath)
                shutil.move(最终编译出来的路径, filepath)
                
                # 还可以顺便清理一下桌面或其他地方可能残留的缓存
                self.root.after(0, lambda: messagebox.showinfo("大功告成 🎉", f"你的易码原生软件已经脱胎换骨，生成完毕！\n请去这里双击：\n{filepath}"))
            except Exception as e:
                错误信息 = str(e)
                self.root.after(0, lambda msg=错误信息: messagebox.showerror("打包失败了", msg))
                
        # 启动后台线程打包，防止界面卡死
        t = threading.Thread(target=后台打包)
        t.daemon = True
        t.start()

if __name__ == "__main__":
    # 必须在初始化 Tk 之前宣告 DPI 感知，否则即使点数(pt)字体缩放了，Tkinter本身也会按照低分屏映射引发排版错乱
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
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


