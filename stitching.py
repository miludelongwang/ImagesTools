from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox, colorchooser
import os
import threading
import queue
import re

class StitchingFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        # 初始化参数
        self.input_folder = ""
        self.output_path = ""
        self.fill_color = tk.StringVar(value="#FFFFFF")
        self.use_transparent = tk.BooleanVar(value=False)
        self.output_format = tk.StringVar(value="PNG")  # 输出格式选项: PNG 或 JPEG

        self.create_widgets()
        self.setup_queue()
        
    def create_widgets(self):
        # --- 控制面板 ---
        control_frame = ttk.Frame(self)
        control_frame.pack(pady=10, fill=tk.X)
        
        # 输入文件夹
        folder_frame = ttk.Frame(control_frame)
        folder_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(folder_frame, text="输入文件夹:").pack(side=tk.LEFT)
        self.folder_entry = ttk.Entry(folder_frame, width=40)
        self.folder_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(folder_frame, text="浏览", command=self.select_input_folder).pack(side=tk.LEFT, padx=5)
        
        # 行列设置
        grid_frame = ttk.Frame(control_frame)
        grid_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(grid_frame, text="行数:").pack(side=tk.LEFT)
        self.row_spin = ttk.Spinbox(grid_frame, from_=1, to=20, width=5)
        self.row_spin.set(4)
        self.row_spin.pack(side=tk.LEFT, padx=5)
        ttk.Label(grid_frame, text="列数:").pack(side=tk.LEFT)
        self.col_spin = ttk.Spinbox(grid_frame, from_=1, to=20, width=5)
        self.col_spin.set(4)
        self.col_spin.pack(side=tk.LEFT, padx=5)
        
        # 输出格式设置
        output_frame = ttk.Frame(control_frame)
        output_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(output_frame, text="输出格式:").pack(side=tk.LEFT)
        self.radio_png = ttk.Radiobutton(output_frame, text="PNG", variable=self.output_format, value="PNG")
        self.radio_png.pack(side=tk.LEFT, padx=5)
        self.radio_jpeg = ttk.Radiobutton(output_frame, text="JPEG", variable=self.output_format, value="JPEG")
        self.radio_jpeg.pack(side=tk.LEFT, padx=5)
        
        # 透明背景与填充色设置
        fill_frame = ttk.Frame(control_frame)
        fill_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Checkbutton(fill_frame, text="透明背景(空像素)", variable=self.use_transparent, command=self.toggle_transparent).pack(side=tk.LEFT, padx=5)
        ttk.Label(fill_frame, text="填充色:").pack(side=tk.LEFT, padx=5)
        self.fill_color_label = ttk.Label(fill_frame, textvariable=self.fill_color, background=self.fill_color.get(), width=10)
        self.fill_color_label.pack(side=tk.LEFT, padx=5)
        self.choose_color_button = ttk.Button(fill_frame, text="选择颜色", command=self.choose_fill_color)
        self.choose_color_button.pack(side=tk.LEFT, padx=5)
        
        # 开始拼接按钮
        ttk.Button(control_frame, text="开始拼接", command=self.start_stitching).pack(pady=5)
        
        # --- 进度与状态显示 ---
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=800, mode="determinate")
        self.progress_bar.pack(pady=5)
        self.status_var = tk.StringVar(value="等待开始...")
        status_label = ttk.Label(self, textvariable=self.status_var, anchor="center")
        status_label.pack(pady=5)
        
        # --- 日志显示区域 ---
        self.log_area = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=20)
        self.log_area.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        
        # 底部状态栏
        self.bottom_status_var = tk.StringVar()
        bottom_status = ttk.Label(self, textvariable=self.bottom_status_var, relief=tk.SUNKEN, anchor="w")
        bottom_status.pack(side=tk.BOTTOM, fill=tk.X)
        
    def toggle_transparent(self):
        if self.use_transparent.get():
            # 透明背景时自动锁定输出格式为PNG，并禁用JPEG选择和填充色选择
            self.output_format.set("PNG")
            self.radio_jpeg.config(state="disabled")
            self.choose_color_button.config(state="disabled")
            self.fill_color_label.config(text="无", background="white")
        else:
            self.radio_jpeg.config(state="normal")
            self.choose_color_button.config(state="normal")
            self.fill_color_label.config(text=self.fill_color.get(), background=self.fill_color.get())
    
    def choose_fill_color(self):
        color = colorchooser.askcolor(initialcolor=self.fill_color.get())
        if color[1]:
            self.fill_color.set(color[1])
            self.fill_color_label.config(text=color[1], background=color[1])
    
    def select_input_folder(self):
        folder = filedialog.askdirectory(title="选择图片文件夹")
        if folder:
            self.input_folder = folder
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
            self.message_queue.put(("info", f"已选择输入文件夹：{folder}"))
    
    def setup_queue(self):
        self.message_queue = queue.Queue()
        self.after(100, self.process_messages)
    
    def process_messages(self):
        while not self.message_queue.empty():
            msg_type, content = self.message_queue.get()
            if msg_type == "progress":
                self.progress_bar["value"] = content
                self.status_var.set(f"进度: {content}/{self.progress_bar['maximum']}")
            else:
                self.update_log(msg_type, content)
        self.after(100, self.process_messages)
    
    def update_log(self, msg_type, content):
        tag = "info"
        if msg_type == "error":
            tag = "error"
            self.log_area.tag_config("error", foreground="red")
        elif msg_type == "success":
            tag = "success"
            self.log_area.tag_config("success", foreground="green")
        self.log_area.insert(tk.END, content + "\n", tag)
        self.log_area.see(tk.END)
        self.bottom_status_var.set(content)
    
    def start_stitching(self):
        if not self.input_folder:
            messagebox.showerror("错误", "请先选择输入文件夹")
            return
        try:
            self.rows = int(self.row_spin.get())
            self.cols = int(self.col_spin.get())
        except Exception as e:
            messagebox.showerror("错误", "行数和列数请输入有效的正整数")
            return
        # 根据输出格式设置默认扩展名和文件类型
        fmt = self.output_format.get()
        if fmt == "PNG":
            def_ext = ".png"
            filetypes = [("PNG 文件", "*.png")]
        else:
            def_ext = ".jpg"
            filetypes = [("JPEG 文件", "*.jpg")]
        self.output_path = filedialog.asksaveasfilename(defaultextension=def_ext, filetypes=filetypes)
        if not self.output_path:
            return
        # 如果选择了透明背景，确保输出格式为PNG
        if self.use_transparent.get() and fmt != "PNG":
            messagebox.showerror("错误", "透明背景仅支持PNG格式，请选择PNG输出")
            return
        threading.Thread(target=self.stitch_images, daemon=True).start()
    
    def stitch_images(self):
        try:
            # 获取图片文件列表，并自然排序
            image_files = [f for f in os.listdir(self.input_folder)
                           if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            def natural_sort_key(s):
                return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]
            image_files.sort(key=natural_sort_key)
            
            total_needed = self.rows * self.cols
            overall_steps = 2 * total_needed  # 加载和拼接各占一半
            self.message_queue.put(("progress", 0))
            self.after(0, lambda: self.progress_bar.config(maximum=overall_steps))
            progress_current = 0

            images = []
            blank_count = 0

            if image_files:
                first_image = Image.open(os.path.join(self.input_folder, image_files[0]))
                img_width, img_height = first_image.size
                first_image.close()
            else:
                messagebox.showerror("错误", "未找到有效图片文件")
                return

            # 根据设置确定图像模式和填充色
            use_transparent = self.use_transparent.get()
            if use_transparent:
                mode = "RGBA"
                fill_color = (0, 0, 0, 0)
            else:
                mode = "RGB"
                fill_color = tuple(int(self.fill_color.get()[i:i+2], 16) for i in (1,3,5)) if self.fill_color.get().startswith("#") else (255, 255, 255)
            
            blank_image = Image.new(mode, (img_width, img_height), fill_color)

            # 加载图片（不足部分用空图片补充）
            for i in range(total_needed):
                if i < len(image_files):
                    filename = image_files[i]
                    try:
                        img = Image.open(os.path.join(self.input_folder, filename))
                        if img.mode != mode:
                            img = img.convert(mode)
                        images.append(img)
                        self.message_queue.put(("info", f"已加载图片：{filename} ({i+1}/{total_needed})"))
                    except Exception as e:
                        images.append(blank_image.copy())
                        blank_count += 1
                        self.message_queue.put(("error", f"加载失败：{filename} - 用空白替代 ({i+1}/{total_needed})"))
                else:
                    images.append(blank_image.copy())
                    blank_count += 1
                    self.message_queue.put(("info", f"补充空白图片 ({i+1}/{total_needed})"))
                progress_current += 1
                self.message_queue.put(("progress", progress_current))
            
            # 创建画布进行拼接
            canvas = Image.new(mode, (self.cols * img_width, self.rows * img_height), fill_color)

            count = 0
            for row in range(self.rows):
                for col in range(self.cols):
                    index = row * self.cols + col
                    if index < len(images):
                        position = (col * img_width, row * img_height)
                        canvas.paste(images[index], position)
                        count += 1
                        self.message_queue.put(("info", f"正在拼接：第{row+1}行 第{col+1}列 ({count}/{total_needed})"))
                    progress_current += 1
                    self.message_queue.put(("progress", progress_current))
            
            canvas.save(self.output_path, quality=95)
            self.message_queue.put(("success", f"拼接完成！保存至：{self.output_path}\n使用空白图片数量：{blank_count}"))
            
            for img in images:
                img.close()
            blank_image.close()
            
        except Exception as e:
            self.message_queue.put(("error", f"发生错误：{str(e)}"))
            if 'canvas' in locals():
                canvas.close()

# 当该模块作为独立文件运行时，启动独立的图片拼接工具
if __name__ == "__main__":
    root = tk.Tk()
    root.title("图片拼接工具")
    root.geometry("850x700")
    app = StitchingFrame(root)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
