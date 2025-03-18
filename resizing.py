import os
import re
import tempfile
import threading
from PIL import Image, ImageOps
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, ttk

from merge import ToolTip

FILE_EXTS = ('.jpg', '.png', '.jpeg', '.webp')

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def resize_image(img, target_width, target_height, keep_aspect_ratio, background_color, resample_method):
    original_width, original_height = img.size
    if keep_aspect_ratio:
        width_ratio = target_width / original_width
        height_ratio = target_height / original_height
        scale_ratio = min(width_ratio, height_ratio)
        new_size = (int(original_width * scale_ratio), int(original_height * scale_ratio))
        resized = img.resize(new_size, resample_method)
        final_img = Image.new("RGB", (target_width, target_height), background_color)
        paste_position = ((target_width - new_size[0]) // 2, (target_height - new_size[1]) // 2)
        final_img.paste(resized, paste_position)
        return final_img
    else:
        return img.resize((target_width, target_height), resample_method)

class ResizingFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)
        self.input_folder = tk.StringVar()
        self.use_reference = tk.BooleanVar(value=False)
        self.ref_image_path = tk.StringVar()
        self.target_width = tk.StringVar(value="876")
        self.target_height = tk.StringVar(value="1237")
        self.keep_aspect_ratio = tk.BooleanVar(value=False)
        self.background_color = tk.StringVar(value="#FFFFFF")
        self.resample_method = tk.StringVar(value="LANCZOS")
        self.create_widgets()

    def create_widgets(self):
        pad = {'padx': 10, 'pady': 5}
        # 警告信息
        warning_label = tk.Label(self, text="警告：此操作将直接覆盖原始文件，请确保已做好备份！", fg="red")
        warning_label.pack(**pad)
        
        # 目录选择区
        frame_folder = tk.Frame(self)
        frame_folder.pack(fill="x", **pad)
        tk.Label(frame_folder, text="图片目录:").pack(side=tk.LEFT)
        self.folder_entry = tk.Entry(frame_folder, textvariable=self.input_folder, width=40)
        self.folder_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_folder, text="选择目录", command=self.select_folder).pack(side=tk.LEFT, padx=5)
        
        # 尺寸一致性提示
        self.size_warning_label = tk.Label(self, text="", fg="red", font=("Arial", 10))
        self.size_warning_label.pack(fill="x", **pad)
        
        # 参考图设置区
        frame_ref = tk.Frame(self)
        frame_ref.pack(fill="x", **pad)
        tk.Checkbutton(frame_ref, text="启用参考尺寸", variable=self.use_reference, command=self.on_reference_toggle).pack(side=tk.LEFT)
        tk.Label(frame_ref, text="参考图:").pack(side=tk.LEFT, padx=5)
        self.ref_entry = tk.Entry(frame_ref, textvariable=self.ref_image_path, width=40)
        self.ref_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_ref, text="选择参考图", command=self.select_reference).pack(side=tk.LEFT, padx=5)
        self.ref_dim_label = tk.Label(frame_ref, text="参考尺寸：未选择", fg="blue")
        self.ref_dim_label.pack(side=tk.LEFT, padx=5)
        
        # 目标尺寸设置区
        frame_size = tk.Frame(self)
        frame_size.pack(fill="x", **pad)
        tk.Label(frame_size, text="目标宽度:").pack(side=tk.LEFT)
        self.width_entry = tk.Entry(frame_size, textvariable=self.target_width, width=8)
        self.width_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(frame_size, text="目标高度:").pack(side=tk.LEFT)
        self.height_entry = tk.Entry(frame_size, textvariable=self.target_height, width=8)
        self.height_entry.pack(side=tk.LEFT, padx=5)
        
        # 保持宽高比选项
        frame_aspect = tk.Frame(self)
        frame_aspect.pack(fill="x", **pad)
        tk.Checkbutton(frame_aspect, text="保持宽高比", variable=self.keep_aspect_ratio).pack(side=tk.LEFT)
        
        # 背景色选择及提示
        frame_color = tk.Frame(self)
        frame_color.pack(fill="x", **pad)
        tk.Label(frame_color, text="背景色:").pack(side=tk.LEFT)
        self.label_color = tk.Label(frame_color, textvariable=self.background_color, bg=self.background_color.get(), width=10)
        self.label_color.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_color, text="选择颜色", command=self.choose_color).pack(side=tk.LEFT, padx=5)
        bg_help = ttk.Label(frame_color, text="?", foreground="blue", cursor="question_arrow", font=("Arial", 10, "bold"))
        bg_help.pack(side=tk.LEFT, padx=3)
        ToolTip(bg_help, "背景色用于填充目标尺寸中，缩放后未被图片占据的区域。")
        
        # 重采样方法选择及提示
        frame_resample = tk.Frame(self)
        frame_resample.pack(fill="x", **pad)
        tk.Label(frame_resample, text="重采样方法:").pack(side=tk.LEFT)
        methods = ["NEAREST", "BILINEAR", "BICUBIC", "LANCZOS"]
        self.combo_resample = ttk.Combobox(frame_resample, values=methods, state="readonly", width=10, textvariable=self.resample_method)
        self.combo_resample.pack(side=tk.LEFT, padx=5)
        self.combo_resample.current(methods.index("LANCZOS"))
        resample_help = ttk.Label(frame_resample, text="?", foreground="blue", cursor="question_arrow", font=("Arial", 10, "bold"))
        resample_help.pack(side=tk.LEFT, padx=3)
        ToolTip(resample_help, "NEAREST: 快但图像粗糙；\nBILINEAR: 平滑；\nBICUBIC: 更高质量；\nLANCZOS: 高质量缩放，适用于精细调整。")
        
        # 进度与状态显示
        frame_progress = tk.Frame(self)
        frame_progress.pack(fill="x", **pad)
        self.progress_label = tk.Label(frame_progress, text="进度: 0/0")
        self.progress_label.pack(side=tk.TOP, anchor="w")
        self.progress_bar = ttk.Progressbar(frame_progress, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(side=tk.TOP, fill="x", padx=5, pady=5)
        
        # 开始按钮
        self.btn_start = tk.Button(self, text="开始处理", command=self.start_processing, bg="green", fg="white")
        self.btn_start.pack(pady=15)

    def select_folder(self):
        folder = filedialog.askdirectory(title="请选择图片目录")
        if folder:
            self.input_folder.set(folder)
            file_list = [f for f in os.listdir(folder) if f.lower().endswith(FILE_EXTS) and os.path.isfile(os.path.join(folder, f))]
            if not file_list:
                self.size_warning_label.config(text="目录中未找到符合要求的图片文件", fg="red")
                return
            first_path = os.path.join(folder, file_list[0])
            try:
                with Image.open(first_path) as img:
                    w, h = img.size
                    if not self.use_reference.get():
                        self.target_width.set(str(w))
                        self.target_height.set(str(h))
                    base_size = (w, h)
            except Exception as e:
                self.size_warning_label.config(text="读取第一个图片尺寸失败", fg="red")
                return
            inconsistent = False
            for f in file_list:
                path = os.path.join(folder, f)
                try:
                    with Image.open(path) as img:
                        if img.size != base_size:
                            inconsistent = True
                            break
                except:
                    continue
            if inconsistent:
                self.size_warning_label.config(text=f"警告：文件夹中图片尺寸不一致（参考尺寸：{base_size[0]} x {base_size[1]}）", fg="red")
            else:
                self.size_warning_label.config(text=f"所有图片尺寸一致：{base_size[0]} x {base_size[1]}", fg="green")
            if not self.use_reference.get():
                self.target_width.set(str(base_size[0]))
                self.target_height.set(str(base_size[1]))

    def select_reference(self):
        path = filedialog.askopenfilename(title="选择参考图", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")])
        if path:
            self.ref_image_path.set(path)
            self.ref_entry.delete(0, tk.END)
            self.ref_entry.insert(0, path)
            try:
                with Image.open(path) as img:
                    w, h = img.size
                    self.ref_dim_label.config(text=f"参考尺寸：{w} x {h}", fg="blue")
                    if self.use_reference.get():
                        self.target_width.set(str(w))
                        self.target_height.set(str(h))
            except Exception as e:
                self.ref_dim_label.config(text="参考图尺寸读取失败", fg="red")

    def choose_color(self):
        color = colorchooser.askcolor(initialcolor=self.background_color.get())
        if color[1]:
            self.background_color.set(color[1])
            self.label_color.config(bg=color[1])

    def on_reference_toggle(self):
        if self.use_reference.get():
            if self.ref_image_path.get():
                try:
                    with Image.open(self.ref_image_path.get()) as img:
                        w, h = img.size
                        self.target_width.set(str(w))
                        self.target_height.set(str(h))
                except Exception as e:
                    messagebox.showerror("错误", "参考图尺寸读取失败")
            else:
                messagebox.showwarning("提示", "请先选择参考图")
        else:
            folder = self.input_folder.get()
            if folder and os.path.isdir(folder):
                file_list = [f for f in os.listdir(folder) if f.lower().endswith(FILE_EXTS) and os.path.isfile(os.path.join(folder, f))]
                if file_list:
                    file_list.sort(key=natural_sort_key)
                    first_path = os.path.join(folder, file_list[0])
                    try:
                        with Image.open(first_path) as img:
                            w, h = img.size
                            self.target_width.set(str(w))
                            self.target_height.set(str(h))
                    except Exception as e:
                        messagebox.showerror("错误", "读取目录内第一张图片尺寸失败")

    def start_processing(self):
        folder = self.input_folder.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("错误", "请选择有效的图片目录")
            return
        try:
            target_w = int(self.target_width.get())
            target_h = int(self.target_height.get())
            if target_w <= 0 or target_h <= 0:
                raise ValueError("尺寸必须大于0")
        except Exception as e:
            messagebox.showerror("错误", f"目标尺寸无效: {str(e)}")
            return
        if not messagebox.askokcancel("确认", "此操作将直接覆盖原始文件，是否继续？"):
            return
        self.btn_start.config(state="disabled")
        resample_mapping = {"NEAREST": Image.NEAREST, "BILINEAR": Image.BILINEAR, "BICUBIC": Image.BICUBIC, "LANCZOS": Image.LANCZOS}
        resample = resample_mapping.get(self.resample_method.get(), Image.LANCZOS)
        keep_ratio = self.keep_aspect_ratio.get()
        bg_color_hex = self.background_color.get()
        bg_color = tuple(int(bg_color_hex[i:i+2], 16) for i in (1, 3, 5)) if bg_color_hex.startswith("#") else (255, 255, 255)
        self.files = sorted([f for f in os.listdir(folder) if f.lower().endswith(FILE_EXTS)], key=natural_sort_key)
        self.total_files = len(self.files)
        self.processed = 0
        self.current_index = 0
        if self.total_files == 0:
            messagebox.showinfo("提示", "目录中没有符合要求的图片文件")
            self.btn_start.config(state="normal")
            return
        self.progress_bar['maximum'] = self.total_files
        threading.Thread(target=self.process_images_thread, args=(folder, target_w, target_h, keep_ratio, bg_color, resample), daemon=True).start()

    def process_images_thread(self, folder, target_w, target_h, keep_ratio, bg_color, resample):
        for idx, filename in enumerate(self.files, start=1):
            input_path = os.path.join(folder, filename)
            temp_path = None
            try:
                with Image.open(input_path) as img:
                    file_ext = os.path.splitext(filename)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext, dir=folder) as tmp_file:
                        temp_path = tmp_file.name
                    if img.mode in ('RGBA', 'LA'):
                        img = img.convert("RGB")
                    final_img = resize_image(img, target_w, target_h, keep_ratio, bg_color, resample)
                    exif = img.info.get('exif')
                    save_format = 'JPEG' if file_ext.lower() in ('.jpg', '.jpeg') else file_ext[1:].upper()
                    final_img.save(temp_path, format=save_format, exif=exif, quality=95, subsampling=0 if save_format == 'JPEG' else -1)
                    os.replace(temp_path, input_path)
                    self.processed += 1
            except Exception as e:
                self.after(0, lambda f=filename, err=str(e): messagebox.showerror("错误", f"处理 {f} 失败: {err}"))
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
            self.current_index = idx
            self.after(0, self.update_progress)
        self.after(0, lambda: messagebox.showinfo("完成", f"处理完成！成功覆盖 {self.processed} 张图片。"))
        self.after(0, lambda: self.btn_start.config(state="normal"))

    def update_progress(self):
        self.progress_bar['value'] = self.current_index
        if self.current_index < self.total_files:
            self.progress_label.config(text=f"进度: {self.current_index}/{self.total_files} - 正在处理: {self.files[self.current_index - 1]}")
        else:
            self.progress_label.config(text="进度: 完成")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("图片尺寸调整工具")
    root.geometry("600x450")
    app = ResizingFrame(root)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
