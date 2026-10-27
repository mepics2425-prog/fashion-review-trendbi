"use strict";
// All calculations are exported by Python. UI only selects scopes and formats.
const $ = (selector) => document.querySelector(selector);
const grades = ["반복 관측", "비교 가능", "추가 관측 필요"];
const colors = ["#315deb", "#81a0ee", "#e2e7f0"];
const escapeHTML = (value) => String(value).replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
const number = (value) => value == null ? "—" : new Intl.NumberFormat("ko-KR", {maximumFractionDigits:2}).format(value);
const signed = (value) => value == null ? "—" : `${value > 0 ? "+" : ""}${number(value)}`;
const kst = (value) => new Intl.DateTimeFormat("sv-SE", {timeZone:"Asia/Seoul",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",hour12:false}).format(new Date(value));
const pill = (grade) => `<span class="pill ${["repeat","compare","need"][grades.indexOf(grade)]}">${escapeHTML(grade)}</span>`;
let data;
let selectedProduct = "DEMO-007";
function scopedProducts() {
  const category = $("#category").value;
  const query = $("#search").value.trim().toLocaleLowerCase();
  return data.products.filter((p) => (category === "all" || p.category === category) && `${p.product_id} ${p.name} ${p.brand}`.toLocaleLowerCase().includes(query));
}
function periodWindow(p) { return p.windows[$("#period").value]; }
function eligible(p) { const w = periodWindow(p); return w.trend.status === "comparable" && w.quality.grade !== "추가 관측 필요"; }
function renderOverview(products) {
  const counts = grades.map((grade) => products.filter((p) => p.windows["7"].quality.grade === grade).length);
  const covered = counts[0] + counts[1];
  const ranked = products.filter(eligible);
  const delta = ranked.reduce((sum,p) => sum + periodWindow(p).trend.delta, 0);
  const metrics = [
    ["탐색 중인 상품", products.length, "개", "필터 적용 · 가상 상품", false],
    ["기간 리뷰 순증 합계", ranked.length ? signed(delta) : "—", "건", `기간 비교 기준 충족 ${ranked.length}개 · 감소 계열 제외`, true],
    ["7일 비교 커버리지", products.length ? number(covered / products.length * 100) : "—", "%", `비교 가능 이상 ${covered} / ${products.length}개`, false],
    ["추가 관측 필요", counts[2], "개", "고정 7일 기준 · 합성 데이터", false]
  ];
  $("#metrics").innerHTML = metrics.map(([label,value,unit,note,blue]) => `<article class="metric ${blue ? "blue" : ""}"><div class="metric-label">${label}</div><div class="metric-value">${value}<small>${unit}</small></div><p>${note}</p></article>`).join("");
  let total = 0;
  const stops = counts.map((count,i) => { const start = total; total += products.length ? count / products.length * 100 : 0; return `${colors[i]} ${start}% ${total}%`; });
  $("#quality-ring").innerHTML = `<div class="ring" style="background:${products.length ? `conic-gradient(${stops.join(",")})` : "#edf0f5"}" role="img" aria-label="관측 품질 분포"><div>${products.length}<small>DEMO PRODUCTS</small></div></div>`;
  $("#mix-legend").innerHTML = grades.map((grade,i) => `<div class="legend-row"><i style="background:${colors[i]}"></i><span>${grade}</span><b>${counts[i]}</b></div>`).join("");
  const categories = ["상의","하의","아우터","원피스"];
  const maximum = Math.max(1, ...categories.map((c) => products.filter((p) => p.category === c).length));
  $("#category-bars").innerHTML = categories.map((category) => {
    const group = products.filter((p) => p.category === category);
    const valid = group.filter((p) => p.windows["7"].quality.grade !== "추가 관측 필요").length;
    return `<div class="bar-row"><span>${category}</span><div class="bar-track"><div class="bar-total" style="width:${group.length / maximum * 100}%"><div class="bar-fill" style="width:${group.length ? valid / group.length * 100 : 0}%"></div></div></div><strong>${valid} / ${group.length}</strong></div>`;
  }).join("");
}
function drawHistory(products) {
  const p = products.find((item) => item.product_id === selectedProduct);
  if (!p) { $("#chart-title").textContent = "상품 관측 추이"; $("#history-chart").innerHTML = '<p class="empty">조건에 맞는 상품이 없습니다.</p>'; $("#chart-caption").textContent = "검색어나 카테고리를 변경해 주세요."; return; }
  const cutoff = Date.parse(data.as_of) - Number($("#period").value) * 86400000;
  const points = p.observations.filter((o) => Date.parse(o.at) >= cutoff && Date.parse(o.at) <= Date.parse(data.as_of));
  const valid = points.filter((o) => o.count !== null);
  $("#chart-title").textContent = p.name;
  if (!valid.length) { $("#history-chart").innerHTML = '<p class="empty">선택 기간에 유효 관측값이 없습니다.</p>'; $("#chart-caption").textContent = "결측값을 0으로 대체하지 않습니다."; return; }
  const width=580,height=230,left=48,right=18,top=18,bottom=35;
  const max=Math.max(...valid.map((o) => o.count));
  const min=Math.min(...valid.map((o) => o.count));
  const padding=Math.max(4, (max-min)*.2);
  const low=Math.max(0, min-padding),high=max+padding;
  const x=(o) => left + (Date.parse(o.at)-cutoff)/(Date.parse(data.as_of)-cutoff)*(width-left-right);
  const y=(o) => top + (high-o.count)/(high-low)*(height-top-bottom);
  const grid=[0,1,2,3].map((i) => {
    const yy=top+i*(height-top-bottom)/3;
    return `<line x1="${left}" x2="${width-right}" y1="${yy}" y2="${yy}" stroke="#edf0f5"/><text x="${left-9}" y="${yy+3}" text-anchor="end">${number(Math.round(high-i*(high-low)/3))}</text>`;
  }).join("");
  const segments=[];
  let segment=[];
  for (const observation of points) {
    if (observation.count === null) { if(segment.length) segments.push(segment); segment=[]; }
    else segment.push(observation);
  }
  if(segment.length) segments.push(segment);
  const paths=segments.map((values) => `<polyline points="${values.map((o) => `${x(o)},${y(o)}`).join(" ")}" fill="none" stroke="#315deb" stroke-width="2.5"/>`).join("");
  const dots=valid.map((o) => `<circle cx="${x(o)}" cy="${y(o)}" r="3.5" fill="#fff" stroke="#315deb" stroke-width="2"><title>${kst(o.at)} KST · ${number(o.count)}건 · Synthetic</title></circle>`).join("");
  const labels=[0,1,2].map((i) => `<text x="${left+i*(width-left-right)/2}" y="${height-9}" text-anchor="${i === 0 ? "start" : i === 2 ? "end" : "middle"}">${kst(new Date(cutoff+i*(Date.parse(data.as_of)-cutoff)/2).toISOString()).slice(5,10)}</text>`).join("");
  const summary = valid.map((o) => `${kst(o.at)} KST ${o.count}건`).join(", ");
  $("#history-chart").innerHTML = `<svg class="history-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHTML(p.name)} 합성 리뷰 관측 추이"><title>${escapeHTML(p.name)} · Synthetic Data</title><desc>${escapeHTML(summary)}</desc>${grid}${paths}${dots}${labels}</svg>`;
  $("#chart-caption").textContent = `유효 관측 ${valid.length}회 · 누적 리뷰 수 · KST · Y축 자동 범위 · 결측 구간은 연결하지 않음`;
}
function renderTrends(products) {
  if (!products.some((p) => p.product_id === selectedProduct)) selectedProduct=products[0]?.product_id;
  $("#product-select").innerHTML = products.map((p) => `<option value="${escapeHTML(p.product_id)}">${escapeHTML(p.name)} · ${escapeHTML(p.product_id)}</option>`).join("");
  $("#product-select").disabled=!products.length;
  if(selectedProduct) $("#product-select").value=selectedProduct;
  drawHistory(products);
  const ranking=products.filter((p) => eligible(p) && periodWindow(p).trend.delta > 0).sort((a,b) => periodWindow(b).trend.delta-periodWindow(a).trend.delta || a.product_id.localeCompare(b.product_id)).slice(0,5);
  $("#ranking-list").innerHTML = ranking.length ? ranking.map((p,i) => `<div class="ranking-item"><span class="rank-index">${String(i+1).padStart(2,"0")}</span><span class="rank-name">${escapeHTML(p.name)}<small>${escapeHTML(p.brand)} · ${p.category}</small></span><span class="rank-count">${signed(periodWindow(p).trend.delta)}<small>${number(periodWindow(p).trend.reviews_per_day)} / 일</small></span></div>`).join("") : '<p class="empty">비교 기준을 충족한 증가 상품이 없습니다.</p>';
  $("#products-body").innerHTML = products.length ? products.map((p) => {
    const trend=periodWindow(p).trend;
    return `<tr><td><button class="product-button" data-product="${escapeHTML(p.product_id)}">${escapeHTML(p.name)}<small>${escapeHTML(p.brand)} / ${p.product_id}</small></button></td><td>${p.category}</td><td>${number(trend.latest_count)}</td><td class="${trend.status === "decrease_detected" ? "negative" : ""}">${signed(trend.delta)}${trend.status === "decrease_detected" ? "<small>감소 감지 · 순위 제외</small>" : ""}</td><td>${number(trend.reviews_per_day)}</td><td>${pill(p.windows["7"].quality.grade)}</td></tr>`;
  }).join("") : '<tr><td colspan="6" class="empty">조건에 맞는 상품이 없습니다.</td></tr>';
}
function renderQuality(products) {
  const backlog=products.filter((p) => p.windows["7"].quality.grade === "추가 관측 필요");
  $("#quality-backlog").innerHTML = backlog.length ? backlog.map((p) => {
    const q=p.windows["7"].quality;
    return `<div class="backlog-row"><span>${escapeHTML(p.name)}<small>${p.product_id} · ${p.category}</small></span><span>${q.distinct_dates}일 / ${q.snapshots}회<small>서로 다른 KST 날짜 / 유효 스냅샷</small></span><span>${number(q.span_hours)}h<small>실제 관측 기간</small></span><span>${number(q.age_hours)}h<small>마지막 유효 관측 이후</small></span></div>`;
  }).join("") : '<p class="empty">현재 범위에 추가 관측 대상이 없습니다.</p>';
}
function renderMonitoring() {
  const cutoff=Date.parse(data.as_of)-Number($("#period").value)*86400000;
  const runs=data.runs.filter((r) => Date.parse(r.started_at)>=cutoff && Date.parse(r.started_at)<=Date.parse(data.as_of));
  const attempted=runs.reduce((sum,r) => sum+r.attempted,0), succeeded=runs.reduce((sum,r) => sum+r.succeeded,0);
  $("#run-total").textContent=`${runs.length}회 · ${attempted ? number(succeeded/attempted*100) : "—"}% · DEMO`;
  const days={};
  for(const run of runs) { const day=kst(run.started_at).slice(0,10); days[day] ??= {attempted:0,succeeded:0}; days[day].attempted+=run.attempted; days[day].succeeded+=run.succeeded; }
  $("#daily-runs").innerHTML=Object.entries(days).sort().map(([day,r]) => `<div class="daily-row"><span>${day.slice(5)}</span><div class="bar-track"><div class="bar-fill" style="width:${r.succeeded/r.attempted*100}%"></div></div><strong>${number(r.succeeded/r.attempted*100)}%</strong></div>`).join("");
  const reasons={timeout:0,identity_mismatch:0,ambiguous_count:0};
  for(const run of runs) for(const key of Object.keys(reasons)) reasons[key]+=run.failure_reasons[key];
  const labels={timeout:"응답 시간 초과",identity_mismatch:"상품 식별 불일치",ambiguous_count:"모호한 리뷰 수"};
  const max=Math.max(1,...Object.values(reasons));
  $("#failure-bars").innerHTML=Object.entries(reasons).map(([key,count]) => `<div class="bar-row" style="grid-template-columns:105px 1fr 22px"><span>${labels[key]}</span><div class="bar-track"><div class="bar-fill" style="width:${count/max*100}%;background:#91a3ca"></div></div><strong>${count}</strong></div>`).join("");
  $("#runs-body").innerHTML=runs.map((r) => `<tr><td>${kst(r.started_at)}</td><td>${escapeHTML(r.job)}<small>${r.run_id}</small></td><td>${r.attempted}</td><td>${r.succeeded}</td><td><span class="pill ${r.succeeded === r.attempted ? "compare" : "need"}">${r.succeeded === r.attempted ? "전체 성공" : "일부 실패"}</span></td></tr>`).join("");
}
function render() {
  const products=scopedProducts();
  $("#scope-label").textContent=`${$("#period").value}일 트렌드 · ${products.length}개 상품 · Synthetic Data`;
  renderOverview(products); renderTrends(products); renderQuality(products); renderMonitoring();
}
async function start() {
  try {
    const response=await fetch("data/demo.json", {cache:"no-cache"});
    if(!response.ok) throw new Error(`HTTP ${response.status}`);
    data=await response.json();
    if(data.synthetic !== true || data.schema_version !== 1 || !Array.isArray(data.products)) throw new Error("Invalid synthetic data contract");
    $("#as-of").textContent=kst(data.as_of);
    render();
    $("#dashboard").hidden=false;
    $("#load-state").textContent="";
    for(const id of ["#category","#period"]) $(id).addEventListener("change",render);
    $("#search").addEventListener("input",render);
    $("#product-select").addEventListener("change",(event) => { selectedProduct=event.target.value; drawHistory(scopedProducts()); });
    $("#products-body").addEventListener("click",(event) => {
      const button=event.target.closest("[data-product]");
      if(button) { selectedProduct=button.dataset.product; $("#product-select").value=selectedProduct; drawHistory(scopedProducts()); $("#product-select").focus(); }
    });
    const observer=new IntersectionObserver((entries) => {
      for(const entry of entries) if(entry.isIntersecting) document.querySelectorAll("nav a").forEach((link) => link.classList.toggle("active",link.hash===`#${entry.target.id}`));
    },{rootMargin:"-5% 0px -70% 0px"});
    document.querySelectorAll("main section").forEach((section) => observer.observe(section));
  } catch(error) {
    $("#load-state").className="load-error";
    $("#load-state").textContent="데모 데이터를 불러오지 못했습니다. 다시 불러오기를 선택해 주세요. 로컬에서는 README의 HTTP 서버 실행 방법을 확인하세요.";
    $("#retry-load").hidden=false;
    console.error("Demo loading failed",error);
  }
}
$("#retry-load").addEventListener("click", () => window.location.reload());
start();
