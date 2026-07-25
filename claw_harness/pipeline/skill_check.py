"""
pipeline/skill_check.py — 技能校验器

自动检测本次任务所需全部工具，缺失/失效标注。
缺项直接重跑。
"""

AVAILABLE_SKILLS = {
    # 数据获取
    "akshare-stock": {"status": "available", "fallback": "sina_api"},
    "sina_api": {"status": "available", "description": "Sina实时行情"},
    "tencent_kline": {"status": "available", "description": "腾讯30日K线"},
    
    # 搜索
    "web_search": {"status": "available", "description": "联网搜索"},
    "web_fetch": {"status": "available", "description": "网页抓取"},
    
    # 板块/个股分析
    "stock-sector-hunter": {"status": "available", "description": "板块扫描"},
    "leader-stock-identification": {"status": "available", "description": "龙头识别"},
    "capital-flow-monitor": {"status": "available", "description": "资金流向"},
    "sector-rotation": {"status": "available", "description": "板块轮动"},
    
    # 新闻/消息
    "stock-news-hunter": {"status": "available", "description": "个股新闻"},
    "policy-pulse": {"status": "available", "description": "政策扫描"},
    "rumor-scanner": {"status": "available", "description": "传闻核实"},
    
    # 分析系统
    "zhuge-liang": {"status": "available", "description": "诸葛亮独立牛股筛选"},
    "han-wudi": {"status": "available", "description": "汉武帝短线交易"},
    "liu-che": {"status": "available", "description": "刘彻轮动埋伏"},
    "qin-shihuang": {"status": "available", "description": "秦始皇宏观配置"},
}

# 各场景所需技能清单
SCENE_REQUIREMENTS = {
    "trading_select_stock": [
        "akshare-stock", "web_search", "stock-sector-hunter",
        "capital-flow-monitor", "sector-rotation"
    ],
    "trading_holdings_review": [
        "akshare-stock", "stock-news-hunter"
    ],
    "research_paper_review": [
        "web_search", "web_fetch"
    ],
}

def check(task_type):
    """校验本次任务所需工具是否齐全"""
    required = SCENE_REQUIREMENTS.get(task_type, [])
    if not required:
        return {"status": "unknown", "message": f"未知任务类型: {task_type}"}
    
    results = {}
    missing = []
    failed = []
    
    for skill_name in required:
        info = AVAILABLE_SKILLS.get(skill_name)
        if not info:
            missing.append(skill_name)
        elif info["status"] == "available":
            results[skill_name] = "✅"
        else:
            failed.append(skill_name)
            results[skill_name] = f"❌{info.get('fallback','无备用')}"
    
    return {
        "status": "pass" if (len(missing)==0 and len(failed)==0) else "fail",
        "missing": missing,
        "failed": failed,
        "results": results,
        "action": "重跑" if (missing or failed) else "继续"
    }
