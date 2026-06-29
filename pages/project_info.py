"""
pages/project_info.py
页面: 项目信息录入页
对应文档: 空调机房优化运行平台 - 用户界面层详细设计文档_v1.docx (3.1)
"""
import streamlit as st
from utils.excel_handler import ExcelDataManager
import os


def render():
    st.set_page_config(page_title="项目信息录入", page_icon="🏢", layout="wide")
    st.title("🏢 项目基本信息配置")

    # 初始化数据管理器
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = ExcelDataManager()

    # --- 侧边栏输入 (对应文档 3.1.1) ---
    st.sidebar.header("📝 项目基础数据")
    st.sidebar.markdown("请填写项目的基本信息")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        project_name = st.text_input("项目名称", value="新项目", key="proj_name")
        building_area = st.number_input("建筑面积 (㎡)", min_value=0, value=10000, step=100)

    with col2:
        project_type = st.selectbox(
            "项目类型",
            options=["commercial", "office", "hospital", "school", "industrial"],
            format_func=lambda x: {"commercial": "商业建筑", "office": "办公楼"}.get(x, x)
        )
        design_cold_load = st.number_input("设计冷负荷 (kW)", min_value=0, value=800)

    operation_hours = st.sidebar.slider("日运行时间 (小时)", min_value=0, max_value=24, value=24)
    annual_days = st.sidebar.slider("年运行天数", min_value=0, max_value=365, value=300)

    # --- 主内容区 ---
    st.markdown("### 项目概览")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("项目名称", project_name)
    with col2:
        st.metric("建筑规模", f"{building_area:,} ㎡")
    with col3:
        st.metric("设计负荷", f"{design_cold_load} kW")

    # --- 保存与下一步 ---
    st.sidebar.markdown("---")
    if st.sidebar.button("💾 保存并继续", type="primary"):
        project_data = {
            "project_info": {
                "project_id": project_name.replace(" ", "_"),
                "project_name": project_name,
                "building_area": building_area,
                "project_type": project_type,
                "design_cold_load": design_cold_load,
                "operation_hours": operation_hours,
                "annual_days": annual_days
            }
        }

        # 保存到会话状态供全局使用
        st.session_state.current_project = project_data
        st.success(f"项目 '{project_name}' 信息已保存！")

        # 自动跳转到下一页 (设备配置)
        st.session_state.page = "equipment_config"
        st.rerun()


if __name__ == "__main__":
    render()