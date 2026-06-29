"""
utils/report_generator.py
报告生成工具
实现文档: 用户界面层详细设计文档 (3.5)
"""
import pandas as pd
from fpdf import FPDF
import base64
import os
import sys
from pathlib import Path
from datetime import datetime

def resource_path(relative_path):
    """ 获取资源的绝对路径，兼容 PyInstaller 打包 """
    try:
        # PyInstaller 创建临时文件夹，并把路径存放在 _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
class ReportGenerator:
    """
    报告生成器
    支持生成 PDF 和 Excel 格式报告
    """

    @staticmethod
    def generate_pdf_report(project_data: dict, audit_results: dict) -> bytes:
        """
        生成 PDF 报告
        包含: 项目概况, 能效指标, 分项分析, 改进建议
        """
        pdf = FPDF()
        pdf.add_page()
        # --- 处理中文编码和字体（如果需要） ---

        # current_dir = os.path.dirname(os.path.abspath(__file__))
        # font_path = os.path.join(current_dir, "simhei.ttf")  # 确保字体文件在这个目录下
        font_path = resource_path('fonts/simhei.ttf')
        # 2. 添加字体 (uni=True 表示支持 Unicode 中文)
        # 如果报错找不到字体，请检查 simhei.ttf 是否真的存在
        pdf.add_font('SimHei', '', font_path, uni=True)

        # 3. 设置当前使用的字体为 SimHei
        pdf.set_font('SimHei', size=12)
        # --- 构建标题和时间 ---
        print(project_data)
        project_name = project_data['project_name']
        current_time = datetime.now().strftime("%Y-%m-%d %A")  # 格式：2026-06-23 Monday
        location = "北京市"  # 你可以根据需求改成动态获取或从 session_state 获取

        # --- 写入 PDF ---
        # 1. 写入主标题
        pdf.set_font('SimHei', size=16) # 设置字体和大小
        pdf.cell(0, 10, f"节能评估报告 - {project_name}", ln=True, align='C')

        # 2. 写入时间地点信息（单独一行）
        pdf.set_font('SimHei', size=10)
        pdf.cell(0, 10, f"评估时间：{current_time} | 地点：{location}", ln=True, align='C')

        # 3. 空一行
        pdf.ln(10)
        # 标题
        # pdf.set_font('SimHei', size=16)
        # pdf.cell(0, 10, f"节能评估报告 - {project_data['project_name']}", ln=True, align='C')
        # pdf.ln(10)

        # 项目概况
        pdf.set_font('SimHei', size=12)
        pdf.cell(0, 10, "1. 项目概况", ln=True)
        pdf.set_font("SimHei", size=10)
        info = project_data
        pdf.cell(0, 8, f"项目名称: {info['project_name']}", ln=True)
        pdf.cell(0, 8, f"建筑面积: {info['building_area']} ㎡", ln=True)
        # pdf.cell(0, 8, f"设计冷负荷: {info['design_cold_load']} kW", ln=True)
        pdf.cell(0, 8, f"年运行天数: {info['operation_days_per_year']} 天", ln=True)

        # 能效指标
        pdf.ln(10)
        pdf.set_font('SimHei', size=12)
        pdf.cell(0, 10, "2. 能效评估结果", ln=True)
        print(audit_results)
        audit_results=audit_results["data"]
        pdf.set_font("SimHei", size=10)
        pdf.cell(0, 8, f"系统当前 COP: {audit_results.get('current_cop', 0):.2f}", ln=True)
        pdf.cell(0, 8, f"预期优化 COP: {audit_results.get('baseline_cop', 0):.2f}", ln=True)
        pdf.cell(0, 8, f"预期节能率: {audit_results.get('expected_saving_rate', 0):.1f}%", ln=True)
        pdf.cell(0, 8, f"年节能费用: {audit_results.get('annual_cost_saving', 0):,.0f} 元", ln=True)
        pdf.ln(10)
        pdf.set_font('SimHei', size=12)
        pdf.cell(0, 10, "3. 节能项目分项结果", ln=True)
        print(audit_results)
        audit_items=audit_results["sub_item_saving_rates"]
        pdf.set_font("SimHei", size=10)
        pdf.cell(0, 8, f"加减机优化: {audit_items.get('start_stop', 0)*100:.2f}%", ln=True)
        pdf.cell(0, 8, f"出水温度优化: {audit_items.get('water_temp', 0)*100:.2f}%", ln=True)
        pdf.cell(0, 8, f"冷塔优化: {audit_items.get('cooling_tower', 0)*100:.1f}%", ln=True)
        pdf.cell(0, 8, f"水泵流量优化: {audit_items.get('pump', 0)*100:,.0f}%", ln=True)
        # 改进建议
        pdf.ln(10)
        pdf.set_font('SimHei', size=12)
        pdf.cell(0, 10, "4. 系统改造建议", ln=True)

        suggestions = audit_results.get("suggestions", [])
        if suggestions:
            for i, sug in enumerate(suggestions, 1):
                pdf.cell(0, 8, f"{i}. {sug}", ln=True)
        else:

            pdf.set_font('SimHei', size=12)
            pdf.cell(0, 8, "系统运行良好，无重大改进项。", ln=True)

        # 输出为字节流
        # return pdf.output(dest='S').encode('utf-8')
        # return bytes(pdf.output(dest='S'), 'latin-1')
        pdf_bytes = pdf.output(dest='S')
        if isinstance(pdf_bytes, str):
            return pdf_bytes.encode('latin-1')  # 只有在返回字符串时才尝试编码
        return pdf_bytes  # 如果已经是 bytes，直接返回

    @staticmethod
    def generate_excel_report(all_data: dict) -> bytes:
        """
        生成详细数据 Excel 报告
        """
        # 创建内存中的 BytesIO 对象
        import io
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 1. 项目基本信息 Sheet
            if "project_info" in all_data:
                pd.DataFrame([all_data["project_info"]]).T.to_excel(writer, sheet_name="项目概况", index=True)
            # all_data=all_data["data"]
            # 2. 设备参数 Sheet
            # if "equipment_params" in all_data:

            pd.DataFrame(all_data["chillers"]).T.to_excel(writer, sheet_name="设备参数_chiller", index=True)
            pd.DataFrame(all_data["pumps"]).T.to_excel(writer, sheet_name="设备参数_pump", index=True)
            pd.DataFrame(all_data["towers"]).T.to_excel(writer, sheet_name="设备参数_tower", index=True)
            # 3. 运行数据 Sheet
            if "operation_data" in all_data:
                pd.DataFrame([all_data["operation_data"]]).to_excel(writer, sheet_name="运行数据", index=True)

            # 4. 评估结果 Sheet
            results_df = pd.DataFrame([all_data.get("data", {})]).T
            results_df.to_excel(writer, sheet_name="评估结果", index=True)

        # 获取字节数据
        return output.getvalue()