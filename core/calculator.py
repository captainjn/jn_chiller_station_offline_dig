"""
core/calculator.py
空调机房优化运行平台 - 核心算法实现
基于详细设计文档 V1.0
"""
import copy
import json
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from enum import Enum

design_temp_diff_min=2            #设计最小温差
ratio_chiller_power_in_total=0.75 #冷机占总耗功比例
# ------------------------------------------------------
# 数据模型定义 (对应详设文档 3.1 - 3.4)
# ------------------------------------------------------

class ProjectType(Enum):
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    HOSPITAL = "hospital"
    SCHOOL = "school"


@dataclass
class ProjectInfo:
    project_id: str
    project_name: str
    building_area: float
    project_type: ProjectType
    design_cold_load: float
    operation_hours_per_day: float
    operation_days_per_year: int
    electricity_price:float

@dataclass
class EquipmentParams:
    total_power            :float
    total_cooling_capacity :float
    total_flow :float
    load_ratio_data        :float
    design_temp_diff=2





@dataclass
class ChillerData:
    chiller_id: str
    chiller_type: str  # "chilled" or "cooling"
    design_supply_temp:float
    design_return_temp:float
    rated_power: float
    rated_cooling_capacity: float
    actual_power: float
    actual_supply_temp:float
    actual_return_temp:float
@dataclass
class PumpData:
    pump_id: str
    pump_type: str  # "chilled" or "cooling"
    rated_flow: float
    rated_head: float
    rated_power: float
    rated_frequency: float
    actual_power: float
    actual_head: float



@dataclass
class CoolingTowerData:
    tower_id: str
    rated_water_flow: float
    rated_fan_power: float
    # rated_fan_frequency: float
    design_approach_temp: float
    actual_fan_power: float
    actual_inlet_temp: float
    actual_outlet_temp: float
    # actual_wet_bulb_temp: float


@dataclass
class OperationData:
    total_power_consumption: float
    total_cooling_capacity: float
    load_ratio_data: List[float]  # 负荷率分档数据
    supply_temp: float
    return_temp: float
    actual_flow: float
    operation_hours: float
    actual_wet_bulb_temp:float

@dataclass
class EvaluationResult:
    project_info: ProjectInfo
    current_cop: float = 0.0
    baseline_cop: float = 0.0
    cop_compliance: bool = False
    water_temp_deviation: float = 0.0
    temp_diff_compliance: bool = False
    pump_efficiencies: List[float] = field(default_factory=list)
    pump_compliance: List[bool] = field(default_factory=list)
    cooling_tower_performance: float = 0.0
    expected_optimal_cop: float = 0.0
    expected_saving_rate: float = 0.0
    sub_item_saving_rates: Dict[str, float] = field(default_factory=dict)
    annual_energy_saving: float = 0.0
    annual_cost_saving: float = 0.0
    payback_period: float = 0.0
    suggestions: List[str] = field(default_factory=list)


# ------------------------------------------------------
# 核心算法计算器 (对应详设文档 4.1 - 4.2)
# ------------------------------------------------------

class EnergyEfficiencyCalculator:
    """
    空调系统能效评估核心类
    实现了PRD文档中定义的所有评估标准和节能计算逻辑
    """

    def __init__(self):
        # 加载标准基准值 (对应详设文档 5.1)
        self.standards = {
            "cop_baseline": {
                ProjectType.COMMERCIAL: 3.0,
                ProjectType.INDUSTRIAL: 2.5,
                ProjectType.HOSPITAL: 2.8,
                ProjectType.SCHOOL: 2.2
            },
            "ideal_pump_ratio": 1 / 7,  # 水泵理想能耗占比
            "cooling_water_influence_coeff": 0.03,  # 冷却水温影响系数
            "chilled_water_influence_coeff": 0.02,  # 冷却水温影响系数
            "theoretical_approach": 3.0  # 理论逼近度
        }

    # 4.1.1 COP 评估算法
    def calculate_cop(self, refrigeration_capacity: float, total_power: float) -> float:
        """计算系统COP值"""
        if total_power <= 0:
            return 0.0
        return refrigeration_capacity / total_power

    def check_cop_compliance(self, current_cop: float, baseline_cop: float) -> bool:
        """检查COP是否达标 (COP > 基准值)"""
        return current_cop > baseline_cop

    # 4.1.2 水温评估算法
    def calculate_water_temp_deviation(self, return_temps: List[float]) -> float:
        """计算回水温度支路偏差"""
        if len(return_temps) < 2:
            return 0.0
        return max(return_temps) - min(return_temps)

    def check_temp_diff_compliance(self, actual_temp_diff: float, design_temp_diff: float) -> bool:
        """检查供回水温差是否达标 (实际 > 设计*0.8)"""
        return actual_temp_diff > (design_temp_diff * 0.8)

    # 4.1.3 水泵效率算法
    def calculate_pump_efficiency(self, flow: float, pressure_diff: float, power: float) -> float:
        """
        计算水泵效率
        流量单位转换: m³/h -> m³/s
        密度: 1000 kg/m³, 重力: 9.8 m/s²
        """
        if power == 0:
            return 0.0
        flow_kg_s = flow / 3.6000
        theoretical_power = flow_kg_s  * 9.8 * pressure_diff/1000
        return theoretical_power / power

    def check_pump_efficiency_compliance(self, actual_efficiency: float, rated_efficiency: float) -> bool:
        """检查水泵效率是否达标 (实际效率 > 铭牌值*0.8)"""
        return actual_efficiency >= (rated_efficiency * 0.8)

    # 4.1.5 冷却塔性能评估
    def evaluate_cooling_tower_performance(self, wet_bulb_temp: float,
                                           range_temp: float,approach_temp: float) -> float:
        """
        评估冷却塔性能
        Performance Factor = Approach/Range
        """
        return approach_temp/range_temp

    # 4.2 节能潜力计算算法
    def calculate_start_stop_saving(self, load_ratio_data: List[float], chillers: list) -> float:
        """
        4.2.1 优化启停节能
        简化逻辑：基于负荷率分档，计算COP提升带来的节能
        这里使用文档中提供的COP公式进行模拟
        COP = -1.9286*r^2 + 2.8143*r - 0.196 (注：文档原文疑似有误，修正为标准二次方程形式)
        """
        load_ratio_list=[]
        for i in range(len(load_ratio_data)):
            load_ratio_list.append((i+1)/len(load_ratio_data))

        total_saving = 0.0
        self.load0=1000
        for i_ratio in range(len(load_ratio_list)):
            load_ratio = load_ratio_list[i_ratio]
            chillers_n_min,chiller_comb_min=self.find_chiller_min_no(load=load_ratio*self.load0)
            cop_min_n=self.calc_avg_cop(chiller_comb_min,load_ratio*self.load0)
            cop_list=[cop_min_n]
            chiller_comb=copy.copy(chiller_comb_min)
            for i_chiller in range(chillers_n_min+1,len(self.chillers)):
                chiller_comb.append(self.chillers[i_chiller])
                cop_i=self.calc_avg_cop(chiller_comb,load_ratio*self.load0)
                cop_list.append(cop_i)
            cop_max=max(cop_list)

            # 节能量 = 提升的COP * 对应负荷的功率
            saving = (cop_max-cop_min_n) * (self.load0 * load_ratio)/cop_min_n
            total_saving+=saving*load_ratio_data[i_ratio]/100
        return total_saving
    def cop_by_load_ratio(self,load_ratio,cop0=5.0):
        r=load_ratio
        r_cop= -1.9286*r*r + 2.8143*r - 0.196
        return cop0*r_cop

    def estimate_approach(self,theoretical_approach, present_approach,tower_actual_power ,total_tower_rated_power,actual_cooling_load,rated_cooling_load):
        #这里描述冷塔台数、功率与逼近度之间的关系
        P=tower_actual_power
        Q=actual_cooling_load
        A=present_approach
        P0=total_tower_rated_power
        A0=theoretical_approach
        Q0=rated_cooling_load
        K=P0*pow(A0,2.2)/Q0
        K1=P*pow(A,2.2)/Q
        Approach=pow(K*Q/P0,1/2.2)
        # Approach=1
        return Approach
    def find_chiller_min_no(self,load=500)  :
        present_load=0
        chiller_comb=[]
        for i_chiller in range(len(self.chillers)) :
            chiller=self.chillers[i_chiller]
            chiller_comb.append(chiller)
            present_load+=chiller.rated_cooling_capacity
            if present_load>=load: return i_chiller ,chiller_comb
        return len(self.chillers),chiller_comb
    def calc_avg_cop(self,chiller_comb,load):
        total_capacity=0
        cop_avg=0
        for chiller in chiller_comb:
            total_capacity+=chiller.rated_cooling_capacity
        for chiller in chiller_comb:
            load_i=load*chiller.rated_cooling_capacity/total_capacity
            cop=self.cop_by_load_ratio(load_i/chiller.rated_cooling_capacity)
            cop_avg+=cop*chiller.rated_cooling_capacity/ total_capacity
        return cop_avg

    def calculate_water_temp_saving(self, chillers: list, supply_temp_improvement: float) -> float:
        """
        4.2.2 优化水温导致 COP 增加节能
        节能量 = 冷机功耗 * (1 - 影响系数 * 出口冷冻水温提升值)
        """
        coeff = self.standards["chilled_water_influence_coeff"]
        sum=0
        for chiller in chillers:
            chiller_power=chiller.actual_power
            supply_temp_improvement=chiller.design_return_temp-chiller.actual_return_temp
            sum+= chiller_power * coeff * supply_temp_improvement
        return  sum

    def calculate_pump_saving(self, pump_actual_consumption: float, total_consumption: float) -> float:
        """
        4.2.3 水泵能耗降低
        节能量 = 水泵实测能耗 - 水泵理想占比 * 总能耗
        """
        #算法1
        ideal_ratio = self.standards["ideal_pump_ratio"]
        pump_actual_consumption=self.total_pump_power
        pump_saving=pump_actual_consumption - ideal_ratio*self.total_power
        #算法2
        ideal_dT=5
        actual_dT=self.project_info.return_temp -self.project_info.supply_temp
        r_flow=ideal_dT-actual_dT
        pump_saving= r_flow*r_flow
        
        return max(pump_saving,0)

    def calculate_cooling_tower_saving(self, project_info:float,chiller_actual_power: float, tower_actual_power: float,
                                       actual_approach: float, total_tower_rated_power: float = 0.0) -> float:
        """
        4.2.4 冷塔优化导致 COP 增加节能
        节能量 = 冷机实测能耗 * 影响系数 * (逼近度 - 理论逼近度) + (冷塔实测能耗 - 冷塔最大能耗)
        """
        coeff = self.standards["cooling_water_influence_coeff"]
        theoretical_approach = self.estimate_approach(
            theoretical_approach=self.standards["theoretical_approach"],
            present_approach= actual_approach,
            tower_actual_power =tower_actual_power ,
            total_tower_rated_power=total_tower_rated_power,
            actual_cooling_load=project_info.total_cooling_load_for_tower,
            rated_cooling_load=project_info.total_cooling_capacity_for_tower
        )

        chiller_saving = chiller_actual_power * coeff * (actual_approach - theoretical_approach)
        tower_unsaving = tower_actual_power - total_tower_rated_power  # 如果风机变频，最大能耗即额定功率
        return chiller_saving + tower_unsaving

    # 5.1 主评估方法
    def evaluate_system(self, project_info: ProjectInfo,
                        chillers,pumps: List[PumpData],
                        cooling_towers: List[CoolingTowerData], electricity_price: float = 1.0) -> EvaluationResult:
        """
        执行完整的系统能效评估
        """
        # project_info, equipment_params, operation_data, chillers, pumps, towers= trans_data1(page_data)
        print("--------------255")
        self.project_info=project_info
        result = EvaluationResult(project_info=project_info)
        total_cooling_load=project_info.total_cooling_load
        dT=project_info.return_temp-project_info.supply_temp
        total_flow=total_cooling_load/dT/4.187*3.6
        total_chiller_power=0
        total_chiller_capacity=0
        total_rated_flow=0
        total_pump_power=0
        tower_saving=0

        for chiller in chillers:
            total_chiller_power+=chiller.actual_power
            total_chiller_capacity+=chiller.rated_cooling_capacity
        for pump in pumps:
            total_pump_power += pump.actual_power
            total_rated_flow+=pump.rated_flow

        total_tower_rated_power = 0
        total_tower_power = 0
        for tower in cooling_towers:
            total_tower_rated_power += tower.rated_fan_power
            total_tower_power += tower.actual_fan_power
        total_power=total_chiller_power+total_pump_power+total_tower_power
        # 1. COP 评估
        # 制冷量 = 实际流量 * 密度 * 比热容 * 温差 (简化计算，假设比热容为定值)
        # 这里直接使用传入的 project_info.total_cooling_capacity
        # total_power = project_info.total_power_consumption
        result.current_cop = self.calculate_cop(project_info.total_cooling_load, total_power) #计算系统COP
        result.baseline_cop = self.standards["cop_baseline"][project_info.project_type]
        result.cop_compliance = self.check_cop_compliance(result.current_cop, result.baseline_cop)


        # 2. 水温评估
        actual_temp_diff = abs(project_info.supply_temp - project_info.return_temp)
        result.water_temp_deviation = self.calculate_water_temp_deviation([project_info.return_temp])
        result.temp_diff_compliance = self.check_temp_diff_compliance(actual_temp_diff,design_temp_diff_min)

        # 3. 水泵评估
        for pump in pumps:
            pump.actual_flow=total_flow*pump.rated_flow/total_rated_flow
            pump.efficiency = self.calculate_pump_efficiency(pump.actual_flow, pump.actual_head, pump.actual_power)
            pump.rated_efficiency= self.calculate_pump_efficiency(pump.rated_flow, pump.rated_head, pump.rated_power)
            result.pump_efficiencies.append(pump.efficiency)
            result.pump_compliance.append(self.check_pump_efficiency_compliance(pump.efficiency, pump.rated_efficiency))


        # 4. 冷却塔性能评估
        project_info.total_cooling_load_for_tower=project_info.total_cooling_load+total_chiller_power
        project_info.total_cooling_capacity_for_tower=total_chiller_capacity+total_chiller_power
        if cooling_towers:
            total_tower_rated_power=0
            total_tower_power=0
            for tower in cooling_towers:
                approach = tower.actual_outlet_temp - project_info.actual_wet_bulb_temp
                range_temp = tower.actual_inlet_temp - tower.actual_outlet_temp
                result.cooling_tower_performance = self.evaluate_cooling_tower_performance(project_info.actual_wet_bulb_temp, approach, range_temp)
                total_tower_rated_power+=tower.rated_fan_power
                total_tower_power+=tower.actual_fan_power
            total_power+=total_tower_power
            # 计算冷塔节能
            tower_saving = self.calculate_cooling_tower_saving(  project_info,
                chiller_actual_power=total_chiller_power ,  # 假设冷机占总能耗50%
                tower_actual_power=total_tower_power,
                actual_approach=approach,
                total_tower_rated_power=total_tower_rated_power
            )
            result.sub_item_saving_rates['cooling_tower'] = tower_saving / total_power if total_power > 0 else 0



        self.chillers,self.pumps,self.towers,self.total_power,self.total_pump_power,self.total_chiller_power,self.total_tower_power=(
            chillers,pumps,cooling_towers,total_power,total_pump_power,total_chiller_power,total_tower_power)
        # 5. 计算节能潜力 (分项计算)
        # 5.1 优化启停

        start_stop_saving = self.calculate_start_stop_saving(project_info.load_ratio_data,chillers)

        # 5.2 优化水温 (假设供水温度优化了1度)
        water_temp_saving = self.calculate_water_temp_saving(chillers, supply_temp_improvement=1.0)

        # 5.3 水泵节能
        pump_saving = self.calculate_pump_saving(total_pump_power, total_power)

        # 5.4 冷塔节能
        tower_saving = tower_saving

        # 汇总分项节能率
        total_saving_power = start_stop_saving + water_temp_saving + pump_saving +tower_saving
        if total_power > 0:
            result.sub_item_saving_rates['start_stop'] = start_stop_saving / total_power
            result.sub_item_saving_rates['water_temp'] = water_temp_saving / total_power
            result.sub_item_saving_rates['pump'] = pump_saving / total_power
            result.sub_item_saving_rates['tower'] = tower_saving / total_power
            total_saving_power=start_stop_saving+water_temp_saving+pump_saving+tower_saving
            result.expected_saving_rate = (total_saving_power *0.85/ total_power) * 100
            result.expected_optimal_cop=result.current_cop*(1+result.expected_saving_rate/100)
        else:
            result.expected_saving_rate = 0.0

        # 6. 年节能量与费用
        annual_hours = project_info.operation_hours_per_day * project_info.operation_days_per_year
        result.annual_energy_saving = total_saving_power * annual_hours
        result.annual_cost_saving = result.annual_energy_saving * electricity_price

        # 7. 生成改进建议 (对应详设文档 2.3.3)
        self._generate_suggestions(result, pumps, cooling_towers)

        return result

    def _generate_suggestions(self, result: EvaluationResult, pumps: List[PumpData],
                              cooling_towers: List[CoolingTowerData]):
        """生成改进建议"""
        if not result.cop_compliance:
            result.suggestions.append("系统COP值未达标，建议检查冷机运行策略或进行设备维护。")

        if not result.temp_diff_compliance:
            result.suggestions.append("供回水温差低于设计值的80%，建议检查水系统平衡或清洗过滤器。")

        if any(not comp for comp in result.pump_compliance):
            result.suggestions.append("部分水泵效率偏低，建议检查水泵选型或更换高效水泵。")

        if cooling_towers and result.cooling_tower_performance < 0.8:
            result.suggestions.append("冷却塔性能欠佳，建议检查填料或风机皮带。")


# ------------------------------------------------------
# 工厂函数/便捷入口
# ------------------------------------------------------

def create_calculator():
    """创建计算器实例"""
    return EnergyEfficiencyCalculator()


# ------------------------------------------------------
# 数据适配层：将 Streamlit 页面的 Dict 数据转换为 计算器需要的 Model
# ------------------------------------------------------

def adapt_and_calculate(page_data: Dict[str, Any]) -> EvaluationResult:
    """
    适配函数：接收从 Streamlit 页面传入的原始字典数据，转换为 Dataclass 对象，执行计算
    page_data: 来自 st.session_state 的合并数据
    """

    # --- 添加调试代码：打印传入的数据结构 ---
    with open("data_dic.json", 'w', encoding='utf-8') as f:
        json.dump(page_data, f, ensure_ascii=False, indent=4)
    print("\n" + "=" * 50)
    print("DEBUG: 正在传入 Calculator 的数据结构:")
    print(f"Keys in page_data: {list(page_data.keys())}")
    if 'equipment_params' in page_data:
        print(f"Type of equipment_params: {type(page_data['equipment_params'])}")
        print(f"Value: {page_data['equipment_params']}")
    else:
        print("WARNING: 'equipment_params' 不存在!")
    print("=" * 50)
    # project_info,equipment_params,project_info= trans_data(project_info,equipment_params,project_info)
    calc = create_calculator()
    project_info,  chillers, pumps, towers = trans_data1(page_data)
        # data_dic={"project_info":project_info,
        #         "equipment_params":equip_params,
        #     "project_info":project_info}
        # with open("data_dic.json", 'w', encoding='utf-8') as f:
        #     json.dump(data_dic, f, ensure_ascii=False, indent=4)
        # 6. 执行计算
    result = calc.evaluate_system(
            project_info=project_info,
            # equipment_params=equip_params,
            # project_info=project_info,
            chillers=chillers,
            pumps=pumps,
            cooling_towers=towers,
            electricity_price=page_data['project_info'].get("electricity_price", 1.0)  # 假设电价在项目信息里
        )

    return result



def trans_data1(page_data):
    # 1. 转换项目信息
    # 假设 page_data 包含: project_info, equipment_params, project_info, pumps_list, cooling_towers_list
    try:
        # 处理项目类型映射
        type_map = {
            "commercial": ProjectType.COMMERCIAL,
            "industrial": ProjectType.INDUSTRIAL,
            "hospital": ProjectType.HOSPITAL,
            "school": ProjectType.SCHOOL
        }
        proj_type_str = page_data['project_info']['project_type']
        # 兼容字符串和 Enum
        if isinstance(proj_type_str, str):
            proj_type = type_map.get(proj_type_str.lower(), ProjectType.COMMERCIAL)
        else:
            proj_type = proj_type_str
        equipment_params={}
        project_info = ProjectInfo(
            project_id=page_data['project_info'].get("project_id", "UNKNOWN"),
            project_name=page_data['project_info']["project_name"],
            building_area=page_data['project_info']["building_area"],
            project_type=proj_type,
            design_cold_load=page_data['project_info']["design_cold_load"],
            operation_hours_per_day=page_data['project_info']["operation_hours_per_day"],
            operation_days_per_year=page_data['project_info']["operation_days_per_year"],
            electricity_price=page_data["project_info"]["electricity_price"]
        )
        print(page_data['equipment_params'])
        # 2. 转换设备参数

        # project_info.total_power             =page_data['operation_data']["total_power"]
        project_info.total_cooling_load      =page_data['operation_data']["total_cooling_load"]
        project_info.load_ratio_data         =page_data['operation_data']["load_ratio_data"]
        project_info.total_flow              =page_data['operation_data']["total_flow"]

        # 3. 转换运行数据
        # 注意：这里需要确保 project_info 包含 total_cooling_capacity
        # 如果页面没有录入制冷量，需要根据公式计算：Q = c * m * ΔT
        op_data = page_data['operation_data']

        # 安全计算制冷量 (如果用户没填，则估算)
        flow = op_data.get("actual_flow", 0)
        supply_temp = op_data.get("supply_temp", 0)
        return_temp = op_data.get("return_temp", 0)
        temp_diff = abs(return_temp - supply_temp)

        # 简单估算制冷量 (kW): 流量(m3/h) * 温差(℃) * 1.163
        estimated_cooling = flow * temp_diff * 1.163


        project_info.total_power_consumption=0,#op_data["total_power"],
        project_info.total_cooling_load=op_data["total_cooling_load"]
        project_info.load_ratio_data=op_data["load_ratio_data"]  # 默认模拟数据
        project_info.supply_temp=8
        project_info.return_temp=12
        project_info.actual_flow=150
        project_info.operation_hours=8760
        project_info.actual_wet_bulb_temp=26


        # 3. 转换冷机列表
        chillers = []
        for chiller_raw in page_data["equipment_params"].get('chillers', []):
            chillers.append(ChillerData(
                chiller_id=chiller_raw.get("chiller_id", "chiller_Unknown"),
                chiller_type=chiller_raw.get("chiller_type", "chilled"),
                design_supply_temp=chiller_raw["design_supply_temp"],
                design_return_temp=chiller_raw["design_return_temp"],
                rated_power=chiller_raw["rated_power"],
                rated_cooling_capacity=chiller_raw.get("rated_cooling_capacity", 500),
                actual_power=chiller_raw["power"],
                actual_supply_temp=op_data["supply_temp"],
                actual_return_temp=op_data["return_temp"]
            ))
        # equip_params.design_temp_diff = equip_params.design_supply_temp - equip_params.design_return_temp
        # 4. 转换水泵列表
        pumps = []
        for pump_raw in page_data["equipment_params"].get('pumps', []):
            # 计算压差 (如果页面存的是进出口压力，则相减；如果是直接压差，则直接取)
            pressure_diff = pump_raw.get("actual_pressure_diff", 0)
            if "actual_inlet_pressure" in pump_raw and "actual_outlet_pressure" in pump_raw:
                pressure_diff = pump_raw["actual_outlet_pressure"] - pump_raw["actual_inlet_pressure"]

            pumps.append(PumpData(
                pump_id=pump_raw.get("pump_id", "Pump_Unknown"),
                pump_type=pump_raw.get("pump_type", "chilled"),
                rated_flow=pump_raw["rated_flow"],
                rated_head=pump_raw["rated_head"],
                rated_power=pump_raw["rated_power"],
                rated_frequency=pump_raw.get("rated_frequency", 50),
                # efficiency=pump_raw["efficiency"],
                actual_head=pump_raw["head"],
                # actual_pressure_diff=pressure_diff,
                actual_power=pump_raw["power"],
                # actual_frequency=pump_raw.get("actual_frequency", 50)
            ))

        # 5. 转换冷却塔列表
        towers = []
        for tower_raw in page_data["equipment_params"].get('towers', []):
            towers.append(CoolingTowerData(
                tower_id=tower_raw.get("tower_id", "Tower_Unknown"),
                rated_water_flow=tower_raw["rated_flow"],
                rated_fan_power=tower_raw["rated_power"],
                design_approach_temp=tower_raw.get("rated_approach_temp", 3.0),
                actual_fan_power=tower_raw["power"],
                actual_inlet_temp=tower_raw["inlet_temp"],
                actual_outlet_temp=tower_raw["outlet_temp"],
                # actual_wet_bulb_temp=25#
            ))
        return project_info, chillers, pumps, towers
    except Exception as e:
        # 捕获数据转换异常，防止崩溃
        import traceback
        print(f"计算数据适配错误: {traceback.format_exc()}")
        result = EvaluationResult(project_info=ProjectInfo("ERROR", "数据错误", 0, ProjectType.COMMERCIAL, 0, 0, 0))
        result.suggestions = [f"数据格式错误，请检查输入: {str(e)}"]
        return result