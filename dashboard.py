"""HTML dashboard for the Trading Research API (served at /dashboard)."""

DASHBOARD_HTML = r"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trading Research Dashboard</title>
<style>
:root{--bg:#0a0d14;--panel:#121722;--panel2:#181e2c;--line:#232b3b;--text:#e6ebf5;--muted:#8b97ad;--up:#2dd4a7;--down:#f6685e;--warn:#f5b451;--accent:#6ea8ff}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(1200px 600px at 20% -10%,#16223a 0%,var(--bg) 55%);color:var(--text);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif}
.wrap{max-width:1200px;margin:0 auto;padding:24px 16px 48px}
header{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:20px}
h1{font-size:22px;margin:0;letter-spacing:.3px}
h1 small{color:var(--muted);font-weight:400;font-size:13px;margin-left:8px}
.live{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--up);box-shadow:0 0 0 0 rgba(45,212,167,.7);animation:pulse 1.6s infinite;margin-right:8px}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(45,212,167,.6)}70%{box-shadow:0 0 0 10px rgba(45,212,167,0)}100%{box-shadow:0 0 0 0 rgba(45,212,167,0)}}
.meta{color:var(--muted);font-size:12px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
button{background:var(--panel2);color:var(--text);border:1px solid var(--line);padding:8px 14px;border-radius:8px;cursor:pointer;font-weight:600}
button:hover{border-color:var(--accent)}
button:disabled{opacity:.5;cursor:wait}
.badge{padding:3px 8px;border-radius:999px;font-size:11px;font-weight:700;border:1px solid var(--line);background:var(--panel2)}
.badge.ok{color:var(--up);border-color:rgba(45,212,167,.4)}
.badge.warn{color:var(--warn);border-color:rgba(245,180,81,.4)}
.badge.bad{color:var(--down);border-color:rgba(246,104,94,.4)}
.grid{display:grid;gap:14px}
.g2{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.g4{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}
.card h2{font-size:12px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin:0 0 10px;font-weight:700}
.big{font-size:34px;font-weight:800;line-height:1.1}
.up{color:var(--up)}.down{color:var(--down)}.muted{color:var(--muted)}
.hero{display:grid;grid-template-columns:1.2fr 1fr;gap:14px;margin:14px 0}
@media(max-width:760px){.hero{grid-template-columns:1fr}}
.heat{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px}
.tile{border-radius:10px;padding:10px;border:1px solid rgba(255,255,255,.05);min-height:70px;display:flex;flex-direction:column;justify-content:space-between}
.tile b{font-size:15px}.tile span{font-size:11px;opacity:.8}
.tile .pct{font-size:16px;font-weight:800}
.tile.sel{outline:2px solid var(--accent)}
table{width:100%;border-collapse:collapse;font-size:13px}
th{color:var(--muted);text-align:left;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.6px;padding:8px 6px;border-bottom:1px solid var(--line)}
td{padding:9px 6px;border-bottom:1px solid rgba(35,43,59,.6);white-space:nowrap}
tr.top td{background:rgba(110,168,255,.06)}
.bar{height:6px;background:var(--panel2);border-radius:99px;overflow:hidden;min-width:80px}
.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--up))}
.levels{position:relative;height:70px;margin:20px 6px 24px}
.levels .track{position:absolute;left:0;right:0;top:32px;height:6px;border-radius:99px;background:linear-gradient(90deg,var(--down),var(--panel2) 35%,var(--panel2) 65%,var(--up))}
.lv{position:absolute;top:0;transform:translateX(-50%);text-align:center;font-size:11px;color:var(--muted)}
.lv b{display:block;color:var(--text);font-size:13px}
.lv:after{content:"";display:block;width:2px;height:22px;margin:4px auto 0;background:currentColor}
.lv.cur{color:var(--accent)}
.lv.below{top:auto;bottom:-14px;display:flex;flex-direction:column-reverse}
.lv.below:after{margin:0 auto 4px}
.meter{height:8px;border-radius:99px;background:linear-gradient(90deg,var(--up) 0 30%,var(--panel2) 30% 70%,var(--down) 70% 100%);position:relative;margin-top:10px}
.meter i{position:absolute;top:-4px;width:16px;height:16px;border-radius:50%;background:#fff;border:3px solid var(--bg);transform:translateX(-50%)}
.kv{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(35,43,59,.6);font-size:13px}
.kv:last-child{border:0}
details{margin-top:14px}summary{cursor:pointer;color:var(--muted);font-weight:600}
pre{white-space:pre-wrap;background:var(--panel2);padding:12px;border-radius:10px;font-size:12px;max-height:360px;overflow:auto}
.skeleton{height:120px;border-radius:14px;background:linear-gradient(90deg,var(--panel),var(--panel2),var(--panel));background-size:200% 100%;animation:sh 1.2s infinite}
@keyframes sh{0%{background-position:200% 0}100%{background-position:-200% 0}}
.err{border-color:rgba(246,104,94,.5);color:var(--down)}
footer{margin-top:24px;color:var(--muted);font-size:12px;text-align:center}
.sc{display:flex;gap:10px;flex-wrap:wrap}
.chip{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:8px 12px;min-width:120px}
.chip small{color:var(--muted);display:block;font-size:11px}
.chip b{font-size:18px}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1><span class="live"></span>Trading Research<small>Daily Research Agent v1</small></h1>
  <div class="meta">
    <span id="stamp">yükleniyor…</span>
    <span id="cache" class="badge">cache</span>
    <button id="refresh">↻ Yenile</button>
  </div>
</header>

<div id="app"><div class="skeleton"></div><br><div class="skeleton"></div></div>

<footer>Sadece araştırma amaçlı · canlı emir yok · insan onayı gerekir · Veri: yfinance</footer>
</div>

<script>
const $=s=>document.querySelector(s);
const f=(v,d=2)=>v==null||isNaN(v)?"—":Number(v).toFixed(d);
const pct=v=>v==null?"—":(v>=0?"+":"")+f(v)+"%";
const cls=v=>v==null?"muted":v>=0?"up":"down";
const heat=v=>{if(v==null)return"var(--panel2)";const a=Math.min(Math.abs(v)/3,1)*.55+.08;return v>=0?`rgba(45,212,167,${a})`:`rgba(246,104,94,${a})`};
const vol=v=>v==null?"—":v>=1e9?(v/1e9).toFixed(2)+"B":v>=1e6?(v/1e6).toFixed(1)+"M":v>=1e3?(v/1e3).toFixed(0)+"K":v;
const statusBadge=s=>s==="watchlist_candidate"?["ok","İZLEME ADAYI"]:s&&s.startsWith("invalid")?["bad","GEÇERSİZ"]:["warn","UYGUN DEĞİL"];

function render(d){
  const sec=d.summary.selected_sector, fc=d.final_candidate_data, b=d.benchmarks;
  const [bc,bt]=statusBadge(d.summary.trade_status);
  const lo=Math.min(fc.stop_reference,fc.support_20d,fc.latest_close), t1=parseFloat(fc.target_1_reference);
  const hi=Math.max(isNaN(t1)?fc.resistance_20d:t1,fc.latest_close);
  const px=v=>((v-lo)/(hi-lo)*100).toFixed(1)+"%";
  const rsi=Math.max(0,Math.min(100,fc.rsi14||50));
  const maxScore=Math.max(...d.stock_scan.map(s=>s.research_score),1);

  $("#app").innerHTML=`
  <div class="sc">
    <div class="chip"><small>SPY (${b.spy.used_symbol})</small><b class="${cls(b.spy.change_pct)}">${pct(b.spy.change_pct)}</b></div>
    <div class="chip"><small>QQQ (${b.qqq.used_symbol})</small><b class="${cls(b.qqq.change_pct)}">${pct(b.qqq.change_pct)}</b></div>
    <div class="chip"><small>Seçilen sektör</small><b>${sec.symbol} <span class="${cls(sec.change_pct)}" style="font-size:13px">${pct(sec.change_pct)}</span></b></div>
    <div class="chip"><small>Risk / Ödül</small><b>${fc.risk_reward}</b></div>
  </div>

  <div class="hero">
    <div class="card">
      <h2>Günün adayı · ${sec.name}</h2>
      <div class="big">${fc.symbol} <span class="${cls(fc.change_1d_pct)}" style="font-size:20px">${pct(fc.change_1d_pct)}</span></div>
      <div class="muted">${fc.name} · Kapanış ${f(fc.latest_close)} · ${fc.date}</div>
      <p style="margin:12px 0 6px"><span class="badge ${bc}">${bt}</span></p>
      <div class="muted" style="font-size:13px">${fc.trade_decision}</div>
      <div class="levels">
        <div class="track"></div>
        <div class="lv down" style="left:${px(fc.stop_reference)}">Stop<b>${f(fc.stop_reference)}</b></div>
        <div class="lv below" style="left:${px(fc.entry_reference)}">Giriş<b>${f(fc.entry_reference)}</b></div>
        <div class="lv cur" style="left:${px(fc.latest_close)}">Fiyat<b>${f(fc.latest_close)}</b></div>
        ${isNaN(t1)?"":`<div class="lv up" style="left:${px(t1)}">Hedef 1<b>${f(t1)}</b></div>`}
      </div>
    </div>
    <div class="card">
      <h2>Teknik görünüm</h2>
      <div class="kv"><span>RSI 14</span><b>${f(fc.rsi14,1)} <span class="muted" style="font-weight:400">${fc.rsi_comment||""}</span></b></div>
      <div class="meter"><i style="left:${rsi}%"></i></div>
      <div class="kv" style="margin-top:10px"><span>Trend</span><b>${fc.trend_status}</b></div>
      <div class="kv"><span>EMA 20 / 50 / 200</span><b>${f(fc.ema20)} / ${f(fc.ema50)} / ${f(fc.ema200)}</b></div>
      <div class="kv"><span>ATR 14</span><b>${f(fc.atr14)}</b></div>
      <div class="kv"><span>Göreli hacim</span><b>${f(fc.relative_volume)}x <span class="muted" style="font-weight:400">${fc.volume_comment||""}</span></b></div>
      <div class="kv"><span>5G / 20G değişim</span><b><span class="${cls(fc.change_5d_pct)}">${pct(fc.change_5d_pct)}</span> / <span class="${cls(fc.change_20d_pct)}">${pct(fc.change_20d_pct)}</span></b></div>
      <div class="kv"><span>Destek 20G / Direnç 50G</span><b>${f(fc.support_20d)} / ${f(fc.resistance_50d)}</b></div>
    </div>
  </div>

  <div class="card" style="margin-bottom:14px">
    <h2>Sektör ısı haritası · günlük değişim</h2>
    <div class="heat">${d.sector_scan.map(s=>`
      <div class="tile ${s.symbol===sec.symbol?"sel":""}" style="background:${heat(s.change_pct)}">
        <div><b>${s.symbol}</b><br><span>${s.sector}</span></div>
        <div class="pct ${cls(s.change_pct)}">${pct(s.change_pct)}</div>
      </div>`).join("")}</div>
  </div>

  <div class="card">
    <h2>${sec.symbol} hisse taraması · araştırma skoru</h2>
    <div style="overflow:auto"><table>
      <tr><th>#</th><th>Sembol</th><th>Şirket</th><th>Kapanış</th><th>1G</th><th>5G</th><th>20G</th><th>SMA20</th><th>SMA50</th><th>RVol</th><th>Skor</th></tr>
      ${d.stock_scan.map((s,i)=>`<tr class="${i===0?"top":""}">
        <td class="muted">${i+1}</td><td><b>${s.symbol}</b></td><td class="muted">${s.name}</td><td>${f(s.latest_close)}</td>
        <td class="${cls(s.change_1d_pct)}">${pct(s.change_1d_pct)}</td><td class="${cls(s.change_5d_pct)}">${pct(s.change_5d_pct)}</td><td class="${cls(s.change_20d_pct)}">${pct(s.change_20d_pct)}</td>
        <td>${s.above_sma20?"✅":"—"}</td><td>${s.above_sma50?"✅":"—"}</td><td>${f(s.relative_volume)}x</td>
        <td><div style="display:flex;align-items:center;gap:8px"><div class="bar"><i style="width:${s.research_score/maxScore*100}%"></i></div><b>${s.research_score}</b></div></td>
      </tr>`).join("")}
    </table></div>
    <details><summary>Agent prompt (rapor için) — kopyala</summary><pre id="prompt">${d.agent_prompt.replace(/</g,"&lt;")}</pre>
      <button onclick="navigator.clipboard.writeText(document.getElementById('prompt').innerText)">Kopyala</button></details>
  </div>`;
  $("#stamp").textContent="Güncellendi "+new Date(d.created_at+"Z").toLocaleString("tr-TR");
  $("#cache").textContent=d.cache==="hit"?"önbellek":"canlı";
  $("#cache").className="badge "+(d.cache==="hit"?"warn":"ok");
}

async function load(refresh){
  const btn=$("#refresh");btn.disabled=true;btn.textContent="⏳ Piyasa taranıyor…";
  try{
    const r=await fetch("/daily-research"+(refresh?"?refresh=true":""));
    const d=await r.json();
    if(d.status!=="ok")throw new Error(d.message||"Bilinmeyen hata");
    render(d);
  }catch(e){
    $("#app").innerHTML=`<div class="card err"><h2>Hata</h2>${e.message}</div>`;
    $("#stamp").textContent="veri alınamadı";
  }finally{btn.disabled=false;btn.textContent="↻ Yenile"}
}
$("#refresh").onclick=()=>load(true);
load(false);
setInterval(()=>load(false),5*60*1000);
</script>
</body>
</html>"""
