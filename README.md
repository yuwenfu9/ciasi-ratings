# 汽车安全测评 · 公开数据 API（中保研 C-IASI + 中汽测评四体系）

自动抓取[中保研官网](https://ciasi.org.cn/products/list-492.html)与[中汽测评](https://www.c-ncap.org.cn/)（C-NCAP / CCRT / C-ICAP / C-GCAP）的车型安全评级，整理成结构化数据，并通过 [jsDelivr](https://www.jsdelivr.com/) 提供**免费、公开、带 CORS 的只读数据接口**。

> 数据来自官方公开发布，本仓库仅做整理与转发，**非官方**，评级以官网为准。
> 各机构评级刻度不可通约（C-IASI 等级制 / C-NCAP 百分制 / CCRT 百分制 / 其余仅状态），**跨机构不折算、不求平均**；但每家机构自己的综合分（C-IASI 综合安全分、C-NCAP/CCRT 百分制综合）会在卡片与表格中展示并可用于排序。C-ICAP / C-GCAP 官方列表接口仅返回"已测评"状态、不含分数，故只标"已测评"（详情页为 JS 渲染，公开接口无法抓取，未硬凑）。

## 公开接口

```
GET https://cdn.jsdelivr.net/gh/yuwenfu9/ciasi-ratings@main/ciasi_ratings.json
```

- 全球 CDN 加速，响应头含 `access-control-allow-origin: *`，浏览器 / 任意客户端可直接 `fetch`。
- 每天（北京时间 09:17）由 GitHub Actions 自动重抓并提交，数据自动更新（jsDelivr CDN 缓存约 12 小时，新数据通常在数小时内生效）。
- 也可访问带版本标签的永久地址，例如 `@latest` 或某次 commit。

返回结构：

```json
{
  "metadata": {
    "generated_at": "2026-08-30T16:00:00+08:00",
    "source_url": "https://ciasi.org.cn/get_products_list.html?...",
    "record_count": 188,
    "grade_map": { "/assets/img/car/level1/1.png": "G+" }
  },
  "records": [
    {
      "year": "2025",
      "brand": "长安",
      "model": "深蓝S09",
      "model_number": "SC6522AAA6HEV",
      "segment": "SUV",
      "manufacturer": "重庆长安汽车股份有限公司",
      "repairability": "A",
      "occupant": "G+",
      "pedestrian": "G+",
      "assist": "G",
      "nev_special": "G*",
      "detail_url": "/products/show-983.html",
      "source": "https://ciasi.org.cn/products/show-983.html"
    }
  ]
}
```

### 字段说明

| 字段 | 含义 |
|---|---|
| `year` | 测评年份 |
| `brand` / `model` | 品牌 / 车型 |
| `model_number` | 车辆型号（公告型号） |
| `segment` | 级别（SUV / 轿车 / MPV …） |
| `manufacturer` | 生产厂家 |
| `occupant` | 车内乘员安全（G+ / G / A / M / P） |
| `pedestrian` | 车外行人安全 |
| `assist` | 辅助安全 |
| `repairability` | 耐撞性与维修经济性 |
| `nev_special` | 新能源汽车专项（带 `*` 表示新能源专项项） |
| `source` | 该车型中保研官方详情页链接 |

评级等级：`G+` 优秀⁺ · `G` 优秀 · `A` 良好 · `M` 一般 · `P` 较差。

## 多机构合并接口（推荐）

```
GET https://cdn.jsdelivr.net/gh/yuwenfu9/ciasi-ratings@main/ratings_all.json
```

单文件聚合五套体系（C-IASI / C-NCAP / CCRT / C-ICAP / C-GCAP），按机构分命名空间，**各自保留原始字段与原始刻度，不折算、不合并**。每条记录另附汽车之家厂商指导价快照（`msrp_guide`，无价则为 `null`）。

返回结构：

```json
{
  "metadata": {
    "generated_at": "2026-08-30T18:00:00+08:00",
    "price_fetched_at": "2026-08-30",
    "record_counts": { "c_iasi": 188, "c_ncap": 600, "ccrt": 136, "c_icap": 25, "c_gcap": 38 },
    "price_note": "指导价仅为厂商指导价时点快照，非成交价；约 70% 测试车型因停售/换代/待上市无价。",
    "score_note": "各机构评级刻度不可通约，仅并列展示。"
  },
  "orgs": {
    "c_iasi": [ { "brand":"长安", "model":"深蓝S09", "year":"2025", "occupant":"G+",
                 "pedestrian":"G+", "assist":"G", "repairability":"A", "nev_special":"G*",
                 "detail_url":"https://ciasi.org.cn/products/show-983.html",
                 "msrp_guide": {"low":23.99,"high":30.99,"text":"23.99-30.99万","source":"autohome","fetched_at":"2026-08-30"} } ],
    "c_ncap": [ { "carName":"红旗HS6", "brand":"中国第一汽车集团有限公司", "year":"2026",
                 "score":"85.4%", "targets":{"乘员保护":"87.26%","行人保护/VRU保护":"81.01%","主动安全":"85.76%"},
                 "evaluationId":"7199cbd4...", "detail_url":"https://www.c-ncap.org.cn/evaluation/7199cbd4...",
                 "msrp_guide": null } ],
    "ccrt": [...], "c_icap": [...], "c_gcap": [...]
  }
}
```

- `orgs.c_iasi[].occupant/pedestrian/assist/repairability` 为等级制（`G+`/`G`/`A`/`M`/`P`）。
- `orgs.c_ncap[].score` 为百分制综合分，`targets` 含乘员保护 / 行人保护 / 主动安全子项。
- `orgs.ccrt / c_icap / c_gcap` 列表接口仅返回测评状态与年份（无数值子项），详细评级见各记录 `detail_url`。

## 调用示例

```bash
# curl
curl -s "https://cdn.jsdelivr.net/gh/yuwenfu9/ciasi-ratings@main/ciasi_ratings.json" | head
```

```js
// 浏览器 / Node fetch
const res = await fetch("https://cdn.jsdelivr.net/gh/yuwenfu9/ciasi-ratings@main/ciasi_ratings.json");
const { records } = await res.json();
// 按综合安全分（示例：乘员50% + 行人25% + 辅助25%，折算百分制）
const S = { "G+": 5, G: 4, A: 3, M: 2, P: 1 };
const score = r => {
  const dims = ["occupant","pedestrian","assist"].map(k => S[r[k]] ?? 0);
  return (dims.reduce((a,b)=>a+b,0) / dims.length) / 5 * 100;
};
records.sort((a,b)=>score(b)-score(a));
```

```python
import json, urllib.request
data = json.load(urllib.request.urlopen(
    "https://cdn.jsdelivr.net/gh/yuwenfu9/ciasi-ratings@main/ciasi_ratings.json"))
print(len(data["records"]), "款车型")
```

## 本地抓取

```bash
python refresh_all.py        # 抓取 C-IASI + 中汽测评四体系 + 汽车之家价格，合并输出 ratings_all.json
python fetch_ciasi.py        # 仅抓取中保研，输出 ciasi_ratings.json + ciasi_ratings.csv
```

依赖仅 Python 标准库（`urllib` / `csv` / `json`），无需安装第三方包。

## 文件

- `fetch_ciasi.py` — 中保研抓取与解析脚本（把官网评级图标映射为 G+/G/A/M/P 文字）
- `feasibility.py` — 中汽测评 / 汽车之家抓取与车型名匹配（被下方脚本复用）
- `fetch_cncap_prices.py` — 抓取中汽测评四体系 + 汽车之家指导价
- `build_ratings_all.py` — 合并五体系 + 价格，生成 `ratings_all.json`
- `refresh_all.py` — 一键统一刷新（抓取 + 合并）
- `ciasi_ratings.json` — 中保研结构化数据（单机构，兼容旧调用方）
- `ciasi_ratings.csv` — 中保研数据表格版
- `ratings_all.json` — 多机构合并数据（推荐接口载体）
- `cncap_all.json` / `prices.json` — 中汽测评 / 价格中间数据
- `.github/workflows/update.yml` — 每天自动更新

## 免责声明

本仓库与中保研（C-IASI）、中汽测评（C-NCAP/CCRT/C-ICAP/C-GCAP）无任何隶属关系。数据用于研究与个人参考，不构成任何购买或投资建议。
