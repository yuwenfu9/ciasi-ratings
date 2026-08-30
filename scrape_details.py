# -*- coding: utf-8 -*-
"""抓取中汽测评 C-ICAP / C-GCAP 详情页，回填子项得分与综合分到 ratings_all.json。

原理（已在 explore11 验证）：
- 详情页 https://www.c-ncap.org.cn/evaluation/{evaluationId} 是服务端渲染 HTML，
  内嵌一段树状 JSON，每条目标含 id / preId(父id) / targetName / targetLevel / gradeScoring。
- gradeScoring 有两种含义：
    * 评级等级：整数 1~6（G+=6,G=5,A=4,M=3,P=2...）→ 这是「大项」的评级，不是分数。
    * 得分：带 % 的得分率（C-ICAP），或 0~100 的数值（C-GCAP 满分100），或带单位的非分数（L/100km、mg/m³ 等，跳过）。
- 「子项得分」= 得分型目标，且其父节点(preId)是评级等级（即它直接挂在大项之下）。
  例：基础行车辅助(97.9%) 的父 行车辅助 是评级6 → 计入；跟车能力(100%) 的父 基础行车辅助 是得分 → 不计入（它是更细的叶子）。
- 综合分 = 各子项得分的均值，作为可排序的代表值。
"""
import json, os, re, sys, gzip, time, urllib.request
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
PROXY = "http://127.0.0.1:7897"


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Encoding": "gzip, deflate"})
    last = None
    for proxy in [None, PROXY]:
        try:
            if proxy:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
            else:
                opener = urllib.request.build_opener()
            r = opener.open(req, timeout=timeout)
            raw = r.read()
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            return raw.decode("utf-8", "ignore")
        except Exception as e:
            last = e
    raise last


OBJ_RE = re.compile(
    r'"id":(\d+),"ruleId":\d+,"targetId":\d+,"targetName":"([^"]+)",'
    r'"attrName":[^,]*,"gradeScoring":"([^"]*)","grade":(?:"[^"]*"|null),"image":[^,]*,"video":[^,]*,'
    r'"targetLevel":(\d+)[^}]*?"preId":(-?\d+)')


def is_rating_level(gs):
    """gradeScoring 为整数 1~6 → 评级等级，不是分数。"""
    if gs is None:
        return False
    if re.fullmatch(r"\d+", gs):
        try:
            return 1 <= int(gs) <= 6
        except ValueError:
            return False
    return False


def score_value(gs):
    """把得分型 gradeScoring 转成浮点；非得分（空/带单位）返回 None。"""
    if gs is None:
        return None
    if re.fullmatch(r"\d+(?:\.\d+)?%", gs):
        return float(gs.rstrip("%"))
    if re.fullmatch(r"\d+(?:\.\d+)?", gs):
        f = float(gs)
        if 1 <= f <= 6:  # 整数评级等级，非分数
            return None
        return f
    return None  # 带单位（L/100km、mg/m³、min、dB、无报告）等


def parse_detail(html, org):
    objs = {}
    for m in OBJ_RE.finditer(html):
        oid = int(m.group(1)); name = m.group(2); gs = m.group(3)
        level = int(m.group(4)); pre = int(m.group(5))
        objs[oid] = {"name": name, "gs": gs, "level": level, "pre": pre}
    # 子项得分：得分型 且其父是评级等级，或自身就是 level-2 模块得分（部分模块无 level-3 子项）
    targets = {}
    vals = []
    for oid, o in objs.items():
        v = score_value(o["gs"])
        if v is None:
            continue
        parent = objs.get(o["pre"])
        if (parent and is_rating_level(parent["gs"])) or o["level"] == 2:
            targets[o["name"]] = o["gs"]
            vals.append(v)
    if not vals:
        return None, {}
    overall = sum(vals) / len(vals)
    if org == "c_icap":
        overall_s = "%.1f%%" % overall          # 得分率均值
    else:  # c_gcap 满分100
        overall_s = "%.1f" % overall
    return overall_s, targets


def main():
    path = os.path.join(HERE, "ratings_all.json")
    data = json.load(open(path, encoding="utf-8"))
    orgs = data["orgs"]
    for org in ["c_icap", "c_gcap"]:
        recs = orgs.get(org, [])
        total = len(recs)
        filled = 0
        for i, r in enumerate(recs):
            eid = r.get("evaluationId")
            if not eid:
                continue
            # 增量：已抓过且成功则跳过
            if r.get("scrape_status") == "ok" and r.get("targets") and r.get("score"):
                filled += 1
                continue
            url = "https://www.c-ncap.org.cn/evaluation/" + eid
            try:
                html = fetch(url)
                score, targets = parse_detail(html, org)
                if score is None:
                    r["scrape_status"] = "empty"
                else:
                    r["score"] = score
                    r["targets"] = targets
                    r["scrape_status"] = "ok"
                    filled += 1
                    print("  [%s] %s -> 综合 %s, 子项 %d" % (org, r.get("carName"), score, len(targets)))
            except Exception as e:
                r["scrape_status"] = "err:" + str(e)[:60]
                print("  [%s] %s ERROR %s" % (org, r.get("carName"), e))
            time.sleep(0.25)
        print("[%s] 已补 %d / %d" % (org, filled, total))

    data["metadata"]["scraped_at"] = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%dT%H:%M:%S+08:00")
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("wrote ratings_all.json")


if __name__ == "__main__":
    main()
