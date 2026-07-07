#!/tmp/whisper_venv/bin/python3
"""
量价异动扫描 — 提前埋伏候选
数据源：腾讯API（实时准确）
逻辑：量比>3 + 涨幅-2%~2% = 聪明钱进场但股价没动 = 最佳埋伏
"""

import urllib.request, re, json

# 产业链映射表
SECTOR_MAP = {
    "002902": "CPO/光通信", "600522": "通信设备", "600487": "通信设备", "600498": "通信设备", "002396": "通信设备",
    "002273": "消费电子/AI眼镜", "002241": "消费电子/VR", "002475": "消费电子", "002008": "消费电子/设备",
    "600171": "半导体/模拟", "600703": "半导体/化合物", "600460": "半导体/功率",
    "002185": "半导体/封测", "002156": "半导体/封测", "600584": "半导体/封测", "002594": "新能源车",
}
    ("sh600487", "亨通光电", "通信设备"),
    ("sh600498", "烽火通信", "通信设备"),
    ("sz002396", "星网锐捷", "通信设备"),
    ("sz002273", "水晶光电", "消费电子/AI眼镜"),
    ("sz002241", "歌尔股份", "消费电子/VR"),
    ("sz002475", "立讯精密", "消费电子"),
    ("sz002008", "大族激光", "消费电子/设备"),
    ("sh600171", "上海贝岭", "半导体/模拟"),
    ("sh600703", "三安光电", "半导体/化合物"),
    ("sh600460", "士兰微", "半导体/功率"),
    ("sz002185", "华天科技", "半导体/封测"),
    ("sz002156", "通富微电", "半导体/封测"),
    ("sh600584", "长电科技", "半导体/封测"),
    ("sz002594", "比亚迪", "新能源车"),
]


def scan():
    codes = [c for c, _, _ in MAPPING]
    url = "http://qt.gtimg.cn/q=" + ",".join(codes)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=10).read()
    text = resp.decode("gbk")

    print("=" * 58)
    print("  📊 量价异动扫描 | 提前埋伏候选")
    print("=" * 58)
    print(f"\n  {'名称':<10}  {'涨幅':>7}  {'量比':>5}  板块")
    print("  " + "-" * 48)

    ambush = []  # 量比>3 且 涨幅-2%~2%
    watch = []   # 量比>5 且 涨幅2~5%

    for line in text.strip().split("\n"):
        m = re.search(r'v_\w+="(.+)"', line.strip())
        if not m:
            continue
        parts = m.group(1).split("~")
        if len(parts) < 40:
            continue

        name, code = parts[1], parts[2]
        price, pct, vr = float(parts[3]), float(parts[32]), float(parts[38])

        sector = ""
        for c, _, s in MAPPING:
            if c.endswith(code):
            if c == code:
                sector = s
                break

        emoji = "🔴" if pct > 0 else ("🟢" if pct < 0 else "⚪")
        print(f"  {emoji} {name:<10} {pct:>+7.2f}% {vr:>5.1f}  {sector}")

        # 判断
        if vr > 3 and -2 < pct < 2:
            ambush.append((code, name, price, pct, vr, sector))
        elif vr > 5 and 2 <= pct < 5:
            watch.append((code, name, price, pct, vr, sector))

    print(f"\n{'=' * 58}")
    if ambush:
        print(f"  🎯 最佳埋伏候选（量比>3 + 涨幅<2% = 聪明钱刚进）：")
        for code, name, price, pct, vr, sector in ambush:
            print(f"     ✅ {name}({code})  {price}  {pct:+.2f}%  量比{vr:.1f}  {sector}")
    if watch:
        print(f"\n  ⭐ 关注候选（量比>5 + 涨幅2~5% = 启动但还有空间）：")
        for code, name, price, pct, vr, sector in watch:
            print(f"     ⭐ {name}({code})  {price}  {pct:+.2f}%  量比{vr:.1f}  {sector}")
    if not ambush and not watch:
        print(f"  📭 今日无符合条件的埋伏候选")

    print(f"\n{'=' * 58}")


if __name__ == "__main__":
    scan()
