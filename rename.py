import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

class RenameFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.folder_path = ""
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 目录选择区
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=0, column=0, sticky="w")
        ttk.Label(dir_frame, text="选择目录：").pack(side=tk.LEFT)
        self.folder_entry = ttk.Entry(dir_frame, width=40)
        self.folder_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(dir_frame, text="浏览", command=self.select_folder).pack(side=tk.LEFT)

        # 前缀、后缀及起始数字输入区
        param_frame = ttk.Frame(main_frame)
        param_frame.grid(row=1, column=0, pady=10, sticky="w")
        ttk.Label(param_frame, text="文件名前缀：").grid(row=0, column=0, sticky="w")
        self.prefix_var = tk.StringVar()
        self.prefix_entry = ttk.Entry(param_frame, textvariable=self.prefix_var, width=20)
        self.prefix_entry.grid(row=0, column=1, padx=5)
        ttk.Label(param_frame, text="文件名后缀：").grid(row=1, column=0, sticky="w")
        self.suffix_var = tk.StringVar()
        self.suffix_entry = ttk.Entry(param_frame, textvariable=self.suffix_var, width=20)
        self.suffix_entry.grid(row=1, column=1, padx=5)
        ttk.Label(param_frame, text="起始数字：").grid(row=2, column=0, sticky="w")
        self.start_var = tk.StringVar(value="0")
        self.start_entry = ttk.Entry(param_frame, textvariable=self.start_var, width=10)
        self.start_entry.grid(row=2, column=1, padx=5, sticky="w")
        # 提示说明：前后缀可为空
        hint_label = ttk.Label(param_frame, text="注：文件名前缀和后缀可以为空", font=("Arial", 9), foreground="gray")
        hint_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(2,10))
        
        # 示例显示区
        self.example_label = ttk.Label(param_frame, text="示例：前缀000后缀.png", foreground="gray")
        self.example_label.grid(row=4, column=0, columnspan=2, pady=5, sticky="w")
        
        # 当用户输入前缀、后缀或起始数字时更新示例
        self.prefix_var.trace_add("write", self.update_example)
        self.suffix_var.trace_add("write", self.update_example)
        self.start_var.trace_add("write", self.update_example)

        # 日志区域
        self.log_area = scrolledtext.ScrolledText(main_frame, height=10)
        self.log_area.grid(row=5, column=0, pady=10, sticky="nsew")

        # 开始重命名按钮
        ttk.Button(main_frame, text="开始重命名", command=self.start_rename).grid(row=6, column=0, pady=10)

        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)

    def update_example(self, *args):
        prefix = self.prefix_var.get()
        suffix = self.suffix_var.get()
        try:
            start = int(self.start_var.get())
        except:
            start = 0
        ext = ".txt"  # 默认后缀
        if self.folder_path:
            file_list = [f for f in os.listdir(self.folder_path) if os.path.isfile(os.path.join(self.folder_path, f))]
            if file_list:
                file_list.sort(key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)])
                ext = os.path.splitext(file_list[0])[1]
                if ext == "":
                    ext = ".txt"
            total_files = len(file_list)
            max_num = start + total_files - 1 if total_files > 0 else start
            pad_length = len(str(max_num))
        else:
            pad_length = 3  # 默认3位
        sample = f"示例：{prefix}{str(start).zfill(pad_length)}{suffix}{ext}"
        self.example_label.config(text=sample)

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if self.folder_path:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, self.folder_path)
            file_list = [f for f in os.listdir(self.folder_path) if os.path.isfile(os.path.join(self.folder_path, f))]
            self.log_area.delete("1.0", tk.END)
            self.log_area.insert(tk.END, f"找到 {len(file_list)} 个文件\n")
            self.update_example()

    def start_rename(self):
        if not self.folder_path:
            messagebox.showerror("错误", "请先选择目录")
            return

        try:
            start = int(self.start_var.get())
        except:
            messagebox.showerror("错误", "起始数字无效")
            return

        prefix = self.prefix_var.get()
        suffix = self.suffix_var.get()

        files = sorted(
            [f for f in os.listdir(self.folder_path) if os.path.isfile(os.path.join(self.folder_path, f))],
            key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]
        )
        total_files = len(files)
        max_num = start + total_files - 1 if total_files > 0 else start
        pad_length = len(str(max_num))
        success = 0
        for idx, f in enumerate(files):
            ext = os.path.splitext(f)[1]
            new_num = start + idx
            new_name = f"{prefix}{str(new_num).zfill(pad_length)}{suffix}{ext}"
            try:
                os.rename(
                    os.path.join(self.folder_path, f),
                    os.path.join(self.folder_path, new_name)
                )
                self.log_area.insert(tk.END, f"{f} → {new_name}\n")
                success += 1
            except Exception as e:
                self.log_area.insert(tk.END, f"错误: {str(e)}\n")
        messagebox.showinfo("完成", f"成功重命名 {success}/{total_files} 个文件")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("批量重命名工具")
    root.geometry("600x400")
    app = RenameFrame(root)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
