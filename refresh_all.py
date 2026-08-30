# -*- coding: utf-8 -*-
"""统一刷新脚本：抓取 C-IASI + 中汽测评四体系 + 汽车之家价格，再合并生成 ratings_all.json。
供 GitHub Actions 每日运行。任一步失败都保留已有文件，保证最终 build 不中断。
"""
import os, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


def run(py):
    r = subprocess.run([sys.executable, os.path.join(HERE, py)], cwd=HERE)
    return r.returncode == 0


def main():
    # 1) 中保研 C-IASI（fetch_ciasi.py 写 ciasi_ratings.json）
    if not run("fetch_ciasi.py"):
        print("⚠ C-IASI 抓取失败，使用已有 ciasi_ratings.json")
    # 2) 中汽测评 + 价格
    if not run("fetch_cncap_prices.py"):
        print("⚠ 中汽测评/价格抓取失败，使用已有缓存")
    # 3) 合并生成 ratings_all.json
    ok = run("build_ratings_all.py")
    print("✅ ratings_all.json 刷新完成" if ok else "❌ build 失败")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
