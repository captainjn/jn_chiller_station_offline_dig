import os
import sys
from PyInstaller.__main__ import run

# 项目根目录
base_dir = os.path.dirname(os.path.abspath(__file__))

# 构建参数
opts = [
    'app.py',  # 你的主入口文件
    '--name=空调机房优化运行平台',  # 生成的软件名
    '--windowed',  # 不显示控制台窗口 (如果需要看报错日志可去掉)
    '--icon=icon.ico',  # 可选：准备一个图标文件
    '--add-data=fonts;fonts', # 携带字体文件夹 (Windows用分号; Linux用冒号:)
    '--add-data=pages;pages', # 携带页面文件夹
    '--add-data=utils;utils', # 携带工具文件夹
    '--hidden-import=fpdf',   # 强制包含 fpdf
    '--hidden-import=plotly', # 强制包含 plotly
    '--hidden-import=pandas', # 强制包含 pandas
    '--clean',
    '--noconfirm'
]

# 执行打包
run(opts)