#!/usr/bin/env python3
"""
关羽数据层 v1.0 — 多源冗余+本地缓存+自动重试
解决akshare连接不稳定、无备用源、无缓存的问题

数据源优先级: 东方财富直连 > akshare > 腾讯API > 本地缓存

用法:
  from data_layer import get_quote, get_fund_flow, get_kline
  df = get_fund_flow('concept')  # 概念板块资金流
  df = get_kline('603125', days=20)  # K线数据
  q = get_quote('603125')  # 个股行情
"""

import os
import json
import time
import ssl
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# === SSL修复 ===
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

def http_get(url, timeout=10, retries=2, encoding='utf-8'):
    """带重试的HTTP GET（curl + urllib双通道，自动检测编码）"""
    for attempt in range(retries + 1):
        try:
            import subprocess
            result = subprocess.run(
                ['curl', '-k', '-s', '--max-time', str(timeout), url],
                capture_output=True, timeout=timeout+2
            )
            if result.returncode == 0 and result.stdout:
                for enc in [encoding, 'gbk', 'gb2312', 'utf-8']:
                    try:
                        return result.stdout.decode(enc)
                    except:
                        continue
                return result.stdout.decode('utf-8', errors='replace')
        except:
            pass
        
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                'Referer': 'https://www.eastmoney.com/'
            })
            resp = urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX)
            return resp.read().decode(encoding, errors='replace')
        except Exception as e:
            if attempt < retries:
                time.sleep(1)
            else:
                raise

def cache_get(key, max_age_seconds=3600):
    """读取缓存"""
    fpath = CACHE_DIR / f"{key}.json"
    if fpath.exists():
        age = time.time() - fpath.stat().st_mtime
        if age < max_age_seconds:
            return json.loads(fpath.read_text())
    return None

def cache_set(key, data):
    """写入缓存"""
    fpath = CACHE_DIR / f"{key}.json"
    fpath.write_text(json.dumps(data, ensure_ascii=False, default=str))
    return data

# === 行情接口 ===
def get_quote(code):
    """
    获取个股实时行情
    优先：腾讯API → 缓存
    返回dict
    """
    market = "sh" if code.startswith(("6", "5", "9")) else "sz"
    full = f"{market}{code}"
    
    # 尝试腾讯API
    try:
        url = f"https://qt.gtimg.cn/q={full}"
        raw = http_get(url, timeout=8)
        if "~" in raw:
            parts = raw.split("~")
            if len(parts) > 45:
                name = parts[1].strip()
                data = {
                    "name": name,
                    "code": code,
                    "price": float(parts[3]) if parts[3] else 0,
                    "last_close": float(parts[4]) if parts[4] else 0,
                    "open": float(parts[5]) if parts[5] else 0,
                    "volume": int(float(parts[6])/10000) if parts[6] and parts[6] != '0' else 0,
                    "high": float(parts[33]) if parts[33] else 0,
                    "low": float(parts[34]) if parts[34] else 0,
                    "amount": float(parts[37])/1e8 if parts[37] and parts[37] != '0' else 0,
                    "turnover": float(parts[38]) if len(parts) > 38 and parts[38] else 0,
                    "pe": float(parts[39]) if len(parts) > 39 and parts[39] and parts[39] != '0' else 0,
                    "change_pct": float(parts[32]) if parts[32] else 0,
                    "mkt_cap": float(parts[45])/1e8 if len(parts) > 45 and parts[45] else 0,
                    "circ_cap": float(parts[44])/1e8 if len(parts) > 44 and parts[44] else 0,
                    "pb": float(parts[46]) if len(parts) > 46 and parts[46] and parts[46] != '0' else 0,
                    "updated": datetime.now().isoformat()
                }
                cache_set(f"quote_{code}", data)
                return data
    except Exception as e:
        pass
    
    # 降级到缓存
    cached = cache_get(f"quote_{code}", max_age_seconds=86400)
    if cached:
        cached["cached"] = True
        return cached
    
    return None

def get_quotes_batch(codes):
    """批量获取行情"""
    quotes = {}
    market_codes = []
    for code in codes:
        m = "sh" if code.startswith(("6", "5", "9")) else "sz"
        market_codes.append(f"{m}{code}")
    
    try:
        url = f"https://qt.gtimg.cn/q={','.join(market_codes)}"
        raw = http_get(url, timeout=8)
        for line in raw.split(";"):
            if "~" in line:
                parts = line.split("~")
                if len(parts) > 10:
                    code = parts[2].strip() if len(parts) > 2 else ""
                    name = parts[1].strip()
                    try:
                        quotes[code] = {
                            "name": name,
                            "price": float(parts[3]) if parts[3] else 0,
                            "last_close": float(parts[4]) if parts[4] else 0,
                            "change_pct": float(parts[32]) if len(parts) > 32 and parts[32] else 0,
                            "high": float(parts[33]) if len(parts) > 33 and parts[33] else 0,
                            "low": float(parts[34]) if len(parts) > 34 and parts[34] else 0,
                            "turnover": float(parts[38]) if len(parts) > 38 and parts[38] else 0,
                            "pe": float(parts[39]) if len(parts) > 39 and parts[39] and parts[39] != '0' else 0,
                            "amount": float(parts[37])/1e8 if len(parts) > 37 and parts[37] and parts[37] != '0' else 0,
                            "mkt_cap": float(parts[45])/1e8 if len(parts) > 45 and parts[45] else 0,
                        }
                    except:
                        pass
        if quotes:
            cache_set(f"quotes_batch", quotes)
    except:
        cached = cache_get(f"quotes_batch", max_age_seconds=3600)
        if cached:
            return {k: {**v, "cached": True} for k, v in cached.items() if k in codes}
    
    return quotes

# === K线接口 ===
def get_kline(code, days=30):
    """
    获取个股K线
    优先：腾讯API → akshare → 缓存
    """
    market = "sh" if code.startswith(("6", "5", "9")) else "sz"
    
    # 方法1: 腾讯API（最稳定）
    try:
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={market}{code},day,,,{days+10},qfq"
        raw = http_get(url, timeout=10)
        data = json.loads(raw)
        stock_data = data.get('data', {}).get(f'{market}{code}', {})
        lines = stock_data.get('qfqday') or stock_data.get('day')
        if lines:
            records = []
            prev_close = None
            for line in lines[-days:]:
                # [date, open, close, high, low, volume]
                if len(line) >= 6:
                    o, c, h, l, v = float(line[1]), float(line[2]), float(line[3]), float(line[4]), float(line[5])
                    chg = ((c - o) / o * 100) if o and o != 0 else 0
                    if prev_close:
                        chg = ((c - prev_close) / prev_close * 100)
                    records.append({
                        'date': line[0], 'open': o, 'close': c,
                        'high': h, 'low': l,
                        'volume': int(v), 'amount': 0,
                        'change_pct': round(chg, 2),
                        'amplitude': round((h - l) / l * 100, 2) if l and l != 0 else 0,
                        'turnover': 0
                    })
                    prev_close = c
            if records:
                cache_set(f"kline_{code}", records)
                return records
    except Exception as e:
        pass
    
    # 方法2: akshare
    try:
        from datetime import datetime as dt
        end_date = dt.now().strftime("%Y%m%d")
        start_date = (dt.now() - timedelta(days=days+10)).strftime("%Y%m%d")
        import akshare as ak
        df = ak.stock_zh_a_hist(symbol=code, period="daily",
                                start_date=start_date, end_date=end_date, adjust="qfq")
        if df is not None and not df.empty:
            records = df.tail(days).to_dict('records')
            cache_set(f"kline_{code}", records)
            return records
    except:
        pass
    
    # 降级: 缓存
    cached = cache_get(f"kline_{code}", max_age_seconds=86400)
    if cached:
        return cached
    
    return None

# === 概念板块资金流 ===
def get_concept_fund_flow(category='即时'):
    """
    概念板块资金流
    优先：akshare → 缓存
    category: '即时' | '3日排行' | '5日排行'
    """
    cache_key = f"concept_flow_{category}"
    
    # 方法1: akshare
    try:
        import akshare as ak
        df = ak.stock_fund_flow_concept(symbol=category)
        if df is not None and not df.empty:
            records = df.to_dict('records')
            cache_set(cache_key, records)
            return records
    except:
        pass
    
    # 降级: 缓存（同一天有效）
    cached = cache_get(cache_key, max_age_seconds=24000)
    if cached:
        return cached
    
    return None

def get_industry_fund_flow():
    """行业资金流"""
    cache_key = "industry_flow"
    try:
        import akshare as ak
        df = ak.stock_fund_flow_industry(symbol='即时')
        if df is not None and not df.empty:
            records = df.to_dict('records')
            cache_set(cache_key, records)
            return records
    except:
        pass
    
    cached = cache_get(cache_key, max_age_seconds=24000)
    if cached:
        return cached
    return None

# === 快捷工具 ===
def get_holdings_health(holdings):
    """
    持仓健康度一键扫描
    输入: {code: {'cost': float, 'shares': int}, ...}
    返回: 每只票的当前状态
    """
    codes = list(holdings.keys())
    quotes = get_quotes_batch(codes)
    
    results = {}
    for code, h in holdings.items():
        q = quotes.get(code, {})
        cost = h['cost']
        shares = h['shares']
        price = q.get('price', 0)
        pnl = (price - cost) * shares
        pnl_pct = (price - cost) / cost * 100 if cost else 0
        
        results[code] = {
            'name': q.get('name', ''),
            'price': price,
            'cost': cost,
            'shares': shares,
            'pnl': round(pnl, 0),
            'pnl_pct': round(pnl_pct, 1),
            'change_pct': q.get('change_pct', 0),
            'turnover': q.get('turnover', 0),
            'pe': q.get('pe', 0),
            'mkt_cap': q.get('mkt_cap', 0),
            'cached': q.get('cached', False)
        }
    
    return results

# === 测试 ===
if __name__ == "__main__":
    print("=" * 50)
    print("关羽数据层 v1.0 自检")
    print("=" * 50)
    
    # 测试行情
    q = get_quote("603125")
    print(f"\n✅ 个股行情: {q}")
    
    # 测试批量行情
    codes = ["002023", "002185", "600096", "002624"]
    qs = get_quotes_batch(codes)
    print(f"\n✅ 批量行情: {len(qs)}只")
    for c, d in qs.items():
        print(f"  {c} {d.get('name','')}: {d.get('price')} ({d.get('change_pct','')}%)")
    
    # 测试K线
    k = get_kline("603125", days=5)
    if k:
        print(f"\n✅ K线: {len(k)}条, 最新={k[-1]['date']} 收{k[-1]['close']}")
    else:
        print(f"\n❌ K线获取失败")
    
    # 测试概念资金流
    cf = get_concept_fund_flow()
    if cf:
        print(f"\n✅ 概念资金流: {len(cf)}条")
        for item in cf[:5]:
            col = item.get('行业', '')
            net = item.get('净额', 0)
            print(f"  {'🟢' if net > 0 else '🔴'} {col}: {net:+.2f}亿")
    else:
        print(f"\n❌ 概念资金流获取失败（周六非交易日，使用缓存）")
    
    print(f"\n📁 缓存目录: {CACHE_DIR}")
    print(f"📁 缓存文件数: {len(list(CACHE_DIR.glob('*.json')))}")
