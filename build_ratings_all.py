# -*- coding: utf-8 -*-
"""合并 C-IASI(中保研) + 中汽测评四体系(C-NCAP/CCRT/C-ICAP/C-GCAP) + 汽车之家指导价
生成统一 ratings_all.json 供多机构切换版仪表盘使用。

设计原则（来自 EXPANSION_REPORT.md）：
- 不合并评级，只按机构分命名空间各自保留原始字段与原始刻度
- 价格仅厂商指导价快照，约 70% 测试车型无价（停售/换代/待上市），标 null
- 车型名对齐靠别名归一 + 品牌前缀剥离（复用 feasibility.py 的 match_price）
"""
import json, os, sys, re
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from feasibility import norm, variants, match_price  # 复用已验证的匹配逻辑

PRICE_DATE = "2026-08-30"

# 品牌线索（长优先，避免「广汽」误匹配「广汽丰田」）：用于
# 1) 还原被源站录错的车型名（如「鹏G3」→「小鹏G3」）
# 2) 从中汽测评 manufacturer / carName 推断 brand，使品牌筛选可用
BRAND_HINTS = sorted([
    "小鹏", "小米汽车", "小米", "理想", "蔚来", "零跑", "哪吒", "问界", "智界", "阿维塔",
    "深蓝", "腾势", "极氪", "领克", "岚图", "欧拉", "飞凡", "荣威", "名爵", "比亚迪",
    "吉利", "长安", "广汽乘用车", "广汽丰田", "广汽本田", "一汽丰田", "一汽大众", "上汽大众",
    "上汽通用", "上汽通用五菱", "东风本田", "东风日产", "东风悦达起亚", "长安福特", "长安马自达",
    "北京现代", "北京奔驰", "华晨宝马", "福建奔驰", "奇瑞新能源", "奇瑞", "特斯拉", "宝马",
    "奔驰", "奥迪", "大众", "丰田", "本田", "日产", "现代", "起亚", "沃尔沃", "别克",
    "凯迪拉克", "雪佛兰", "马自达", "福特", "保时捷", "雷克萨斯", "捷豹", "路虎", "捷达",
    "斯柯达", "智马达", "睿蓝", "沙龙", "仰望", "方程豹", "极狐", "五菱", "宝骏", "北京",
    "江淮", "星途", "星纪元", "享界", "尊界", "乐道", "萤火虫", "广汽", "一汽", "上汽",
    "东风", "长城", "三菱", "标致", "雪铁龙", "雷诺", "Jeep", "吉普", "林肯", "英菲尼迪",
    "讴歌", "斯巴鲁", "双龙", "合众", "天际", "高合", "威马", "云度", "力帆", "众泰",
    "海马", "奔腾", "启辰", "凯翼", "宝沃", "观致", "斯威", "金杯", "大通", "福田",
    "智己", "埃安", "极越", "极石", "思皓", "远航", "创维", "开瑞", "北汽", "合创",
    "广汽埃安", "思浩", "天美", "国机智骏", "小米汽车",
], key=len, reverse=True)


def repair_name(carName, manufacturer):
    """还原被源站漏掉首字的车型名，如「鹏G3」(manufacturer 含'小鹏')→「小鹏G3」。"""
    if not carName:
        return carName
    for b in BRAND_HINTS:
        if b in (manufacturer or ""):
            tail = b[1:]
            if tail and carName.startswith(tail) and not carName.startswith(b):
                return b + carName[len(tail):]
    return carName


def derive_brand(carName, manufacturer):
    for b in BRAND_HINTS:
        if b in (carName or "") or b in (manufacturer or ""):
            return b
    return ""


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
            raw_name = r.get("carName", "")
            carName = repair_name(raw_name, r.get("manufacturer"))
            recs.append({
                "carName": carName,
                "brand": derive_brand(carName, r.get("manufacturer")),
                "year": r.get("testYear", ""),
                "score": r.get("score"),
                "targets": clean_target(r.get("targetList")),
                "evaluationId": r.get("evaluationId"),
                "detail_url": ("https://www.c-ncap.org.cn/evaluation/" + r["evaluationId"]
                               if r.get("evaluationId") else None),
                "msrp_guide": attach_price(carName, "", pk, keys, all_keys),
            })
        orgs[key] = recs

    out = {
        "metadata": {
            "generated_at": datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00"),
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
