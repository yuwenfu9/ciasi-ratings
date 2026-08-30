# -*- coding: utf-8 -*-
"""生成多机构切换版仪表盘 dashboard.html。

特性（来自用户决策）：
- 顶部机构切换 Tab：中保研 C-IASI / C-NCAP / CCRT / C-ICAP / C-GCAP，不合并、只切换
- 搜索：当前机构无结果时，跨机构推荐（点一下跳到那家）
- 往年车型改表格：点车型弹出多期表格（一年一行），去掉折线图
- 价格：仅显示在售车型（有 msrp_guide），附「仅看在售」筛选开关
数据注入 ratings_all.json（内嵌兜底 + jsDelivr 拉取最新）。
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "ratings_all.json"), encoding="utf-8"))

TPL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>汽车安全测评 · 多机构切换台</title>
<style>
  :root{
    --bg:#f5f6f8; --card:#ffffff; --ink:#1c2430; --sub:#67707d; --line:#e6e9ee;
    --brand:#2b6cf0; --brand-d:#1d54c4;
    --gp:#15803d; --gp-bg:#dcfce7;
    --g:#22a05a; --g-bg:#e3f7ea;
    --a:#2563eb; --a-bg:#e3edfd;
    --m:#d97706; --m-bg:#fdeccb;
    --p:#dc2626; --p-bg:#fde3e3;
    --none-bg:#eef0f3; --none:#9aa3af;
  }
  *{box-sizing:border-box;-webkit-tap-highlight-color:transparent;}
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
    background:var(--bg);color:var(--ink);font-size:15px;line-height:1.5;padding-bottom:80px;}
  .wrap{max-width:1100px;margin:0 auto;padding:14px 14px 0;}
  header h1{font-size:20px;margin:6px 0 2px;}
  header p{margin:0;color:var(--sub);font-size:13px;}
  .tag{display:inline-block;font-size:12px;color:var(--brand-d);background:#e8f0fe;border-radius:6px;padding:1px 8px;margin-right:6px;}
  .srcline{display:none;font-size:12px;color:var(--good,#15803d);background:#e7f7ec;border-radius:6px;padding:1px 8px;margin-left:4px;}
  .srcline.bad{color:var(--p);background:var(--p-bg);}

  /* 机构切换 Tab */
  .orgtabs{display:flex;gap:6px;overflow-x:auto;margin:12px 0 6px;padding-bottom:4px;-webkit-overflow-scrolling:touch;}
  .orgtab{flex:0 0 auto;border:1px solid var(--line);background:#fff;color:var(--sub);
    padding:8px 14px;border-radius:999px;font-size:13px;cursor:pointer;white-space:nowrap;font-weight:600;}
  .orgtab .ct{font-size:11px;color:var(--none);margin-left:5px;font-weight:400;}
  .orgtab.on{background:var(--brand);color:#fff;border-color:var(--brand);}
  .orgtab.on .ct{color:#dbe7ff;}

  .stat{font-size:12px;color:var(--sub);margin:2px 2px 8px;}

  .controls{position:sticky;top:0;z-index:5;background:var(--bg);padding:8px 0 10px;border-bottom:1px solid var(--line);}
  .row1{display:flex;gap:8px;flex-wrap:wrap;align-items:center;}
  .search{flex:1 1 200px;min-width:160px;padding:9px 11px;border:1px solid var(--line);border-radius:9px;font-size:14px;}
  .sel{padding:9px 10px;border:1px solid var(--line);border-radius:9px;background:#fff;font-size:13px;color:var(--ink);}
  .row2{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:8px;}
  .chk{display:inline-flex;align-items:center;gap:6px;font-size:13px;color:var(--ink);
    border:1px solid var(--line);border-radius:9px;padding:8px 11px;background:#fff;cursor:pointer;user-select:none;}
  .chk input{width:16px;height:16px;accent-color:var(--brand);}
  .view-toggle{margin-left:auto;display:flex;border:1px solid var(--line);border-radius:9px;overflow:hidden;}
  .view-toggle button{border:0;background:#fff;padding:8px 12px;font-size:13px;cursor:pointer;color:var(--sub);}
  .view-toggle button.on{background:var(--brand);color:#fff;}
  .order-btn{padding:9px 11px;border:1px solid var(--line);border-radius:9px;background:#fff;cursor:pointer;font-size:13px;}

  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px;margin-top:10px;}
  .vcard{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:11px 12px;cursor:pointer;transition:box-shadow .12s;}
  .vcard:active{box-shadow:0 2px 10px rgba(0,0,0,.08);}
  .vcard .nm{font-weight:700;font-size:15px;display:flex;justify-content:space-between;align-items:baseline;gap:6px;}
  .vcard .yr{font-size:12px;color:var(--sub);font-weight:400;}
  .vcard .dims{display:flex;flex-wrap:wrap;align-items:center;gap:5px;margin-top:8px;}
  .vcard .dim{display:inline-flex;align-items:center;gap:4px;background:#f4f6f9;border-radius:6px;padding:2px 6px;}
  .vcard .diml{font-size:11px;color:var(--sub);font-weight:600;}
  .vcard .pr{margin-top:8px;font-size:13px;}
  .vcard .pr.has{color:var(--gp);font-weight:600;}
  .vcard .pr.none{color:var(--none);}
  .vcard .src{margin-top:7px;font-size:12px;}
  .vcard .src a{color:var(--brand-d);text-decoration:none;}

  .table-wrap{overflow-x:auto;overscroll-behavior-x:contain;margin-top:10px;border:1px solid var(--line);border-radius:12px;background:#fff;}
  table{border-collapse:collapse;width:100%;font-size:13px;min-width:680px;}
  th,td{padding:9px 10px;text-align:center;border-bottom:1px solid var(--line);white-space:nowrap;}
  th{background:#fafbfc;position:sticky;top:0;font-weight:600;color:var(--sub);}
  td.nm,th.nm{text-align:left;}
  td a{color:var(--brand-d);text-decoration:none;}

  .badge{display:inline-block;min-width:26px;padding:2px 7px;border-radius:6px;font-size:12px;font-weight:700;}
  .b-gp{color:var(--gp);background:var(--gp-bg);} .b-g{color:var(--g);background:var(--g-bg);}
  .b-a{color:var(--a);background:var(--a-bg);} .b-m{color:var(--m);background:var(--m-bg);}
  .b-p{color:var(--p);background:var(--p-bg);} .b-none{color:var(--none);background:var(--none-bg);}
  .pct{font-weight:700;color:var(--ink);}
  .pctpill{display:inline-block;min-width:30px;padding:2px 7px;border-radius:6px;font-size:12px;font-weight:700;text-align:center;}
  .pctpill.bold{font-size:13px;min-width:42px;}
  .pct-gp{color:var(--gp);background:var(--gp-bg);}
  .pct-g{color:var(--g);background:var(--g-bg);}
  .pct-m{color:var(--m);background:var(--m-bg);}
  .pct-p{color:var(--p);background:var(--p-bg);}
  .nev{display:inline-block;font-size:11px;color:#0891b2;background:#cffafe;border-radius:5px;padding:1px 6px;margin-left:5px;}

  .recos{margin-top:12px;}
  .recot{font-size:13px;color:var(--sub);margin-bottom:8px;}
  .recochip{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--brand);color:var(--brand-d);
    background:#eef4ff;border-radius:999px;padding:8px 14px;margin:0 8px 8px 0;cursor:pointer;font-size:13px;font-weight:600;}
  .recochip .n{background:var(--brand);color:#fff;border-radius:999px;padding:0 7px;font-size:11px;}

  .empty{text-align:center;color:var(--sub);padding:40px 16px;}
  .empty .e{font-size:16px;color:var(--ink);margin-bottom:6px;}

  /* 详情弹窗：多期表格 */
  .modal{display:none;position:fixed;inset:0;background:rgba(15,23,42,.45);z-index:30;padding:18px;}
  .modal .box{background:#fff;border-radius:14px;max-width:760px;margin:5vh auto 0;max-height:86vh;overflow:auto;padding:16px 16px 18px;}
  .modal .hd{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;}
  .modal .hd b{font-size:17px;}
  .modal .x{font-size:20px;color:var(--sub);cursor:pointer;line-height:1;padding:2px 6px;}
  .modal .meta{font-size:12px;color:var(--sub);margin:4px 0 10px;}
  .modal .note{font-size:12px;color:var(--m);background:var(--m-bg);border-radius:8px;padding:7px 10px;margin:8px 0;}
  .mtab{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px;}
  .mtab th,.mtab td{padding:8px 9px;text-align:center;border-bottom:1px solid var(--line);white-space:nowrap;}
  .mtab th{background:#fafbfc;color:var(--sub);font-weight:600;}
  .mtab td.nm{text-align:left;}
  .modal .acts{margin-top:12px;display:flex;gap:10px;flex-wrap:wrap;}
  .modal .acts a{color:#fff;background:var(--brand);text-decoration:none;padding:8px 14px;border-radius:9px;font-size:13px;}
  .modal .price{margin-top:10px;font-size:14px;}
  .modal .price.has{color:var(--gp);font-weight:700;}
  .modal .price.none{color:var(--none);}
  .legend{font-size:11px;color:var(--none);margin-top:6px;}
  @media(max-width:560px){
    .grid{grid-template-columns:1fr;}
    header h1{font-size:18px;}
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>汽车安全测评 · 多机构切换台</h1>
    <p><span class="tag">买车看安全</span>中保研 / 中汽测评 五套体系 · 不合并只切换<span class="srcline" id="srcline">内嵌</span></p>
  </header>

  <div class="orgtabs" id="orgtabs"></div>
  <div class="stat" id="stat"></div>

  <div class="controls">
    <div class="row1">
      <input class="search" id="q" placeholder="搜索车型 / 品牌，如 智界S7、Model 3">
      <select class="sel" id="seg"></select>
      <select class="sel" id="brand"></select>
      <select class="sel" id="year"></select>
    </div>
    <div class="row2">
      <label class="chk"><input type="checkbox" id="inprod">仅看在售（有指导价）</label>
      <select class="sel" id="sort"></select>
      <button class="order-btn" id="ord">降序 ↓</button>
      <div class="view-toggle">
        <button id="vc" class="on">卡片</button>
        <button id="vt">表格</button>
      </div>
    </div>
  </div>

  <div class="grid" id="grid"></div>
  <div class="table-wrap" id="twrap" style="display:none"></div>
  <div class="recos" id="recos"></div>
  <div id="empty"></div>
</div>

<div class="modal" id="detail"><div class="box"><div id="dbody"></div></div></div>

<script>
const DATA = __DATA__;
const API_URL = "https://cdn.jsdelivr.net/gh/yuwenfu9/ciasi-ratings@main/ratings_all.json";

/* 各机构配置：只保留各自原始刻度，不折算 */
const ORG_CFG = {
  c_iasi:{ label:"中保研 C-IASI", short:"C-IASI", color:"#2b6cf0",
    name:r=>r.brand+" "+r.model, key:r=>r.brand+" "+r.model, brand:r=>r.brand, year:r=>r.year,
    dims:[{k:"__ciasi__",l:"综合安全分",t:"ciasi",bold:true},
          {k:"occupant",l:"乘员",t:"grade"},{k:"pedestrian",l:"行人",t:"grade"},
          {k:"assist",l:"辅助",t:"grade"},{k:"repairability",l:"维修经济",t:"grade"}],
    scoreKind:"ciasi", detail:r=>r.detail_url, nev:r=>r.nev_special },
  c_ncap:{ label:"C-NCAP", short:"C-NCAP", color:"#e0532a",
    name:r=>r.carName, key:r=>r.carName, brand:r=>r.brand, year:r=>r.year,
    dims:[{k:"score",l:"综合",t:"pct",bold:true},
          {k:"targets.乘员保护",l:"乘员保护",t:"pct"},
          {k:"targets.行人保护/VRU保护",l:"行人保护",t:"pct"},
          {k:"targets.主动安全",l:"主动安全",t:"pct"}],
    scoreKind:"pct", detail:r=>r.detail_url },
  ccrt:{ label:"CCRT", short:"CCRT", color:"#7c3aed",
    name:r=>r.carName, key:r=>r.carName, brand:r=>r.brand, year:r=>r.year,
    dims:[{k:"score",l:"综合",t:"pct",bold:true}], scoreKind:"pct", detail:r=>r.detail_url },
  c_icap:{ label:"C-ICAP", short:"C-ICAP", color:"#0d9488",
    name:r=>r.carName, key:r=>r.carName, brand:r=>r.brand, year:r=>r.year,
    dims:[], note:"C-ICAP 列表接口仅含测评状态，详细评级请见官方详情页。", scoreKind:"none", detail:r=>r.detail_url },
  c_gcap:{ label:"C-GCAP", short:"C-GCAP", color:"#16a34a",
    name:r=>r.carName, key:r=>r.carName, brand:r=>r.brand, year:r=>r.year,
    dims:[], note:"C-GCAP 列表接口仅含测评状态，详细评级请见官方详情页。", scoreKind:"none", detail:r=>r.detail_url },
};
const ORG_ORDER = ["c_iasi","c_ncap","ccrt","c_icap","c_gcap"];

const GRADE = {"G+":["G+","b-gp"],"G":["G","b-g"],"A":["A","b-a"],"M":["M","b-m"],"P":["P","b-p"]};
const GN = {"G+":5,"G":4,"A":3,"M":2,"P":1};

let state = { org:"c_iasi", q:"", seg:"", brand:"", year:"", inprod:false, sort:"model", ord:"asc", view:"card" };

function norm(s){return (s||"").toLowerCase().replace(/\s+/g,"");}
function getVal(r,path){return path.split(".").reduce((o,k)=> (o==null?null:o[k]), r);}
function gradeBadge(g){
  if(!g) return '<span class="badge b-none">—</span>';
  const m=GRADE[g]; return m? '<span class="badge '+m[1]+'">'+m[0]+'</span>' : '<span class="badge b-none">'+g+'</span>';
}
/* 分数配色：越高越绿（安全），越低越红。用于 C-NCAP / CCRT / 综合安全分 */
function pctClass(v){ if(v>=90)return 'pct-gp'; if(v>=80)return 'pct-g'; if(v>=70)return 'pct-m'; return 'pct-p'; }
function pctPill(v, bold){
  const n=parseFloat(v);
  if(isNaN(n)) return '<span class="badge b-none">—</span>';
  return '<span class="pctpill '+pctClass(n)+(bold?' bold':'')+'">'+v+'</span>';
}
function pctCell(v){ return v? pctPill(v,false) : '<span class="badge b-none">—</span>'; }
function dimCell(r,d){
  if(d.t==="grade") return gradeBadge(getVal(r,d.k));
  if(d.t==="ciasi"){ const v=ciasiScore(r); return v? pctPill(v,true) : '<span class="badge b-none">—</span>'; }
  return pctCell(getVal(r,d.k));
}
function priceHtml(r){
  const p=r.msrp_guide;
  if(p) return '<span class="pr has">指导价 '+p.text+'</span>';
  return '<span class="pr none">暂无报价</span>';
}
function ciasiScore(r){
  const a=GN[r.occupant]||0,b=GN[r.pedestrian]||0,c=GN[r.assist]||0;
  if(!a&&!b&&!c) return 0;
  return Math.round((a*0.5+b*0.25+c*0.25)/5*100);
}
function sortVal(r){
  const cfg=ORG_CFG[state.org];
  if(state.sort==="model") return norm(cfg.name(r));
  if(state.sort==="year") return parseInt(cfg.year(r)||"0",10);
  if(state.sort==="price"){ const p=r.msrp_guide; return p? ((p.low+p.high)/2): 1e9; }
  if(state.sort==="score"){
    if(cfg.scoreKind==="ciasi") return ciasiScore(r);
    if(cfg.scoreKind==="pct"){ const s=getVal(r,"score"); return (s!=null&&s!=="")? parseFloat(String(s).replace("%","")) : -1e9; }
  }
  return norm(cfg.name(r));
}

function curRecs(){ return (DATA.orgs[state.org]||[]).slice(); }
function searchHits(org, qn){
  const cfg=ORG_CFG[org]; const out=[];
  (DATA.orgs[org]||[]).forEach(r=>{ if(norm(cfg.name(r)).includes(qn)||norm(cfg.brand(r)).includes(qn)) out.push(r); });
  return out;
}

function renderTabs(){
  const el=document.getElementById("orgtabs"); el.innerHTML="";
  ORG_ORDER.forEach(o=>{
    const cfg=ORG_CFG[o]; const n=(DATA.orgs[o]||[]).length;
    const b=document.createElement("div");
    b.className="orgtab"+(o===state.org?" on":"");
    b.innerHTML=cfg.label+'<span class="ct">'+n+'</span>';
    b.onclick=()=>switchOrg(o);
    el.appendChild(b);
  });
}
function buildFilters(){
  const recs=curRecs(); const cfg=ORG_CFG[state.org];
  const seg=document.getElementById("seg");
  if(state.org==="c_iasi"){
    seg.style.display=""; const segs=[...new Set(recs.map(r=>r.segment).filter(Boolean))].sort();
    seg.innerHTML='<option value="">全部级别</option>'+segs.map(s=>'<option>'+s+'</option>').join("");
  } else { seg.style.display="none"; seg.innerHTML='<option value=""></option>'; }
  const br=document.getElementById("brand");
  const brands=[...new Set(recs.map(r=>cfg.brand(r)).filter(Boolean))].sort();
  br.innerHTML='<option value="">全部品牌</option>'+brands.map(b=>'<option>'+b+'</option>').join("");
  const yr=document.getElementById("year");
  const years=[...new Set(recs.map(r=>cfg.year(r)).filter(Boolean))].sort().reverse();
  yr.innerHTML='<option value="">全部年份</option>'+years.map(y=>'<option>'+y+'</option>').join("");
  const so=document.getElementById("sort");
  let opts='<option value="model">车型名</option><option value="year">年份</option><option value="price">指导价</option>';
  const hasScore=(cfg.scoreKind==="ciasi"||cfg.scoreKind==="pct");
  if(hasScore) opts+='<option value="score">'+(cfg.scoreKind==="ciasi"?"综合安全分":"综合分")+'</option>';
  // 切到没有「综合分」的机构时，若之前选了 score 则回退到车型名
  if((state.sort==="score"&&!hasScore) || !["model","year","price","score"].includes(state.sort)) state.sort="model";
  so.innerHTML=opts; so.value=state.sort;
}

function filtered(){
  const cfg=ORG_CFG[state.org]; const qn=norm(state.q);
  let a=curRecs();
  if(qn) a=a.filter(r=>norm(cfg.name(r)).includes(qn)||norm(cfg.brand(r)).includes(qn));
  if(state.seg) a=a.filter(r=>r.segment===state.seg);
  if(state.brand) a=a.filter(r=>cfg.brand(r)===state.brand);
  if(state.year) a=a.filter(r=>cfg.year(r)===state.year);
  if(state.inprod) a=a.filter(r=>r.msrp_guide);
  a.sort((x,y)=>{ const s=sortVal(x),t=sortVal(y);
    if(s<t)return state.ord==="asc"?-1:1; if(s>t)return state.ord==="asc"?1:-1; return 0; });
  return a;
}

function cardHTML(r){
  const cfg=ORG_CFG[state.org];
  let dims="";
  if(cfg.dims.length){
    dims='<div class="dims">'+cfg.dims.map(d=> '<span class="dim"><span class="diml">'+d.l+'</span>'+dimCell(r,d)+'</span>').join("")+'</div>';
  } else {
    dims='<div class="dims"><span class="badge b-g">已测评</span></div>';
  }
  let nev=""; if(cfg.nev && r.nev_special) nev='<span class="nev">新能源 '+r.nev_special.replace("*","")+'</span>';
  let src=""; if(cfg.detail(r)) src='<div class="src"><a href="'+cfg.detail(r)+'" target="_blank" rel="noopener" onclick="event.stopPropagation()">官方详情 ↗</a></div>';
  return '<div class="vcard" onclick="openDetail(\''+state.org+'\',\''+cssEsc(cfg.key(r))+'\')">'
    +'<div class="nm"><span>'+cfg.name(r)+nev+'</span><span class="yr">'+cfg.year(r)+'</span></div>'
    +dims+priceHtml(r)+src+'</div>';
}
function cssEsc(s){return (s||"").replace(/'/g,"\\'");}

function renderGrid(a){
  const g=document.getElementById("grid");
  g.style.display="grid"; document.getElementById("twrap").style.display="none";
  document.getElementById("recos").innerHTML=""; document.getElementById("empty").innerHTML="";
  g.innerHTML=a.map(cardHTML).join("");
}
function tableHead(){
  const cfg=ORG_CFG[state.org];
  let h='<th class="nm">车型</th><th>年份</th>';
  cfg.dims.forEach(d=>h+='<th>'+d.l+'</th>');
  h+='<th>指导价</th><th>官方</th>';
  return '<tr>'+h+'</tr>';
}
function tableRow(r){
  const cfg=ORG_CFG[state.org];
  let c='<td class="nm">'+cfg.name(r)+'</td><td>'+cfg.year(r)+'</td>';
  if(cfg.dims.length){
    c+=cfg.dims.map(d=>'<td>'+(d.t==="grade"?gradeBadge(getVal(r,d.k)):pctCell(getVal(r,d.k)))+'</td>').join("");
  } else { c+='<td><span class="badge b-g">已测评</span></td>'; }
  c+='<td>'+(r.msrp_guide?r.msrp_guide.text:'<span class="badge b-none">暂无</span>')+'</td>';
  c+='<td>'+(cfg.detail(r)?'<a href="'+cfg.detail(r)+'" target="_blank" rel="noopener">↗</a>':'—')+'</td>';
  return '<tr onclick="openDetail(\''+state.org+'\',\''+cssEsc(cfg.key(r))+'\')" style="cursor:pointer">'+c+'</tr>';
}
function renderTable(a){
  const tw=document.getElementById("twrap"); document.getElementById("grid").style.display="none"; tw.style.display="block";
  document.getElementById("recos").innerHTML=""; document.getElementById("empty").innerHTML="";
  tw.innerHTML='<table>'+tableHead()+a.map(tableRow).join("")+'</table>';
}

function showEmpty(){
  document.getElementById("grid").style.display="none"; document.getElementById("twrap").style.display="none";
  const q=state.q.trim(); const em=document.getElementById("empty");
  if(q){
    const qn=norm(q); const recos=[];
    ORG_ORDER.forEach(o=>{ if(o===state.org)return;
      const hits=searchHits(o,qn); if(!hits.length)return;
      const models=new Set(hits.map(r=>ORG_CFG[o].key(r)));
      recos.push('<div class="recochip" onclick="jumpOrg(\''+o+'\')">在 '+ORG_CFG[o].short+' 找到 <span class="n">'+models.size+'</span> 款 · 点此切换</div>');
    });
    if(recos.length){
      em.innerHTML='<div class="recos"><div class="recot">「'+q.replace(/</g,"&lt;")+'」在 '+ORG_CFG[state.org].short+' 暂无结果，但其它机构测过：</div>'+recos.join("")+'</div>';
      document.getElementById("recos").innerHTML=""; return;
    }
    em.innerHTML='<div class="empty"><div class="e">未找到「'+q.replace(/</g,"&lt;")+'」</div><div>当前机构（'+ORG_CFG[state.org].short+'）未收录该车型。可切换上方其它机构标签查看，或调整筛选条件。</div></div>';
  } else {
    em.innerHTML='<div class="empty"><div class="e">没有符合条件的车型</div><div>请调整筛选条件（级别 / 品牌 / 年份 / 仅看在售）。</div></div>';
  }
}
function switchOrg(o){
  if(o===state.org){ const t=document.getElementById("orgtabs"); if(t)t.scrollIntoView({behavior:"smooth",block:"nearest"}); return; }
  state.org=o; state.seg="";state.brand="";state.year=""; state.q="";
  const q=document.getElementById("q"); if(q)q.value="";
  renderTabs(); buildFilters(); render();
  const t=document.getElementById("orgtabs"); if(t)t.scrollIntoView({behavior:"smooth",block:"nearest"});
}
function jumpOrg(o){ switchOrg(o); }

function openDetail(org, key){
  const cfg=ORG_CFG[org];
  const grp=DATA.orgs[org].filter(r=>cfg.key(r)===key).sort((a,b)=>parseInt(cfg.year(a)||"0",10)-parseInt(cfg.year(b)||"0",10));
  if(!grp.length)return; const r0=grp[0];
  let html='<div class="hd"><b>'+cfg.name(r0)+'</b><span class="x" onclick="closeDetail()">✕</span></div>';
  html+='<div class="meta">'+(cfg.brand(r0))+' · 共 '+grp.length+' 期测评'+(grp.length>1?'（一年一行）':'')+'</div>';
  if(cfg.note) html+='<div class="note">'+cfg.note+'</div>';
  // 多期表格：一年一行
  let h='<th class="nm">年份</th>'; cfg.dims.forEach(d=>h+='<th>'+d.l+'</th>'); h+='<th>指导价</th><th>官方详情</th>';
  let rows=grp.map(r=>{
    let c='<td class="nm">'+cfg.year(r)+'</td>';
    if(cfg.dims.length) c+=cfg.dims.map(d=>'<td>'+(d.t==="grade"?gradeBadge(getVal(r,d.k)):pctCell(getVal(r,d.k)))+'</td>').join("");
    else c+='<td><span class="badge b-g">已测评</span></td>';
    c+='<td>'+(r.msrp_guide?r.msrp_guide.text:'<span class="badge b-none">暂无</span>')+'</td>';
    c+='<td>'+(cfg.detail(r)?'<a href="'+cfg.detail(r)+'" target="_blank" rel="noopener">↗</a>':'—')+'</td>';
    return '<tr>'+c+'</tr>';
  }).join("");
  html+='<table class="mtab"><tr>'+h+'</tr>'+rows+'</table>';
  // 价格
  const priced=grp.find(r=>r.msrp_guide);
  html+='<div class="price '+(priced?'has':'none')+'">'+(priced?('指导价（'+priced.msrp_guide.fetched_at+' 快照）：'+priced.msrp_guide.text+'　来源：汽车之家'):'指导价：暂无报价（停售 / 换代 / 待上市）')+'</div>';
  // 官方详情（多期各自链接）
  html+='<div class="acts">'+grp.map(r=> cfg.detail(r)?('<a href="'+cfg.detail(r)+'" target="_blank" rel="noopener">'+cfg.year(r)+' 官方详情 ↗</a>'):'').join("")+'</div>';
  const m=document.getElementById("detail"); m.querySelector("#dbody").innerHTML=html; m.style.display="block";
}
function closeDetail(){document.getElementById("detail").style.display="none";}
document.getElementById("detail").onclick=e=>{if(e.target.id==="detail")closeDetail();};

function render(){
  const a=filtered();
  const cfg=ORG_CFG[state.org];
  const total=(DATA.orgs[state.org]||[]).length;
  const wp=total? (DATA.orgs[state.org].filter(r=>r.msrp_guide).length):0;
  document.getElementById("stat").innerHTML=cfg.label+' · 共 '+total+' 款测评车型'
    + (wp? ' · 其中 <b style="color:var(--gp)">'+wp+'</b> 款有指导价':'')
    + (state.inprod?' · 已筛选在售':'');
  if(a.length===0){ showEmpty(); return; }
  document.getElementById("empty").innerHTML="";
  document.getElementById("recos").innerHTML="";
  if(state.view==="card") renderGrid(a); else renderTable(a);
}

/* 事件 */
document.getElementById("q").oninput=e=>{state.q=e.target.value;render();};
document.getElementById("seg").onchange=e=>{state.seg=e.target.value;render();};
document.getElementById("brand").onchange=e=>{state.brand=e.target.value;render();};
document.getElementById("year").onchange=e=>{state.year=e.target.value;render();};
document.getElementById("inprod").onchange=e=>{state.inprod=e.target.checked;render();};
document.getElementById("sort").onchange=e=>{state.sort=e.target.value;state.ord=(state.sort==="model"||state.sort==="brand")?"asc":"desc";document.getElementById("ord").textContent=state.ord==="desc"?"降序 ↓":"升序 ↑";render();};
document.getElementById("ord").onclick=()=>{state.ord=state.ord==="desc"?"asc":"desc";document.getElementById("ord").textContent=state.ord==="desc"?"降序 ↓":"升序 ↑";render();};
document.getElementById("vc").onclick=()=>{state.view="card";document.getElementById("vc").classList.add("on");document.getElementById("vt").classList.remove("on");render();};
document.getElementById("vt").onclick=()=>{state.view="table";document.getElementById("vt").classList.add("on");document.getElementById("vc").classList.remove("on");render();};

/* 拉取最新（jsDelivr）；失败用内嵌兜底。
   关键：以 generated_at 比较，只采纳「比内嵌快照更新」的在线数据——
   避免 jsDelivr @main 边缘缓存尚未刷新时，用旧数据覆盖掉已修正的内嵌快照。 */
function loadLive(){
  fetch(API_URL,{cache:"no-store"}).then(r=>{if(!r.ok)throw new Error("http");return r.json();}).then(j=>{
    const sl=document.getElementById("srcline"); sl.style.display="inline";
    if(j&&j.orgs&&j.orgs.c_iasi){
      const live=(j.metadata&&j.metadata.generated_at)||"";
      const cur=(DATA.metadata&&DATA.metadata.generated_at)||"";
      if(live>cur){
        DATA.orgs=j.orgs; DATA.metadata=j.metadata;
        sl.classList.remove("bad"); sl.textContent="在线 · "+live.slice(0,10);
        renderTabs(); buildFilters(); render();
      } else {
        sl.classList.remove("bad"); sl.textContent="内嵌快照 · "+cur.slice(0,10);
      }
    } else { sl.classList.add("bad"); sl.textContent="内嵌兜底"; }
  }).catch(()=>{ const sl=document.getElementById("srcline"); sl.style.display="inline"; sl.classList.add("bad"); sl.textContent="内嵌兜底"; });
}

renderTabs(); buildFilters(); render(); loadLive();
</script>
</body>
</html>"""

html = TPL.replace("__DATA__", json.dumps(DATA, ensure_ascii=False))
open(os.path.join(HERE, "dashboard.html"), "w", encoding="utf-8").write(html)
print("wrote dashboard.html  (%d bytes)" % len(html))
