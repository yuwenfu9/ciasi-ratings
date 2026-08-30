# -*- coding: utf-8 -*-
"""合并 C-IASI(中保研) + 中汽测评四体系(C-NCAP/CCRT/C-ICAP/C-GCAP) + 汽车之家指导价
生成统一 ratings_all.json 供多机构切换版仪表盘使用。

设计原则（来自 EXPANSION_REPORT.md）：
- 不合并评级，只按机构分命名空间各自保留原始字段与原始刻度
- 价格仅厂商指导价快照，约 70% 测试车型无价（停售/换代/待上市），标 null
- 车型名对齐靠别名归一 + 品牌前缀剥离（复用 feasibility.py 的 match_price）
"""
import json, os, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from feasibility import norm, variants, match_price  # 复用已验证的匹配逻辑

PRICE_DATE = "2026-08-30"


def load():
    ciasi = json.load(open(os.path.join(HERE, "ciasi_ratings.json"), encoding="utf-8"))
    if isinstance(ciasi, dict):
        ciasi = ciasi.get("records") or []
    ciasi = [r for r in ciasi if isinstance(r, dict)]
    cncap = json.load(open(os.path.join(HERE, "cncap_all.json"), encoding="utf-8"))
    prices = json.load(open(os.path.join(HERE, "prices.json"), encoding="utf-8"))
    return ciasi, cncap, prices


def build_price_index(prices):
    pk = {}
    for k, v in prices.items():
        nk = norm(k)
        pk.setdefault(nk, v)
        b = norm(v.get("brand", ""))
        if b and not nk.startswith(b):
            pk.setdefault(b + nk, v)
    all_keys = set(pk.keys())
    keys = set(k for k, v in pk.items() if v["price_low"])  # 只含有效指导价
    return pk, keys, all_keys


def attach_price(model, brand, pk, keys, all_keys):
    k, lvl = match_price(model, brand, keys, all_keys)
    if k and lvl != "车系(无价)":
        v = pk[k]
        return {"low": v["price_low"], "high": v["price_high"],
                "text": v["price_text"], "source": "autohome", "fetched_at": PRICE_DATE}
    return None


def clean_target(tl):
    if not tl:
        return None
    out = {}
    for t in tl:
        name = (t.get("targetName") or "").replace("\\VRU保护", "/VRU保护").replace("\\", "")
        if name:
            out[name] = t.get("score")
    return out or None


def main():
    ciasi, cncap, prices = load()
    pk, keys, all_keys = build_price_index(prices)
    orgs = {}

    # ---- C-IASI（中保研）----
    oi = []
    for r in ciasi:
        oi.append({
            "brand": r.get("brand", ""),
            "model": r.get("model", ""),
            "year": r.get("year", ""),
            "segment": r.get("segment", ""),
            "manufacturer": r.get("manufacturer", ""),
            "occupant": r.get("occupant"),
            "pedestrian": r.get("pedestrian"),
            "assist": r.get("assist"),
            "repairability": r.get("repairability"),
            "nev_special": r.get("nev_special"),
            "detail_url": r.get("source") or (
                "https://ciasi.org.cn" + r["detail_url"] if r.get("detail_url") else None),
            "msrp_guide": attach_price(r.get("model", ""), r.get("brand", ""), pk, keys, all_keys),
        })
    orgs["c_iasi"] = oi

    # ---- 中汽测评四体系 ----
    SYS_MAP = {"C-NCAP": "c_ncap", "CCRT": "ccrt", "C-ICAP": "c_icap", "C-GCAP": "c_gcap"}
    for sys, key in SYS_MAP.items():
        recs = []
        for r in cncap.get(sys, []):
            recs.append({
                "carName": r.get("carName", ""),
                "brand": r.get("manufacturer") or r.get("brand", ""),
                "year": r.get("testYear", ""),
                "score": r.get("score"),
                "targets": clean_target(r.get("targetList")),
                "evaluationId": r.get("evaluationId"),
                "detail_url": ("https://www.c-ncap.org.cn/evaluation/" + r["evaluationId"]
                               if r.get("evaluationId") else None),
                "msrp_guide": attach_price(r.get("carName", ""), "", pk, keys, all_keys),
            })
        orgs[key] = recs

    out = {
        "metadata": {
            "generated_at": "2026-08-30T18:00:00+08:00",
            "price_fetched_at": PRICE_DATE,
            "sources": {
                "c_iasi": "ciasi.org.cn（中保研）",
                "c_ncap": "www.c-ncap.org.cn（C-NCAP 中国新车评价规程）",
                "ccrt": "www.c-ncap.org.cn（CCRT 汽车消费者研究与评价）",
                "c_icap": "www.c-ncap.org.cn（C-ICAP 智能网联汽车技术规程）",
                "c_gcap": "www.c-ncap.org.cn（C-GCAP 绿色汽车评价规程）",
                "prices": "autohome.com.cn（厂商指导价，仅约 25% 车系有价）",
            },
            "price_note": "指导价仅为厂商指导价时点快照，非成交价；约 70% 测试车型因停售/换代/待上市无价，统一标「暂无报价」。",
            "score_note": "各机构评级刻度不可通约（C-IASI 等级制 / C-NCAP 百分制 / 其余仅状态），仅并列展示，不折算、不求平均、不做综合分。",
            "record_counts": {k: len(v) for k, v in orgs.items()},
        },
        "orgs": orgs,
    }
    json.dump(out, open(os.path.join(HERE, "ratings_all.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("wrote ratings_all.json")
    print("counts:", out["metadata"]["record_counts"])
    # 价格覆盖率抽查
    for k, v in orgs.items():
        wp = sum(1 for x in v if x.get("msrp_guide"))
        print("  %-8s 有价 %d / %d (%.0f%%)" % (k, wp, len(v), wp * 100 / max(1, len(v))))


if __name__ == "__main__":
    main()
