# -*- coding: utf-8 -*-
"""可行性验证：1) 汽车之家全量指导价  2) C-NCAP 四套体系全量  3) 与 C-IASI 名称匹配率"""
import json, re, time, urllib.request, urllib.parse, gzip, io, os, sys

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
HERE = os.path.dirname(os.path.abspath(__file__))


def fetch(url, data=None, referer=None, retry=3):
    for i in range(retry):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", UA)
            req.add_header("Accept-Encoding", "gzip")
            if referer:
                req.add_header("Referer", referer)
            body = None
            if data is not None:
                body = urllib.parse.urlencode(data).encode()
                req.add_header("Content-Type", "application/x-www-form-urlencoded")
            with urllib.request.urlopen(req, body, timeout=30) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return raw.decode("utf-8", "replace")
        except Exception as e:
            if i == retry - 1:
                print("  FAIL", url[:70], e)
                return ""
            time.sleep(1.5)
    return ""


# ---------- 1. 汽车之家全量指导价 ----------
def fetch_prices():
    """保留品牌名：<div class="h3-tit"><a ...>品牌</a></div> 后面跟该品牌的 <li> 车系"""
    out = {}
    BLOCK = re.compile(r'<div class="h3-tit"><a[^>]*>([^<]+)</a></div>(.*?)(?=<div class="h3-tit">|</dl>)', re.S)
    LI = re.compile(r'<li\s+id="s(\d+)">.*?<h4><a[^>]*>([^<]+)</a></h4>(.*?)</li>', re.S)
    PRICE = re.compile(r"指导价：(?:<a[^>]*>)?([^<]+?)(?:</a>)?(?:</div>|<div)")
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        t = fetch("https://www.autohome.com.cn/grade/carhtml/%s.html" % ch,
                  referer="https://www.autohome.com.cn/")
        n = 0
        for brand, body in BLOCK.findall(t):
            brand = re.sub(r"\(.*?\)|（.*?）", "", brand).strip()
            for sid, name, tail in LI.findall(body):
                m = PRICE.search(tail)
                price = m.group(1).strip() if m else "暂无"
                lo = hi = None
                nums = re.findall(r"(\d+\.?\d*)", price.replace("万", ""))
                if "万" in price and nums:
                    lo = float(nums[0])
                    hi = float(nums[-1]) if len(nums) > 1 else lo
                out[name.strip()] = {"series_id": int(sid), "brand": brand,
                                     "price_text": price, "price_low": lo,
                                     "price_high": hi}
                n += 1
        print("  autohome %s: %d 车系" % (ch, n))
        time.sleep(0.4)
    return out


# ---------- 2. C-NCAP 四套体系全量 ----------
TYPES = {1: "C-NCAP", 2: "CCRT", 4: "C-ICAP", 5: "C-GCAP"}


def fetch_cncap():
    res = {}
    for tp, nm in TYPES.items():
        recs, page = [], 1
        while True:
            t = fetch("https://www.c-ncap.org.cn/api/crashSearch",
                      data={"brandId": "", "ruleYear": "", "seriesId": "",
                            "manufacturerId": "", "fuleKind": "", "categoryName": "",
                            "keyword": "", "pageNumber": page, "pageSize": 100, "type": tp},
                      referer="https://www.c-ncap.org.cn/cncapAllData")
            try:
                d = json.loads(t)["data"]
            except Exception:
                break
            recs += d.get("records") or []
            if page >= (d.get("pages") or 1):
                break
            page += 1
            time.sleep(0.3)
        res[nm] = recs
        print("  %-8s %d 条" % (nm, len(recs)))
    return res


# ---------- 3. 名称匹配 ----------
NOISE = re.compile(r"(新能源|插电式|混合动力|增程|纯电|燃油|版|款|PLUS|Pro|Max|L$)", re.I)


def norm(s):
    s = re.sub(r"[\s\(\)（）\-—·]", "", s or "")
    return s


BRAND_PREFIX = ["奇瑞", "赛力斯", "一汽", "东风", "上汽", "广汽", "北汽", "长安", "吉利",
                "江淮", "比亚迪", "本田", "丰田", "日产", "大众", "别克", "雪佛兰",
                "现代", "起亚", "沃尔沃", "领克", "上汽通用", "华晨"]


def variants(model, brand=""):
    """生成候选写法：原名 / 品牌+原名 / 剥离厂商前缀"""
    m, b = norm(model), norm(brand)
    out = [m]
    if b:
        out.append(b + m)
    for p in BRAND_PREFIX:
        if m.startswith(p) and len(m) > len(p) + 1:
            out.append(m[len(p):])
    return [x for x in out if x]


def match_price(model, brand, exact_keys, all_keys):
    for v in variants(model, brand):
        if v in exact_keys:
            return v, "精确"
    for v in variants(model, brand):
        if v in all_keys:
            return v, "车系(无价)"
    # 宽松包含：只对有价格的键做，避免误配老车系
    for v in variants(model, brand):
        if len(v) >= 3:
            for k in exact_keys:
                if v in k or k in v:
                    return k, "模糊"
    return None, None


def main():
    pf = os.path.join(HERE, "prices.json")
    cf = os.path.join(HERE, "cncap_all.json")
    if os.path.exists(pf):
        prices = json.load(open(pf, encoding="utf-8"))
        print("[1/3] 复用已抓取价格库 %d 车系" % len(prices))
    else:
        print("[1/3] 抓取汽车之家全量指导价 ...")
        prices = fetch_prices()
        json.dump(prices, open(pf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    withp = sum(1 for v in prices.values() if v["price_low"])
    print("  => 车系 %d 个，其中有明确指导价 %d 个 (%.0f%%)\n"
          % (len(prices), withp, withp * 100 / max(1, len(prices))))

    if os.path.exists(cf):
        cncap = json.load(open(cf, encoding="utf-8"))
        print("[2/3] 复用已抓取中汽测评数据 " +
              " ".join("%s=%d" % (k, len(v)) for k, v in cncap.items()))
    else:
        print("[2/3] 抓取中汽测评四套体系 ...")
        cncap = fetch_cncap()
        json.dump(cncap, open(cf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print()

    print("[3/3] 名称匹配率实测")
    # 建索引：车系名 + 品牌拼车系名 两种写法都指向同一价格
    pk = {}
    for k, v in prices.items():
        nk = norm(k)
        pk.setdefault(nk, v)
        b = norm(v.get("brand", ""))
        if b and not nk.startswith(b):
            pk.setdefault(b + nk, v)
    all_keys = set(pk.keys())
    keys = set(k for k, v in pk.items() if v["price_low"])  # 只含有效指导价
    print("  价格索引 %d 键（含品牌拼写变体）" % len(pk))

    _cj = json.load(open(os.path.join(HERE, "..", "ciasi-workbench",
                                      "ciasi_ratings.json"), encoding="utf-8"))
    if isinstance(_cj, dict):
        ciasi = _cj.get("records") or _cj.get("data") or []
        if isinstance(ciasi, dict):
            ciasi = ciasi.get("records") or []
    else:
        ciasi = _cj
    ciasi = [r for r in ciasi if isinstance(r, dict)]
    print("  C-IASI 载入 %d 条" % len(ciasi))
    report = {}

    def run(recs, get_model, get_brand=lambda r: ""):
        hit, misses, samples = 0, [], []
        for r in recs:
            k, lvl = match_price(get_model(r), get_brand(r), keys, all_keys)
            if k and lvl != "车系(无价)":
                hit += 1
                if len(samples) < 6:
                    samples.append("%s→%s %s" % (get_model(r), k, pk[k]["price_text"]))
            else:
                misses.append(get_model(r))
        return (len(recs), hit, misses, samples)

    report["C-IASI"] = run(ciasi, lambda r: r["model"], lambda r: r["brand"])
    for nm, recs in cncap.items():
        report[nm] = run(recs, lambda r: r.get("carName", ""))

    print("\n%-10s %8s %10s %8s" % ("数据源", "总数", "匹配到价格", "匹配率"))
    print("-" * 42)
    for nm, (tot, h, ms, sp) in report.items():
        print("%-10s %8d %10d %7.1f%%" % (nm, tot, h, h * 100 / max(1, tot)))
    print("\n[匹配样例]")
    for s in report["C-IASI"][3]:
        print("   ", s)
    print("\n未匹配样例(C-IASI):", "、".join(report["C-IASI"][2][:14]))
    print("未匹配样例(C-NCAP):", "、".join(report["C-NCAP"][2][:14]))

    # 交叉覆盖：C-IASI 与 C-NCAP 车型重叠度
    ci = set(norm(r["model"]) for r in ciasi)
    cn = set()
    for r in cncap.get("C-NCAP", []):
        cn.add(norm(r.get("carName", "")))
    both = 0
    for a in ci:
        if any(a and (a in b or b in a) for b in cn):
            both += 1
    print("\n[交叉覆盖] C-IASI %d 款；其中 C-NCAP 也测过约 %d 款 (%.0f%%)；"
          "仅 C-IASI 独有约 %d 款" % (len(ci), both, both * 100 / max(1, len(ci)), len(ci) - both))
    print("[并集估算] C-IASI ∪ C-NCAP ≈ %d 款车型" % (len(ci) + len(cn) - both))


if __name__ == "__main__":
    main()
