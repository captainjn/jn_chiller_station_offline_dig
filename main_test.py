from core.calculator import *
from pages.report import  *
# 1. 准备数据 (通常来自Excel读取或UI输入)
project_info = ProjectInfo(
    project_id="P001",
    project_name="测试项目",
    building_area=10000,
    project_type=ProjectType.COMMERCIAL,
    design_cold_load=1000,
    operation_hours_per_day=24,
    operation_days_per_year=300
)

equipment_params = EquipmentParams(
    total_power            =0,
    total_cooling_capacity =0,
    load_ratio_data        =0,
    total_flow=0

    # chiller_type="离心式",
    # rated_cooling_capacity=800,
    # rated_power=200,
    # design_supply_temp=7,
    # design_return_temp=12,
    # design_temp_diff=5
)

operation_data = OperationData(
    total_power_consumption=250,
    total_cooling_capacity=1000,
    load_ratio_data=[0.3, 0.5, 0.7, 0.9], # 示例负荷分档
    supply_temp=7.5,
    return_temp=11.5,
    actual_flow=150,
    operation_hours=8760,
    actual_wet_bulb_temp=26
)

import os


# 1. 获取当前脚本所在的绝对目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 2. 拼接出文件的绝对路径
FILE_PATH = os.path.join(BASE_DIR, "app_data.json")
with open(FILE_PATH, 'r', encoding='utf-8') as f:
    ss=f.read()
    page_data=json.loads(ss)
    project_info, chillers, pumps, towers= trans_data1(page_data)
# 2. 创建计算器并执行评估
if False:
    calc = create_calculator()
    result = calc.evaluate_system(
        project_info=project_info,
        chillers=chillers,
        pumps=pumps, # 这里填入PumpData列表
        cooling_towers=towers, # 这里填入CoolingTowerData列表
        electricity_price=0.8 # 电价
    )

    # 3. 输出结果
    print(f"当前COP: {result.current_cop:.2f}")
    print(f"节能率: {result.expected_saving_rate:.2f}%")
    print("建议:", result.suggestions)
if True:
    app_data = page_data
    audit_results = app_data.get('audit_results', {})
    equipment_params = app_data.get('equipment_params', {})
    combined_data = {**{'project_info': project_info}, **audit_results,**equipment_params}
    excel_bytes = ReportGenerator.generate_excel_report(combined_data)
    pass