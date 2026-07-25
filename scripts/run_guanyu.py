#!/usr/bin/env python3
"""
run_guanyu.py — 关羽全线扫描一键启动

用法: python3 run_guanyu.py
效果: 启动关羽V4五线 + V5三线，共8条线全量扫描
"""

import os, sys, json, time

BASE = os.path.dirname(os.path.abspath(__file__))
V4 = os.path.join(BASE, "guanyu_v4.py")
V5 = os.path.join(BASE, "guanyu_v5_integrations.py")

print("=" * 60)
print("⚔️ 关羽全线扫描 · 8线全开")
print("=" * 60)

# 跑V4（线1-线5）
print("\n【Phase 1】关羽 V4 · 五线")
print("-" * 40)
os.system(f"python3 {V4}")

# 跑V5（线6-线8）
print("\n【Phase 2】关羽 V5 · 北向+龙虎榜+龙头识别")
print("-" * 40)
os.system(f"python3 {V5}")

print("\n" + "=" * 60)
print("✅ 关羽全线扫描完成")
print("=" * 60)
