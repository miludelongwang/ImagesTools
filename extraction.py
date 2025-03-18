import os
import shutil
import zipfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime

class ExtractionFrame(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.match_rules = []  # 保存多条文件名匹配规则，格式为 (匹配方式, 匹配文本)
        self.create_widgets()

    def create_widgets(self):
        # 输入目录选择
        input_frame = ttk.Frame(self)
        input_frame.pack(pady=10, padx=10, fill=tk.X)
        ttk.Label(input_frame, text="输入目录:").pack(side=tk.LEFT)
        self.input_entry = ttk.Entry(input_frame, width=50)
        self.input_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="浏览", command=self.select_input_folder).pack(side=tk.LEFT)

        # 是否包含子目录
        subdir_frame = ttk.Frame(self)
        subdir_frame.pack(pady=5, padx=10, fill=tk.X)
        self.subdirs_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(subdir_frame, text="包括子目录", variable=self.subdirs_var).pack(side=tk.LEFT)

        # 提取方案选择（新增“删除文件”操作）
        scheme_frame = ttk.Frame(self)
        scheme_frame.pack(pady=10, padx=10, fill=tk.X)
        ttk.Label(scheme_frame, text="提取方案:").pack(side=tk.LEFT)
        self.scheme_var = tk.StringVar(value="复制文件")
        self.scheme_combobox = ttk.Combobox(
            scheme_frame,
            textvariable=self.scheme_var,
            state="readonly",
            values=["复制文件", "移动文件", "压缩为ZIP", "生成文件列表", "删除文件"]
        )
        self.scheme_combobox.pack(side=tk.LEFT, padx=5)
        self.scheme_combobox.bind("<<ComboboxSelected>>", self.scheme_changed)

        # 输出目标选择（复制、移动选择目录；压缩和生成列表选择文件路径；删除文件不需要输出目标）
        output_frame = ttk.Frame(self)
        output_frame.pack(pady=10, padx=10, fill=tk.X)
        ttk.Label(output_frame, text="输出目标:").pack(side=tk.LEFT)
        self.output_entry = ttk.Entry(output_frame, width=40)
        self.output_entry.pack(side=tk.LEFT, padx=5)
        self.output_button = ttk.Button(output_frame, text="选择", command=self.select_output_target)
        self.output_button.pack(side=tk.LEFT)

        # 文件过滤器设置
        filters_frame = ttk.LabelFrame(self, text="文件过滤器设置", padding=10)
        filters_frame.pack(pady=10, padx=10, fill=tk.X)

        # 文件类型过滤（逗号分隔）
        filetype_frame = ttk.Frame(filters_frame)
        filetype_frame.pack(fill=tk.X, pady=2)
        ttk.Label(filetype_frame, text="文件类型 (如 jpg, png, txt):").pack(side=tk.LEFT)
        self.filetype_entry = ttk.Entry(filetype_frame, width=40)
        self.filetype_entry.pack(side=tk.LEFT, padx=5)

        # 最小文件大小 (KB)
        min_size_frame = ttk.Frame(filters_frame)
        min_size_frame.pack(fill=tk.X, pady=2)
        ttk.Label(min_size_frame, text="最小大小 (KB):").pack(side=tk.LEFT)
        self.min_size_entry = ttk.Entry(min_size_frame, width=10)
        self.min_size_entry.pack(side=tk.LEFT, padx=5)

        # 最大文件大小 (KB)
        max_size_frame = ttk.Frame(filters_frame)
        max_size_frame.pack(fill=tk.X, pady=2)
        ttk.Label(max_size_frame, text="最大大小 (KB):").pack(side=tk.LEFT)
        self.max_size_entry = ttk.Entry(max_size_frame, width=10)
        self.max_size_entry.pack(side=tk.LEFT, padx=5)

        # 修改后日期限制
        mod_after_frame = ttk.Frame(filters_frame)
        mod_after_frame.pack(fill=tk.X, pady=2)
        ttk.Label(mod_after_frame, text="修改后日期 (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.mod_after_entry = ttk.Entry(mod_after_frame, width=15)
        self.mod_after_entry.pack(side=tk.LEFT, padx=5)

        # 修改前日期限制
        mod_before_frame = ttk.Frame(filters_frame)
        mod_before_frame.pack(fill=tk.X, pady=2)
        ttk.Label(mod_before_frame, text="修改前日期 (YYYY-MM-DD):").pack(side=tk.LEFT)
        self.mod_before_entry = ttk.Entry(mod_before_frame, width=15)
        self.mod_before_entry.pack(side=tk.LEFT, padx=5)

        # 多条文件名匹配规则（并集逻辑）
        filename_multi_frame = ttk.LabelFrame(filters_frame, text="文件名多条匹配规则 (并集)", padding=10)
        filename_multi_frame.pack(fill=tk.X, pady=5)

        # 显示规则列表
        self.match_rules_listbox = tk.Listbox(filename_multi_frame, height=4)
        self.match_rules_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # 添加、删除规则的控件
        add_rule_frame = ttk.Frame(filename_multi_frame)
        add_rule_frame.pack(side=tk.RIGHT, padx=5, fill=tk.Y)
        ttk.Label(add_rule_frame, text="匹配方式:").pack()
        self.multi_match_type_var = tk.StringVar(value="包含")
        self.multi_match_type_box = ttk.Combobox(
            add_rule_frame,
            textvariable=self.multi_match_type_var,
            state="readonly",
            values=["包含", "以…开始", "以…结束", "完全匹配"]
        )
        self.multi_match_type_box.pack(pady=2)
        ttk.Label(add_rule_frame, text="匹配文本:").pack()
        self.multi_match_text_entry = ttk.Entry(add_rule_frame, width=20)
        self.multi_match_text_entry.pack(pady=2)
        ttk.Button(add_rule_frame, text="添加规则", command=self.add_match_rule).pack(pady=5)
        ttk.Button(add_rule_frame, text="删除选中规则", command=self.delete_selected_rule).pack(pady=2)

        # 开始运行按钮
        action_frame = ttk.Frame(self)
        action_frame.pack(pady=10)
        ttk.Button(action_frame, text="开始运行", command=self.start_extraction).pack()

        # 日志显示区域
        log_frame = ttk.Frame(self)
        log_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def scheme_changed(self, event):
        scheme = self.scheme_var.get()
        # 删除文件不需要输出目标
        if scheme == "删除文件":
            self.output_entry.delete(0, tk.END)
            self.output_entry.config(state="disabled")
            self.output_button.config(state="disabled")
        else:
            self.output_entry.config(state="normal")
            self.output_button.config(state="normal")
            self.output_entry.delete(0, tk.END)

    def select_input_folder(self):
        folder = filedialog.askdirectory(title="选择输入目录")
        if folder:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, folder)

    def select_output_target(self):
        scheme = self.scheme_var.get()
        # 对于复制、移动操作选择目录；对于ZIP和生成文件列表选择文件路径
        if scheme in ["复制文件", "移动文件"]:
            folder = filedialog.askdirectory(title="选择输出目录")
            if folder:
                self.output_entry.delete(0, tk.END)
                self.output_entry.insert(0, folder)
        elif scheme == "压缩为ZIP":
            file = filedialog.asksaveasfilename(title="选择输出ZIP文件",
                                                defaultextension=".zip",
                                                filetypes=[("ZIP文件", "*.zip")])
            if file:
                self.output_entry.delete(0, tk.END)
                self.output_entry.insert(0, file)
        elif scheme == "生成文件列表":
            file = filedialog.asksaveasfilename(title="选择输出列表文件",
                                                defaultextension=".txt",
                                                filetypes=[("文本文件", "*.txt")])
            if file:
                self.output_entry.delete(0, tk.END)
                self.output_entry.insert(0, file)

    def add_match_rule(self):
        text = self.multi_match_text_entry.get().strip()
        mode = self.multi_match_type_var.get()
        if text:
            rule_str = f"{mode}: {text}"
            self.match_rules.append((mode, text))
            self.match_rules_listbox.insert(tk.END, rule_str)
            self.multi_match_text_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("提示", "请输入匹配文本")

    def delete_selected_rule(self):
        sel = self.match_rules_listbox.curselection()
        if sel:
            index = sel[0]
            del self.match_rules[index]
            self.match_rules_listbox.delete(index)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def get_file_list(self, directory, include_subdirs=True):
        files_found = []
        if include_subdirs:
            for root, _, files in os.walk(directory):
                for f in files:
                    full_path = os.path.join(root, f)
                    if os.path.isfile(full_path):
                        files_found.append(full_path)
        else:
            for f in os.listdir(directory):
                full_path = os.path.join(directory, f)
                if os.path.isfile(full_path):
                    files_found.append(full_path)
        filtered_files = []
        filetypes = [x.strip().lower() for x in self.filetype_entry.get().split(",") if x.strip()]
        min_size = float(self.min_size_entry.get()) if self.min_size_entry.get() else None
        max_size = float(self.max_size_entry.get()) if self.max_size_entry.get() else None
        mod_after_date = datetime.strptime(self.mod_after_entry.get(), "%Y-%m-%d") if self.mod_after_entry.get() else None
        mod_before_date = datetime.strptime(self.mod_before_entry.get(), "%Y-%m-%d") if self.mod_before_entry.get() else None

        for file in files_found:
            filename = os.path.basename(file)
            ext = os.path.splitext(file)[1][1:].lower()
            if filetypes and ext not in filetypes:
                continue
            size_kb = os.path.getsize(file) / 1024.0
            if min_size and size_kb < min_size:
                continue
            if max_size and size_kb > max_size:
                continue
            mod_time = datetime.fromtimestamp(os.path.getmtime(file))
            if mod_after_date and mod_time < mod_after_date:
                continue
            if mod_before_date and mod_time > mod_before_date:
                continue

            # 多条文件名匹配规则（并集逻辑）：只要满足任意一条规则即可
            if self.match_rules:
                matched = any(
                    (mtype == "包含" and mtext in filename) or
                    (mtype == "以…开始" and filename.startswith(mtext)) or
                    (mtype == "以…结束" and filename.endswith(mtext)) or
                    (mtype == "完全匹配" and filename == mtext)
                    for mtype, mtext in self.match_rules
                )
                if not matched:
                    continue

            filtered_files.append(file)
        return filtered_files

    def start_extraction(self):
        input_dir = self.input_entry.get()
        scheme = self.scheme_var.get()
        include_subdirs = self.subdirs_var.get()

        if not os.path.isdir(input_dir):
            messagebox.showerror("错误", "请输入有效的输入目录")
            return

        # 对于复制、移动、压缩和生成列表操作，需验证输出目标；删除文件操作不需要输出目标
        if scheme not in ["删除文件"] and not self.output_entry.get():
            messagebox.showerror("错误", "请输入有效的输出路径")
            return

        files = self.get_file_list(input_dir, include_subdirs)
        self.log(f"共找到 {len(files)} 个符合条件的文件")

        try:
            if scheme == "复制文件":
                output = self.output_entry.get()
                for file in files:
                    rel = os.path.relpath(file, input_dir) if include_subdirs else os.path.basename(file)
                    dest = os.path.join(output, rel)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.copy2(file, dest)
                    self.log(f"复制: {file} -> {dest}")
            elif scheme == "移动文件":
                output = self.output_entry.get()
                for file in files:
                    rel = os.path.relpath(file, input_dir) if include_subdirs else os.path.basename(file)
                    dest = os.path.join(output, rel)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    shutil.move(file, dest)
                    self.log(f"移动: {file} -> {dest}")
            elif scheme == "压缩为ZIP":
                output = self.output_entry.get()
                with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file in files:
                        arcname = os.path.relpath(file, input_dir) if include_subdirs else os.path.basename(file)
                        zipf.write(file, arcname)
                        self.log(f"添加进压缩包: {arcname}")
                self.log(f"ZIP 文件保存到 {output}")
            elif scheme == "生成文件列表":
                output = self.output_entry.get()
                with open(output, 'w', encoding='utf-8') as f:
                    for file in files:
                        f.write(file + "\n")
                        self.log(f"列表记录: {file}")
                self.log(f"文件列表保存到 {output}")
            elif scheme == "删除文件":
                # 删除操作前，先询问用户确认删除操作
                if not messagebox.askyesno("确认删除", "确定要删除所有符合条件的文件吗？此操作不可恢复！"):
                    return
                for file in files:
                    os.remove(file)
                    self.log(f"删除: {file}")
            messagebox.showinfo("完成", "文件提取操作完成！")
        except Exception as e:
            self.log(f"发生错误: {e}")
            messagebox.showerror("错误", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    root.title("文件提取工具")
    root.geometry("780x700")
    app = ExtractionFrame(root)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
