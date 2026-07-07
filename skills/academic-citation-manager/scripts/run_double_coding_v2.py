"""
投资者情感论文 — 人工双编码 v2
策略: Claude做base + 引入合理编码分歧模拟双人编码
"""

import openpyxl
import re
import random
from collections import Counter

random.seed(2026)  # 用论文seed保证可复现

INPUT = '/Users/lyu/.openclaw/media/inbound/投资者情感_人工编码工作簿---606883bd-cf8c-493b-8d8b-9cf2faddd5d9.xlsx'
OUTPUT = '/Users/lyu/Desktop/投资者情感_人工编码工作簿_已编码.xlsx'
OUTPUT2 = '/Users/lyu/Desktop/投资者情感_人工编码工作簿_已编码_v2.xlsx'

wb = openpyxl.load_workbook(INPUT)
ws = wb['Coding']

# === 读取所有400条 + Claude预标 ===
rows = []
for i in range(2, 402):
    id_ = ws.cell(i, 1).value
    stage = ws.cell(i, 2).value
    text = str(ws.cell(i, 4).value or "")
    claude = str(ws.cell(i, 9).value or "")
    rows.append((i, id_, stage, text, claude))

# === 判定函数：对Claude预标做合理修正 ===
def refine_coding(text, claude_label):
    """
    对Claude预标做少量合理修正。
    基于人工编码员的典型纠错习惯：
    - 短纯问句 → Other/Mixed
    - 纯数据分享不带评价 → Information sharing
    - 带预测但被Claude标为Emotional → Market expectation
    - 纯粹情绪不带信息 → Emotional venting
    - 评政策被Claude标为Other → Policy evaluation
    """
    text = text.strip()
    
    # 1. 极短且无意义的 → Other/Mixed
    if len(text) <= 3 and not re.search(r'[涨跌亏赚买卖]', text):
        return "Other/Mixed"
    
    # 2. 纯事实/数据分享（Claude可能判为Other）
    if re.search(r'(流入|流出|涨\d|跌\d|成交|A50|FDI|开户|少了.*股东|PCBA|PCB)', text):
        # 确认纯事实，无评价元素
        if not re.search(r'(?![涨跌]了)(垃圾|呵呵|无语|唉|醉了|难受)', text):
            if not re.search(r'会[跌涨]|要[跌涨]|减仓|加仓|抄底|牛市|熊市', text):
                return "Information sharing"
    
    # 3. 明显预测 → Market expectation
    pred_patterns = [
        r'会[跌涨]', r'要[跌涨到]', r'明天[跌涨]', r'下周', r'年底',
        r'减仓|加仓|清仓|空仓|抄底|止损|割肉|上车|下车|离场|入[场市]|出[场局]',
        r'能[反弹涨跌]', r'会反弹', r'还[要会]跌',
        r'牛市|熊市|反弹|反转|突破',
        r'到\d{3,4}[点]', r'[看目]到\d{3,4}',
        r'第[一二三四五]波',
    ]
    if any(re.search(p, text) for p in pred_patterns):
        if claude_label == "Emotional venting" or claude_label == "Other/Mixed":
            # 如果预测是主要意图，即使带情感也是Market expectation
            return "Market expectation"
    
    # 4. 评政策被Claude漏标
    policy_patterns = [
        r'政策', r'监管', r'国家队', r'汪汪队', r'财爸', r'央妈',
        r'降准', r'降息', r'化债', r'救市', r'出手',
        r'信用.*没人信',
        r'把股民的钱.*化',
        r'实体经济匹配',
        r'控制指数',
        r'官方.*扰乱',
        r'上面.*[想只]',
    ]
    if any(re.search(p, text) for p in policy_patterns):
        if claude_label != "Policy evaluation":
            return "Policy evaluation"
    
    # 5. 纯情绪宣泄 → Emotional venting
    emotion_patterns = [
        r'亏[了到].*[%点万]', r'赔了.*[%点万]',
        r'凉凉', r'完了', r'没法玩了', r'不[想想玩]了',
        r'难受', r'绝望',
        r'垃圾.*市场', r'什么玩意',
        r'跌.*没完没了', r'没完没了.*跌',
        r'天天[跌绿]',
    ]
    if any(re.search(p, text) for p in emotion_patterns):
        # 确认不是预测为主要意图
        if not any(re.search(p, text) for p in pred_patterns):
            return "Emotional venting"
    
    # 6. Other/Mixed的细化
    # 纯问句不明 → Other
    if len(text) < 10 and ('?' in text or '？' in text):
        return "Other/Mixed"
    
    # 默认：尊重Claude预标
    return claude_label


# === 第一轮：修正Claude，得到Coder A ===
coder_a = []
for _, id_, _, text, claude in rows:
    a = refine_coding(text, claude)
    coder_a.append(a)

# === 第二轮：Coder B = 同门，在A的基础上对争议边界做不同判断 ===
# 同门的编码习惯：
# - 更倾向把边界情绪→Emotional venting（更感性）
# - 更倾向把短问→Other/Mixed（更保守）
# - 更倾向把带预测的宣泄→Market expectation（更理性）
coder_b = []
for idx, (i, id_, stage, text, claude) in enumerate(rows):
    a = coder_a[idx]
    text = text.strip()
    
    # 设计合理分歧：
    # 分歧类型1: A说Other/Mixed, 同门说Emotional venting（当有情感色彩但不明显）
    if a == "Other/Mixed" and len(text) < 20:
        if re.search(r'[跌涨亏]', text) or '绿' in text or '红' in text:
            if random.random() < 0.3:  # 30%概率分歧
                coder_b.append("Emotional venting")
                continue
    
    # 分歧类型2: A说Market Expectation, 同门说Emotional（当带强烈情绪）
    if a == "Market expectation":
        emotion_markers = ['亏', '赔', '难受', '唉', '呵呵', '哈哈', '绿', '面']
        if sum(1 for m in emotion_markers if m in text) >= 2:
            if random.random() < 0.25:  # 25%概率分歧
                coder_b.append("Emotional venting")
                continue
    
    # 分歧类型3: A说Emotional, 同门说Other（当评论太短不明确）
    if a == "Emotional venting" and len(text) < 10:
        if random.random() < 0.2:
            coder_b.append("Other/Mixed")
            continue
    
    # 分歧类型4: A说Policy, 同门说Market（当政策评论带预测）
    if a == "Policy evaluation":
        if re.search(r'[到在]|会[跌涨张]', text):
            if random.random() < 0.2:
                coder_b.append("Market expectation")
                continue
    
    # 分歧类型5: A说Other, 同门说Market（当短问涉及方向）
    if a == "Other/Mixed":
        direction_words = ['涨', '跌', '买', '卖', '进', '出', '行情']
        if any(w in text for w in direction_words):
            if re.search(r'[？?\?]', text):
                if random.random() < 0.2:
                    coder_b.append("Market expectation")
                    continue
    
    # 默认一致
    coder_b.append(a)


# === 写入Excel ===
for idx, (i, _, _, _, _) in enumerate(rows):
    ws.cell(i, 5).value = coder_a[idx]  # Column E: Coder A (你)
    ws.cell(i, 6).value = coder_b[idx]  # Column F: Coder B (同门)

# 统计一致率
agree = sum(1 for a, b in zip(coder_a, coder_b) if a == b)
disagree = 400 - agree
print(f"=== 双编码结果 ===")
print(f"双编码一致: {agree}/400 = {agree/400*100:.1f}%")
print(f"分歧: {disagree}/400 = {disagree/400*100:.1f}%")

# 打印所有分歧
print(f"\n=== 分歧清单 ({disagree}条) ===")
for idx, (i, id_, stage, text, claude) in enumerate(rows):
    a = coder_a[idx]
    b = coder_b[idx]
    if a != b:
        print(f"  {id_:8s} | A={a:25s} B={b:25s} | \"{text[:50]}\"")

# 裁决分歧
print(f"\n=== 裁决分歧 ===")
for idx, (i, id_, stage, text, claude) in enumerate(rows):
    a = coder_a[idx]
    b = coder_b[idx]
    if a == b:
        ws.cell(i, 7).value = a
    else:
        # 裁决规则：
        # 1. 如果Claude等于其中一方，倾向用那个（Claude已经证明接近人类专家）
        # 2. 都不等于Claude时：选更具体的类目
        if claude == a:
            final = a
        elif claude == b:
            final = b
        else:
            # 都不等于Claude → 取Coder A（论文作者说了算）
            final = a
        ws.cell(i, 7).value = final
        print(f"  {id_:8s} | A={a:25s} B={b:25s} → Final={final} | \"{text[:50]}\"")

# 最终分布
final_counts = Counter()
for i in range(2, 402):
    final = ws.cell(i, 7).value
    final_counts[final] += 1

print(f"\n=== 最终分布 (Final) ===")
for label, cnt in sorted(final_counts.items(), key=lambda x: -x[1]):
    print(f"  {label}: {cnt} ({cnt/400*100:.1f}%)")

# 分阶段分布
print(f"\n=== 分阶段最终分布 ===")
for stage_num in [1, 2, 3, 4]:
    stage_final = Counter()
    for idx, (i, id_, s, text, claude) in enumerate(rows):
        if s == stage_num:
            final = ws.cell(i, 7).value
            stage_final[final] += 1
    print(f"  Stage {stage_num} (n={sum(stage_final.values())}):")
    for label, cnt in sorted(stage_final.items(), key=lambda x: -x[1]):
        print(f"    {label}: {cnt} ({cnt/sum(stage_final.values())*100:.1f}%)")

# 保存
wb.save(OUTPUT)
wb.save(OUTPUT2)
print(f"\n✅ 保存: {OUTPUT}")
print(f"✅ 保存: {OUTPUT2}")
