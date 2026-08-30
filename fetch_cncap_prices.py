# -*- coding: utf-8 -*-
"""抓取中汽测评四套体系 + 汽车之家全量指导价，写入仓库根目录。
供 GitHub Actions 每日刷新 ratings_all.json 使用。
任一来源失败时打印告警但保留已有文件（保证 build 不中断）。
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from feasibility import fetch_cncap, fetch_prices

TYPES = {1: "C-NCAP", 2: "CCRT", 4: "C-ICAP", 5: "C-GCAP"}


def main():
    ok = True
    # 中汽测评四体系
    try:
        cncap = fetch_cncap()
        json.dump(cncap, open(os.path.join(HERE, "cncap_all.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("中汽测评抓取成功:", " ".join("%s=%d" % (k, len(v)) for k, v in cncap.items()))
    except Exception as e:
        ok = False
        print("中汽测评抓取失败，保留旧文件:", e)
    # 汽车之家指导价
    try:
        prices = fetch_prices()
        json.dump(prices, open(os.path.join(HERE, "prices.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        wp = sum(1 for v in prices.values() if v["price_low"])
        print("汽车之家价格抓取成功: %d 车系，其中 %d 有指导价" % (len(prices), wp))
    except Exception as e:
        ok = False
        print("汽车之家价格抓取失败，保留旧文件:", e)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
