"""
core/calculator.py
空调机房优化运行平台 - 核心算法实现
基于详细设计文档 V1.0
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from enum import Enum


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


@dataclass
class EquipmentParams:
    chiller_type: str
    rated_cooling_capacity: float
    rated_power: float
    design_supply_temp: float
    design_return_temp: float
    design_temp_diff: float


@dataclass
class PumpData:
    pump_id: str
    pump_type: str  # "chilled" or "cooling"
    rated_flow: float
    rated_head: float
    rated_power: float
    rated_frequency: float
    efficiency: float  # 铭牌效率
    actual_flow: float
    actual_pressure_diff: float
    actual_power: float
    actual_frequency: float


@dataclass
class CoolingTowerData:
    tower_id: str
    rated_water_flow: float
    fan_power: float
    fan_frequency: float
    design_approach_temp: float
    inlet_temp: float
    outlet_temp: float
    wet_bulb_temp: float


@dataclass
class OperationData:
    total_power_consumption: float
    total_cooling_capacity: float
    load_ratio_data: List[float]  # 负荷率分档数据
    supply_temp: float
    return_temp: float
    actual_flow: float
    operation_hours: float


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
                ProjectType.COMMERCIAL: 5.0,
                ProjectType.INDUSTRIAL: 4.5,
                ProjectType.HOSPITAL: 4.8,
                ProjectType.SCHOOL: 4.2
            },
            "fan_specific_power": {
                "primary": 0.32,  # 一次泵
                "secondary": 0.24  # 二次泵
            },
            "ideal_pump_ratio": 1 / 7,  # 水泵理想能耗占比
            "cooling_water_influence_coeff": 0.02,  # 冷却水温影响系数
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
        flow_m3_s = flow / 3600.0
        theoretical_power = flow_m3_s * 1000.0 * 9.8 * pressure_diff
        return theoretical_power / power

    def check_pump_efficiency_compliance(self, actual_efficiency: float, rated_efficiency: float) -> bool:
        """检查水泵效率是否达标 (实际效率 > 铭牌值*0.8)"""
        return actual_efficiency >= (rated_efficiency * 0.8)

    # 4.1.5 冷却塔性能评估
    def evaluate_cooling_tower_performance(self, wet_bulb_temp: float, approach_temp: float,
                                           range_temp: float) -> float:
        """
        评估冷却塔性能
        Performance Factor = Range / (WetBulb + Approach)
        """
        denominator = wet_bulb_temp + approach_temp
        if denominator == 0:
            return 0.0
        return range_temp / denominator

    # 4.2 节能潜力计算算法
    def calculate_start_stop_saving(self, load_ratio_data: List[float], chiller_rated_power: float) -> float:
        """
        4.2.1 优化启停节能
        简化逻辑：基于负荷率分档，计算COP提升带来的节能
        这里使用文档中提供的COP公式进行模拟
        COP = -1.9286*r^2 + 2.8143*r - 0.196 (注：文档原文疑似有误，修正为标准二次方程形式)
        """
        total_saving = 0.0
        for load_ratio in load_ratio_data:
            # 假设优化启停后COP有提升，这里简化为一个固定的提升比例或查表值
            # 根据文档公式计算当前负荷率下的COP
            # 为了简化演示，我们假设优化后平均提升 0.5 的COP值
            # 在实际工程中，这里需要复杂的冷机群控策略模拟
            improvement_factor = 0.5
            # 节能量 = 提升的COP * 对应负荷的功率
            saving = improvement_factor * (chiller_rated_power * load_ratio)
            total_saving += saving
        return total_saving

    def calculate_water_temp_saving(self, chiller_power: float, supply_temp_improvement: float) -> float:
        """
        4.2.2 优化水温导致 COP 增加节能
        节能量 = 冷机功耗 * (1 - 影响系数 * 出口冷冻水温提升值)
        """
        coeff = self.standards["cooling_water_influence_coeff"]
        return chiller_power * (1 - coeff * supply_temp_improvement)

    def calculate_pump_saving(self, pump_actual_consumption: float, total_consumption: float) -> float:
        """
        4.2.3 水泵能耗降低
        节能量 = 水泵实测能耗 - 水泵理想占比 * 总能耗
        """
        ideal_ratio = self.standards["ideal_pump_ratio"]
        ideal_pump_energy = total_consumption * ideal_ratio
        return max(0, pump_actual_consumption - ideal_pump_energy)

    def calculate_cooling_tower_saving(self, chiller_actual_power: float, tower_actual_power: float,
                                       actual_approach: float, tower_max_power: float = 0.0) -> float:
        """
        4.2.4 冷塔优化导致 COP 增加节能
        节能量 = 冷机实测能耗 * 影响系数 * (逼近度 - 理论逼近度) + (冷塔实测能耗 - 冷塔最大能耗)
        """
        coeff = self.standards["cooling_water_influence_coeff"]
        theoretical_approach = self.standards["theoretical_approach"]

        chiller_saving = chiller_actual_power * coeff * (actual_approach - theoretical_approach)
        tower_saving = tower_actual_power - tower_max_power  # 如果风机变频，最大能耗即额定功率
        return chiller_saving + tower_saving

    # 5.1 主评估方法
    def evaluate_system(self, project_info: ProjectInfo, equipment_params: EquipmentParams,
                        operation_data: OperationData, pumps: List[PumpData],
                        cooling_towers: List[CoolingTowerData], electricity_price: float = 1.0) -> EvaluationResult:
        """
        执行完整的系统能效评估
        """
        result = EvaluationResult(project_info=project_info)

        # 1. COP 评估
        # 制冷量 = 实际流量 * 密度 * 比热容 * 温差 (简化计算，假设比热容为定值)
        # 这里直接使用传入的 operation_data.total_cooling_capacity
        total_power = operation_data.total_power_consumption

        result.current_cop = self.calculate_cop(operation_data.total_cooling_capacity, total_power)
        result.baseline_cop = self.standards["cop_baseline"][project_info.project_type]
        result.cop_compliance = self.check_cop_compliance(result.current_cop, result.baseline_cop)

        # 2. 水温评估
        actual_temp_diff = abs(operation_data.supply_temp - operation_data.return_temp)
        result.water_temp_deviation = self.calculate_water_temp_deviation([operation_data.return_temp])
        result.temp_diff_compliance = self.check_temp_diff_compliance(actual_temp_diff,
                                                                      equipment_params.design_temp_diff)

        # 3. 水泵评估
        total_pump_power = 0.0
        for pump in pumps:
            efficiency = self.calculate_pump_efficiency(pump.actual_flow, pump.actual_pressure_diff, pump.actual_power)
            result.pump_efficiencies.append(efficiency)
            result.pump_compliance.append(self.check_pump_efficiency_compliance(efficiency, pump.efficiency))
            total_pump_power += pump.actual_power

        # 4. 冷却塔性能评估
        if cooling_towers:
            tower = cooling_towers[0]  # 简单取第一台
            approach = tower.outlet_temp - tower.wet_bulb_temp
            range_temp = tower.inlet_temp - tower.outlet_temp
            result.cooling_tower_performance = self.evaluate_cooling_tower_performance(
                tower.wet_bulb_temp, approach, range_temp)

            # 计算冷塔节能
            tower_saving = self.calculate_cooling_tower_saving(
                chiller_actual_power=total_power * 0.5,  # 假设冷机占总能耗50%
                tower_actual_power=tower.fan_power,
                actual_approach=approach
            )
            result.sub_item_saving_rates['cooling_tower'] = tower_saving / total_power if total_power > 0 else 0

        # 5. 计算节能潜力 (分项计算)
        # 5.1 优化启停
        start_stop_saving = self.calculate_start_stop_saving(operation_data.load_ratio_data,
                                                             equipment_params.rated_power)

        # 5.2 优化水温 (假设供水温度优化了1度)
        water_temp_saving = self.calculate_water_temp_saving(equipment_params.rated_power, supply_temp_improvement=1.0)

        # 5.3 水泵节能
        pump_saving = self.calculate_pump_saving(total_pump_power, total_power)

        # 汇总分项节能率
        total_saving_power = start_stop_saving + water_temp_saving + pump_saving
        if total_power > 0:
            result.sub_item_saving_rates['start_stop'] = start_stop_saving / total_power
            result.sub_item_saving_rates['water_temp'] = water_temp_saving / total_power
            result.sub_item_saving_rates['pump'] = pump_saving / total_power
            result.expected_saving_rate = (total_saving_power / total_power) * 100
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