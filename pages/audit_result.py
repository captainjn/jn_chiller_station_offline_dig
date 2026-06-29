"""
pages/audit_result.py
评估结果展示页
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os
import json
from core.calculator import adapt_and_calculate, ProjectType
# DATA_FILE = "app_data.json"
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app_data.json")

def render():
    st.title("📈 系统能效评估结果")
    # --- 新增：顶部返回按钮 ---
    col1, col2 = st.columns([1, 10])
    with col1:
        if st.button("⬅️ 返回上一页"):
                st.session_state.page = "operation_data"
                st.rerun()
    # 模拟计算结果 (实际应调用 core/calculator.py)
    # 这里使用模拟数据演示 UI
    current_cop = 3.5
    target_cop = 4.8
    annual_hour =8760
    #读取结果文件
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
        rslt=all_data["audit_results"]
        current_cop = rslt["data"]["current_cop"]
        target_cop = current_cop*(1+rslt["data"]["expected_saving_rate"]/100)
        operation_days_per_year = rslt["data"]["project_info"]["operation_days_per_year"]
        operation_hours_per_day = rslt["data"]["project_info"]["operation_hours_per_day"]
        annual_hour = operation_days_per_year * operation_hours_per_day
    except Exception as e:
        print("【EXCEPT】捕获到异常:", str(e))
        st.error(f"流程出错: {e}")

    saving_rate = (1 - current_cop/target_cop) * 100
    annual_saving_cost = saving_rate *  annual_hour # 简单换算模拟

    # 顶部指标卡 (文档 3.4.1)
    tab1, tab2, tab3 = st.tabs(["整体概览", "分项分析", "改进建议"])

    with tab1:
        st.subheader("核心能效指标")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("系统当前 COP", f"{current_cop:.3f}", delta=f"{current_cop-target_cop:.2f}", delta_color="inverse")
        col2.metric("预期优化 COP", f"{target_cop:.2f}")
        col3.metric("预期节能率", f"{saving_rate:.1f}%", delta_color="normal")
        col4.metric("年节能费用", f"{annual_saving_cost:,.0f} 元")

        # 环形图：能效等级
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = current_cop,
            title = {'text': "COP 状态"},
            gauge = {
                'axis': {'range': [0, 6]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 3], 'color': "red"},
                    {'range': [3, 4.5], 'color': "yellow"},
                    {'range': [4.5, 6], 'color': "lightgreen"}
                ]
            }
        ))
        fig_gauge.update_layout(height=250)
        st.plotly_chart(fig_gauge, width='stretch')

    with tab2:
        st.subheader("设备能效分析")

        # 水泵效率对比 (文档 3.4.2)
        st.markdown("**水泵效率对比**")
        # 模拟数据
        pump_data = px.data.tips()
        pump_df = pd.DataFrame({
            "Pump": ["冷冻泵 1", "冷冻泵 2", "冷却泵 1"],
            "实际效率": [0.65, 0.70, 0.60],
            "额定效率": [0.85, 0.85, 0.85]
        })
        fig_pump = px.bar(pump_df, x="Pump", y=["实际效率", "额定效率"],
                         barmode="group", color_discrete_sequence=["#1E88E5", "#FFC107"])
        st.plotly_chart(fig_pump, width='stretch')

        # 冷机 COP 对比
        st.markdown("**不同负荷率下 COP 对比**")
        load_ratios = ["20%", "40%", "60%", "80%", "100%"]
        baseline_cops = [2.0, 3.0, 4.0, 4.5, 5.0]
        optimized_cops = [2.5, 3.8, 4.8, 5.2, 5.5] # 模拟优化后

        fig_chiller = go.Figure()
        fig_chiller.add_trace(go.Scatter(x=load_ratios, y=baseline_cops, mode='lines+markers', name='基准 COP'))
        fig_chiller.add_trace(go.Scatter(x=load_ratios, y=optimized_cops, mode='lines+markers', name='优化 COP', line=dict(dash='dot')))
        fig_chiller.update_layout(yaxis_title="COP", xaxis_title="负荷率")
        st.plotly_chart(fig_chiller, width='stretch')

    with tab3:
        st.subheader("💡 改进建议")

        # 根据规则生成建议 (文档 3.4.3)
        suggestions = []

        if current_cop < target_cop:
            suggestions.append("🔴 系统整体能效偏低，建议进行全面的设备维护和控制策略优化。")
        if True: # 模拟温差问题
            suggestions.append("🔵 实际供回水温差偏低，建议检查水系统平衡及阀门状态。")
        if True: # 模拟水泵效率
            suggestions.append("水泵效率仅为额定值的 70%，建议检查叶轮磨损或变频器设置。")

        for sug in suggestions:
            st.info(sug)

    # 导出按钮
    if st.button("📤 生成详细报告"):
        st.session_state.page = "report"
        st.rerun()


def perform_calculation():
    """
    执行完整的计算流程
    """
    # 1. 合并所有需要的数据
    # 注意：这里的 key 需要和你页面存储的 key 一致
    all_data = {
        'project_info': st.session_state.get('project_info', {}),
        'equipment_params': st.session_state.get('equipment_params', []),  # 假设是列表
        'operation_data': st.session_state.get('operation_data', {}),
        'pumps_list': st.session_state.get('pumps_list', []),  # 确保页面保存了这个列表
        'cooling_towers_list': st.session_state.get('cooling_towers_list', [])
    }

    # 2. 调用适配后的计算器
    try:
        from core.calculator import adapt_and_calculate
        result = adapt_and_calculate(all_data)

        # 3. 将结果对象转换为字典存储 (因为 Session State 最好存原生类型或简单对象)
        # 这里简单处理，直接存对象 (Streamlit 通常支持)
        return result

    except ImportError:
        # 防止导入错误
        return None

if __name__ == "__main__":
    render()