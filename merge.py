import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, colorchooser, simpledialog
from PIL import Image, ImageOps

# 支持的图片格式
SUPPORTED_EXTS = ('.png', '.jpg', '.jpeg')

# 优化版 ToolTip 类（用于问号提示）
class ToolTip:
    def __init__(self, widget, text=''):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.delay = 500  # 延迟500毫秒显示提示
        widget.bind("<Enter>", self.enter)
        widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.showtip)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def showtip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("Arial", 9))
        label.pack(ipadx=4, ipady=2)

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

class MergeFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # 参数初始化
        self.bg_path = ""
        self.fg_folder = ""
        self.out_folder = ""
        # 操作模式：合成、添加相框、背景为相框
        self.operation_mode = tk.StringVar(value="合成")
        # 合成模式参数
        self.auto_adjust = tk.BooleanVar(value=False)
        self.position_mode = tk.StringVar(value="居中")
        self.custom_x = tk.StringVar(value="0")
        self.custom_y = tk.StringVar(value="0")
        self.opacity = tk.IntVar(value=100)
        self.merge_mode = tk.StringVar(value="普通合成")  # 普通合成或混合
        # 添加相框模式参数
        self.frame_width = tk.IntVar(value=20)
        self.frame_color = tk.StringVar(value="#000000")
        # 背景为相框模式参数（内嵌区域设置）
        self.inner_left = tk.StringVar(value="50")
        self.inner_top = tk.StringVar(value="50")
        self.inner_width = tk.StringVar(value="400")
        self.inner_height = tk.StringVar(value="300")
        # 背景尺寸显示
        self.bg_dimensions = tk.StringVar(value="未读取")
        self.create_widgets()
        self.setup_queue()

    def create_widgets(self):
        container = ttk.Frame(self, padding=10)
        container.pack(fill=tk.BOTH, expand=True)

        # 操作模式选择
        mode_frame = ttk.LabelFrame(container, text="操作模式", padding=10)
        mode_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Label(mode_frame, text="模式：").grid(row=0, column=0, sticky="w")
        mode_options = ["合成", "添加相框", "背景为相框"]
        self.mode_cb = ttk.Combobox(mode_frame, values=mode_options, state="readonly",
                                    textvariable=self.operation_mode, width=12)
        self.mode_cb.grid(row=0, column=1, padx=5, sticky="w")
        self.mode_cb.bind("<<ComboboxSelected>>", self.on_mode_change)
        # 添加模式问号提示
        self.mode_help_label = ttk.Label(mode_frame, text="?", foreground="blue", cursor="question_arrow",
                                         font=("Arial", 12, "bold"))
        self.mode_help_label.grid(row=0, column=2, padx=3)
        mode_help_text = ("合成：将前景图叠加到背景图上。\n"
                          "添加相框：在背景图周围添加边框。\n"
                          "背景为相框：背景图本身为相框，设置内嵌区域供前景图填充。")
        ToolTip(self.mode_help_label, mode_help_text)

        # 背景图设置
        bg_frame = ttk.LabelFrame(container, text="背景图设置", padding=10)
        bg_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Label(bg_frame, text="背景图路径：").grid(row=0, column=0, sticky="w")
        self.bg_entry = ttk.Entry(bg_frame, width=50)
        self.bg_entry.grid(row=0, column=1, padx=5, sticky="w")
        ttk.Button(bg_frame, text="选择", command=self.select_bg).grid(row=0, column=2, padx=5)
        ttk.Label(bg_frame, text="背景尺寸：").grid(row=1, column=0, sticky="w", pady=2)
        self.bg_dim_label = ttk.Label(bg_frame, textvariable=self.bg_dimensions, foreground="blue")
        self.bg_dim_label.grid(row=1, column=1, padx=5, sticky="w")

        # 合成模式设置（适用于“合成”和“背景为相框”模式）
        self.merge_settings = ttk.LabelFrame(container, text="图片合成设置", padding=10)
        self.merge_settings.grid(row=2, column=0, sticky="ew", pady=5)
        ttk.Button(self.merge_settings, text="选择前景文件夹", command=self.select_fg).grid(row=0, column=0, sticky="w")
        self.fg_entry = ttk.Entry(self.merge_settings, width=40)
        self.fg_entry.grid(row=0, column=1, padx=5, sticky="w")
        ttk.Button(self.merge_settings, text="选择输出目录", command=self.select_out).grid(row=1, column=0, sticky="w")
        self.out_entry = ttk.Entry(self.merge_settings, width=40)
        self.out_entry.grid(row=1, column=1, padx=5, sticky="w")
        ttk.Checkbutton(self.merge_settings, text="自动调整前景尺寸为背景尺寸", variable=self.auto_adjust).grid(row=2, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(self.merge_settings, text="前景位置：").grid(row=3, column=0, sticky="w", pady=2)
        pos_options = ["居中", "左上角", "右下角", "自定义"]
        self.pos_cb = ttk.Combobox(self.merge_settings, values=pos_options, state="readonly",
                                     textvariable=self.position_mode, width=10)
        self.pos_cb.grid(row=3, column=1, sticky="w", padx=5)
        self.pos_cb.bind("<<ComboboxSelected>>", self.on_pos_change)
        self.custom_pos_frame = ttk.Frame(self.merge_settings)
        ttk.Label(self.custom_pos_frame, text="X：").pack(side=tk.LEFT)
        self.entry_x = ttk.Entry(self.custom_pos_frame, textvariable=self.custom_x, width=5)
        self.entry_x.pack(side=tk.LEFT, padx=2)
        ttk.Label(self.custom_pos_frame, text="Y：").pack(side=tk.LEFT)
        self.entry_y = ttk.Entry(self.custom_pos_frame, textvariable=self.custom_y, width=5)
        self.entry_y.pack(side=tk.LEFT, padx=2)
        self.custom_pos_frame.grid(row=4, column=1, sticky="w", padx=5)
        self.custom_pos_frame.grid_remove()
        ttk.Label(self.merge_settings, text="前景透明度：").grid(row=5, column=0, sticky="w", pady=2)
        self.opacity_scale = ttk.Scale(self.merge_settings, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.opacity)
        self.opacity_scale.grid(row=5, column=1, sticky="w", padx=5)
        # 合成模式选择及问号说明
        mode_frame2 = ttk.Frame(self.merge_settings)
        mode_frame2.grid(row=6, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(mode_frame2, text="合成模式：").pack(side=tk.LEFT)
        merge_options = ["普通合成", "混合"]
        self.mode_merge_cb = ttk.Combobox(mode_frame2, values=merge_options, state="readonly",
                                          textvariable=self.merge_mode, width=10)
        self.mode_merge_cb.pack(side=tk.LEFT, padx=5)
        self.help_label = ttk.Label(mode_frame2, text="?", foreground="blue", cursor="question_arrow", font=("Arial", 12, "bold"))
        self.help_label.pack(side=tk.LEFT, padx=3)
        help_text = ("普通合成：直接将前景粘贴到背景，利用前景透明通道决定显示区域。\n"
                     "混合模式：背景与前景按比例混合，产生渐变效果（要求尺寸一致）。")
        ToolTip(self.help_label, help_text)

        # 添加相框模式设置
        self.frame_settings = ttk.LabelFrame(container, text="添加相框设置", padding=10)
        self.frame_settings.grid(row=3, column=0, sticky="ew", pady=5)
        ttk.Label(self.frame_settings, text="相框宽度（像素）：").grid(row=0, column=0, sticky="w")
        self.entry_frame_width = ttk.Entry(self.frame_settings, textvariable=self.frame_width, width=5)
        self.entry_frame_width.grid(row=0, column=1, sticky="w", padx=5)
        ttk.Label(self.frame_settings, text="相框颜色：").grid(row=0, column=2, sticky="w", padx=5)
        self.frame_color_label = ttk.Label(self.frame_settings, textvariable=self.frame_color, background=self.frame_color.get(), width=10)
        self.frame_color_label.grid(row=0, column=3, sticky="w", padx=5)
        ttk.Button(self.frame_settings, text="选择颜色", command=self.choose_frame_color).grid(row=0, column=4, sticky="w", padx=5)
        self.frame_settings.grid_remove()

        # 背景为相框模式设置
        self.bgframe_settings = ttk.LabelFrame(container, text="背景为相框设置", padding=10)
        self.bgframe_settings.grid(row=4, column=0, sticky="ew", pady=5)
        ttk.Label(self.bgframe_settings, text="内嵌区域左边距：").grid(row=0, column=0, sticky="w")
        self.entry_inner_left = ttk.Entry(self.bgframe_settings, textvariable=self.inner_left, width=5)
        self.entry_inner_left.grid(row=0, column=1, padx=5)
        ttk.Label(self.bgframe_settings, text="上边距：").grid(row=0, column=2, sticky="w")
        self.entry_inner_top = ttk.Entry(self.bgframe_settings, textvariable=self.inner_top, width=5)
        self.entry_inner_top.grid(row=0, column=3, padx=5)
        ttk.Label(self.bgframe_settings, text="区域宽度：").grid(row=1, column=0, sticky="w")
        self.entry_inner_width = ttk.Entry(self.bgframe_settings, textvariable=self.inner_width, width=5)
        self.entry_inner_width.grid(row=1, column=1, padx=5)
        ttk.Label(self.bgframe_settings, text="区域高度：").grid(row=1, column=2, sticky="w")
        self.entry_inner_height = ttk.Entry(self.bgframe_settings, textvariable=self.inner_height, width=5)
        self.entry_inner_height.grid(row=1, column=3, padx=5)
        self.bgframe_settings.grid_remove()

        # 日志与进度显示
        sep = ttk.Separator(container, orient="horizontal")
        sep.grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)
        self.progress_bar = ttk.Progressbar(container, orient="horizontal", length=600, mode="determinate")
        self.progress_bar.grid(row=6, column=0, columnspan=2, pady=5)
        self.status_var = tk.StringVar(value="等待开始...")
        ttk.Label(container, textvariable=self.status_var).grid(row=7, column=0, columnspan=2, pady=5)
        self.log_area = scrolledtext.ScrolledText(container, wrap=tk.WORD, height=10)
        self.log_area.grid(row=8, column=0, columnspan=2, sticky="nsew", pady=5)
        container.rowconfigure(8, weight=1)

        # 开始按钮
        ttk.Button(container, text="开始合成", command=self.start_merge).grid(row=9, column=0, columnspan=2, pady=10)

    def on_mode_change(self, event=None):
        mode = self.operation_mode.get()
        if mode == "合成":
            self.merge_settings.grid()
            self.frame_settings.grid_remove()
            self.bgframe_settings.grid_remove()
        elif mode == "添加相框":
            self.merge_settings.grid()
            self.frame_settings.grid()
            self.bgframe_settings.grid_remove()
        elif mode == "背景为相框":
            self.merge_settings.grid()
            self.bgframe_settings.grid()
            self.frame_settings.grid_remove()

    def on_pos_change(self, event=None):
        if self.position_mode.get() == "自定义":
            self.custom_pos_frame.grid()
        else:
            self.custom_pos_frame.grid_remove()

    def select_bg(self):
        path = filedialog.askopenfilename(title="选择背景图", filetypes=[("图片文件", "*.png;*.jpg;*.jpeg")])
        if path:
            self.bg_path = path
            self.bg_entry.delete(0, tk.END)
            self.bg_entry.insert(0, path)
            try:
                with Image.open(path) as img:
                    w, h = img.size
                    self.bg_dimensions.set(f"{w} x {h}")
            except Exception as e:
                self.bg_dimensions.set("读取失败")

    def select_fg(self):
        folder = filedialog.askdirectory(title="选择前景文件夹")
        if folder:
            self.fg_folder = folder
            self.fg_entry.delete(0, tk.END)
            self.fg_entry.insert(0, folder)

    def select_out(self):
        folder = filedialog.askdirectory(title="选择输出目录")
        if folder:
            self.out_folder = folder
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, folder)
        else:
            self.out_folder = self.fg_folder if self.fg_folder else os.path.dirname(self.bg_path)
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, self.out_folder)

    def choose_frame_color(self):
        color = colorchooser.askcolor(initialcolor=self.frame_color.get())
        if color[1]:
            self.frame_color.set(color[1])
            self.frame_color_label.config(text=color[1], background=color[1])

    def setup_queue(self):
        import queue
        self.message_queue = queue.Queue()
        self.after(100, self.process_messages)

    def process_messages(self):
        while not self.message_queue.empty():
            msg_type, content = self.message_queue.get()
            self.log_area.insert(tk.END, content + "\n")
            self.log_area.see(tk.END)
            if msg_type == "progress":
                self.progress_bar["value"] = content
                self.status_var.set(f"进度: {content}/{self.progress_bar['maximum']}")
        self.after(100, self.process_messages)

    def start_merge(self):
        if not self.bg_path:
            messagebox.showerror("错误", "请先选择背景图")
            return
        mode = self.operation_mode.get()
        if mode in ["合成", "添加相框"]:
            if not self.fg_folder:
                messagebox.showerror("错误", "请先选择前景文件夹")
                return
        if not self.out_folder:
            self.out_folder = self.fg_folder if self.fg_folder else os.path.dirname(self.bg_path)
            self.out_entry.delete(0, tk.END)
            self.out_entry.insert(0, self.out_folder)
        threading.Thread(target=self.process_merge, daemon=True).start()

    def process_merge(self):
        mode = self.operation_mode.get()
        try:
            bg = Image.open(self.bg_path).convert("RGBA")
            bg_width, bg_height = bg.size
            self.message_queue.put(("info", f"背景图尺寸：{bg_width} x {bg_height}"))
            if mode == "添加相框":
                try:
                    frame_w = int(self.frame_width.get())
                except:
                    self.message_queue.put(("error", "相框宽度无效"))
                    return
                f_color = self.frame_color.get() if self.frame_color.get().startswith("#") else "#000000"
                framed = ImageOps.expand(bg, border=frame_w, fill=f_color)
                new_w, new_h = framed.size
                self.message_queue.put(("info", f"添加相框后尺寸：{new_w} x {new_h}"))
                out_path = os.path.join(self.out_folder, os.path.basename(self.bg_path))
                framed.convert("RGB").save(out_path)
                self.message_queue.put(("info", f"相框添加成功，保存至：{out_path}"))
            else:
                # 合成模式或背景为相框模式
                if mode == "背景为相框":
                    try:
                        inner_left = int(self.inner_left.get())
                        inner_top = int(self.inner_top.get())
                        inner_width = int(self.inner_width.get())
                        inner_height = int(self.inner_height.get())
                    except:
                        self.message_queue.put(("error", "内嵌区域参数无效"))
                        return
                    target_region = (inner_left, inner_top, inner_left + inner_width, inner_top + inner_height)
                    self.message_queue.put(("info", f"内嵌区域设置：{target_region}"))
                fg_files = [f for f in os.listdir(self.fg_folder) if f.lower().endswith(SUPPORTED_EXTS)]
                total = len(fg_files)
                self.progress_bar["maximum"] = total
                processed = 0
                for idx, fg_file in enumerate(fg_files, start=1):
                    fg_path = os.path.join(self.fg_folder, fg_file)
                    try:
                        fg = Image.open(fg_path).convert("RGBA")
                        if self.auto_adjust.get():
                            fg = fg.resize((bg_width, bg_height), Image.LANCZOS)
                            pos = (0, 0)
                        else:
                            if mode == "背景为相框":
                                pos = (target_region[0], target_region[1])
                                fg = fg.resize((inner_width, inner_height), Image.LANCZOS)
                            else:
                                if self.position_mode.get() == "居中":
                                    pos = ((bg_width - fg.width) // 2, (bg_height - fg.height) // 2)
                                elif self.position_mode.get() == "左上角":
                                    pos = (0, 0)
                                elif self.position_mode.get() == "右下角":
                                    pos = (bg_width - fg.width, bg_height - fg.height)
                                elif self.position_mode.get() == "自定义":
                                    try:
                                        pos = (int(self.custom_x.get()), int(self.custom_y.get()))
                                    except:
                                        pos = ((bg_width - fg.width) // 2, (bg_height - fg.height) // 2)
                                else:
                                    pos = ((bg_width - fg.width) // 2, (bg_height - fg.height) // 2)
                        if self.opacity.get() < 100:
                            alpha = fg.split()[3]
                            alpha = alpha.point(lambda p: int(p * (self.opacity.get() / 100)))
                            fg.putalpha(alpha)
                        if self.merge_mode.get() == "混合":
                            if fg.size != (bg_width, bg_height):
                                self.message_queue.put(("error", f"{fg_file} 尺寸 {fg.size} 与背景尺寸不一致，无法混合，跳过"))
                                continue
                            factor = self.opacity.get() / 100
                            composite = Image.blend(bg, fg, factor)
                        else:
                            composite = bg.copy()
                            composite.paste(fg, pos, mask=fg)
                        out_path = os.path.join(self.out_folder, fg_file)
                        composite.convert("RGB").save(out_path)
                        self.message_queue.put(("info", f"合成成功: {fg_file}"))
                        processed += 1
                    except Exception as e:
                        self.message_queue.put(("error", f"{fg_file} 合成失败: {str(e)}"))
                    self.message_queue.put(("progress", idx))
                self.message_queue.put(("info", f"合成完成！成功合成 {processed} 个文件，共 {total} 个文件"))
            bg.close()
        except Exception as e:
            self.message_queue.put(("error", f"全局错误: {str(e)}"))

if __name__ == "__main__":
    root = tk.Tk()
    root.title("图片合成/相框工具")
    app = MergeFrame(root)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
