#!/usr/bin/env python3
"""
harness-check — 全局自检
输出所有模块运行状态
"""

import os, sys, json, datetime

WORKSPACE = "/Users/lyu/.openclaw/workspace"
HARNESS = os.path.join(WORKSPACE, "claw_harness")

def check_dir(path, name):
    exists = os.path.isdir(path)
    return (name, "✅" if exists else "❌", path)

def check_file(path, name):
    exists = os.path.isfile(path)
    size = os.path.getsize(path) if exists else 0
    return (name, "✅" if exists else "❌", f"{size}B" if exists else "")

def check_pipeline():
    """测试各流水线"""
    results = {}
    
    # preload
    try:
        sys.path.insert(0, HARNESS)
        from pipeline.preload import preload
        r = preload("trading", WORKSPACE)
        results["preload"] = f"✅ {r['loaded']}/{r['total']} 文档加载" if r['success'] else f"❌ 缺{r['missing']}"
    except Exception as e:
        results["preload"] = f"❌ {e}"
    
    # skill_check
    try:
        from pipeline.skill_check import check
        r = check("trading_select_stock")
        results["skill_check"] = f"✅ {len(r['results'])}技能就绪" if r['status']=='pass' else f"❌ 缺{r['missing']+r['failed']}"
    except Exception as e:
        results["skill_check"] = f"❌ {e}"
    
    # validator
    try:
        from pipeline.validator import run_all
        r = run_all("test", ["sina_today"], ["step1"], ["step1","step2"],
                     ["claim1"], ["claim1"], ["header"], ["header"])
        results["validator"] = f"✅ 4层校验框架就绪 (最后运行: {r.overall})"
    except Exception as e:
        results["validator"] = f"❌ {e}"
    
    # scheduler
    try:
        from pipeline.scheduler import list_all
        tasks = list_all()
        active = sum(1 for t in tasks.values() if t.get("enabled"))
        results["scheduler"] = f"✅ {active}/{len(tasks)} 定时任务活跃"
    except Exception as e:
        results["scheduler"] = f"❌ {e}"
    
    return results

print("="*60)
print("🔧 claw_harness — 全局自检报告")
print(f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("="*60)

# 目录结构
print(f"\n📁 目录结构:")
dirs = [
    ("config", "config"),
    ("memory", "memory"),
    ("memory/scene_trading", "memory/scene_trading"),
    ("memory/scene_research", "memory/scene_research"),
    ("pipeline", "pipeline"),
    ("skills_pool", "skills_pool"),
    ("scene_profiles", "scene_profiles"),
    ("logs", "logs"),
]
for name, rel in dirs:
    status = check_dir(os.path.join(HARNESS, rel), name)
    print(f"  {status[1]} {status[0]}")

# 核心文件
print(f"\n📄 核心文件:")
files = [
    ("base.toml", "config/base.toml"),
    ("global_memory.md", "memory/global_memory.md"),
    ("error_shturl.md", "memory/error_shturl.md"),
    ("trading记忆", "memory/scene_trading/memory.md"),
    ("preload.py", "pipeline/preload.py"),
    ("skill_check.py", "pipeline/skill_check.py"),
    ("validator.py", "pipeline/validator.py"),
    ("scheduler.py", "pipeline/scheduler.py"),
    ("trading场景配置", "scene_profiles/trading_v1.json"),
    ("research场景配置", "scene_profiles/research_v1.json"),
]
for name, rel in files:
    status = check_file(os.path.join(HARNESS, rel), name)
    print(f"  {status[1]} {status[0]} ({status[2]})")

# 流水线测试
print(f"\n🔬 流水线测试:")
pipeline_results = check_pipeline()
for name, status in pipeline_results.items():
    print(f"  {status}")

print(f"\n{'='*60}")
print("🏁 自检完成")
print("="*60)
