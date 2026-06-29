""" pages/operation_data.py 运行数据输入页 """
import streamlit as st
import os
import json
from datetime import datetime
from core.calculator import adapt_and_calculate, ProjectType

DATA_FILE = "app_data.json"

def render():
    od = {}
    st.title("📊 运行数据输入")
    st.markdown("请录入系统实测运行数据，用于节能潜力分析。")

    # --- 阶段 1：表单渲染 ---
    print("【STAGE 1】页面渲染开始...")
    # --- 新增：顶部返回按钮 ---
    col1, col2 = st.columns([1, 10])
    with col1:
        if st.button("⬅️ 返回上一页"):
                st.session_state.page = "equipment_config"
                st.rerun()
    # 总能耗与制冷量
    col1, col2 = st.columns(2)
    with col1:
        od['wet_bulb_temp'] = st.number_input("湿球温度（℃）", value=float(od.get('wet_bulb_temp', 26.1)),min_value=0.0, step=100.0)
    with col1:
        od["total_cooling_load"] = st.number_input("系统实测总制冷量 (kW)(必填)", value=float(od.get('total_cooling_load', 1900)),min_value=0.0, step=100.0)
        od['total_flow'] = st.number_input("实测冷冻水流量 (m³/h)(选填)", value=float(od.get('total_flow', 200)))
        od['supply_temp'] = col2.number_input("实测供水温度 (℃)", value=float(od.get('supply_temp', 7)))
        od['return_temp'] = col2.number_input("实测回水温度 (℃)", value=float(od.get('return_temp', 10)))
    # 负荷率分布
    st.subheader("负荷率分布")
    st.caption("请按 20% 分档填写各负荷区间的运行时间百分比")
    load_20 = st.slider("0-20% 负荷占比 (%)", 0, 100, 10)
    load_40 = st.slider("20-40% 负荷占比 (%)", 0, 100, 20)
    load_60 = st.slider("40-60% 负荷占比 (%)", 0, 100, 30)
    load_80 = st.slider("60-80% 负荷占比 (%)", 0, 100, 25)
    load_100 = st.slider("80-100% 负荷占比 (%)", 0, 100, 15)

    # 验证总和
    total_load = load_20 + load_40 + load_60 + load_80 + load_100
    if abs(total_load - 100) > 0.1:
        st.warning(f"警告: 负荷占比总和为 {total_load:.1f}%，将自动调整至 100%")
        r=total_load/100
        load_20, load_40, load_60, load_80, load_100=load_20/r, load_40/r, load_60/r, load_80/r, load_100/r
    od["load_ratio_data"] = [load_20, load_40, load_60, load_80, load_100]


    # --- 阶段 2：按钮逻辑 ---
    if st.button("🚀 开始评估", type="primary", use_container_width=True):
        print("【STAGE 2】按钮被点击！")
        st.success("✅ 开始评估流程")

        try:
            # 2.1 检查文件
            if not os.path.exists(DATA_FILE):
                print("【ERROR】文件不存在:", DATA_FILE)
                st.error("❌ 数据文件丢失，请重新配置。")
                return
            else:
                print("【OK】文件存在，准备读取...")

            # 2.2 读取数据
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
            print("【STAGE 3】数据读取成功，当前数据 Keys:", all_data.keys())

            # 2.3 更新数据
            all_data["operation_data"] = od
            print("【STAGE 4】数据更新完成，准备写入...")

            # 2.4 写入文件
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=4)
            print("【STAGE 5】数据保存成功！")
            st.success("💾 数据已保存")

            # --- 数据整合与计算 ---
            print("【STAGE 6】开始数据整合...")

            # 调试：打印原始数据结构，看是否包含 equipment_params
            print("Raw JSON Data Structure:", list(all_data.keys()))
            if "equipment_params" not in all_data:
                print("【CRITICAL】错误：JSON 中没有 equipment_params 键！")
                st.error("数据结构错误：缺少设备参数，请先配置设备。")
                return

            input_data_for_calc = {
                "project_info": all_data.get("project_info", {}),
                "equipment_params": all_data.get("equipment_params", {}),
                "chillers": all_data.get("equipment_params", {}).get("chillers", [{}]),
                "pumps": all_data.get("equipment_params", {}).get("pumps", []),
                "towers": all_data.get("equipment_params", {}).get("towers", []),
                "operation_data": od
            }

            print("【STAGE 7】调用计算引擎 adapt_and_calculate...")
            print(input_data_for_calc)
            calculation_result = adapt_and_calculate(input_data_for_calc)
            print("【STAGE 8】计算完成！", calculation_result)

            # --- 结果处理 ---
            if hasattr(calculation_result, 'project_info') and calculation_result.project_info.project_id == "ERROR":
                print("【RESULT】计算引擎返回错误")
                st.error("计算失败，请检查输入参数")
            else:
                print("【RESULT】计算成功，准备保存结果...")
                print(calculation_result)
                # 重新读取最新文件，防止覆盖
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    final_data = json.load(f)

                final_data['audit_results'] = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "data": object_to_dict(calculation_result)  # 使用新函数
                }

                with open(DATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump(final_data, f, ensure_ascii=False, indent=4)
                print("【RESULT】结果已写入 JSON")

                st.success("✅ 评估完成！正在跳转...")
                st.session_state.page = "audit_result"
                st.rerun()

        except Exception as e:
            print("【EXCEPT】捕获到异常:", str(e))
            st.error(f"流程出错: {e}")

    # st.title("📊 运行数据输入")
def object_to_dict(obj):
    """递归将对象转换为字典"""
    if hasattr(obj, '__dict__'):
        return {
            key: object_to_dict(value)
            for key, value in obj.__dict__.items()
            if not key.startswith('_')
        }
    elif isinstance(obj, list):
        return [object_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: object_to_dict(value) for key, value in obj.items()}
    else:
        return obj
if __name__ == "__main__":
    render()