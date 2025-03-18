import tkinter as tk
from tkinter import ttk
from home import HomeFrame
from stitching import StitchingFrame
from dds_conversion import DDSConversionFrame
from crop import CropFrame
from rename import RenameFrame
from resizing import ResizingFrame
from rotate import RotationFrame
from merge import MergeFrame
from extraction import ExtractionFrame

class ToolboxApp:
    def __init__(self, root):
        self.root = root
        self.root.title("多功能图片工具箱")
        self.root.geometry("1000x800")
        self.create_widgets()

    def create_widgets(self):
        # 创建 Notebook 作为标签页容器
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 创建各功能模块界面，注意这里的顺序必须与 HomeFrame 中的索引映射对应：
        # 主页索引为 0，后续依次为：图片拼接、DDS转换、批量裁剪、批量重命名、图片尺寸调整、图片旋转、图片合成
        self.home_frame = HomeFrame(self.notebook, notebook=self.notebook)
        self.stitching_frame = StitchingFrame(self.notebook)
        self.dds_conversion_frame = DDSConversionFrame(self.notebook)
        self.crop_frame = CropFrame(self.notebook)
        self.rename_frame = RenameFrame(self.notebook)
        self.resizing_frame = ResizingFrame(self.notebook)
        self.rotate_frame = RotationFrame(self.notebook)
        self.merge_frame = MergeFrame(self.notebook)
        self.extraction_frame = ExtractionFrame(self.notebook)

        # 将各模块添加到 Notebook 中
        self.notebook.add(self.home_frame, text="主页")
        self.notebook.add(self.stitching_frame, text="图片拼接")
        self.notebook.add(self.dds_conversion_frame, text="DDS转换为图片")
        self.notebook.add(self.crop_frame, text="批量裁剪")
        self.notebook.add(self.rename_frame, text="批量重命名")
        self.notebook.add(self.resizing_frame, text="图片尺寸调整")
        self.notebook.add(self.rotate_frame, text="图片旋转")
        self.notebook.add(self.merge_frame, text="图片合并")
        self.notebook.add(self.extraction_frame, text="文件提删")

if __name__ == "__main__":
    root = tk.Tk()
    app = ToolboxApp(root)
    root.mainloop()
