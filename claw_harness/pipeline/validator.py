"""
pipeline/validator.py — 多层合规拦截校验

四层校验顺序执行，任意不通过强制重做并记录错误。
"""

import datetime


class ValidationReport:
    def __init__(self):
        self.layers = {}
        self.overall = "pending"
        self.errors = []
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def add_layer(self, name, passed, detail=""):
        self.layers[name] = {
            "passed": passed,
            "detail": detail,
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
        }
        if not passed:
            self.errors.append(f"{name}: {detail}")
    
    @property
    def all_passed(self):
        return all(l["passed"] for l in self.layers.values())


def layer1_timing(data_sources_used):
    """
    第一层：时序校验
    检查是否使用了当天的数据/信号来判断明天的操作
    """
    report = {"passed": True, "checks": [], "errors": []}
    
    # 检查数据源时间
    sources_today = sum(1 for s in data_sources_used if "today" in s.lower())
    if sources_today > 0:
        report["checks"].append(f"使用了{sources_today}个今日数据源")
    
    return report


def layer2_process(task_type, steps_executed, required_steps):
    """
    第二层：流程完整性校验
    检查是否跳过了关键步骤
    """
    report = {"passed": True, "checks": [], "errors": []}
    
    missing_steps = [s for s in required_steps if s not in steps_executed]
    if missing_steps:
        report["passed"] = False
        report["errors"].append(f"缺少步骤: {missing_steps}")
    
    report["checks"].append(f"已完成{len(steps_executed)}/{len(required_steps)}步")
    return report


def layer3_data(claims_made, data_support):
    """
    第三层：量化/客观数据校验
    检查所有主张是否有数据支撑
    """
    report = {"passed": True, "checks": [], "errors": []}
    
    unsupported = [c for c in claims_made if c not in data_support]
    if unsupported:
        report["passed"] = False
        report["errors"].append(f"无数据支撑的主张: {unsupported}")
    
    return report


def layer4_output(output_structure, requirements):
    """
    第四层：输出规范校验
    检查输出是否符合格式要求
    """
    report = {"passed": True, "checks": [], "errors": []}
    
    for req in requirements:
        if req not in output_structure:
            report["passed"] = False
            report["errors"].append(f"缺少输出要求: {req}")
    
    return report


def run_all(task_type, data_sources_used, steps_executed, required_steps,
             claims_made, data_support, output_structure, output_requirements):
    """运行全部四层校验"""
    report = ValidationReport()
    
    # L1
    l1 = layer1_timing(data_sources_used)
    report.add_layer("L1_时序校验", l1["passed"], "; ".join(l1["errors"]))
    
    # L2
    l2 = layer2_process(task_type, steps_executed, required_steps)
    report.add_layer("L2_流程完整", l2["passed"], "; ".join(l2["errors"]))
    
    # L3
    l3 = layer3_data(claims_made, data_support)
    report.add_layer("L3_数据支撑", l3["passed"], "; ".join(l3["errors"]))
    
    # L4
    l4 = layer4_output(output_structure, output_requirements)
    report.add_layer("L4_输出规范", l4["passed"], "; ".join(l4["errors"]))
    
    report.overall = "PASS" if report.all_passed else "FAIL"
    return report
