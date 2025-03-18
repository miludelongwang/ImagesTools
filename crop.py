import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image
import sys

FILE_EXTS = ('.jpg', '.jpeg', '.png', '.webp')
def resource_path(relative_path):
    """获取打包后资源文件的绝对路径"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class CropFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)
        self.input_folder = tk.StringVar()
        self.crop_mode = tk.IntVar(value=1)  # 1: 比例裁剪, 2: 固定尺寸裁剪
        self.ratio_w = tk.StringVar(value="16")
        self.ratio_h = tk.StringVar(value="9")
        self.fixed_width = tk.StringVar(value="800")
        self.fixed_height = tk.StringVar(value="600")
        self.position_mode = tk.IntVar(value=2)  # 默认居中
        self.custom_left = tk.StringVar(value="0")
        self.custom_top = tk.StringVar(value="0")
        self.create_widgets()

    def create_widgets(self):
        # ** 目录选择 **
        frame_dir = ttk.LabelFrame(self, text="图片目录", padding=10)
        frame_dir.grid(row=0, column=0, columnspan=3, sticky="ew", pady=5)
        ttk.Entry(frame_dir, textvariable=self.input_folder, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_dir, text="浏览", command=self.select_folder).pack(side=tk.LEFT)

        # ** 裁剪模式 **
        frame_mode = ttk.LabelFrame(self, text="裁剪模式", padding=10)
        frame_mode.grid(row=1, column=0, sticky="ew", pady=5)
        ttk.Radiobutton(frame_mode, text="比例裁剪 (如 16:9)", variable=self.crop_mode, value=1, command=self.update_mode).pack(anchor="w")
        ttk.Radiobutton(frame_mode, text="固定尺寸裁剪", variable=self.crop_mode, value=2, command=self.update_mode).pack(anchor="w")

        # ** 裁剪尺寸输入框 **
        self.frame_ratio = ttk.LabelFrame(self, text="比例裁剪设置", padding=10)
        self.frame_ratio.grid(row=2, column=0, sticky="ew", pady=5)
        ttk.Label(self.frame_ratio, text="宽:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(self.frame_ratio, textvariable=self.ratio_w, width=5).pack(side=tk.LEFT)
        ttk.Label(self.frame_ratio, text="高:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(self.frame_ratio, textvariable=self.ratio_h, width=5).pack(side=tk.LEFT)

        self.frame_fixed = ttk.LabelFrame(self, text="固定尺寸裁剪设置", padding=10)
        self.frame_fixed.grid(row=2, column=0, sticky="ew", pady=5)
        ttk.Label(self.frame_fixed, text="宽度:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(self.frame_fixed, textvariable=self.fixed_width, width=6).pack(side=tk.LEFT)
        ttk.Label(self.frame_fixed, text="高度:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(self.frame_fixed, textvariable=self.fixed_height, width=6).pack(side=tk.LEFT)

        # ** 裁剪定位方式 **
        frame_pos = ttk.LabelFrame(self, text="裁剪定位", padding=10)
        frame_pos.grid(row=3, column=0, columnspan=3, sticky="ew", pady=5)
        positions = [("左边", 1), ("中间", 2), ("右边", 3), ("自定义", 4), ("左上角", 5), ("右下角", 6)]
        for text, val in positions:
            ttk.Radiobutton(frame_pos, text=text, variable=self.position_mode, value=val, command=self.update_position).pack(anchor="w")

        self.frame_custom = ttk.Frame(frame_pos)
        self.frame_custom.pack(fill="x", pady=5)
        ttk.Label(self.frame_custom, text="左边距:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(self.frame_custom, textvariable=self.custom_left, width=5).pack(side=tk.LEFT)
        ttk.Label(self.frame_custom, text="上边距:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(self.frame_custom, textvariable=self.custom_top, width=5).pack(side=tk.LEFT)
        self.frame_custom.pack_forget()

        # ** 进度条 & 日志 **
        frame_log = ttk.LabelFrame(self, text="日志信息", padding=10)
        frame_log.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=5)
        self.log_area = scrolledtext.ScrolledText(frame_log, wrap=tk.WORD, height=10)
        self.log_area.pack(fill="both", expand=True)

        frame_progress = ttk.Frame(self)
        frame_progress.grid(row=5, column=0, columnspan=3, sticky="ew", pady=5)
        self.progress_bar = ttk.Progressbar(frame_progress, orient="horizontal", mode="determinate")
        self.progress_bar.pack(fill="x", padx=5, pady=5)

        # ** 按钮 **
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row=6, column=0, columnspan=3, pady=10)
        ttk.Button(frame_buttons, text="开始裁剪", command=self.start_crop).pack(side=tk.LEFT, padx=5)
        
        self.update_mode()

    def select_folder(self):
        folder = filedialog.askdirectory(title="选择图片目录")
        if folder:
            self.input_folder.set(folder)
            self.log_area.insert(tk.END, f"已选择目录: {folder}\n")

    def update_mode(self):
        if self.crop_mode.get() == 1:
            self.frame_fixed.grid_remove()
            self.frame_ratio.grid(row=2, column=0, sticky="ew", pady=5)
        else:
            self.frame_ratio.grid_remove()
            self.frame_fixed.grid(row=2, column=0, sticky="ew", pady=5)

    def update_position(self):
        if self.position_mode.get() == 4:
            self.frame_custom.pack(fill="x", pady=5)
        else:
            self.frame_custom.pack_forget()

    def start_crop(self):
        folder = self.input_folder.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("错误", "请选择有效的图片目录")
            return
        threading.Thread(target=self.batch_crop, args=(folder,), daemon=True).start()

    def batch_crop(self, folder):
        files = sorted([f for f in os.listdir(folder) if f.lower().endswith(FILE_EXTS)])
        total = len(files)
        self.progress_bar["maximum"] = total
        for idx, filename in enumerate(files, start=1):
            filepath = os.path.join(folder, filename)
            try:
                with Image.open(filepath) as img:
                    crop_box = (0, 0, img.width, img.height)  # 这里需要根据定位计算裁剪框
                    cropped = img.crop(crop_box)
                    cropped.save(filepath, quality=95)
                    self.log_area.insert(tk.END, f"成功裁剪: {filename}\n")
            except Exception as e:
                self.log_area.insert(tk.END, f"裁剪失败: {filename} - {str(e)}\n")
            self.progress_bar["value"] = idx
        messagebox.showinfo("完成", "裁剪完成！")

if __name__ == "__main__":
    root = tk.Tk()
    # 设置图标
    root.iconbitmap(resource_path("myicon.ico"))
    root.title("批量裁剪工具")
    root.geometry("600x500")
    app = CropFrame(root)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
