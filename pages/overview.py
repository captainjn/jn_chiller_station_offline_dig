"""
pages/overview.py
首页 - 项目概览与历史项目复用
"""
import streamlit as st
import json
import os
import time
from pathlib import Path
from pages.project_config import *

# --- 1. 配置区域 ---
# 获取项目根目录下的 data 文件夹
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)  # 确保 data 目录存在
print(str(DATA_DIR))
# 定义全局工作区文件 (用于当前运行时的缓存)
WORKSPACE_FILE = DATA_DIR / "app_data.json"
def render():
    st.title("🏠 项目概览")
    st.markdown("### 欢迎使用空调机房运行优化预期效果评估工具")

    # 历史项目复用 (文档 3.2 交互设计原则)
    st.sidebar.header("快速开始")
    if st.sidebar.button("➕ 新建项目"):
        st.session_state.page = "project_info"
        st.rerun()

        # --- 左侧导航栏：历史项目列表 ---
    with st.sidebar:
            st.header("📂 历史项目")

            # 获取 data 目录下所有历史项目
            history_projects = get_all_project_files()

            if history_projects:
                selected_project = st.selectbox("选择历史项目", ["--- 请选择 ---"] + history_projects)

                if selected_project != "--- 请选择 ---":
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📂 加载", type="primary", key=f"load_{selected_project}"):
                            # 加载选中项目的数据
                            data = load_project_data(selected_project)
                            if data:
                                # 覆盖写入工作区 (app_data.json)
                                save_project_data(data)
                                st.session_state.current_project_name = selected_project
                                st.session_state.page = "project_info"
                                st.rerun()
                    with col2:
                        # 删除按钮
                        if st.button("🗑️ 删除", key=f"del_{selected_project}"):
                            delete_project(selected_project)
            else:
                st.info("暂无历史项目")

    # 主内容区
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("平台功能")
        st.markdown("""
        - **参数配置**: 录入项目、设备及运行数据
        - **智能评估**: 基于行业标准算法的能效分析
        - **报告导出**: 一键生成 PDF/Excel 报告
        """)

    with col2:
        st.subheader("评估流程")
        st.markdown("""
        1. 输入项目基本信息
        2. 配置设备参数
        3. 录入运行实测数据
        4. 查看评估结果
        5. 导出报告
        """)

if __name__ == "__main__":
    render()