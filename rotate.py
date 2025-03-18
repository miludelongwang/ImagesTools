import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from PIL import Image

OPERATIONS = {
    "顺时针旋转90°": Image.Transpose.ROTATE_90,
    "顺时针旋转180°": Image.Transpose.ROTATE_180,
    "顺时针旋转270°": Image.Transpose.ROTATE_270,
    "水平翻转": Image.Transpose.FLIP_LEFT_RIGHT,
    "垂直翻转": Image.Transpose.FLIP_TOP_BOTTOM
}

class RotationFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.dir_path = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
        # 目录选择区域
        dir_frame = ttk.LabelFrame(self, text="图片目录", padding=10)
        dir_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dir_frame, text="目录路径:").pack(side=tk.LEFT, padx=5)
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_path, width=40)
        self.dir_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(dir_frame, text="浏览", command=self.select_folder).pack(side=tk.LEFT, padx=5)
        
        # 操作选择区域
        op_frame = ttk.LabelFrame(self, text="操作设置", padding=10)
        op_frame.pack(fill=tk.X, pady=5)
        ttk.Label(op_frame, text="选择操作:").pack(side=tk.LEFT, padx=5)
        self.operation_var = tk.StringVar(value="顺时针旋转90°")
        self.operation_cb = ttk.Combobox(op_frame, values=list(OPERATIONS.keys()), state="readonly",
                                         textvariable=self.operation_var, width=12)
        self.operation_cb.pack(side=tk.LEFT, padx=5)
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(self, text="日志信息", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        # 进度条区域
        progress_frame = ttk.Frame(self, padding=10)
        progress_frame.pack(fill=tk.X, pady=5)
        self.progress_label = ttk.Label(progress_frame, text="进度: 0/0")
        self.progress_label.pack(anchor="w")
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # 开始按钮
        self.btn_start = tk.Button(self, text="开始旋转", command=self.start_rotation, bg="green", fg="white")
        self.btn_start.pack(pady=10)

    def select_folder(self):
        folder = filedialog.askdirectory(title="选择图片目录")
        if folder:
            self.dir_path.set(folder)
            self.log_area.insert(tk.END, f"已选择目录: {folder}\n")

    def start_rotation(self):
        folder = self.dir_path.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("错误", "请先选择有效的图片目录")
            return
        threading.Thread(target=self.process_images, args=(folder,), daemon=True).start()

    def process_images(self, folder):
        op = OPERATIONS[self.operation_var.get()]
        supported_exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp')
        try:
            files = [f for f in os.listdir(folder) if f.lower().endswith(supported_exts)]
        except Exception as e:
            messagebox.showerror("错误", f"读取目录失败: {str(e)}")
            return
        total = len(files)
        if total == 0:
            messagebox.showinfo("提示", "所选目录中没有符合要求的图片文件！")
            return
        self.progress_bar["maximum"] = total
        for idx, filename in enumerate(files, start=1):
            filepath = os.path.join(folder, filename)
            try:
                self.log_area.insert(tk.END, f"开始处理: {filename}\n")
                with Image.open(filepath) as img:
                    # 使用 transpose() 执行旋转或翻转操作
                    img.transpose(op).save(filepath, format=img.format)
                self.log_area.insert(tk.END, f"成功处理: {filename}\n")
            except Exception as e:
                self.log_area.insert(tk.END, f"处理失败: {filename} - {str(e)}\n")
            self.progress_bar["value"] = idx
            self.progress_label.config(text=f"进度: {idx}/{total}")
            self.log_area.see(tk.END)
        messagebox.showinfo("完成", "所有文件处理完成！")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("图片旋转工具")
    root.geometry("600x450")
    app = RotationFrame(root)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
