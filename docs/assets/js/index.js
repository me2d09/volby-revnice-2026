/* Úvodní stránka */
(function () {
  "use strict";
  const RV = window.RV;
  RV.init("uvod");
  const D = RV.data.zakladni;
  if (!D) return;
  const T = D.totals, TU = D.turnout;
  const parties = D.parties;
  const byShort = Object.fromEntries(parties.map((p) => [p.short, p]));

  /* ---------- rychlá čísla ---------- */
  const ico = {
    people: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="9" cy="8" r="3.2"/><path d="M3.5 19c.6-3.2 2.8-5 5.5-5s4.9 1.8 5.5 5"/><circle cx="17" cy="9" r="2.5"/><path d="M16 14.2c2.4.1 4 1.7 4.5 4.3"/></svg>',
    ballot: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="9" width="16" height="11" rx="2"/><path d="M8 9V4h8v5M9.5 6.5l1.6 1.5L14.5 5"/></svg>',
    trophy: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 4h10v5a5 5 0 0 1-10 0V4ZM7 6H4v1.5A3.5 3.5 0 0 0 7.5 11M17 6h3v1.5a3.5 3.5 0 0 1-3.5 3.5M12 14v4M8.5 20h7"/></svg>',
    venus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="9" r="5"/><path d="M12 14v7M9 18h6"/></svg>',
  };
  const win = parties[0];
  document.getElementById("h-votes").textContent = RV.int(T.votes_2026);
  const tiles = [
    { icon: ico.people, cls: "", label: "Volební účast", value: RV.pct(TU.turnout_pct, 2),
      sub: `<span class="delta-up">${RV.pp(TU.turnout_change_pp)}</span> proti roku 2022` },
    { icon: ico.ballot, cls: "river", label: "Platné hlasy", value: RV.int(T.votes_2026),
      sub: `<span class="delta-up">${RV.signed(T.change_votes)}</span> (${RV.signed(T.change_pct, 2)}&nbsp;%) · ${RV.int(TU.valid_ballots)} lístků` },
    { icon: ico.trophy, cls: "gold", label: "Vítěz voleb", value: RV.esc(win.short),
      sub: `${RV.pct(win.share_2026, 2)} · ${win.seats_2026} ${RV.plural(win.seats_2026, "mandát", "mandáty", "mandátů")} · nová kandidátka` },
    { icon: ico.venus, cls: "warm", label: "Ženy v zastupitelstvu", value: `${T.women_elected} <small>z ${D.meta.seats}</small>`,
      sub: `průměrný věk zastupitelů ${RV.fmt(T.avg_age_elected, 1)} let` },
  ];
  document.getElementById("quick").innerHTML = tiles.map((t) =>
    `<div class="card stat reveal in"><div class="stat-icon ${t.cls}">${t.icon}</div><span class="label">${t.label}</span>` +
    `<span class="value">${t.value}</span><span class="sub">${t.sub}</span></div>`).join("");

  /* ---------- zastupitelstvo: zasedací pořádek do písmene U ---------- */
  // Pořadí kandidátek podél U (levé rameno shora dolů, spodek zleva doprava, pravé rameno zdola nahoru).
  const U_ORDER = ["ŠANCE", "DOBŘE", "Naše Řevnice", "PRO", "TOP 09", "Perspektiva"];
  const seatParties = U_ORDER.map((s) => byShort[s]).filter((p) => p && p.seats_2026 > 0);
  const elected = D.elected;
  const N = D.meta.seats, ARM = 5;                     // 5 + 5 + 5 křesel
  const uSeats = [];
  for (let k = 0; k < ARM; k++) uSeats.push({ x: 0, y: ARM - k });          // levé rameno
  for (let k = 0; k < N - 2 * ARM; k++) uSeats.push({ x: 1 + k, y: 0 });    // spodek
  const W = N - 2 * ARM + 1;
  for (let k = 0; k < ARM; k++) uSeats.push({ x: W, y: 1 + k });            // pravé rameno
  function seatingU(width) {
    let i = 0;
    const traces = seatParties.map((p) => {
      const people = elected.filter((e) => e.party === p.short);
      const xs = [], ys = [], texts = [];
      for (let k = 0; k < p.seats_2026; k++, i++) {
        xs.push(uSeats[i].x); ys.push(uSeats[i].y);
        const e = people[k];
        texts.push(`<b>${RV.esc(e.name)}</b><br>${RV.esc(p.short)} · ${e.position}. místo<br>${RV.int(e.votes)} hlasů`);
      }
      return {
        type: "scatter", mode: "markers", x: xs, y: ys, text: texts, hovertemplate: "%{text}<extra></extra>", name: p.short,
        marker: { size: Math.max(20, Math.min(40, width / 10)), color: RV.color(p.short), line: { color: RV.token("surface"), width: 2 } },
      };
    });
    const t = 0.62;                                     // stůl uvnitř U, křesla sedí zvenku
    const table = `M ${t} ${ARM + 0.45} L ${t} ${t} L ${W - t} ${t} L ${W - t} ${ARM + 0.45}`;
    return {
      data: traces,
      layout: {
        height: Math.round(Math.min(440, Math.max(260, width * 0.86))),
        margin: { l: 4, r: 4, t: 4, b: 4 },
        xaxis: { visible: false, range: [-0.7, W + 0.7] },
        yaxis: { visible: false, range: [-0.7, ARM + 0.8], scaleanchor: "x" },
        shapes: [{ type: "path", path: table, line: { color: RV.token("surface-3"), width: Math.max(10, width / 26) }, layer: "below" }],
        annotations: [{ x: W / 2, y: ARM / 2 + 0.6, text: `<b style="font-size:30px">${N}</b><br>mandátů`, showarrow: false,
          font: { color: RV.token("ink"), size: 13, family: "Inter, system-ui, sans-serif" } }],
      },
    };
  }
  RV.plot("#hemicycle", seatingU);
  document.getElementById("hemi-legend").innerHTML = seatParties.map((p) =>
    `<span><span class="sw round" style="--c:${RV.cssColor(p.short)}"></span>${RV.esc(p.short)} <strong>${p.seats_2026}</strong></span>`).join("");

  /* ---------- výsledky stran ---------- */
  function renderResults(year) {
    const key = year === "2022" ? "_2022" : "_2026";
    const rows = parties.filter((p) => p["votes" + key] > 0).sort((a, b) => b["votes" + key] - a["votes" + key]);
    const max = Math.max(...rows.map((p) => p["share" + key]));
    const scale = (v) => (100 * v) / (max * 1.04);
    const html = [`<div class="res-row res-head"><span>Kandidátka</span><span></span><span class="pct" style="font-weight:650">Podíl</span><span class="votes">Hlasy</span><span class="seats">Mandáty</span></div>`];
    rows.forEach((p) => {
      const seats = p["seats" + key], share = p["share" + key];
      const out = share < D.meta.threshold_pct;
      const dots = seats ? Array.from({ length: seats }, () => "<i></i>").join("") : '<span class="zero">0</span>';
      const sub = p.name !== p.short ? `<small>${RV.esc(p.name)}</small>` : "";
      html.push(`<div class="res-row${out ? " out" : ""}" style="--c:${RV.cssColor(p.short)}" title="${RV.esc(p.name)}: ${RV.int(p["votes" + key])} hlasů">` +
        `<span class="nm">${RV.esc(p.short)}${sub}</span>` +
        `<span class="bar"><i style="width:${scale(share)}%"></i><span class="thr" style="left:${scale(D.meta.threshold_pct)}%"></span></span>` +
        `<span class="pct">${RV.pct(share, 2)}</span><span class="votes">${RV.int(p["votes" + key])}</span>` +
        `<span class="seats">${dots}</span></div>`);
    });
    document.getElementById("results").innerHTML = html.join("");
    document.getElementById("results-note").innerHTML = year === "2022"
      ? "Rok 2022: DOBŘE ještě nekandidovalo, naopak kandidovalo Řevnice SPOLEČNĚ. Mandáty 2022 jsou přepočtené stejnou d’Hondtovou metodou ze zveřejněných hlasů. Čárka = hranice 5&nbsp;%."
      : "Svislá čárka v pruhu = hranice 5&nbsp;%, pod kterou kandidátka nezíská žádný mandát.";
  }
  renderResults("2026");
  RV.seg("#year-seg", renderResults);

  /* ---------- tři momenty ---------- */
  const F = D.facts;
  const cervena = D.candidates.find((c) => c.name === "Terezie Červená");
  const p4 = D.precincts.find((p) => p.id === 4);
  const without4 = Object.entries(p4.city_without).sort((a, b) => b[1] - a[1]);
  const moments = [
    { ic: "gold", icon: ico.trophy, title: "Nováček vyhrál – díky okrsku 4",
      text: `DOBŘE kandidovalo poprvé a získalo ${RV.int(byShort["DOBŘE"].votes_2026)} hlasů. Bez východního okrsku 4 by ale těsně vedla ŠANCE (${RV.int(without4[0][1])} : ${RV.int(p4.city_without["DOBŘE"])}).`,
      href: "vysledky.html#okrsky", link: "Okrsky" },
    { ic: "warm", icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20V5M6 11l6-6 6 6"/></svg>',
      title: "Z 10. místa do zastupitelstva",
      text: `Terezie Červená (ŠANCE) přeskočila osm kandidátů před sebou. Matematicky jisté je, že dostala nejméně ${cervena.min_personal_marks} osobních křížků.`,
      href: "krizky.html#cervena", link: "Osobní křížky" },
    { ic: "river", icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".8" fill="currentColor"/></svg>',
      title: `ODS chybělo ${F.ods_threshold_votes_new} hlasů`,
      text: `S ${RV.pct(F.ods_share_pct, 2)} zůstala ODS těsně pod 5% hranicí. Stačil by jediný volič, který by místo jiné strany zakřížkoval celou ODS.`,
      href: "vysledky.html#tesne", link: "Těsné momenty" },
  ];
  document.getElementById("moments").innerHTML = moments.map((m) =>
    `<div class="card fact reveal"><div class="ic ${m.ic}">${m.icon}</div><div><h3>${m.title}</h3><p>${m.text}</p>` +
    `<p style="margin-top:10px"><a href="${m.href}">${m.link} →</a></p></div></div>`).join("");
  document.querySelectorAll("#moments .reveal").forEach((e) => e.classList.add("in"));
})();
