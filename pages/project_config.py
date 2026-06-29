import streamlit as st
import json
import os
import time
from pathlib import Path

# --- 1. 配置区域 ---
# 获取项目根目录下的 data 文件夹
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)  # 确保 data 目录存在
print(str(DATA_DIR))
# 定义全局工作区文件 (用于当前运行时的缓存)
WORKSPACE_FILE = DATA_DIR / "app_data.json"


def get_all_project_files():
    """
    从 data 目录下扫描所有符合 '*_info.json' 格式的文件，提取项目名称。
    Returns:
        list: 项目名称列表 (不包含后缀)
    """
    projects = []
    for file in DATA_DIR.glob("*_info.json"):
        # 去掉 '_info.json' 后缀，得到项目名
        project_name = file.stem.replace("_info", "")
        projects.append(project_name)
        print("====================project_name")
        print(project_name)
    return projects


def load_project_data(project_name):
    """
    加载指定的历史项目数据。
    Args:
        project_name (str): 项目名称
    Returns:
        dict: 项目数据，如果失败则返回空字典
    """
    file_path = DATA_DIR / f"{project_name}_info.json"
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"读取项目文件失败: {e}")
    return {}


def save_project_data(project_info):
    """
    1. 保存项目数据到独立的 JSON 文件 (备份)。
    2. 同时更新 app_data.json (工作区)。
    """
    project_name = project_info.get("project_name", "未命名项目").strip()
    if not project_name:
        project_name = "未命名项目"

    # 构建文件名
    file_path = DATA_DIR / f"{project_name}_info.json"

    # 1. 保存到独立文件 (备份)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(project_info, f, ensure_ascii=False, indent=4)
        # st.success(f"项目 [{project_name}] 已备份到 {file_path.name}")
    except Exception as e:
        st.error(f"❌ 备份项目文件失败: {e}")

    # 2. 保存到工作区 (app_data.json)，供其他页面读取
    try:
        with open(WORKSPACE_FILE, 'w', encoding='utf-8') as f:
            json.dump({"project_info": project_info}, f, ensure_ascii=False, indent=4)
        # 更新 Session State
        if 'app_data' in st.session_state:
            st.session_state.app_data = {"project_info": project_info}
    except Exception as e:
        st.error(f"❌ 更新工作区失败: {e}")


def delete_project(project_name):
    """
    删除指定的历史项目文件。
    """
    file_path = DATA_DIR / f"{project_name}_info.json"
    if file_path.exists():
        try:
            # os.remove(file_path)
            file_path.unlink()
            st.success(f"🗑️ 项目 [{project_name}] 已删除")
            # 如果删除的是当前加载的项目，清空工作区
            if st.session_state.get('current_project_name') == project_name:
                if os.path.exists(WORKSPACE_FILE):
                    os.remove(WORKSPACE_FILE)
                st.session_state.app_data = {}
            st.rerun()
        except Exception as e:
            st.error(f"删除文件失败: {e}")


# --- 页面渲染逻辑 ---
def render():
    st.title("🏢 项目信息配置")
    st.write("请填写或修改项目的基本信息...")

    # 1. 获取当前工作区数据 (app_data.json)
    if 'app_data' in st.session_state:
        app_data = st.session_state.app_data
    else:
        # 如果 Session State 没有，则读取文件
        if os.path.exists(WORKSPACE_FILE):
            try:
                with open(WORKSPACE_FILE, 'r', encoding='utf-8') as f:
                    app_data = json.load(f)
            except:
                app_data = {}
        else:
            app_data = {}

    current_info = app_data.get('project_info', {})
    if not isinstance(current_info, dict):
        current_info = {}

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
                            st.rerun()
                with col2:
                    # 删除按钮
                    if st.button("🗑️ 删除", key=f"del_{selected_project}"):
                        delete_project(selected_project)
        else:
            st.info("暂无历史项目")

    # --- 主页面：表单输入 ---

    # 返回按钮
    if st.button("⬅️ 返回上一页"):
        st.session_state.page = "overview"
        st.rerun()

    # 表单
    with st.form(key="project_info_form"):
        col1, col2 = st.columns(2)

        with col1:
            # 如果是加载的历史项目，显示其名称；否则允许输入新名称
            project_name = st.text_input(
                "项目名称",
                value=current_info.get("project_name", f"项目_{int(time.time())}")
            )
            building_area = st.number_input(
                "建筑面积 (㎡)",
                min_value=0,
                value=current_info.get("building_area", 10000)
            )

        with col2:
            project_type = st.selectbox(
                "项目类型",
                options=["retrofit", "commercial", "office", "hospital", "school"],
                format_func=lambda x: {
                    "retrofit": "改造项目",
                    "commercial": "商业建筑",
                    "office": "办公楼",
                    "hospital": "医院",
                    "school": "学校"
                }.get(x, x),
                index=0
            )
            op_hours = st.slider(
                "日运行时间 (小时)",
                min_value=0,
                max_value=24,
                value=current_info.get("operation_hours_per_day", 10)
            )
            op_days = st.slider(
                "年运行天数",
                min_value=0,
                max_value=365,
                value=current_info.get("operation_days_per_year", 180)
            )

        submit = st.form_submit_button("💾 保存并继续", type="primary")

        if submit:
            # 构建新数据
            new_project_info = {
                "project_name": project_name,
                "building_area": building_area,
                "project_type": project_type,
                "operation_hours_per_day": op_hours,
                "operation_days_per_year": op_days,
                "project_id": current_info.get("project_id", f"PROJ_{int(time.time())}")
            }

            # 保存 (备份到独立文件 + 更新工作区)
            save_project_data(new_project_info)

            # 跳转
            st.session_state.page = "equipment_config"
            st.rerun()


# 如果直接运行此文件进行调试
if __name__ == "__main__":
    render()