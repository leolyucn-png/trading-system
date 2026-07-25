# -*- coding: utf-8 -*-
"""
观察池v1 · 确定性筛选脚本
规则(写死,与实验日志一致):
 1. 非ST/非退市整理
 2. 上市满一年(以能取到>=240个交易日日线为准)
 3. 流通市值 8-40亿
 4. 近20日日均成交额 > 3000万
 5. 按近60日累计换手率降序取前200
输出:
 pool_YYYYMMDD.csv (代码/名称/流通市值亿/20日均成交额万/60日换手率%)
 funnel_YYYYMMDD.txt (漏斗报告,每步剩余数量)
用法: pip install akshare pandas 后直接 python build_pool.py
说明: 全程无任何模型参与,同一天任何人跑结果一致。
"""
import os, time, datetime
import pandas as pd
import akshare as ak

TODAY = datetime.date.today().strftime("%Y%m%d")
CACHE = f"hist_cache_{TODAY}.csv" # 断点续跑缓存
OUT_POOL = f"pool_{TODAY}.csv"
OUT_FUNNEL = f"funnel_{TODAY}.txt"

funnel = []
def log(step, n):
    line = f"{step}: 剩余 {n}"
    print(line); funnel.append(line)

# ---------- 第0步: 全市场快照 ----------
spot = ak.stock_zh_a_spot_em()
spot = spot.rename(columns=lambda c: c.strip())
spot["代码"] = spot["代码"].astype(str).str.zfill(6)
log("全A快照", len(spot))

# ---------- 第1步: 剔除ST/退市/新股标记 ----------
bad = spot["名称"].str.contains("ST|退", na=False)
new_mark = spot["名称"].str.match(r"^[NCU]", na=False) # N新股/C次新/U未盈利标记
spot = spot[~bad & ~new_mark].copy()
log("剔除ST/退/新股标记", len(spot))

# ---------- 第2步: 流通市值 8-40亿 ----------
spot["流通市值亿"] = pd.to_numeric(spot["流通市值"], errors="coerce") / 1e8
spot = spot[(spot["流通市值亿"] >= 8) & (spot["流通市值亿"] <= 40)].copy()
log("流通市值8-40亿", len(spot))

# ---------- 第3步: 逐只取日线,算20日均成交额/60日换手/上市时长 ----------
if os.path.exists(CACHE):
    done = pd.read_csv(CACHE, dtype={"代码": str})
else:
    done = pd.DataFrame(columns=["代码", "交易日数", "均成交额万20", "换手率60"])

todo = spot[~spot["代码"].isin(done["代码"])]
rows = done.to_dict("records")
for i, (_, r) in enumerate(todo.iterrows(), 1):
    code = r["代码"]
    try:
        h = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="")
        h = h.tail(250)
        rows.append({
            "代码": code,
            "交易日数": len(h),
            "均成交额万20": h["成交额"].tail(20).mean() / 1e4,
            "换手率60": h["换手率"].tail(60).sum(),
        })
    except Exception as e:
        rows.append({"代码": code, "交易日数": 0,
                     "均成交额万20": 0, "换手率60": 0})
        print(f" [失败] {code}: {e}")
    if i % 25 == 0:
        pd.DataFrame(rows).to_csv(CACHE, index=False)
        print(f" 进度 {i}/{len(todo)}")
    time.sleep(0.25)  # 限速,别把接口打死

hist = pd.DataFrame(rows)
hist["代码"] = hist["代码"].astype(str).str.zfill(6)
pd.DataFrame(rows).to_csv(CACHE, index=False)
df = spot.merge(hist, on="代码", how="left")

# ---------- 第4步: 上市满一年 ----------
df = df[df["交易日数"] >= 240].copy()
log("上市满一年(>=240交易日)", len(df))

# ---------- 第5步: 20日均成交额>3000万 ----------
df = df[df["均成交额万20"] > 3000].copy()
log("20日均成交额>3000万", len(df))

# ---------- 第6步: 按60日换手率取前200 ----------
df = df.sort_values("换手率60", ascending=False).head(200)
log("按60日换手率取前200", len(df))

# ---------- 输出 ----------
out = df[["代码", "名称", "流通市值亿", "均成交额万20", "换手率60"]].round(2)
out.columns = ["代码", "名称", "流通市值亿", "20日均成交额万", "60日累计换手率%"]
out.to_csv(OUT_POOL, index=False, encoding="utf-8-sig")
with open(OUT_FUNNEL, "w", encoding="utf-8") as f:
    f.write(f"观察池v1漏斗报告 {TODAY}\n" + "\n".join(funnel) + "\n")
print(f"\n完成: {OUT_POOL} / {OUT_FUNNEL}")
print("提示: 雷点剔除(立案/预亏/解禁)属文本层,由模型在池内逐只标注,不在本脚本内。")
