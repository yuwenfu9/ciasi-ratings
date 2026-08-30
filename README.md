# 中保研 C-IASI 汽车安全评级 · 公开数据 API

自动抓取[中保研官网](https://ciasi.org.cn/products/list-492.html)的车型安全评级，整理成结构化数据，并通过 [jsDelivr](https://www.jsdelivr.com/) 提供**免费、公开、带 CORS 的只读数据接口**。

> 数据来自中保研（C-IASI）官方公开发布，本仓库仅做整理与转发，**非官方**，评级以官网为准。

## 公开接口

```
GET https://cdn.jsdelivr.net/gh/yuwenfu9/ciasi-ratings@main/ciasi_ratings.json
```

- 全球 CDN 加速，响应头含 `access-control-allow-origin: *`，浏览器 / 任意客户端可直接 `fetch`。
- 每周日（北京时间 09:17）由 GitHub Actions 自动重抓并提交，数据自动更新（jsDelivr CDN 缓存约 12 小时，新数据通常在数小时内生效）。
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
python fetch_ciasi.py        # 输出 ciasi_ratings.json + ciasi_ratings.csv
```

依赖仅 Python 标准库（`urllib` / `csv` / `json`），无需安装第三方包。

## 文件

- `fetch_ciasi.py` — 抓取与解析脚本（把官网评级图标映射为 G+/G/A/M/P 文字）
- `ciasi_ratings.json` — 结构化数据（本 API 的载体）
- `ciasi_ratings.csv` — 同一数据的表格版
- `.github/workflows/update.yml` — 每周自动更新

## 免责声明

本仓库与中保研（C-IASI）无任何隶属关系。数据用于研究与个人参考，不构成任何购买或投资建议。
