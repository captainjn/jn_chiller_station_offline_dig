import streamlit as st
import json
import os

# 定义全局数据文件名（需与 main.py 保持一致）
DATA_FILE = "app_data.json"

def render():
    st.title("🏭 设备参数配置")

    # --- 新增：顶部返回按钮 ---
    col1, col2 = st.columns([1, 10])
    with col1:
        if st.button("⬅️ 返回上一页"):
                st.session_state.page = "project_config"
                st.rerun()
    st.markdown("### 点击下面一行选择设备类型，点击底部按钮继续")
    # --- 1. 安全加载数据 (核心修复点) ---
    # 初始化一个标准的默认结构，防止 KeyError
    default_structure = {
        "chillers": [{"name": "冷机 1", "capacity": 1000, "power": 200, "supply_temp": 7, "return_temp": 12}],
        "pumps": [
            {"name": "冷冻泵 1", "flow": 200, "head": 32, "power": 30,"type":1},
            {"name": "冷却泵 1", "flow": 240, "head": 32, "power": 37,"type":0}
        ],
        "towers": [{"name": "冷却塔 1", "flow": 240, "power": 15}]
    }

    params = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                file_data = json.load(f)

            # 兼容处理：尝试从不同层级获取数据
            if isinstance(file_data, dict):
                # 情况 A：标准结构 {'equipment_params': {...}}
                if 'equipment_params' in file_data:
                    params = file_data['equipment_params']
                # 情况 B：旧结构或扁平结构，直接包含了 chillers/pumps
                elif 'chillers' in file_data:
                    params = file_data
                else:
                    # 情况 C：文件存在但结构完全不对，使用默认值
                    params = default_structure.copy()
            else:
                # 情况 D：文件内容不是字典（例如是空文件或纯列表），使用默认值
                params = default_structure.copy()

        except (json.JSONDecodeError, Exception) as e:
            st.warning(f"⚠️ 数据文件损坏，已重置为默认值: {e}")
            params = default_structure.copy()
    else:
        # 文件不存在，使用默认值
        params = default_structure.copy()

    # --- 确保所有必要的键都存在 (双重保险) ---
    for key in ['chillers', 'pumps', 'towers']:
        if key not in params:
            params[key] = default_structure[key]

    # --- 2. 渲染界面 (使用 session_state 保持状态) ---
    # 将加载的数据放入 session_state，避免每次 rerun 都重新读文件导致输入框闪烁
    if 'current_params' not in st.session_state:
        st.session_state.current_params = params

    current_params = st.session_state.current_params

    # 创建三个标签页
    tab_chiller, tab_pump, tab_tower = st.tabs(["🧊 冷机参数", "💧 水泵参数", "🌬️ 冷却塔参数"])

    with tab_chiller:
        _render_device_list("chillers", current_params)

    with tab_pump:
        _render_device_list("pumps", current_params)

    with tab_tower:
        _render_device_list("towers", current_params)

    # --- 3. 保存按钮与跳转逻辑 ---
    st.divider()


    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 保存设备参数", type="primary"):
            # --- 修复开始 ---
            # 1. 获取当前所有数据
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
            else:
                all_data = {}

            # 2. 更新设备参数
            all_data["equipment_params"] = current_params
            # 注意：不要 touch all_data['project_info']，让它保持原样

            # 3. 写回
            try:
                with open(DATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, ensure_ascii=False, indent=4)
                st.success("✅ 保存成功！")
                # --- 新增：跳转逻辑 ---
                st.session_state.page = "operation_data"
                st.rerun()
            except Exception as e:
                st.error(f"❌ 保存失败: {e}")
            # --- 修复结束 ---

def _render_device_list(device_type, params_dict):
    """通用的设备列表渲染函数"""
    devices = params_dict.get(device_type, [])

    # 允许用户动态增删设备
    num_devices = st.number_input(
        f"{device_type} 数量（修改数字以增减台数，点击输入框下方生效）",
        min_value=0,
        max_value=10,
        value=len(devices),
        step=1,
        key=f"num_{device_type}"
    )

    # 调整列表长度以匹配用户输入的数量
    while len(devices) < num_devices:
        if device_type == "chillers": devices.append({"name": f"冷机 {len(devices)+1}"})
        if device_type == "pumps":    devices.append({"name": f"水泵 {len(devices)+1}"})
        if device_type == "towers":   devices.append({"name": f"冷塔 {len(devices)+1}"})
    while len(devices) > num_devices:
        devices.pop()

    # 渲染具体的输入框
    for i, device in enumerate(devices):
        if device_type == "chillers":   st.markdown(f"**--- 冷机 {i+1} ---**")
        if device_type == "pumps":      st.markdown(f"**--- 水泵 {i+1} ---**")
        if device_type == "towers":     st.markdown(f"**--- 冷塔 {i+1} ---**")

        cols = st.columns(3)

        # 名称输入
        device['name'] = cols[0].text_input(
            "设备名称",
            value=device.get('name', ''),
            key=f"{device_type}_name_{i}"
        )

        # 根据设备类型渲染不同的参数
        if device_type == "chillers":
            device['rated_cooling_capacity'] = cols[0].number_input("额定制冷量 (kW)", value=float(device.get('capacity', 1000)), key=f"{device_type}_cap0_{i}")
            device['rated_power'] = cols[0].number_input("额定功率 (kW)", value=float(device.get('rated_power', 200)), key=f"{device_type}_pow0_{i}")
            device['power'] = cols[1].number_input("实测功率 (kW)", value=float(device.get('power', 230)), key=f"{device_type}_pow_{i}")
            # 第二行参数
            device['design_supply_temp'] = cols[0].number_input("设计供水温度 (℃)", value=float(device.get('rated_supply_temp', 7)), key=f"{device_type}_sup0_{i}")
            device['design_return_temp'] = cols[0].number_input("设计回水温度 (℃)", value=float(device.get('rated_return_temp', 12)), key=f"{device_type}_ret0_{i}")


        elif device_type == "pumps":
            device['rated_flow'] = cols[0].number_input("额定流量 (m³/h)", value=float(device.get('rated_flow', 460)), key=f"{device_type}_flow0_{i}")
            device['rated_head'] = cols[0].number_input("额定扬程 (m)", value=float(device.get('rated_head', 12)), key=f"{device_type}_head0_{i}")
            device['rated_power'] = cols[0].number_input("额定功率 (kW)", value=float(device.get('rated_power', 20)), key=f"{device_type}_pow0_{i}")
            device['type'] = cols[0].number_input("冷冻/冷却水泵 (1/0)", value=int(device.get('type', 1)), key=f"{device_type}_type0_{i}")

            device['head'] = cols[1].number_input("实测扬程 (m)", value=float(device.get('head', 11)), key=f"{device_type}_head_{i}")
            device['power'] = cols[1].number_input("实测功率 (kW)", value=float(device.get('power', 18)), key=f"{device_type}_pow_{i}")

        elif device_type == "towers":
            device['rated_flow'] = cols[0].number_input("额定流量 (m³/h)", value=float(device.get('rated_flow', 240)), key=f"{device_type}_flow0_{i}")
            device['rated_power'] = cols[0].number_input("额定功率 (kW)", value=float(device.get('rated_power', 5)), key=f"{device_type}_pow0_{i}")
            device['rated_approach_temp'] = cols[0].number_input("额定逼近温差 (℃)", value=float(device.get('rated_approach_temp', 3)), key=f"{device_type}_dif0_{i}")

            device['power'] = cols[1].number_input("实测功率 (kW)", value=float(device.get('power', 5.1)), key=f"{device_type}_pow_{i}")
            device['inlet_temp'] = cols[1].number_input("实测入口温度 (℃)", value=float(device.get('inlet_temp', 35)), key=f"{device_type}_inT_{i}")
            device['outlet_temp'] = cols[1].number_input("实测出口温度 (℃)", value=float(device.get('outlet_temp', 32)), key=f"{device_type}_outT_{i}")


        st.caption("") # 增加一点间距


    params_dict[device_type] = devices