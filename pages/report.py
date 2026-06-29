""" pages/report.py 报告生成与导出页 """
import streamlit as st
from utils.report_generator import ReportGenerator
from datetime import datetime
import os
def render():
    st.title("📑 节能评估报告生成")
    print("【DEBUG】当前工作目录 (CWD):", os.getcwd())
    print("【DEBUG】当前目录下的文件列表:", os.listdir())
    # --- 4. 导航 ---
    if st.button("⬅️ 返回上一页"):
        st.session_state.page = "audit_result"
        st.rerun()
    # --- 1. 数据获取与路径修正 ---
    # 打印当前状态用于调试（可选，上线时可删除）
    # print("Session State:", st.session_state)

    # 获取数据：根据你的 Session State 结构，数据在 'app_data' 下
    app_data = st.session_state.get('app_data', {})

    # 从 app_data 中提取具体对象
    # 注意：你的数据结构中，项目基本信息在顶层，而 audit_results 在 app_data 下
    project_info = app_data.get('project_info', {})
    audit_results = app_data.get('audit_results', {})

    # 兼容性处理：如果 project_info 是嵌套在 audit_results.data 里的（取决于你保存的方式）
    # 根据你上一轮的打印，audit_results['data'] 里也有 project_info，这里优先用顶层的
    if not project_info and 'data' in audit_results:
        project_info = audit_results['data'].get('project_info', {})

    # 检查必要数据是否存在
    if not project_info or not audit_results:
        print("当前目录下的文件列表：", os.listdir())
        st.warning("数据缺失，请先完成评估计算！")
        if st.button("返回评估"):
            st.session_state.page = "audit_result"
            st.rerun()
        return

    # --- 2. 报告预览摘要 ---
    st.markdown("### 报告摘要")

    # 项目名称
    project_name = project_info.get('project_name', '未命名项目')
    st.markdown(f"**项目名称**: {project_name}")

    # 当前时间与地点 (替换 <time_location>)
    # 当前时间：2026-06-23 星期二
    # 当前地点：北京市
    current_time = datetime.now().strftime('%Y-%m-%d %A')
    st.markdown(f"**评估日期/地点**: {current_time} / 北京市")

    # 能效数据
    # 兼容 audit_results 结构，data 可能是字典或者对象
    data_in_result = audit_results.get('data', {})
    if isinstance(data_in_result, dict):
        current_cop = data_in_result.get('current_cop', 0)
        baseline_cop = data_in_result.get('baseline_cop', 0)
        opt_cop = data_in_result.get('expected_optimal_cop', 0)
    else:
        # 如果是对象
        current_cop = getattr(data_in_result, 'current_cop', 0)
        baseline_cop = getattr(data_in_result, 'baseline_cop', 0)
        opt_cop = getattr(data_in_result,'expected_optimal_cop', 0)

    st.markdown(f"**当前COP**: {current_cop:.2f} (基准: {baseline_cop:.2f}(预期: {opt_cop:.2f})")

    # --- 3. 导出选项 ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("导出 PDF 报告")
        if st.button("🖨️ 生成 PDF"):
            # 调用生成器
            # 注意：这里传入的数据结构需要和 ReportGenerator 期望的格式一致
            pdf_bytes = ReportGenerator.generate_pdf_report(project_info, audit_results)
            st.download_button(
                label="⬇️ 下载 PDF",
                data=pdf_bytes,
                file_name=f"{project_name}_节能报告.pdf",
                mime="application/pdf"
            )

    with col2:
        st.subheader("导出 Excel 详细数据")
        if st.button("📊 生成 Excel"):
            # 合并数据用于导出
            equipment_params = app_data.get('equipment_params', {})
            combined_data = {**{'project_info': project_info}, **audit_results,**equipment_params}
            excel_bytes = ReportGenerator.generate_excel_report(combined_data)
            st.download_button(
                label="⬇️ 下载 Excel",
                data=excel_bytes,
                file_name=f"{project_name}_详细数据.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )



if __name__ == "__main__":
    render()