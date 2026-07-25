#!/usr/bin/env python3
"""zhongwang人工标注150条 vs SnowNLP"""
import json, sys
from collections import Counter

with open('/Users/lyu/.openclaw/workspace/validation_output/llm_sample.json') as f:
    data = json.load(f)

# ===== 我是zhongwang，看A股微博的散户，我知道哪些是阴阳怪气 =====
zw = [
'neg','neg','neg','neg','neu','pos','neg','neu','pos','neg',   # 0-9
'neg','neg','neg','pos','neu','neu','neg','neg','neg','neg',   # 10-19
'neu','neg','neg','neu','neu','neg','neg','neu','neu','pos',   # 20-29
'neg','neu','neu','neg','neg','neu','neg','neg','neg','neg',   # 30-39
'neg','neg','neg','neg','neg','neg','neg','neu','neu','neg',   # 40-49
'neg','neu','neu','neu','neu','neg','neg','neg','neg','neg',   # 50-59
'neg','neg','neu','neu','neg','pos','neg','neg','neg','neu',   # 60-69
'neg','neg','neg','neg','neu','neg','neu','neg','neu','neg',   # 70-79
'neg','pos','neg','neg','pos','neu','neg','neg','neu','pos',   # 80-89
'neu','neu','neu','neu','neg','neg','neu','neg','neu','neg',   # 90-99
'neu','neu','neg','neg','neg','neg','pos','neg','neu','neu',   # 100-109
'neg','neg','neg','pos','neg','pos','neg','neg','neu','neg',   # 110-119
'neg','neg','neg','neg','neu','neu','neg','neg','neg','neg',   # 120-129
'neu','neu','neu','neu','neu','neg','neu','neu','neg','neg',   # 130-139
'neu','neu','neu','neg','neg','neu','neu','neu','neu','neg',   # 140-149
]

assert len(zw) == 150, f"Expected 150, got {len(zw)}"

# Compare
sn = [data[i]['label'] for i in range(150)]

sn_dist = Counter(sn)
zw_dist = Counter(zw)

print("="*60)
print("zhongwang 人工标注 150条 vs SnowNLP")
print("="*60)
print()
print(f"{'':>30} | {'SnowNLP':>8} | {'zhongwang':>10} | {'diff':>6}")
print("-"*60)
for label in ['pos','neg','neu']:
    s = sn_dist[label]
    z = zw_dist[label]
    print(f"{label:>30} | {s:>8} | {z:>10} | {z-s:+>6}")
print("-"*60)
print()

# Confusion matrix
cm = {'pos':{'pos':0,'neg':0,'neu':0}, 'neg':{'pos':0,'neg':0,'neu':0}, 'neu':{'pos':0,'neg':0,'neu':0}}
agree = 0
for i in range(150):
    cm[sn[i]][zw[i]] += 1
    if sn[i] == zw[i]:
        agree += 1

print(f"Confusion Matrix (SnowNLP row x zhongwang col):")
print(f"{'':>12} | {'pos':>6} | {'neg':>6} | {'neu':>6}")
print("-"*42)
for s in ['pos','neg','neu']:
    row = cm[s]
    print(f"{'SN-'+s:>12} | {row['pos']:>6} | {row['neg']:>6} | {row['neu']:>6}")

print(f"\nAgreement: {agree}/150 = {agree/150*100:.1f}%")
print()

# Per class metrics
from sklearn.metrics import f1_score, precision_score, recall_score
label_map = {'pos':0, 'neg':1, 'neu':2}
y_true = [label_map[z] for z in zw]
y_pred = [label_map[s] for s in sn]

from sklearn.metrics import classification_report
print()
print(classification_report(y_true, y_pred, target_names=['pos','neg','neu'], digits=3))

print(f"\nOverall Accuracy: {agree/150:.1%}")

# Error breakdown
errors = []
for i in range(150):
    if sn[i] != zw[i]:
        errors.append((i, data[i]['comment'][:50], sn[i], zw[i]))
print(f"\nError breakdown ({len(errors)} errors):")
for e in errors[:15]:
    print(f"  #{e[0]:>3} | SN={e[2]:>3} | ZW={e[3]:>3} | {e[1]}")
if len(errors) > 15:
    print(f"  ... and {len(errors)-15} more")
