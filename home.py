import tkinter as tk
from tkinter import ttk
import webbrowser

class HomeFrame(ttk.Frame):
    def __init__(self, parent, notebook=None):
        super().__init__(parent, padding=20)
        self.notebook = notebook
        self.tool_map = {
            "图片拼接": 1,
            "DDS转换为图片": 2,
            "批量裁剪": 3,
            "批量重命名": 4,
            "图片尺寸调整": 5,
            "图片旋转": 6,
            "图片合并": 7,
            "文件提删": 8
        }
        self.create_widgets()
        # 渐变颜色列表
        self.gradient_colors = ["#FF0000", "#0000FF", "#00FF00", "#FFFF00", "#800080"]
        self.current_color_index = 0
        self.next_color_index = 1
        self.t = 0.0
        self.dt = 0.01
        self.update_author_gradient()

    def create_widgets(self):
        # 标题 Label（添加鼠标悬停效果）
        self.title_label = ttk.Label(self, text="多功能图片工具箱", font=("微软雅黑", 24, "bold"))
        self.title_label.pack(pady=(30, 20))
        self.title_label.bind("<Enter>", lambda e: self.title_label.config(font=("微软雅黑", 26, "bold")))
        self.title_label.bind("<Leave>", lambda e: self.title_label.config(font=("微软雅黑", 24, "bold")))

        # 工具列表（竖向排列），每个工具名称添加鼠标悬停效果
        tools_frame = ttk.Frame(self)
        tools_frame.pack(pady=10)
        tool_styles = [
            ("图片拼接", "#4A90E2"),
            ("DDS转换为图片", "#50B285"),
            ("批量裁剪", "#5C6BC0"),
            ("批量重命名", "#4DB6AC"),
            ("图片尺寸调整", "#7986CB"),
            ("图片旋转", "#81C784"),
            ("图片合并", "#BA68C8"),
            ("文件提删", "#FF9800")
        ]
        for tool_name, color in tool_styles:
            lbl = tk.Label(tools_frame, text=tool_name, fg=color,
                           font=("微软雅黑", 14, "bold"), cursor="hand2")
            lbl.pack(pady=6, anchor="center")
            lbl.bind("<Button-1>", lambda e, name=tool_name: self.switch_tab(name))
            lbl.bind("<Enter>", lambda e: e.widget.config(font=("微软雅黑", 16, "bold")))
            lbl.bind("<Leave>", lambda e: e.widget.config(font=("微软雅黑", 14, "bold")))

        # 底部区域：显示作者信息和 GitHub 链接，使用一个 Label 显示完整文本
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side=tk.BOTTOM, pady=20)
        self.author_label = tk.Label(bottom_frame,
                                     text="Author: miludelongang",
                                     font=("Arial", 9))
        self.author_label.pack(side=tk.LEFT, padx=5)
        # GitHub 链接
        github_label = ttk.Label(bottom_frame,
                                 text="GitHub",
                                 font=("Arial", 9, "underline"),
                                 foreground="blue", cursor="hand2")
        github_label.pack(side=tk.LEFT, padx=5)
        github_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/miludelongwang/ImagesTools"))

    def update_author_gradient(self):
        # 根据当前插值参数计算渐变颜色
        current = self.gradient_colors[self.current_color_index]
        nxt = self.gradient_colors[self.next_color_index]
        new_color = self.interpolate_color(current, nxt, self.t)
        self.author_label.config(foreground=new_color)
        self.t += self.dt
        if self.t >= 1.0:
            self.t = 0.0
            self.current_color_index = self.next_color_index
            self.next_color_index = (self.next_color_index + 1) % len(self.gradient_colors)
        self.after(50, self.update_author_gradient)

    def interpolate_color(self, color1, color2, t):
        # 将 #RRGGBB 转换为 (r, g, b)，进行插值后返回新颜色字符串
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f"#{r:02X}{g:02X}{b:02X}"

    def switch_tab(self, tool_name):
        if self.notebook and tool_name in self.tool_map:
            index = self.tool_map[tool_name]
            self.notebook.select(index)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("多功能图片工具箱")
    root.geometry("500x500")
    frame = HomeFrame(root)
    frame.pack(fill=tk.BOTH, expand=True)
    root.mainloop()
