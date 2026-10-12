/* Výsledky v kostce – interaktivní verze infografiky */
(function () {
  "use strict";
  const RV = window.RV;
  RV.init("vysledky");
  const D = RV.data.zakladni;
  if (!D) return;
  const T = D.totals, TU = D.turnout, F = D.facts;
  const P = D.parties.filter((p) => p.votes_2026 > 0);           // 8 kandidátek 2026, seřazeno podle hlasů
  const byShort = Object.fromEntries(D.parties.map((p) => [p.short, p]));
  const PCS = D.precincts;
  const FONT = "Inter, system-ui, sans-serif";
  const ink = () => RV.token("ink"), ink2 = () => RV.token("ink-2"), muted = () => RV.token("muted");
  const surface = () => RV.token("surface");
  document.querySelectorAll('[data-k="change_pct"]').forEach((e) => { e.textContent = RV.fmt(T.change_pct, 2); });

  /* =========================================================== 1 dlaždice */
  const top = F.top_candidate;
  const tiles = [
    ["Volební účast", RV.pct(TU.turnout_pct, 2), `<span class="delta-up">${RV.pp(TU.turnout_change_pp)}</span> proti 2022 (${RV.pct(TU.turnout_2022_pct, 2)})`],
    ["Platné hlasy", RV.int(T.votes_2026), `<span class="delta-up">${RV.signed(T.change_votes)}</span> proti 2022 (${RV.signed(T.change_pct, 2)}&nbsp;%)`],
    ["Lístky s platným hlasem", RV.int(TU.valid_ballots), `${RV.int(TU.envelopes)} vydaných a ${RV.int(TU.envelopes_submitted)} odevzdaných obálek, ${RV.int(TU.registered_voters)} voličů v seznamu`],
    ["Hlasů na jeden lístek", RV.fmt(T.votes_per_ballot, 2) + " <small>z 15</small>", `voliči nevyužili ${RV.int(T.unused_votes)} hlasů`],
    ["Hlasy bez zastoupení", RV.int(T.unrepresented_votes), `${RV.pct(T.unrepresented_pct, 2)} · ODS a Srdce Řevnic pod 5&nbsp;%`],
    ["Nejvíc preferenčních hlasů", RV.int(top.votes), `${RV.esc(top.name)} (${RV.esc(top.party)}, 1. místo)`],
    ["Ženy mezi zvolenými", `${T.women_elected} <small>z 15</small>`, `průměrný věk zastupitelů ${RV.fmt(T.avg_age_elected, 1)} let`],
    ["Kandidátů", RV.int(T.candidates), `8 kandidátek po 15 lidech · věk ${F.youngest[0].age}–${F.oldest[0].age} let`],
  ];
  document.getElementById("tiles").innerHTML = tiles.map(([l, v, s]) =>
    `<div class="card stat"><span class="label">${l}</span><span class="value">${v}</span><span class="sub">${s}</span></div>`).join("");

  /* =========================================================== 2 kandidátky */
  let partiesMode = "share";
  const drawParties = RV.plot("#parties-chart", (w) => {
    const narrow = w < 560;
    const rows = P.slice().reverse();
    const isShare = partiesMode === "share";
    const val = (p) => isShare ? p.share_2026 : p.votes_2026;
    const xmax = Math.max(...P.map(val)) * (narrow ? 1.3 : 1.42);
    const label = (p) => (isShare ? RV.pct(p.share_2026, 2) : RV.int(p.votes_2026)) + (narrow ? "" :
      (p.seats_2026 ? `  ·  ${p.seats_2026} ${RV.plural(p.seats_2026, "mandát", "mandáty", "mandátů")}` : "  ·  bez mandátu"));
    const ylab = (p) => (narrow ? `${p.short} <b>${p.seats_2026}</b>` : p.short);
    const traces = [{
      type: "bar", orientation: "h", y: rows.map(ylab), x: rows.map(val),
      marker: { color: rows.map((p) => RV.color(p.short)), line: { width: 0 } },
      text: rows.map(label), textposition: "outside", cliponaxis: false,
      textfont: { color: ink(), size: narrow ? 12 : 13.5, family: FONT },
      customdata: rows.map((p) => [p.name, RV.int(p.votes_2026), RV.pct(p.share_2026, 2), p.seats_2026, p.votes_2022 ? RV.pct(p.share_2022, 2) : "nekandidovalo"]),
      hovertemplate: "<b>%{customdata[0]}</b><br>%{customdata[1]} hlasů · %{customdata[2]}<br>mandáty: %{customdata[3]}<br>2022: %{customdata[4]}<extra></extra>",
    }];
    const shapes = isShare ? [{ type: "line", x0: 5, x1: 5, yref: "paper", y0: 0, y1: 1, line: { color: muted(), width: 1.5 } }] : [];
    return {
      data: traces,
      layout: {
        height: narrow ? 380 : 400, barcornerradius: 4, bargap: 0.32,
        margin: { l: 6, r: 6, t: 24, b: 30 },
        xaxis: { range: [0, xmax], showgrid: true, ticksuffix: isShare ? " %" : "", zeroline: false },
        yaxis: { tickfont: { color: ink(), size: 14 }, showgrid: false },
        shapes,
        annotations: isShare ? [{ x: 5, y: 1, yref: "paper", yanchor: "bottom", text: "hranice 5 %", showarrow: false, font: { size: 12, color: muted() } }] : [],
      },
    };
  });
  RV.seg("#parties-seg", (v) => {
    partiesMode = v;
    document.getElementById("parties-title").textContent = v === "share" ? "Podíl hlasů 2026" : "Počet hlasů 2026";
    drawParties();
  });
  document.getElementById("parties-table").innerHTML =
    `<table class="data"><thead><tr><th>Kandidátka</th><th class="r">Hlasy 2026</th><th class="r">Podíl</th><th class="r">Mandáty</th><th class="r">Hlasy 2022</th><th class="r">Podíl 2022</th><th class="r">Mandáty 2022*</th></tr></thead><tbody>` +
    D.parties.map((p) => `<tr><td>${RV.partyLabel(p.short)} <span class="muted">${p.name !== p.short ? RV.esc(p.name) : ""}</span></td>` +
      `<td class="r">${p.votes_2026 ? RV.int(p.votes_2026) : "–"}</td><td class="r">${p.votes_2026 ? RV.pct(p.share_2026, 2) : "–"}</td><td class="r">${p.seats_2026}</td>` +
      `<td class="r">${p.votes_2022 ? RV.int(p.votes_2022) : "–"}</td><td class="r">${p.votes_2022 ? RV.pct(p.share_2022, 2) : "–"}</td><td class="r">${p.votes_2022 ? p.seats_2022 : "–"}</td></tr>`).join("") +
    `</tbody></table><p class="chart-note">* mandáty 2022 přepočtené d’Hondtovou metodou ze zveřejněných hlasů.</p>`;

  /* =========================================================== 3 kdo reprezentuje kolik voličů */
  // Hrubý ekvivalent voličů: hlasy kandidátky / 15. Zbytek do voličů v seznamu = nepřišli + nevyužité hlasy.
  const SEATS = D.meta.seats;
  const REG = TU.registered_voters;
  const invalid = TU.envelopes_submitted - TU.valid_ballots;      // odevzdané obálky bez platného hlasu
  const notSubmitted = TU.envelopes - TU.envelopes_submitted;      // obálku si vzal, ale neodevzdal → nechtěl volit
  const absent = REG - TU.envelopes_submitted;
  const unusedEq = T.unused_votes / SEATS;
  const REST = "Nechtějí ostatním přikazovat, jak mají žít";
  const repRows = P.map((p) => ({ key: p.short, label: p.short, n: p.votes_2026 / SEATS, seats: p.seats_2026, color: () => RV.color(p.short), css: RV.cssColor(p.short), light: p.short === "ŠANCE" }))
    .concat([
      { key: "invalid", label: "Neplatné hlasy", n: invalid, seats: null, color: () => RV.token("muted"), css: "var(--muted)" },
      { key: "rest", label: REST, n: REG - T.votes_2026 / SEATS - invalid, seats: null, color: () => RV.token("line-strong"), css: "var(--line-strong)", light: true },
    ]);
  repRows.forEach((r) => { r.pct = 100 * r.n / REG; });
  document.querySelectorAll('[data-k="registered"]').forEach((e) => { e.textContent = RV.int(REG); });
  document.querySelectorAll('[data-k="top_share"]').forEach((e) => { e.textContent = RV.pct(repRows[0].pct, 1); });
  RV.plot("#rep-chart", (w) => {
    const narrow = w < 460;
    const big = (r) => r.pct >= (narrow ? 8 : 5);
    return {
      data: [{
        type: "pie", sort: false, direction: "clockwise", rotation: 0, hole: 0,
        labels: repRows.map((r) => r.label), values: repRows.map((r) => r.n),
        marker: { colors: repRows.map((r) => r.color()), line: { color: surface(), width: 2 } },
        text: repRows.map((r) => (big(r) ? (r.key === "rest" ? (narrow ? "Nechtějí ostatním<br>přikazovat,<br>jak mají žít" : "Nechtějí ostatním<br>přikazovat, jak mají žít") + `<br><b>${RV.pct(r.pct, 1)}</b>` : `<b>${RV.esc(r.label)}</b><br>${RV.pct(r.pct, 1)}`) : "")),
        textinfo: "text", textposition: "inside", insidetextorientation: "horizontal",
        insidetextfont: { family: FONT, size: narrow ? 13 : 15, color: repRows.map((r) => (r.light ? ink() : "#ffffff")) },
        customdata: repRows.map((r) => [RV.fmt(r.n, 1), RV.pct(r.pct, 1)]),
        hovertemplate: "<b>%{label}</b><br>≈ %{customdata[0]} voličů · %{customdata[1]}<extra></extra>",
      }],
      layout: { height: narrow ? 360 : 460, margin: { l: 8, r: 8, t: 8, b: 8 } },
    };
  });
  document.getElementById("rep-table").innerHTML =
    `<table class="data"><thead><tr><th>Koho volili</th><th class="r">Voličů ≈</th><th class="r">Podíl</th><th class="r">Mandáty</th></tr></thead><tbody>` +
    repRows.map((r) => `<tr${r.key === "rest" ? ' style="font-weight:650"' : ""}><td><span class="party"${r.key === "rest" ? ' style="white-space:normal"' : ""}><span class="sw" style="--c:${r.css}"></span>${RV.esc(r.label)}</span></td>` +
      `<td class="r">${RV.fmt(r.n, 1)}</td><td class="r">${RV.pct(r.pct, 1)}</td><td class="r">${r.seats == null ? "" : r.seats}</td></tr>`).join("") +
    `</tbody></table>`;
  document.getElementById("rep-note").innerHTML =
    `Metodika: hlasy kandidátky / ${SEATS} = hrubý odhad počtu voličů. Kdo nevyužil všech ${SEATS} hlasů, ten se svými nevyužitými hlasy ` +
    `počítá do skupiny „${REST}“ – stejně jako ti, kdo k volbám nepřišli. Ta skupina tedy zahrnuje ${RV.int(absent)} voličů, kteří neodevzdali obálku ` +
    `(z toho ${RV.int(notSubmitted)} si obálku vzal, ale do urny ji nevhodil), a ${RV.fmt(unusedEq, 1)} voliče jako ekvivalent ${RV.int(T.unused_votes)} nevyužitých hlasů. ` +
    `Neplatné hlasy = ${RV.int(TU.envelopes_submitted)} odevzdaných obálek minus ${RV.int(TU.valid_ballots)} lístků s platným hlasem.`;

  /* =========================================================== 4 změna proti 2022 */
  let changeMode = "votes";
  const drawChange = RV.plot("#change-chart", (w) => {
    const narrow = w < 560;
    const isVotes = changeMode === "votes";
    const rows = D.parties.slice().sort((a, b) => (isVotes ? a.change_votes - b.change_votes : a.change_pp - b.change_pp));
    const val = (p) => (isVotes ? p.change_votes : p.change_pp);
    const note = (p) => (!p.votes_2022 ? " (nová)" : !p.votes_2026 ? (narrow ? " (2022)" : " (jen 2022)") : "");
    const lo = Math.min(...rows.map(val)), hi = Math.max(...rows.map(val));
    return {
      data: [{
        type: "bar", orientation: "h", y: rows.map((p) => p.short + note(p)), x: rows.map(val),
        marker: { color: rows.map((p) => RV.color(p.short)) },
        text: rows.map((p) => (isVotes ? RV.signed(p.change_votes) : RV.pp(p.change_pp, narrow ? 1 : 2))),
        textposition: "outside", cliponaxis: false, textfont: { color: ink(), size: narrow ? 11.5 : 13, family: FONT },
        customdata: rows.map((p) => [p.name, p.votes_2022 ? RV.int(p.votes_2022) : "–", p.votes_2026 ? RV.int(p.votes_2026) : "–", RV.pp(p.change_pp)]),
        hovertemplate: "<b>%{customdata[0]}</b><br>2022: %{customdata[1]} hlasů<br>2026: %{customdata[2]} hlasů<br>podíl: %{customdata[3]}<extra></extra>",
      }],
      layout: {
        height: 420, barcornerradius: 4, margin: { l: 6, r: 10, t: 6, b: 30 },
        xaxis: { range: [lo - (hi - lo) * (narrow ? 0.42 : 0.26), hi + (hi - lo) * (narrow ? 0.4 : 0.2)], zeroline: true, zerolinecolor: ink2(), zerolinewidth: 1.5, ticksuffix: isVotes ? "" : " p. b." },
        yaxis: { tickfont: { color: ink(), size: 14 }, showgrid: false },
      },
    };
  });
  RV.seg("#change-seg", (v) => {
    changeMode = v;
    document.getElementById("change-title").textContent = v === "votes" ? "Změna počtu hlasů" : "Změna podílu hlasů (procentní body)";
    drawChange();
  });

  /* =========================================================== 5 okrsky */
  let selPc = 4, mapMode = "winner";
  const mapModeEl = document.getElementById("map-mode");
  mapModeEl.innerHTML = `<button type="button" class="chip" data-v="winner" aria-pressed="true">Vítěz okrsku</button>` +
    P.map((p) => `<button type="button" class="chip" data-v="${RV.esc(p.short)}" aria-pressed="false"><span class="sw" style="--c:${RV.cssColor(p.short)}"></span>${RV.esc(p.short)}</button>`).join("");
  mapModeEl.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
    mapModeEl.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
    mapMode = b.dataset.v; paintMap();
  }));
  function paintMap() {
    const legend = document.getElementById("map-legend");
    if (mapMode === "winner") {
      PCS.forEach((pc) => {
        const el = document.querySelector(`#map .pc[data-p="${pc.id}"]`);
        el.style.fill = RV.cssColor(pc.winner); el.style.fillOpacity = 1;
      });
      const ws = [...new Set(PCS.map((p) => p.winner))];
      legend.innerHTML = ws.map((w) => `<span><span class="sw" style="--c:${RV.cssColor(w)}"></span>${RV.esc(w)} – okrsky ${PCS.filter((p) => p.winner === w).map((p) => p.id).join(" a ")}</span>`).join("");
    } else {
      const sh = PCS.map((pc) => pc.shares[mapMode]);
      const lo = Math.min(...sh), hi = Math.max(...sh);
      PCS.forEach((pc) => {
        const el = document.querySelector(`#map .pc[data-p="${pc.id}"]`);
        const t = hi > lo ? (pc.shares[mapMode] - lo) / (hi - lo) : 1;
        el.style.fill = RV.cssColor(mapMode); el.style.fillOpacity = (0.22 + 0.78 * t).toFixed(2);
      });
      legend.innerHTML = `<span>${RV.partyLabel(mapMode)}: nejslabší v okrsku ${PCS[sh.indexOf(lo)].id} (${RV.pct(lo)}), nejsilnější v okrsku ${PCS[sh.indexOf(hi)].id} (${RV.pct(hi)})</span>`;
    }
    document.querySelectorAll("#map .pc").forEach((el) => {
      const sel = +el.dataset.p === selPc;
      el.style.stroke = sel ? RV.token("ink") : ""; el.style.strokeWidth = sel ? 5 : "";
      el.setAttribute("aria-pressed", sel ? "true" : "false");
      const pc = PCS.find((p) => p.id === +el.dataset.p);
      el.setAttribute("aria-label", `Okrsek ${pc.id} (${pc.label}), vyhrálo ${pc.winner}`);
    });
  }
  function selectPc(id) {
    selPc = +id;
    document.querySelectorAll("#pc-seg button").forEach((b) => b.setAttribute("aria-pressed", +b.dataset.v === selPc ? "true" : "false"));
    paintMap(); drawPc(); drawTurnout();
  }
  document.querySelectorAll("#map .pc").forEach((el) => {
    el.addEventListener("click", () => selectPc(el.dataset.p));
    el.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); selectPc(el.dataset.p); } });
  });
  RV.seg("#pc-seg", (v) => selectPc(v));

  const drawPc = RV.plot("#pc-chart", (w) => {
    const pc = PCS.find((p) => p.id === selPc);
    document.getElementById("pc-title").textContent = `Okrsek ${pc.id} · ${pc.label}`;
    document.getElementById("pc-sub").innerHTML = `Účast ${RV.pct(pc.turnout_pct, 2)} · ${RV.int(pc.votes_total)} hlasů · vyhrálo <strong>${RV.esc(pc.winner)}</strong>`;
    const rows = P.slice().sort((a, b) => pc.shares[a.short] - pc.shares[b.short]);
    const narrow = w < 520;
    return {
      data: [{
        type: "bar", orientation: "h", y: rows.map((p) => p.short), x: rows.map((p) => pc.shares[p.short]),
        marker: { color: rows.map((p) => RV.color(p.short)) },
        text: rows.map((p) => RV.pct(pc.shares[p.short], 1)), textposition: "outside", cliponaxis: false,
        textfont: { color: ink(), size: 13, family: FONT },
        customdata: rows.map((p) => [RV.int(pc.votes[p.short]), RV.pct(p.share_2026, 1)]),
        hovertemplate: "<b>%{y}</b><br>%{customdata[0]} hlasů (%{x:.2f} %)<br>celé město: %{customdata[1]}<extra></extra>",
      }, {
        type: "scatter", mode: "markers", y: rows.map((p) => p.short), x: rows.map((p) => p.share_2026),
        marker: { symbol: "line-ns", size: 18, line: { width: 2.5, color: ink() } },
        hovertemplate: "celé město: %{x:.2f} %<extra></extra>",
      }],
      layout: {
        height: narrow ? 330 : 350, barcornerradius: 4, margin: { l: 6, r: 8, t: 6, b: 28 },
        xaxis: { range: [0, 34], ticksuffix: " %" }, yaxis: { tickfont: { color: ink(), size: 13.5 }, showgrid: false },
        annotations: [{ xref: "paper", yref: "paper", x: 1, y: 0.02, xanchor: "right", showarrow: false, text: "┃ = celé město", font: { size: 12, color: muted() } }],
      },
    };
  });

  const drawTurnout = RV.plot("#turnout-chart", () => ({
    data: [{
      type: "bar", x: PCS.map((p) => `Okrsek ${p.id}`), y: PCS.map((p) => p.turnout_pct),
      marker: { color: PCS.map((p) => (p.id === selPc ? RV.token("accent") : RV.alpha(RV.token("accent"), 0.38))) },
      text: PCS.map((p) => RV.pct(p.turnout_pct, 2)), textposition: "outside", cliponaxis: false,
      textfont: { color: ink(), size: 13, family: FONT },
      customdata: PCS.map((p) => p.label), hovertemplate: "<b>%{x}</b> (%{customdata})<br>účast %{y:.2f} %<extra></extra>",
    }],
    layout: {
      height: 400, barcornerradius: 4, bargap: 0.4, margin: { l: 6, r: 6, t: 26, b: 30 },
      yaxis: { range: [0, 80], ticksuffix: " %" }, xaxis: { tickfont: { color: ink(), size: 13 } },
      shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: TU.turnout_pct, y1: TU.turnout_pct, line: { color: ink2(), width: 1.5 } }],
      annotations: [{ xref: "paper", x: 0, y: TU.turnout_pct, xanchor: "left", yanchor: "top", yshift: -2, showarrow: false, text: `celé město ${RV.pct(TU.turnout_pct, 2)}`, font: { size: 12, color: ink2() } }],
    },
  }));

  // co kdyby
  let whatMode = "without";
  function renderWhatIf() {
    const id = +document.getElementById("whatif-pc").value;
    const pc = PCS.find((p) => p.id === id);
    const votes = whatMode === "without" ? pc.city_without : pc.votes;
    const res = RV.dhondt(votes);
    const rows = P.map((p) => ({ p: p.short, v: votes[p.short], s: res.seats[p.short], real: p.seats_2026 })).sort((a, b) => b.v - a.v);
    const tot = res.total, max = rows[0].v;
    const head = whatMode === "without"
      ? `Bez okrsku ${id} by vyhrála <strong>${RV.esc(rows[0].p)}</strong> (${RV.int(rows[0].v)} hlasů), druhá ${RV.esc(rows[1].p)} (${RV.int(rows[1].v)}).`
      : `Kdyby volil jen okrsek ${id}, vyhrála by <strong>${RV.esc(rows[0].p)}</strong> (${RV.pct(100 * rows[0].v / tot)}).`;
    document.getElementById("whatif-out").innerHTML = `<p style="font-size:15.5px">${head}</p><div class="results">` +
      rows.map((r) => {
        const d = r.s - r.real;
        const out = r.v < 0.05 * tot;
        return `<div class="res-row${out ? " out" : ""}" style="--c:${RV.cssColor(r.p)};grid-template-columns:minmax(96px,1fr) minmax(0,2fr) 64px 92px">` +
          `<span class="nm">${RV.esc(r.p)}</span><span class="bar"><i style="width:${(96 * r.v) / max}%"></i></span>` +
          `<span class="pct" style="font-weight:600">${RV.pct(100 * r.v / tot)}</span>` +
          `<span class="seats" title="mandáty">${r.s ? Array.from({ length: r.s }, () => "<i></i>").join("") : '<span class="zero">0</span>'}` +
          `${d ? `<span style="font-size:12px;font-weight:700;margin-left:4px;color:var(${d > 0 ? "--good" : "--bad"})">${d > 0 ? "+" : "−"}${Math.abs(d)}</span>` : ""}</span></div>`;
      }).join("") + `</div><p class="chart-note">Tečky = mandáty v tomto scénáři, číslo = rozdíl proti skutečnosti.</p>`;
  }
  RV.seg("#whatif-mode", (v) => { whatMode = v; renderWhatIf(); });
  document.getElementById("whatif-pc").addEventListener("change", renderWhatIf);

  // tabulka okrsků
  function pcTable() {
    const cols = PCS.map((p) => p.id);
    const html = [`<table class="data"><thead><tr><th>Kandidátka</th>${cols.map((c) => `<th class="r">Okrsek ${c}</th>`).join("")}<th class="r">Město</th></tr></thead><tbody>`];
    html.push(`<tr><td class="muted">Volební účast</td>${PCS.map((p) => `<td class="r">${RV.pct(p.turnout_pct, 2)}</td>`).join("")}<td class="r">${RV.pct(TU.turnout_pct, 2)}</td></tr>`);
    P.forEach((p) => {
      html.push(`<tr><td>${RV.partyLabel(p.short)}</td>` + PCS.map((pc) => {
        const s = pc.shares[p.short], win = pc.winner === p.short;
        return `<td class="r" style="background:color-mix(in srgb, ${RV.cssColor(p.short)} ${Math.round(s * 2.2)}%, transparent);${win ? "font-weight:750" : ""}">${RV.pct(s, 2)}</td>`;
      }).join("") + `<td class="r" style="font-weight:600">${RV.pct(p.share_2026, 2)}</td></tr>`);
    });
    html.push(`<tr><td class="muted">Hlasů celkem</td>${PCS.map((p) => `<td class="r">${RV.int(p.votes_total)}</td>`).join("")}<td class="r">${RV.int(T.votes_2026)}</td></tr></tbody></table>`);
    document.getElementById("pc-table").innerHTML = html.join("");
  }
  paintMap(); renderWhatIf(); pcTable();
  document.addEventListener("rv-theme", paintMap);

  /* =========================================================== 6 zvolení */
  const jumped = D.elected.filter((e) => e.jumped).length;
  document.getElementById("jumped-text").textContent =
    `${["Žádný", "Jeden", "Dva", "Tři", "Čtyři", "Pět", "Šest", "Sedm"][jumped] || jumped} ${RV.plural(jumped, "zvolený", "zvolení", "zvolených")}`;
  document.getElementById("elected").innerHTML = D.elected.map((e, i) => {
    const party = byShort[e.party];
    return `<button type="button" class="person" style="--c:${RV.cssColor(e.party)}" data-party="${RV.esc(e.party)}" data-pos="${e.position}">` +
      (e.jumped ? `<span class="badge">z ${e.position}. místa</span>` : "") +
      `<span class="av">${i + 1}</span><span><span class="nm">${RV.esc(e.name)}</span><br>` +
      `<span class="meta">${RV.esc(party.short)} · ${e.position}. místo · <strong style="color:var(--ink)">${RV.int(e.votes)}</strong> hlasů</span></span></button>`;
  }).join("");
  document.querySelectorAll("#elected .person").forEach((b) => b.addEventListener("click", () => {
    selectParty(b.dataset.party, +b.dataset.pos);
    document.getElementById("kandidati").scrollIntoView({ behavior: "smooth" });
  }));

  /* =========================================================== 7 kandidáti zblízka */
  let candParty = "ŠANCE", candHl = 10, candScope = "city";
  const cp = document.getElementById("cand-party");
  cp.innerHTML = P.map((p) => `<button type="button" class="chip" data-v="${RV.esc(p.short)}" aria-pressed="${p.short === candParty}"><span class="sw" style="--c:${RV.cssColor(p.short)}"></span>${RV.esc(p.short)}</button>`).join("");
  cp.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => selectParty(b.dataset.v, null)));
  function selectParty(p, pos) {
    candParty = p; candHl = pos;
    cp.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x.dataset.v === p ? "true" : "false"));
    drawCand();
  }
  RV.seg("#cand-scope", (v) => { candScope = v; drawCand(); });
  const drawCand = RV.plot("#cand-chart", (w) => {
    const party = byShort[candParty];
    const cands = D.candidates.filter((c) => c.party === candParty).sort((a, b) => b.position - a.position);
    const narrow = w < 560;
    const avg = party.votes_2026 / 15, thr = party.pref_threshold;
    document.getElementById("cand-title").textContent = party.name;
    document.getElementById("cand-sub").innerHTML =
      `${RV.int(party.votes_2026)} hlasů · ${party.seats_2026} ${RV.plural(party.seats_2026, "mandát", "mandáty", "mandátů")} · průměr na kandidáta ${RV.fmt(avg, 1)} · hranice přednosti <strong>${RV.fmt(thr, 1)}</strong> hlasů`;
    const col = RV.color(candParty);
    const lab = (c) => `${c.position}. ${narrow ? c.name.split(" ").slice(-1)[0] : c.name}`;
    const ylab = cands.map((c) => (c.elected ? `<b>${RV.esc(lab(c))}</b>` : RV.esc(lab(c))));
    const hl = cands.map((c) => c.position === candHl);
    const common = {
      customdata: cands.map((c) => [c.name, c.age, RV.int(c.votes), c.votes_precincts.join(" / "), c.elected ? "zvolen(a)" : "nezvolen(a)", c.preference ? "ano" : "ne"]),
      hovertemplate: "<b>%{customdata[0]}</b> (%{customdata[1]} let)<br>%{customdata[2]} hlasů · %{customdata[4]}<br>po okrscích 1/2/3/4: %{customdata[3]}<br>nad hranicí přednosti: %{customdata[5]}<extra></extra>",
    };
    let data;
    if (candScope === "city") {
      data = [Object.assign({
        type: "bar", orientation: "h", y: ylab, x: cands.map((c) => c.votes),
        marker: { color: cands.map((c) => (c.elected ? col : RV.alpha(col, 0.38))), line: { color: hl.map((h) => (h ? ink() : "rgba(0,0,0,0)")), width: hl.map((h) => (h ? 2 : 0)) } },
        text: cands.map((c) => RV.int(c.votes)), textposition: "outside", cliponaxis: false, textfont: { color: ink2(), size: 12.5, family: FONT },
      }, common)];
    } else {
      const alphas = [0.3, 0.52, 0.76, 1];
      data = [0, 1, 2, 3].map((k) => Object.assign({
        type: "bar", orientation: "h", y: ylab, x: cands.map((c) => c.votes_precincts[k]), name: `okrsek ${k + 1}`,
        marker: { color: RV.alpha(col, alphas[k]), line: { color: surface(), width: 1 } },
      }, common, {
        customdata: cands.map((c) => [c.name, k + 1, c.votes_precincts[k], RV.int(c.votes)]),
        hovertemplate: "<b>%{customdata[0]}</b><br>okrsek %{customdata[1]}: %{customdata[2]} hlasů<br>celkem %{customdata[3]}<extra></extra>",
      }));
    }
    const xmax = Math.max(...cands.map((c) => c.votes)) * 1.14;
    return {
      data,
      layout: {
        height: narrow ? 520 : 560, barmode: "stack", barcornerradius: 3, bargap: 0.22,
        margin: { l: 6, r: 10, t: 26, b: 30 },
        xaxis: { range: [0, xmax] }, yaxis: { tickfont: { color: ink(), size: narrow ? 12 : 13 }, showgrid: false },
        shapes: candScope === "city" ? [{ type: "line", x0: thr, x1: thr, yref: "paper", y0: 0, y1: 1, line: { color: ink(), width: 1.5, dash: "dot" } }] : [],
        annotations: candScope === "city" ? [{ x: thr, y: 1, yref: "paper", yanchor: "bottom", xanchor: thr > xmax * 0.7 ? "right" : "left", showarrow: false,
          text: `hranice přednosti ${RV.fmt(thr, 1)}`, font: { size: 12, color: ink() } }] : [],
        showlegend: candScope !== "city", legend: { orientation: "h", y: 1.06, x: 0, font: { size: 12.5, color: ink2() } },
      },
    };
  });
  document.getElementById("cand-legend").innerHTML =
    `<span><span class="sw" style="--c:var(--ink-2)"></span><strong>Tučně a plnou barvou</strong> = zvolen(a)</span><span><span class="sw" style="--c:var(--line-strong)"></span>světlá = nezvolen(a)</span>`;

  const yo = F.youngest, ol = F.oldest;
  const ageByParty = P.slice().sort((a, b) => a.avg_age - b.avg_age);
  document.getElementById("age-facts").innerHTML = [
    ["Průměrný věk", `${RV.fmt(T.avg_age_candidates, 1)} <small>let</small>`, `všech kandidátů; zvolených ${RV.fmt(T.avg_age_elected, 1)} let`],
    ["Nejmladší kandidát", `${yo[0].age} <small>let</small>`, yo.map((c) => `${RV.esc(c.name)} (${RV.esc(c.party)})`).join(", ")],
    ["Nejstarší kandidáti", `${ol[0].age} <small>let</small>`, ol.map((c) => `${RV.esc(c.name)} (${RV.esc(c.party)})`).join(" a ")],
  ].map(([l, v, s]) => `<div class="card stat reveal in"><span class="label">${l}</span><span class="value">${v}</span><span class="sub">${s}</span></div>`).join("") +
    `<div class="card reveal in" style="grid-column:1/-1"><span class="label muted" style="font-size:13.5px;font-weight:560">Průměrný věk kandidátky</span>
     <div class="chips" style="margin-top:8px">${ageByParty.map((p) => `<span class="chip" style="cursor:default"><span class="sw" style="--c:${RV.cssColor(p.short)}"></span>${RV.esc(p.short)} <strong>${RV.fmt(p.avg_age, 1)}</strong></span>`).join("")}</div></div>`;

  /* =========================================================== 8 osobní změny */
  RV.plot("#personal-chart", (w) => {
    const narrow = w < 560;
    const rows = D.elected.filter((e) => e.votes_2022).map((e) => Object.assign({ d: e.votes - e.votes_2022 }, e)).sort((a, b) => a.d - b.d);
    const y = rows.map((e) => (narrow ? e.name.split(" ").slice(-1)[0] : e.name));
    const lines = rows.map((e, i) => ({ type: "line", x0: e.votes_2022, x1: e.votes, y0: y[i], y1: y[i], line: { color: RV.token("line-strong"), width: 3 } }));
    return {
      data: [{
        type: "scatter", mode: "markers", x: rows.map((e) => e.votes_2022), y, marker: { size: 12, color: muted(), line: { color: surface(), width: 2 } },
        customdata: rows.map((e) => [e.name, e.party_2022]), hovertemplate: "<b>%{customdata[0]}</b><br>2022: %{x} hlasů (%{customdata[1]})<extra></extra>",
      }, {
        type: "scatter", mode: "markers+text", x: rows.map((e) => e.votes), y,
        marker: { size: 15, color: rows.map((e) => RV.color(e.party)), line: { color: surface(), width: 2 } },
        text: rows.map((e) => `  ${RV.signed(e.d)}`), textposition: rows.map((e) => (e.d >= 0 ? "middle right" : "middle left")),
        textfont: { color: rows.map((e) => (e.d >= 0 ? RV.token("good") : RV.token("bad"))), size: 13, family: FONT },
        customdata: rows.map((e) => [e.name, e.party, RV.signed(e.d)]),
        hovertemplate: "<b>%{customdata[0]}</b><br>2026: %{x} hlasů (%{customdata[1]})<br>změna %{customdata[2]}<extra></extra>",
      }],
      layout: {
        height: 420, margin: { l: 6, r: 20, t: 10, b: 36 }, shapes: lines,
        xaxis: { range: [120, 540], title: { text: "preferenční hlasy" } }, yaxis: { tickfont: { color: ink(), size: 13.5 }, showgrid: false },
      },
    };
  });

  /* =========================================================== 9 těsné momenty */
  const naseLose = byShort["Naše Řevnice"].votes_to_lose_seat;
  const sanceGain = byShort["ŠANCE"].votes_to_next_seat;
  const srdce = byShort["Srdce Řevnic"], total = T.votes_2026;
  const srdceNew = Math.ceil((0.05 * total - srdce.votes_2026) / 0.95), srdceMoved = Math.ceil(0.05 * total - srdce.votes_2026);
  const icons = {
    target: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".8" fill="currentColor"/></svg>',
    scale: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v16M7 20h10M5 8h14M5 8l-2.5 6a3 3 0 0 0 5 0L5 8Zm14 0-2.5 6a3 3 0 0 0 5 0L19 8Z"/></svg>',
    person: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="8" r="3.6"/><path d="M5 20c.8-3.6 3.6-5.6 7-5.6s6.2 2 7 5.6"/></svg>',
    pie: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 3a9 9 0 1 0 9 9h-9V3Z"/><path d="M15 3.5A9 9 0 0 1 20.5 9H15V3.5Z"/></svg>',
    ballot: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h3"/></svg>',
    star: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="m12 3.5 2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9L12 3.5Z"/></svg>',
  };
  const facts = [
    ["river", icons.target, `ODS: ${RV.pct(F.ods_share_pct, 2)}`, `K 5% hranici chybělo <strong>${F.ods_threshold_votes_new} nových hlasů</strong> – nebo ${F.ods_threshold_votes_moved} hlasů přetažených od jiné kandidátky, tedy jediný volič, který by místo jiné strany zakřížkoval ODS. K zisku mandátu by pak potřebovala zhruba ${byShort["ODS"].votes_to_next_seat} hlasů navíc.`],
    ["gold", icons.star, "ŠANCE těsně pod čarou", `Čtvrtý mandát ŠANCE unikl o ${RV.fmt(F.last_seat.quotient - F.first_loser.quotient, 1)} bodu d’Hondtova podílu (${RV.fmt(F.first_loser.quotient, 0)} vs. ${RV.fmt(F.last_seat.quotient, 1)}). Stačilo by <strong>${sanceGain} hlasů</strong> navíc, tedy asi ${Math.ceil(sanceGain / 15)} voličů.`],
    ["warm", icons.scale, "Naše Řevnice na hraně", `Druhý mandát Naší Řevnice byl poslední rozdělený. Kdyby kandidátka měla o <strong>${naseLose} hlasů</strong> méně, její podíl by se vyrovnal ŠANCE (1 210) a při rovnosti rozhoduje vyšší celkový počet hlasů – mandát by tedy připadl ŠANCE.`],
    ["", icons.person, "Dudová vs. Bobek", `Renata Dudová (DOBŘE, 5.) měla ${F.dudova.votes} hlasů, víc než zvolený Vladimír Bobek (${F.dudova.bobek_votes}). K přednosti ale potřebovala ${RV.fmt(F.dudova.threshold, 1)} hlasů – <strong>chyběly jí ${Math.ceil(F.dudova.threshold - F.dudova.votes)}</strong>, a tak rozhodlo pořadí na lístku.`],
    ["river", icons.pie, `${RV.int(T.unrepresented_votes)} hlasů bez zastoupení`, `${RV.pct(T.unrepresented_pct, 2)} hlasů dostaly kandidátky, které neprošly 5% hranicí (ODS a Srdce Řevnic). Srdci Řevnic chybělo ${srdceNew} nových hlasů (${srdceMoved} přetažených).`],
    ["gold", icons.ballot, `${RV.int(T.unused_votes)} nevyužitých hlasů`, `Každý volič mohl rozdat 15 hlasů. Na ${RV.int(TU.valid_ballots)} platných lístcích to je ${RV.int(TU.valid_ballots * 15)} hlasů, odevzdáno bylo ${RV.int(T.votes_2026)}. Nevyužité hlasy vznikají jen tam, kde volič křížkoval jednotlivce a nevyčerpal všech 15.`],
  ];
  document.getElementById("facts").innerHTML = facts.map(([c, i, h, t]) =>
    `<div class="card fact"><div class="ic ${c}">${i}</div><div><h3>${h}</h3><p>${t}</p></div></div>`).join("");

  RV.plot("#dhondt-chart", (w) => {
    const narrow = w < 560;
    const q = D.dhondt.slice().reverse();
    const lab = q.map((r) => `${r.party} ÷ ${r.divisor}`);
    const nSeat = q.filter((r) => !r.seat).length;
    return {
      data: [{
        type: "bar", orientation: "h", y: lab, x: q.map((r) => r.quotient),
        marker: { color: q.map((r) => (r.seat ? RV.color(r.party) : RV.alpha(RV.color(r.party), 0.3))) },
        text: q.map((r) => RV.fmt(r.quotient, r.quotient % 1 ? 1 : 0)), textposition: "outside", cliponaxis: false,
        textfont: { color: ink2(), size: 12, family: FONT },
        customdata: q.map((r, i) => [r.party, r.divisor, r.seat ? `${D.dhondt.length - i}. mandát` : "bez mandátu"]),
        hovertemplate: "<b>%{customdata[0]}</b>: hlasy ÷ %{customdata[1]} = %{x:,.1f}<br>%{customdata[2]}<extra></extra>",
      }],
      layout: {
        height: narrow ? 560 : 600, barcornerradius: 3, bargap: 0.25, margin: { l: 6, r: 14, t: 6, b: 30 },
        xaxis: { range: [0, 6400] }, yaxis: { tickfont: { color: ink(), size: 12.5 }, showgrid: false },
        shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: nSeat - 0.5, y1: nSeat - 0.5, line: { color: ink(), width: 1.5 } }],
        annotations: [{ xref: "paper", x: 1, y: nSeat - 0.5, xanchor: "right", yanchor: "bottom", showarrow: false, text: "↑ 15 mandátů · pod čarou bez mandátu ↓", font: { size: 12, color: ink() } }],
      },
    };
  });

  document.getElementById("margin-table").innerHTML =
    `<table class="data"><thead><tr><th>Kandidátka</th><th class="r">Mandáty</th><th class="r">Chybělo k dalšímu</th><th class="r">≈ voličů</th><th class="r">Rezerva (lze ztratit)</th></tr></thead><tbody>` +
    P.map((p) => `<tr><td>${RV.partyLabel(p.short)}</td><td class="r">${p.seats_2026}</td><td class="r">${RV.int(p.votes_to_next_seat)} hlasů</td>` +
      `<td class="r">${Math.ceil(p.votes_to_next_seat / 15)}</td><td class="r">${p.votes_to_lose_seat ? RV.int(p.votes_to_lose_seat) + " hlasů" : "–"}</td></tr>`).join("") +
    `</tbody></table>`;

  /* =========================================================== 10 kalkulačka */
  const real = Object.fromEntries(P.map((p) => [p.short, p.votes_2026]));
  const realSeats = RV.dhondt(real).seats;
  const fromEl = document.getElementById("calc-from"), toEl = document.getElementById("calc-to"), nEl = document.getElementById("calc-n");
  const opts = P.map((p) => `<option value="${RV.esc(p.short)}">${RV.esc(p.short)}</option>`).join("");
  fromEl.innerHTML = opts; toEl.innerHTML = opts;
  fromEl.value = "DOBŘE"; toEl.value = "ŠANCE";
  let calcSeats = realSeats;
  function calc() {
    const n = +nEl.value, from = fromEl.value, to = toEl.value;
    document.querySelector('label[for="calc-n"]').innerHTML = `<strong>${n}</strong> ${RV.plural(n, "volič", "voliči", "voličů")} (${RV.int(n * 15)} hlasů)`;
    const v = Object.assign({}, real);
    if (from !== to) { const m = Math.min(n * 15, v[from]); v[from] -= m; v[to] += m; }
    const r = RV.dhondt(v);
    calcSeats = r.seats;
    const diffs = P.filter((p) => r.seats[p.short] !== realSeats[p.short]);
    const out = document.getElementById("calc-out");
    if (from === to) out.innerHTML = `<p class="muted">Vyberte dvě různé kandidátky.</p>`;
    else if (!diffs.length) out.innerHTML = `<p>Rozdělení mandátů se <strong>nezmění</strong>.</p>`;
    else out.innerHTML = `<p style="margin-bottom:6px">Mandáty by se změnily:</p><div class="seat-diff">` +
      diffs.map((p) => { const d = r.seats[p.short] - realSeats[p.short]; return `<span class="${d > 0 ? "up" : "down"}"><span class="sw" style="--c:${RV.cssColor(p.short)}"></span>${RV.esc(p.short)} ${d > 0 ? "+" : "−"}${Math.abs(d)}</span>`; }).join("") + `</div>`;
    const below = P.filter((p) => v[p.short] < 0.05 * r.total && real[p.short] >= 0.05 * T.votes_2026);
    const above = P.filter((p) => v[p.short] >= 0.05 * r.total && real[p.short] < 0.05 * T.votes_2026);
    if (above.length) out.innerHTML += `<p class="chart-note" style="margin:8px 0 0">${above.map((p) => RV.esc(p.short)).join(", ")} by překročila 5&nbsp;% hranici.</p>`;
    if (below.length) out.innerHTML += `<p class="chart-note" style="margin:8px 0 0">${below.map((p) => RV.esc(p.short)).join(", ")} by spadla pod 5&nbsp;%.</p>`;
    drawCalc();
  }
  const drawCalc = RV.plot("#calc-chart", (w) => {
    const rows = P.slice().reverse();
    return {
      data: [{
        type: "bar", orientation: "h", y: rows.map((p) => p.short), x: rows.map((p) => calcSeats[p.short]),
        marker: { color: rows.map((p) => RV.color(p.short)),
          pattern: { shape: rows.map((p) => (calcSeats[p.short] !== realSeats[p.short] ? "/" : "")), fgcolor: surface(), size: 7, solidity: 0.3 } },
        text: rows.map((p) => { const d = calcSeats[p.short] - realSeats[p.short]; return `${calcSeats[p.short]}${d ? ` (${d > 0 ? "+" : "−"}${Math.abs(d)})` : ""}`; }),
        textposition: "outside", cliponaxis: false, textfont: { color: ink(), size: 13.5, family: FONT },
        customdata: rows.map((p) => realSeats[p.short]),
        hovertemplate: "<b>%{y}</b><br>%{x} mandátů (skutečně %{customdata})<extra></extra>",
      }],
      layout: {
        height: 340, barcornerradius: 4, margin: { l: 6, r: 10, t: 6, b: 30 },
        xaxis: { range: [0, 6.5], dtick: 1 }, yaxis: { tickfont: { color: ink(), size: 13.5 }, showgrid: false },
      },
    };
  });
  [fromEl, toEl].forEach((e) => e.addEventListener("change", calc));
  nEl.addEventListener("input", calc);
  document.getElementById("calc-reset").addEventListener("click", () => { nEl.value = 0; calc(); });
  calc();
})();
