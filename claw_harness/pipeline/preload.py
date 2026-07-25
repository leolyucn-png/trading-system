"""
pipeline/preload.py — 文档预加载器

所有任务启动前自动执行，读取绑定场景全部规则文档。
未完整加载直接拦截输出。
"""

import os

REQUIRED_DOCS = {
    "trading": [
        "claw_harness/config/base.toml",
        "claw_harness/memory/global_memory.md",
        "claw_harness/memory/error_shturl.md",
        "claw_harness/memory/scene_trading/memory.md",
        "MEMORY.md",
        "memory/经验教训库.md",
        "memory/trades.md",
    ],
    "research": [
        "claw_harness/config/base.toml",
        "claw_harness/memory/global_memory.md",
        "claw_harness/memory/error_shturl.md",
        "claw_harness/memory/scene_research/memory.md",
        "MEMORY.md",
    ]
}

def preload(scene="trading", workspace="/Users/lyu/.openclaw/workspace"):
    """预加载指定场景的全部文档"""
    if scene not in REQUIRED_DOCS:
        return False, f"未知场景: {scene}"
    
    loaded = []
    missing = []
    
    for rel_path in REQUIRED_DOCS[scene]:
        full_path = os.path.join(workspace, rel_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            loaded.append((rel_path, len(content)))
        else:
            missing.append(rel_path)
    
    report = {
        "scene": scene,
        "total": len(REQUIRED_DOCS[scene]),
        "loaded": len(loaded),
        "missing": missing,
        "files": loaded,
        "success": len(missing) == 0
    }
    
    return report
