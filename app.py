"""
app.py - 空调机房优化平台主入口
"""

import streamlit as st
import json
import os

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="空调机房优化平台",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"  # 侧边栏默认展开
)

# --- 2. 全局常量与默认数据 ---
DATA_FILE = "app_data.json"

# 定义默认项目信息，防止 KeyError
DEFAULT_PROJECT_INFO = {
    "project_name": "未命名项目",
    "building_area": 10000,
    "project_type": "retrofit",
    "design_cold_load": 800,
    "operation_hours_per_day": 10,
    "operation_days_per_year": 180
}

DEFAULT_DATA = {
    "project_info": DEFAULT_PROJECT_INFO.copy(),
    "equipment_params": {
        "chillers": [{"name": "冷机 1", "capacity": 1000, "power": 200}],
        "pumps": [],
        "towers": []
    },
    "operation_data": {}
}


# --- 3. 辅助函数：确保数据文件存在及结构完整 ---
# --- 3. 辅助函数：初始化数据文件并返回数据 ---
def init_data_file():
    """
    初始化数据文件。
    Returns:
        dict: 返回文件中的数据字典
    """
    # 1. 如果文件不存在，创建新文件并返回默认数据
    if not os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_DATA, f, ensure_ascii=False, indent=4)
            st.toast(" 数据文件初始化成功", icon="✅")
        except Exception as e:
            st.error(f" 数据文件创建失败: {e}")
        return DEFAULT_DATA.copy()  # 返回默认数据副本

    # 2. 如果文件存在，读取并修复结构
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        need_save = False
        # 情况 A：文件是空的或不是字典
        if not isinstance(data, dict):
            data = {}
            need_save = True

        # 情况 B：缺少 'project_info' 键
        if 'project_info' not in data:
            # 将顶层的键值对尝试合并到 project_info 中（兼容旧版）
            # 或者直接使用默认值
            data['project_info'] = DEFAULT_PROJECT_INFO.copy()
            # 将旧版的顶层数据迁移过来（如果存在）
            for key in ['project_name', 'building_area', 'project_type']:
                if key in data:
                    data['project_info'][key] = data[key]
                    del data[key]  # 删除旧的顶层键
            need_save = True

        # 情况 C：project_info 存在但缺少具体字段
        else:
            default_proj = DEFAULT_PROJECT_INFO
            proj_info = data['project_info']
            for key, value in default_proj.items():
                if key not in proj_info:
                    proj_info[key] = value
                    need_save = True

        # 如果有结构变动，写回文件
        if need_save:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            st.toast("🔧 项目数据结构已更新", icon="🔄")

        return data  # 返回读取到的数据

    except json.JSONDecodeError as e:
        st.error(f" 数据文件损坏: {e}")
        # 损坏时重置文件
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_DATA, f, ensure_ascii=False, indent=4)
        return DEFAULT_DATA.copy()


# --- 4. 初始化 Session State ---
if 'page' not in st.session_state:
    st.session_state.page = "overview"

# --- 新增逻辑：加载全局数据 ---
# 调用函数获取数据
loaded_data = init_data_file()
# 将数据存入 session_state，这样其他页面也能方便地使用
if 'app_data' not in st.session_state:
    st.session_state.app_data = loaded_data
    # --- 4. 初始化 Session State ---
if 'page' not in st.session_state:
    st.session_state.page = "overview"

# 确保数据文件已初始化
init_data_file()

# --- 5. 页面路由配置 ---
# 注意：这里的键对应 st.session_state.page 的值
# 假设你已创建 pages/project_config.py 作为项目信息录入页
PAGES = {
    "overview": lambda: __import__('pages.overview', fromlist=['render']).render(),
    "project_info": lambda: __import__('pages.project_config', fromlist=['render']).render(),  # 指向新的配置页
    "equipment_config": lambda: __import__('pages.equipment_config', fromlist=['render']).render(),
    "operation_data": lambda: __import__('pages.operation_data', fromlist=['render']).render(),
    "audit_result": lambda: __import__('pages.audit_result', fromlist=['render']).render(),
    "report": lambda: __import__('pages.report', fromlist=['render']).render()
}


# --- 6. 主程序逻辑 ---
def main():
    current_page = st.session_state.get("page", "overview")

    # 安全检查：防止页面名称错误
    if current_page not in PAGES:
        st.warning(f" 页面 '{current_page}' 未找到，正在返回首页...")
        st.session_state.page = "overview"
        st.rerun()

    # 渲染当前页面
    try:
        PAGES[current_page]()
    except Exception as e:
        st.error(f" 页面加载出错: {e}")
        st.exception(e)  # 开发阶段显示详细堆栈


if __name__ == "__main__":
    main()