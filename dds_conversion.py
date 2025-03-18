import os
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading

class DDSConversionFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.input_dir = ""
        self.output_dir = ""
        self.output_format = "PNG"
        self.overwrite_mode = "ask"  # ask/skip/all
        self.processed_files = 0
        self.total_files = 0
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Button(main_frame, text="选择输入目录", command=self.select_input_dir).grid(row=0, column=0, pady=5, sticky=tk.W)
        self.input_label = ttk.Label(main_frame, text="未选择")
        self.input_label.grid(row=0, column=1, padx=10, sticky=tk.W)
        ttk.Button(main_frame, text="选择输出目录", command=self.select_output_dir).grid(row=1, column=0, pady=5, sticky=tk.W)
        self.output_label = ttk.Label(main_frame, text="默认: ./output")
        self.output_label.grid(row=1, column=1, padx=10, sticky=tk.W)
        ttk.Button(main_frame, text="选择输出格式", command=self.select_format).grid(row=2, column=0, pady=5, sticky=tk.W)
        self.format_label = ttk.Label(main_frame, text="当前格式: PNG")
        self.format_label.grid(row=2, column=1, padx=10, sticky=tk.W)
        ttk.Label(main_frame, text="覆盖策略:").grid(row=3, column=0, pady=5, sticky=tk.W)
        self.overwrite_var = tk.StringVar(value="ask")
        ttk.Radiobutton(main_frame, text="逐个询问", variable=self.overwrite_var, value="ask").grid(row=3, column=1, sticky=tk.W)
        ttk.Radiobutton(main_frame, text="全部覆盖", variable=self.overwrite_var, value="all").grid(row=4, column=1, sticky=tk.W)
        ttk.Radiobutton(main_frame, text="全部跳过", variable=self.overwrite_var, value="skip").grid(row=5, column=1, sticky=tk.W)
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.grid(row=6, columnspan=2, pady=15)
        self.log_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10)
        self.log_area.grid(row=7, columnspan=2, sticky=tk.EW)
        ttk.Button(main_frame, text="开始转换", command=self.start_conversion).grid(row=8, columnspan=2, pady=10)

    def select_input_dir(self):
        self.input_dir = filedialog.askdirectory(title="选择包含DDS文件的目录")
        if self.input_dir:
            self.input_label.config(text=self.input_dir)
            self.count_dds_files()

    def select_output_dir(self):
        default_dir = os.path.join(os.path.dirname(__file__), "output")
        self.output_dir = filedialog.askdirectory(title="选择输出目录", initialdir=default_dir)
        if not self.output_dir:
            self.output_dir = default_dir
        self.output_label.config(text=self.output_dir)

    def select_format(self):
        format_win = tk.Toplevel(self)
        format_win.title("输出格式设置")
        ttk.Label(format_win, text="选择格式:").pack(pady=10)
        self.format_var = tk.StringVar(value=self.output_format)
        for fmt, desc in {"PNG": "支持透明通道，无损压缩", "JPEG": "有损压缩", "BMP": "无压缩", "TIFF": "支持多图层"}.items():
            rb = ttk.Radiobutton(format_win, text=f"{fmt} - {desc}", variable=self.format_var, value=fmt)
            rb.pack(anchor=tk.W, padx=20)
        ttk.Button(format_win, text="确定", command=format_win.destroy).pack(pady=10)
        self.wait_window(format_win)
        self.output_format = self.format_var.get()
        self.format_label.config(text=f"当前格式: {self.output_format}")

    def count_dds_files(self):
        count = 0
        for root, dirs, files in os.walk(self.input_dir):
            for f in files:
                if f.lower().endswith(".dds"):
                    count += 1
        self.total_files = count
        self.progress["maximum"] = count
        self.log_area.insert(tk.END, f"找到 {count} 个DDS文件\n")

    def start_conversion(self):
        if not self.input_dir:
            messagebox.showwarning("警告", "请先选择输入目录")
            return
        self.overwrite_mode = self.overwrite_var.get()
        threading.Thread(target=self.convert_files, daemon=True).start()

    def convert_files(self):
        for root, dirs, files in os.walk(self.input_dir):
            for file in files:
                if file.lower().endswith(".dds"):
                    self.convert_file(root, file)
        messagebox.showinfo("完成", f"成功转换 {self.processed_files}/{self.total_files} 个文件\n跳过 {self.total_files - self.processed_files} 个文件")

    def convert_file(self, root, file):
        import subprocess
        input_path = os.path.join(root, file)
        relative_path = os.path.relpath(root, self.input_dir)
        output_dir = os.path.join(self.output_dir, relative_path)
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(file)[0]
        output_path = os.path.join(output_dir, f"{base_name}.{self.output_format.lower()}")
        if os.path.exists(output_path):
            if self.overwrite_mode == "skip":
                self.log_area.insert(tk.END, f"跳过已存在文件: {output_path}\n")
                return
            elif self.overwrite_mode == "ask":
                answer = messagebox.askyesnocancel("文件冲突", f"目标文件已存在:\n{output_path}\n是否覆盖？")
                if answer is None:
                    raise Exception("用户中止操作")
                elif not answer:
                    self.log_area.insert(tk.END, f"用户选择跳过: {output_path}\n")
                    return
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", input_path, "-vf", "format=rgba", "-y", output_path]
        if self.output_format == "JPEG":
            cmd += ["-q:v", "95"]
        try:
            self.log_area.insert(tk.END, f"正在转换: {file} → {output_path}\n")
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.processed_files = getattr(self, 'processed_files', 0) + 1
            self.progress["value"] = self.processed_files
        except subprocess.CalledProcessError as e:
            self.log_area.insert(tk.END, f"转换失败: {file}\n错误信息: {e.stderr.strip()}\n")
