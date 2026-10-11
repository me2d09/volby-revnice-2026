/* Osobní křížky – výcuc bayesovské analýzy Claude */
(function () {
  "use strict";
  const RV = window.RV;
  RV.init("krizky");
  const B = RV.data.zakladni, C = RV.data.claude;
  if (!B || !C) return;
  const H = C.headline;
  const FONT = "Inter, system-ui, sans-serif";
  const ink = () => RV.token("ink"), ink2 = () => RV.token("ink-2"), muted = () => RV.token("muted"), surface = () => RV.token("surface");
  const PARTIES = RV.PARTY_ORDER;
  const SHORT = { "Srdce": "Srdce Řevnic" };
  const norm = (p) => SHORT[p] || p;
  const cands = C.candidates.map((c) => Object.assign({}, c, { party: norm(c.party) }));
  const basicByKey = Object.fromEntries(B.candidates.map((c) => [c.party + "|" + c.position, c]));
  cands.forEach((c) => { c.basic = basicByKey[c.party + "|" + c.position]; c.mult = Math.exp(c.u); });
  const parties = C.parties.map((p) => Object.assign({}, p, { party: norm(p.party) }));
  const partyFull = Object.fromEntries(B.parties.map((p) => [p.short, p.name]));
  const xFmt = (m) => "×" + RV.fmt(m, m < 1 ? 2 : 1);
  const surname = (n) => n.split(" ").slice(-1)[0];

  document.querySelectorAll("[data-h]").forEach((e) => { e.textContent = RV.int(H[e.dataset.h]); });
  document.querySelectorAll("[data-b]").forEach((e) => { e.textContent = RV.int(B.totals.votes_2026); });

  /* =========================================================== 1 hlasovací lístek */
  const sance = B.candidates.filter((c) => c.party === "ŠANCE").sort((a, b) => a.position - b.position);
  const others = [];
  for (let pos = 1; others.length < 15; pos++) {
    PARTIES.filter((p) => p !== "ŠANCE").forEach((p) => {
      const c = B.candidates.find((x) => x.party === p && x.position === pos * 2);
      if (c && others.length < 15) others.push(c);
    });
  }
  let ballotMode = "party";
  const kEl = document.getElementById("ballot-k");
  function renderBallot() {
    const k = +kEl.value;
    const partyMode = ballotMode === "party";
    document.getElementById("ballot-k-label").innerHTML = partyMode
      ? `Křížky u kandidátů jiných stran: <strong>${k}</strong>`
      : `Počet křížků u jednotlivců: <strong>${k}</strong>`;
    const partyGets = partyMode ? 15 - k : 0;
    const col1 = `<div class="ballot-col"><h4><span>ŠANCE Řevnice</span><span class="box">${partyMode ? "✕" : ""}</span></h4><ul class="ballot-list">` +
      sance.map((c, i) => {
        const pers = !partyMode && i < Math.ceil(k / 2) && i % 3 === 0;
        const get = partyMode && i < partyGets;
        return `<li class="${get ? "get" : pers ? "personal" : partyMode ? "lost" : ""}"><span class="pos">${c.position}.</span><span>${RV.esc(c.name)}</span><span class="v">${get || pers ? "+1" : ""}</span></li>`;
      }).join("") + `</ul></div>`;
    const ownPersonal = partyMode ? 0 : sance.filter((c, i) => i < Math.ceil(k / 2) && i % 3 === 0).length;
    const nOthers = partyMode ? k : k - ownPersonal;
    const col2 = `<div class="ballot-col"><h4><span>Kandidáti jiných stran</span></h4><ul class="ballot-list">` +
      (nOthers ? others.slice(0, nOthers).map((c) => `<li class="personal"><span class="pos"><span class="sw" style="--c:${RV.cssColor(c.party)}"></span></span><span>${RV.esc(c.name)} <span class="muted">(${RV.esc(c.party)})</span></span><span class="v">+1</span></li>`).join("")
        : `<li><span></span><span>žádný křížek</span><span></span></li>`) + `</ul></div>`;
    const personal = partyMode ? k : k;
    const unused = partyMode ? 0 : 15 - k;
    const col3 = `<div class="ballot-col"><h4><span>Co z lístku vzejde</span></h4>
      <div class="grid" style="gap:10px;margin-top:6px">
        <div class="stat"><span class="label">Stranické hlasy (ŠANCE)</span><span class="value" style="font-size:2rem">${partyGets}</span></div>
        <div class="stat"><span class="label">Osobní křížky</span><span class="value" style="font-size:2rem;color:var(--warm)">${personal}</span></div>
        <div class="stat"><span class="label">Nevyužité hlasy</span><span class="value" style="font-size:2rem;color:var(--muted)">${unused}</span></div>
      </div></div>`;
    document.getElementById("ballot-cols").innerHTML = col1 + col2 + col3;
    let sum;
    if (partyMode && k === 0) sum = "Volič zakřížkoval jen celou ŠANCI: všech 15 kandidátů dostane po jednom hlasu. <strong>Žádný osobní křížek.</strong>";
    else if (partyMode && k < 15) sum = `Křížek u strany a ${k} ${RV.plural(k, "křížek", "křížky", "křížků")} jinde: ${k} ${RV.plural(k, "hlas jde", "hlasy jdou", "hlasů jde")} kandidátům jiných stran a ŠANCE dostane zbylých ${15 - k} – prvním ${15 - k} kandidátům shora. <strong>Posledních ${k} na kandidátce ŠANCE z tohoto lístku nedostane nic.</strong>`;
    else if (partyMode) sum = "Patnáct křížků jinde: stranický křížek už nic nepřinese, lístek se chová, jako by strana zakřížkovaná nebyla.";
    else sum = `Bez stranického křížku dostane hlas jen ${k} ${RV.plural(k, "označený kandidát", "označení kandidáti", "označených kandidátů")}. ${unused ? `<strong>${unused} ${RV.plural(unused, "hlas zůstane", "hlasy zůstanou", "hlasů zůstane")} nevyužito</strong> – takové lístky v Řevnicích prokazatelně byly.` : "Všech 15 hlasů je využito."}`;
    document.getElementById("ballot-sum").innerHTML = sum + ' <span class="muted">Křížky u kandidátů zakřížkované strany se nepočítají zvlášť.</span>';
  }
  kEl.addEventListener("input", renderBallot);
  RV.seg("#ballot-mode", (v) => { ballotMode = v; kEl.min = v === "party" ? 0 : 1; if (v === "people" && +kEl.value < 1) kEl.value = 1; renderBallot(); });
  renderBallot();

  /* =========================================================== 2 meze */
  RV.plot("#bounds-chart", (w) => {
    const narrow = w < 600;
    const acc = RV.token("accent"), warm = RV.token("warm");
    const yM = "Odhad modelu";
    const rowsB = [
      { y: "Z městských součtů", x: H.lb_city, a: 0.4, h: "Stranické hlasy nerostou směrem dolů po kandidátce → rozdíly musí být osobní křížky" },
      { y: "Po okrscích", x: H.lb_monotone, a: 0.66, h: "Stejná úvaha v každém okrsku zvlášť" },
      { y: "+ zákon zachování hlasů", x: H.lb_lp, a: 1, h: "Lístek se stranou dává vždy přesně 15 hlasů → silnější mez (lineární program)" },
    ];
    return {
      data: [{
        type: "bar", orientation: "h", y: rowsB.map((r) => r.y), x: rowsB.map((r) => r.x),
        marker: { color: rowsB.map((r) => RV.alpha(acc, r.a)) },
        text: rowsB.map((r) => `≥ ${RV.int(r.x)}`), textposition: "outside", cliponaxis: false, textfont: { color: ink(), size: 14, family: FONT },
        customdata: rowsB.map((r) => r.h), hovertemplate: "<b>jisté minimum %{x:,.0f}</b><br>%{customdata}<extra></extra>",
      }, {
        type: "bar", orientation: "h", y: [yM], x: [H.total_C], marker: { color: RV.alpha(warm, 0.85) },
        hovertemplate: `Bayesovský model: medián ${RV.int(H.total_C)}<br>90% interval ${RV.int(H.total_C_q05)}–${RV.int(H.total_C_q95)} (≈ ${RV.fmt(100 * H.total_C_share, 0)} % hlasů)<extra></extra>`,
      }, {
        type: "scatter", mode: "lines", y: [yM, yM], x: [H.total_C_q05, H.total_C_q95], line: { color: ink(), width: 2.5 }, hoverinfo: "skip",
      }],
      layout: {
        height: 340, barcornerradius: 4, bargap: 0.35, margin: { l: 6, r: 10, t: 26, b: 44 },
        xaxis: { range: [0, narrow ? 12500 : 10500], title: { text: "osobní křížky v celém městě" } },
        yaxis: { tickfont: { color: ink(), size: 13.5 }, showgrid: false, categoryorder: "array", categoryarray: rowsB.map((r) => r.y).concat([yM]) },
        shapes: [{ type: "rect", xref: "x", yref: "y", x0: H.sens_min, x1: H.sens_max, y0: 2.55, y1: 3.45, fillcolor: RV.alpha(warm, 0.13), line: { width: 0 }, layer: "below" }],
        annotations: [
          { x: H.total_C_q95, y: yM, xanchor: "left", xshift: 8, showarrow: false, align: "left", font: { size: 14, color: ink() },
            text: `≈ ${RV.int(H.total_C)}<br><span style="font-size:11.5px">90 %: ${RV.int(H.total_C_q05)}–${RV.int(H.total_C_q95)}</span>` },
          { x: (H.sens_min + H.sens_max) / 2, y: 3.45, yanchor: "bottom", showarrow: false, text: `varianty modelu ${RV.int(H.sens_min)}–${RV.int(H.sens_max)}`, font: { size: 11.5, color: muted() } },
        ],
      },
    };
  });

  /* =========================================================== 3 přínos pro stranu */
  let prinosParty = "ŠANCE";
  const pp = document.getElementById("prinos-party");
  pp.innerHTML = PARTIES.map((p) => `<button type="button" class="chip" data-v="${RV.esc(p)}" aria-pressed="${p === prinosParty}"><span class="sw" style="--c:${RV.cssColor(p)}"></span>${RV.esc(p)}</button>`).join("") +
    `<button type="button" class="chip" data-v="__top" aria-pressed="false">Top 25 celkem</button>`;
  pp.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
    pp.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
    prinosParty = b.dataset.v; drawPrinos();
  }));
  const drawPrinos = RV.plot("#prinos-chart", (w) => {
    const narrow = w < 600;
    const top = prinosParty === "__top";
    let rows = top ? cands.slice().sort((a, b) => b.C - a.C).slice(0, 25) : cands.filter((c) => c.party === prinosParty).sort((a, b) => a.position - b.position);
    rows = rows.slice().reverse();
    const lab = (c) => (top ? `${narrow ? surname(c.name) : c.name} (${c.party})` : `${c.position}. ${narrow ? surname(c.name) : c.name}`);
    const ylab = rows.map((c) => (c.elected ? `<b>${RV.esc(lab(c))}</b>` : RV.esc(lab(c))));
    const colors = rows.map((c) => RV.color(c.party));
    const cd = rows.map((c) => [c.name, c.party, c.position, RV.int(c.votes), RV.int(c.S), RV.int(c.C), RV.int(c.C_q05), RV.int(c.C_q95), RV.int(c.lb), RV.fmt(100 * c.C_share, 0)]);
    const ht = "<b>%{customdata[0]}</b> (%{customdata[1]}, %{customdata[2]}.)<br>%{customdata[3]} hlasů celkem<br>" +
      "≈ %{customdata[4]} díky křížku u kandidátky<br><b>≈ %{customdata[5]} osobních křížků</b> (%{customdata[9]} %)<br>90% interval %{customdata[6]}–%{customdata[7]} · jisté minimum %{customdata[8]}<extra></extra>";
    const party = parties.find((p) => p.party === prinosParty);
    if (top) {
      document.getElementById("prinos-title").textContent = "25 kandidátů s nejvíce osobními křížky";
      document.getElementById("prinos-sub").textContent = "Napříč všemi kandidátkami; seřazeno podle odhadu osobních křížků.";
    } else {
      const best = cands.filter((c) => c.party === prinosParty).sort((a, b) => b.C - a.C)[0];
      document.getElementById("prinos-title").textContent = partyFull[prinosParty] || prinosParty;
      document.getElementById("prinos-sub").innerHTML = `Odhadem <strong>${RV.int(party.C)}</strong> osobních křížků (90&nbsp;%: ${RV.int(party.C_q05)}–${RV.int(party.C_q95)}),
        tj. ${RV.fmt(100 * party.C_share, 0)}&nbsp;% hlasů kandidátky. Nejvíc přinesl(a) <strong>${RV.esc(best.name)}</strong> (≈ ${RV.int(best.C)}).`;
    }
    return {
      data: [{
        type: "bar", orientation: "h", y: ylab, x: rows.map((c) => c.S), name: "díky křížku u kandidátky",
        marker: { color: colors.map((c) => RV.alpha(c, 0.28)) }, customdata: cd, hovertemplate: ht,
      }, {
        type: "bar", orientation: "h", y: ylab, x: rows.map((c) => c.C), name: "osobní křížky",
        marker: { color: colors }, customdata: cd, hovertemplate: ht,
        text: rows.map((c) => RV.int(c.C)), textposition: "outside", cliponaxis: false, textfont: { color: ink(), size: 12.5, family: FONT },
      }],
      layout: {
        barmode: "stack", height: Math.max(460, rows.length * (narrow ? 27 : 30) + 50), bargap: 0.22, barcornerradius: 3,
        margin: { l: 6, r: 14, t: 6, b: 36 },
        xaxis: { range: [0, Math.max(...rows.map((c) => c.votes)) * 1.1], title: { text: "hlasy kandidáta" } },
        yaxis: { tickfont: { color: ink(), size: narrow ? 11.5 : 12.5 }, showgrid: false },
      },
    };
  });
  document.getElementById("prinos-legend").innerHTML =
    `<span><span class="sw" style="--c:var(--line-strong)"></span>světlá = hlasy díky křížku u celé kandidátky</span>` +
    `<span><span class="sw" style="--c:var(--ink-2)"></span>sytá = osobní křížky (číslo)</span><span><strong>tučně</strong> = zvolen(a)</span>`;

  /* =========================================================== 4 žebříček */
  let rankMetric = "C", rankFilter = "all";
  const drawRank = RV.plot("#rank-chart", (w) => {
    const narrow = w < 600;
    const isC = rankMetric === "C";
    const pool = cands.filter((c) => rankFilter === "all" || c.elected);
    const key = isC ? (c) => c.C : (c) => c.C_share;
    const rows = pool.slice().sort((a, b) => key(b) - key(a)).slice(0, 30).reverse();
    const y = rows.map((c) => `${narrow ? surname(c.name) : c.name} <span style="color:${muted()}">${c.party}</span>`);
    const sc = (v) => (isC ? v : 100 * v);
    const lo = (c) => (isC ? c.C_q05 : c.C_q05 / c.votes), hi = (c) => (isC ? c.C_q95 : c.C_q95 / c.votes);
    const data = [{
      type: "scatter", mode: "markers", y, x: rows.map((c) => sc(key(c))),
      marker: { size: 11, color: rows.map((c) => RV.color(c.party)), line: { color: surface(), width: 2 } },
      error_x: { type: "data", symmetric: false, array: rows.map((c) => sc(hi(c)) - sc(key(c))), arrayminus: rows.map((c) => sc(key(c)) - sc(lo(c))), color: RV.token("line-strong"), thickness: 3, width: 0 },
      customdata: rows.map((c) => [c.name, c.party, c.position, RV.int(c.C), RV.int(c.C_q05), RV.int(c.C_q95), RV.int(c.lb), RV.fmt(100 * c.C_share, 0), RV.int(c.votes)]),
      hovertemplate: "<b>%{customdata[0]}</b> (%{customdata[1]}, %{customdata[2]}.)<br>≈ %{customdata[3]} osobních křížků (%{customdata[4]}–%{customdata[5]})<br>%{customdata[7]} % z jeho %{customdata[8]} hlasů · jisté minimum %{customdata[6]}<extra></extra>",
    }];
    if (isC) data.push({
      type: "scatter", mode: "markers", y, x: rows.map((c) => c.lb),
      marker: { symbol: "line-ns", size: 14, line: { width: 2.5, color: ink() } }, hovertemplate: "jisté minimum: %{x}<extra></extra>",
    });
    return {
      data,
      layout: {
        height: rows.length * 26 + 70, margin: { l: 6, r: 14, t: 6, b: 40 },
        xaxis: { rangemode: "tozero", title: { text: isC ? "osobní křížky (medián, 90% interval; ┃ = jisté minimum)" : "podíl osobních křížků na hlasech kandidáta" }, ticksuffix: isC ? "" : " %" },
        yaxis: { tickfont: { color: ink(), size: 12.5 }, showgrid: true, gridcolor: RV.token("line") },
      },
    };
  });
  RV.seg("#rank-metric", (v) => { rankMetric = v; drawRank(); });
  RV.seg("#rank-filter", (v) => { rankFilter = v; drawRank(); });

  /* =========================================================== 5 osobnosti */
  const order = Object.fromEntries(PARTIES.map((p, i) => [p, i]));
  const topU = cands.slice().sort((a, b) => b.u - a.u);
  const labelSet = new Set(topU.slice(0, 6).map((c) => c.name));
  RV.plot("#pers-chart", (w) => {
    const narrow = w < 600;
    const traces = PARTIES.map((p) => {
      const rows = cands.filter((c) => c.party === p);
      return {
        type: "scatter", mode: "markers+text", name: p,
        x: rows.map((c) => c.position + (order[p] - 3.5) * 0.075), y: rows.map((c) => c.mult),
        marker: { opacity: 1, size: rows.map((c) => (c.elected ? 13 : 9)), color: RV.color(p), line: { color: surface(), width: 1.5 } },
        text: rows.map((c) => (labelSet.has(c.name) && w > 420 ? surname(c.name) : "")), textposition: "top center",
        textfont: { size: 11.5, color: ink(), family: FONT },
        customdata: rows.map((c) => [c.name, p, c.position, xFmt(c.mult), xFmt(Math.exp(c.u_q05)), xFmt(Math.exp(c.u_q95)), RV.fmt(100 * c.p_u_pos, 0), RV.int(c.C)]),
        hovertemplate: "<b>%{customdata[0]}</b> (%{customdata[1]}, %{customdata[2]}.)<br>osobní efekt <b>%{customdata[3]}</b> (90 %: %{customdata[4]}–%{customdata[5]})<br>pravděpodobnost nadprůměru %{customdata[6]} % · ≈ %{customdata[7]} křížků<extra></extra>",
      };
    });
    return {
      data: traces,
      layout: {
        height: narrow ? 500 : 640, margin: { l: 6, r: 10, t: 10, b: 44 }, showlegend: true,
        legend: { orientation: "h", y: -0.16, x: 0, font: { size: 12, color: ink2() } },
        xaxis: { title: { text: "pozice na kandidátce" }, dtick: 1, range: [0.4, 15.6], showgrid: false },
        yaxis: { type: "log", title: { text: "osobní efekt (×)" }, tickvals: [0.5, 0.75, 1, 1.5, 2, 3], ticktext: ["×0,5", "×0,75", "×1", "×1,5", "×2", "×3"], range: [Math.log10(0.42), Math.log10(3.9)] },
        shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: 1, y1: 1, line: { color: ink2(), width: 1.5 } }],
        annotations: [{ xref: "paper", x: 0.01, y: 0, yanchor: "top", xanchor: "left", yshift: -2, showarrow: false, text: "×1 = typický kandidát na stejném místě", bgcolor: surface(), font: { size: 11.5, color: ink2() } }],
      },
    };
  });
  document.getElementById("pers-table").innerHTML =
    `<thead><tr><th>#</th><th>Kandidát</th><th class="r">Efekt</th><th class="r">Křížky</th></tr></thead><tbody>` +
    topU.slice(0, 10).map((c, i) => `<tr><td class="muted">${i + 1}</td><td>${RV.esc(c.name)}${c.elected ? " ✓" : ""}<br><span class="muted" style="font-size:12.5px">${RV.partyLabel(c.party)} · ${c.position}. místo</span></td>` +
      `<td class="r"><strong>${xFmt(c.mult)}</strong></td><td class="r">≈ ${RV.int(c.C)}</td></tr>`).join("") + `</tbody>`;
  const leadersLow = cands.filter((c) => c.position === 1 && c.u < 0).sort((a, b) => a.u - b.u);
  document.getElementById("pers-leaders").innerHTML = `<strong>Lídři nejsou automaticky osobnosti.</strong> ` +
    leadersLow.slice(0, 3).map((c) => `${RV.esc(c.name)} (${RV.esc(c.party)}, ${xFmt(c.mult)})`).join(", ") +
    ` dostali méně osobních křížků, než by lídr jejich kandidátky „měl“. Většinu jejich hlasů tvoří stranické křížky.`;

  /* =========================================================== 6 Červená */
  const tc = cands.find((c) => c.name === "Terezie Červená");
  const tcb = tc.basic;
  const above = B.candidates.filter((c) => c.party === "ŠANCE" && c.position < tc.position && c.votes < tc.votes).length;
  document.getElementById("cervena-text").innerHTML =
    `Na lístku ŠANCE byla desátá a dostala ${RV.int(tc.votes)} hlasů – víc než ${above} kandidátů nad ní. Díky pravidlu o přednostních hlasech
    získala mandát <span class="tag tag-fact">fakt</span>. Stranické hlasy směrem dolů po kandidátce jen ubývají, takže její „přebytek“ musí být osobní křížky:
    v každém okrsku zvlášť to dává jisté minimum <strong>${tcb.min_personal_marks_precincts.join(" + ")} = ${tc.lb}</strong> <span class="tag tag-bound">jisté minimum</span>.
    Model odhaduje asi <strong>${RV.int(tc.C)}</strong> osobních křížků (90&nbsp;%: ${RV.int(tc.C_q05)}–${RV.int(tc.C_q95)}) a osobní efekt ${xFmt(tc.mult)} – jeden z nejvyšších ve městě <span class="tag tag-model">model</span>.`;
  document.getElementById("cervena-quote").textContent =
    `Každý z nejméně ${tc.lb} křížků přišel od voliče, který nezakřížkoval celou ŠANCI – a přesto chtěl právě ji.`;
  RV.plot("#cervena-chart", () => {
    const col = RV.color("ŠANCE");
    const x = ["Okrsek 1", "Okrsek 2", "Okrsek 3", "Okrsek 4"];
    const lb = tcb.min_personal_marks_precincts, v = tc.votes_precincts;
    return {
      data: [{
        type: "bar", x, y: lb, name: "jisté minimum osobních křížků", marker: { color: col },
        text: lb.map((n) => `≥ ${n}`), textposition: "inside", insidetextanchor: "middle", textfont: { color: "#1b2420", size: 13, family: FONT },
        hovertemplate: "%{x}: nejméně %{y} osobních křížků<extra></extra>",
      }, {
        type: "bar", x, y: v.map((n, i) => n - lb[i]), name: "ostatní hlasy", marker: { color: RV.alpha(col, 0.3) },
        text: v.map((n) => `${n} hlasů`), textposition: "outside", cliponaxis: false, textfont: { color: ink(), size: 13, family: FONT },
        customdata: v, hovertemplate: "%{x}: celkem %{customdata} hlasů<extra></extra>",
      }],
      layout: {
        barmode: "stack", height: 300, barcornerradius: 4, bargap: 0.38, margin: { l: 6, r: 6, t: 26, b: 30 },
        yaxis: { range: [0, 125] }, xaxis: { tickfont: { color: ink(), size: 13 } },
      },
    };
  });

  /* =========================================================== 7 kandidátky a okrsky */
  const errBars = (rows, lo, mid, hi, s = 1) => ({ type: "data", symmetric: false, array: rows.map((r) => s * (r[hi] - r[mid])), arrayminus: rows.map((r) => s * (r[mid] - r[lo])), color: ink(), thickness: 1.5, width: 5 });
  RV.plot("#party-share-chart", () => {
    const rows = parties.slice().sort((a, b) => a.C_share - b.C_share);
    return {
      data: [{
        type: "bar", orientation: "h", y: rows.map((p) => p.party), x: rows.map((p) => 100 * p.C_share),
        marker: { color: rows.map((p) => RV.color(p.party)) }, error_x: errBars(rows, "C_share_q05", "C_share", "C_share_q95", 100),
        text: rows.map((p) => RV.pct(100 * p.C_share, 0)), textposition: "inside", insidetextanchor: "start",
        textfont: { color: "#ffffff", size: 12.5, family: FONT },
        customdata: rows.map((p) => [RV.int(p.C), RV.int(p.C_q05), RV.int(p.C_q95), RV.int(p.votes), RV.fmt(100 * p.C_share_q05, 0), RV.fmt(100 * p.C_share_q95, 0)]),
        hovertemplate: "<b>%{y}</b><br>≈ %{customdata[0]} osobních křížků z %{customdata[3]} hlasů<br>podíl %{x:.0f} % (90 %: %{customdata[4]}–%{customdata[5]} %)<extra></extra>",
      }],
      layout: { height: 360, barcornerradius: 4, margin: { l: 6, r: 14, t: 6, b: 30 }, xaxis: { range: [0, 72], ticksuffix: " %" }, yaxis: { tickfont: { color: ink(), size: 13 }, showgrid: false } },
    };
  });
  RV.plot("#party-ballots-chart", () => {
    const rows = parties.slice().sort((a, b) => a.party_ballots - b.party_ballots);
    return {
      data: [{
        type: "bar", orientation: "h", y: rows.map((p) => p.party), x: rows.map((p) => p.party_ballots),
        marker: { color: rows.map((p) => RV.color(p.party)) }, error_x: errBars(rows, "party_ballots_q05", "party_ballots", "party_ballots_q95"),
        customdata: rows.map((p) => [RV.int(p.party_ballots_q05), RV.int(p.party_ballots_q95), RV.fmt(100 * p.p_k0, 0)]),
        hovertemplate: "<b>%{y}</b><br>≈ %{x:.0f} lístků se zakřížkovanou stranou (90 %: %{customdata[0]}–%{customdata[1]})<br>%{customdata[2]} % z nich bez dalšího křížku jinde<extra></extra>",
      }],
      layout: { height: 360, barcornerradius: 4, margin: { l: 6, r: 14, t: 6, b: 30 }, xaxis: { rangemode: "tozero", title: { text: "voliči (lístky)" } }, yaxis: { tickfont: { color: ink(), size: 13 }, showgrid: false } },
    };
  });
  RV.plot("#pc-share-chart", () => {
    const rows = C.precincts;
    return {
      data: [{
        type: "bar", x: rows.map((p) => `Okrsek ${p.id}`), y: rows.map((p) => 100 * p.C_share),
        marker: { color: RV.alpha(RV.token("warm"), 0.8) },
        error_y: { type: "data", symmetric: false, array: rows.map((p) => 100 * (p.C_q95 - p.C) / p.votes), arrayminus: rows.map((p) => 100 * (p.C - p.C_q05) / p.votes), color: ink(), thickness: 1.5, width: 6 },
        text: rows.map((p) => RV.pct(100 * p.C_share, 0)), textposition: "inside", insidetextanchor: "start", textfont: { color: "#ffffff", size: 13, family: FONT },
        customdata: rows.map((p) => [RV.int(p.C), RV.int(p.votes), RV.int(p.lb_lp)]),
        hovertemplate: "<b>%{x}</b><br>≈ %{customdata[0]} osobních křížků z %{customdata[1]} hlasů<br>jisté minimum %{customdata[2]}<extra></extra>",
      }],
      layout: { height: 300, barcornerradius: 4, bargap: 0.4, margin: { l: 6, r: 6, t: 10, b: 30 }, yaxis: { range: [0, 45], ticksuffix: " %" }, xaxis: { tickfont: { color: ink(), size: 13 } } },
    };
  });
  const minNoParty = Math.ceil(H.unused_votes / 14);
  document.getElementById("pure-text").innerHTML =
    `Voliči v Řevnicích nevyužili <strong>${RV.int(H.unused_votes)}</strong> hlasů <span class="tag tag-fact">fakt</span>. To jde jen na lístku bez zakřížkované strany,
    takže takových lístků bylo nejméně ${minNoParty} <span class="tag tag-bound">jisté minimum</span>. Model jich odhaduje asi <strong>${RV.int(H.no_party_ballots)}</strong>
    (${RV.fmt(100 * H.no_party_ballots / H.valid_ballots, 0)}&nbsp;% lístků, 90&nbsp;%: ${RV.int(H.no_party_ballots_q05)}–${RV.int(H.no_party_ballots_q95)}) s průměrně asi ${H.no_party_mean_marks} křížky
    <span class="tag tag-model">model</span>. Tahle část je ze všech odhadů nejméně jistá – nejvíc by ji zpřesnil počet platných lístků v jednotlivých okrscích.`;

  /* =========================================================== 8 najdi kandidáta */
  const sel = document.getElementById("cand-select");
  sel.innerHTML = PARTIES.map((p) => `<optgroup label="${RV.esc(p)}">` + cands.filter((c) => c.party === p).sort((a, b) => a.position - b.position)
    .map((c) => `<option value="${RV.esc(c.party + "|" + c.position)}">${c.position}. ${RV.esc(c.name)}${c.elected ? " ✓" : ""}</option>`).join("") + `</optgroup>`).join("");
  sel.value = "ŠANCE|10";
  function renderCand() {
    const [p, pos] = sel.value.split("|");
    const c = cands.find((x) => x.party === p && x.position === +pos);
    const robust = { "stabilní": "stabilní", "střední": "středně jisté", "nestabilní": "nejisté (interval pořadí je široký)" }[c.robust] || c.robust;
    document.getElementById("cand-card").innerHTML =
      `<div class="head" style="--c:${RV.cssColor(c.party)}"><span class="av">${RV.esc(RV.initials(c.name))}</span><div><h3>${RV.esc(c.name)}</h3>` +
      `<span class="muted">${RV.esc(partyFull[c.party] || c.party)} · ${c.position}. místo · ${c.age} let · ${c.elected ? "<strong style='color:var(--good)'>zvolen(a)</strong>" : "nezvolen(a)"}</span></div></div>` +
      `<dl class="kv">
        <div><dt>Hlasy <span class="tag tag-fact">fakt</span></dt><dd>${RV.int(c.votes)}</dd></div>
        <div><dt>Po okrscích 1 / 2 / 3 / 4</dt><dd style="font-size:17px">${c.votes_precincts.join(" / ")}</dd></div>
        <div><dt>Osobní křížky – jisté minimum</dt><dd>${RV.int(c.lb)} <small>${c.lb ? "dokázáno" : "nelze dokázat"}</small></dd></div>
        <div><dt>Osobní křížky – odhad <span class="tag tag-model">model</span></dt><dd>≈ ${RV.int(c.C)} <small>${RV.int(c.C_q05)}–${RV.int(c.C_q95)}</small></dd></div>
        <div><dt>Podíl osobních na hlasech</dt><dd>${RV.pct(100 * c.C_share, 0)}</dd></div>
        <div><dt>Osobní efekt</dt><dd>${xFmt(c.mult)} <small>${xFmt(Math.exp(c.u_q05))}–${xFmt(Math.exp(c.u_q95))}</small></dd></div>
        <div><dt>Pořadí podle křížků (ze 120)</dt><dd>${RV.int(c.rank)}. <small>${RV.int(c.rank_q05)}.–${RV.int(c.rank_q95)}.</small></dd></div>
        <div><dt>Šance být v top 10</dt><dd>${RV.pct(100 * c.p_top10, 0)}</dd></div>
      </dl>` +
      `<p class="muted" style="margin:0;font-size:14px">Pořadí je ${robust}. Intervaly jsou 90%: s pravděpodobností 90&nbsp;% (podle modelu) leží skutečná hodnota uvnitř.
       Osobní efekt ×1 = tolik křížků jako typický kandidát na stejném místě stejné kandidátky.</p>`;
  }
  sel.addEventListener("change", renderCand);
  renderCand();

  /* =========================================================== 9 důvěra */
  RV.plot("#sens-chart", (w) => {
    const narrow = w < 560;
    const rows = C.sensitivity.slice().reverse();
    const main = (r) => r.label === "hlavní model";
    const PRETTY = {
      "hlavní model": "hlavní model ★",
      "P(K=0) prior 0,30": "méně stranických voličů bez křížků jinde",
      "P(K=0) prior 0,70": "víc stranických voličů bez křížků jinde",
      "ocas K: ratio 0,50 (krátký)": "málokdo dává hodně křížků jinde",
      "ocas K: ratio 0,85 (dlouhý)": "častěji hodně křížků jinde",
      "m̄ prior rovnoměrný": "lístky bez strany: neutrální předpoklad",
      "m̄ prior vysoký (Beta 5,2)": "lístky bez strany: hodně křížků",
      "efekt pozice: prior β ~ N(0, 1)": "výhoda pozice: volnější předpoklad",
      "σ_u prior úzký (HN 0,25)": "osobnosti: menší rozdíly",
      "σ_u prior široký (HN 1,5)": "osobnosti: větší rozdíly",
      "likelihood Poisson": "jiný model náhodného šumu",
      "bez saturace (1 křížek/lístek ignorován)": "bez pravidla „1 křížek na osobu“",
    };
    const pretty = (l) => PRETTY[l] || l;
    return {
      data: [{
        type: "scatter", mode: "markers", y: rows.map((r) => pretty(r.label)), x: rows.map((r) => r.C),
        marker: { size: rows.map((r) => (main(r) ? 13 : 10)), color: rows.map((r) => (main(r) ? RV.token("warm") : ink2())), line: { color: surface(), width: 2 } },
        error_x: { type: "data", symmetric: false, array: rows.map((r) => r.C_q95 - r.C), arrayminus: rows.map((r) => r.C - r.C_q05), color: RV.token("line-strong"), thickness: 3, width: 0 },
        customdata: rows.map((r) => [RV.int(r.C_q05), RV.int(r.C_q95), RV.int(r.cervena), RV.esc(r.label)]),
        hovertemplate: "<b>%{y}</b><br>≈ %{x:,.0f} křížků (90 %: %{customdata[0]}–%{customdata[1]})<br>T. Červená ≈ %{customdata[2]}<br>technicky: %{customdata[3]}<extra></extra>",
      }],
      layout: {
        height: narrow ? 520 : 500, margin: { l: 6, r: 14, t: 24, b: 40 },
        xaxis: { range: [0, 9500], title: { text: "osobní křížky celkem" } }, yaxis: { tickfont: { color: ink(), size: narrow ? 11 : 12 } },
        shapes: [{ type: "line", x0: H.lb_lp, x1: H.lb_lp, yref: "paper", y0: 0, y1: 1, line: { color: RV.token("accent"), width: 2 } }],
        annotations: [{ x: H.lb_lp, y: 1, yref: "paper", yanchor: "bottom", xanchor: "right", showarrow: false, text: `jisté minimum ${RV.int(H.lb_lp)}`, font: { size: 11.5, color: RV.token("accent") } }],
      },
    };
  });
  const scen = { A_malo_krizku: "Málo křížků", B_hodne_krizku: "Hodně křížků", D_ruzne_strany: "Kandidátky se liší" };
  RV.plot("#rec-chart", () => {
    const rows = C.recovery;
    const y = rows.map((r) => scen[r.scenario] || r.scenario);
    return {
      data: [{
        type: "scatter", mode: "markers", name: "skutečnost", y, x: rows.map((r) => r.true),
        marker: { symbol: "diamond", size: 14, color: ink() }, hovertemplate: "skutečně %{x:,.0f} křížků<extra></extra>",
      }, {
        type: "scatter", mode: "markers", name: "odhad modelu", y, x: rows.map((r) => r.est),
        marker: { size: 12, color: RV.token("warm"), line: { color: surface(), width: 2 } },
        error_x: { type: "data", symmetric: false, array: rows.map((r) => r.hi - r.est), arrayminus: rows.map((r) => r.est - r.lo), color: RV.alpha(RV.token("warm"), 0.6), thickness: 3, width: 0 },
        hovertemplate: "model %{x:,.0f} křížků<extra></extra>",
      }],
      layout: {
        height: 250, margin: { l: 6, r: 14, t: 8, b: 40 }, showlegend: true,
        legend: { orientation: "h", y: -0.32, x: 0, font: { size: 12.5, color: ink2() } },
        xaxis: { rangemode: "tozero", title: { text: "osobní křížky celkem" } }, yaxis: { tickfont: { color: ink(), size: 13 } },
      },
    };
  });
  const rc = C.recovery.map((r) => r.rank_corr);
  document.getElementById("rec-text").innerHTML =
    `<p style="font-size:15px">Celkový počet model trefil s chybou ${RV.signed(100 * H.recovery_err_min)} až ${RV.signed(100 * H.recovery_err_max)}&nbsp;% a spíš podstřeluje.
     Pořadí kandidátů ale sedí výborně: shoda pořadí s pravdou ${RV.fmt(Math.min(...rc), 2)}–${RV.fmt(Math.max(...rc), 2)} (1 = dokonalá) a všech 15 nejsilnějších kandidátů
     model pokaždé našel mezi svými top 20.</p>`;
})();
