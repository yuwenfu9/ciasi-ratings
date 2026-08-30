#!/usr/bin/env python3
"""
中保研 C-IASI 评级数据抓取器
- 数据来源：https://ciasi.org.cn/products/list-492.html
- 接口：https://ciasi.org.cn/get_products_list.html?year_id=0&rule_id=0&brand_id=0
- 输出：ciasi_ratings.json / ciasi_ratings.csv
"""
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

# 评级图片文件名 → 等级文字映射
# 官网把等级做成了小图标，level1/N.png 是新版，levelold/X.png 是旧版，G.png 用于新能源专项
GRADE_MAP = {
    "/assets/img/car/level1/1.png": "G+",
    "/assets/img/car/level1/2.png": "G",
    "/assets/img/car/level1/3.png": "A",
    "/assets/img/car/level1/4.png": "M",
    "/assets/img/car/level1/5.png": "P",
    "/assets/img/car/levelold/G.png": "G",
    "/assets/img/car/levelold/A.png": "A",
    "/assets/img/car/levelold/M.png": "M",
    "/assets/img/car/levelold/P.png": "P",
    "/assets/img/car/G.png": "G",
}

API_URL = "https://ciasi.org.cn/get_products_list.html?year_id=0&rule_id=0&brand_id=0"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://ciasi.org.cn/products/list-492.html",
}


def strip_html(raw: str) -> str:
    """去掉 HTML 标签并压缩空白。"""
    text = re.sub(r"<[^>]+>", "", raw)
    text = re.sub(r"&nbsp;|\s+", " ", text)
    return text.strip()


def extract_grade(cell_html: str) -> str:
    """从单元格里的图片推导出等级，未知图片保留文件名。"""
    cell_html = cell_html.strip()
    if not cell_html:
        return "—"

    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', cell_html)
    grade = None
    if img_match:
        src = img_match.group(1)
        grade = GRADE_MAP.get(src)
        if grade is None:
            # 未知图片：保留路径最后一段，方便人工核对
            grade = f"img:{Path(src).name}"

    if grade is None:
        # 没有图片时看有没有纯文字
        text = strip_html(cell_html)
        grade = text if text else "—"

    # 新能源专项的 * 标记
    if re.search(r'<span[^>]*ev_i_bs_[^>]*>\s*\*\s*</span>', cell_html):
        grade += "*"

    return grade


def extract_detail_url(row_html: str) -> str:
    """提取车型详情页相对链接（官网用 <a href="/products/show-NNN.html">）。"""
    m = re.search(r'<a[^>]+href=["\']([^"\']+)["\']', row_html)
    return m.group(1) if m else ""


def parse_views(views_html: str) -> list[dict]:
    """解析 API 返回的 views HTML，得到所有评级记录。"""
    records = []

    # 每个年份一个 tableTit + table 块
    blocks = list(
        re.finditer(
            r'<div class="tableTit">(.*?)</div>\s*<table[^>]*>(.*?)</table>',
            views_html,
            re.S | re.I,
        )
    )
    if not blocks:
        raise ValueError("未找到任何年份表格块")

    for block in blocks:
        year_text = strip_html(block.group(1))
        year_match = re.search(r"\d{4}", year_text)
        year = year_match.group(0) if year_match else ""

        table_html = block.group(2)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.S | re.I)

        for row in rows:
            # 跳过头行（<th>）和空行
            if not re.search(r"<td", row):
                continue

            cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)
            if len(cells) < 11:
                # 保险：有时单元格里可能嵌套了 td，这种情况极少
                continue

            detail_url = extract_detail_url(row)
            record = {
                "year": year,
                "index": strip_html(cells[0]),
                "brand": strip_html(cells[1]),
                "model": strip_html(cells[2]),
                "model_number": strip_html(cells[3]),
                "segment": strip_html(cells[4]),
                "manufacturer": strip_html(cells[5]),
                "repairability": extract_grade(cells[6]),
                "occupant": extract_grade(cells[7]),
                "pedestrian": extract_grade(cells[8]),
                "assist": extract_grade(cells[9]),
                "nev_special": extract_grade(cells[10]),
                "detail_url": detail_url,
                "source": f"https://ciasi.org.cn{detail_url}" if detail_url else "",
            }
            records.append(record)

    return records


def fetch_json() -> dict:
    """调用 C-IASI 数据接口并返回 JSON。"""
    req = Request(API_URL, headers=HEADERS)
    with urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data


def save_outputs(records: list[dict], output_dir: Path) -> None:
    """保存 JSON + CSV，并附带元数据。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        "source_url": API_URL,
        "record_count": len(records),
        "grade_map": GRADE_MAP,
        "note": "grade 图片来自 /assets/img/car/level1/N.png 或 levelold/X.png，已映射为 G+/G/A/M/P",
    }

    json_path = output_dir / "ciasi_ratings.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {"metadata": metadata, "records": records},
            f,
            ensure_ascii=False,
            indent=2,
        )

    csv_path = output_dir / "ciasi_ratings.csv"
    if records:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)

    print(f"已保存 {len(records)} 条记录")
    print(f"  JSON: {json_path}")
    print(f"  CSV : {csv_path}")


def main() -> int:
    out_dir = Path(__file__).parent
    print(f"抓取中：{API_URL}")
    try:
        payload = fetch_json()
        views = payload.get("data", {}).get("views")
        if not views:
            print("错误：接口未返回 data.views", file=sys.stderr)
            return 1
        records = parse_views(views)
        save_outputs(records, out_dir)
        return 0
    except Exception as e:
        print(f"抓取失败：{e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
