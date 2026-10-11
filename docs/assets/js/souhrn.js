/* Souhrn analýz – srovnání Claude × GPT a výsledky ověřené oběma */
(function () {
  "use strict";
  const RV = window.RV;
  RV.init("souhrn");
  const B = RV.data.zakladni, CL = RV.data.claude, GP = RV.data.gpt, S = RV.data.srovnani;
  if (!B || !CL || !GP || !S) return;
  const K = S.consensus, ST = S.stats;
  const FONT = "Inter, system-ui, sans-serif";
  const ink = () => RV.token("ink"), ink2 = () => RV.token("ink-2"), muted = () => RV.token("muted"), surface = () => RV.token("surface");
  const cCl = () => RV.token("warm"), cGp = () => RV.token("river");
  const xFmt = (m) => "×" + RV.fmt(m, m < 1 ? 2 : 1);
  const pct = (x) => RV.pct(100 * x, 0);
  const rng = (a, b) => `${RV.fmt(100 * Math.min(a, b), 0)}–${RV.fmt(100 * Math.max(a, b), 0)}\u00a0%`;
  const set = (id, html) => { const e = document.getElementById(id); if (e) e.innerHTML = html; };
  const surname = (n) => n.split(" ").slice(-1)[0];
  const both = (a, b) => `<span class="chips" style="margin-top:10px"><span class="chip" style="cursor:default"><span class="sw round" style="--c:var(--warm)"></span>Claude <strong>${a}</strong></span>` +
    `<span class="chip" style="cursor:default"><span class="sw round" style="--c:var(--river)"></span>GPT <strong>${b}</strong></span></span>`;
  const card = (tag, cls, title, text, extra = "") =>
    `<div class="card reveal in"><span class="tag ${cls}">${tag}</span><h3 style="margin-top:10px">${title}</h3><p class="ink-2" style="margin:0">${text}</p>${extra}</div>`;
  const clC = Object.fromEntries(CL.candidates.map((c) => [c.party + "|" + c.position, c]));
  const gpC = Object.fromEntries(GP.candidates.map((c) => [c.party + "|" + c.position, c]));
  const tcC = clC["ŠANCE|10"], tcG = gpC["ŠANCE|10"];
  const ballotsCl = CL.parties.reduce((a, p) => a + p.ballots, 0), ballotsGp = GP.parties.reduce((a, p) => a + p.ballots, 0);
  const partyOrder = K.parties.slice().sort((a, b) => (b.cl + b.gp) - (a.cl + a.gp));
  const pcOrder = K.precincts.slice().sort((a, b) => (b.cl + b.gp) - (a.cl + a.gp));
  const sameParty = K.parties.slice().sort((a, b) => b.cl - a.cl).map((p) => p.party).join() === K.parties.slice().sort((a, b) => b.gp - a.gp).map((p) => p.party).join();
  const samePc = K.precincts.slice().sort((a, b) => b.cl - a.cl).map((p) => p.id).join() === K.precincts.slice().sort((a, b) => b.gp - a.gp).map((p) => p.id).join();
  const effNames = K.top_eff.filter((r) => r.name !== "Terezie Červená");

  /* =========================================================== 1 konsenzus */
  set("consensus", [
    card("jisté minimum", "tag-bound", `Nejméně ${RV.int(K.lb_exact)} osobních křížků`,
      `Plyne jen z pravidel sčítání, bez jakéhokoli modelu – to je ${RV.fmt(100 * K.lb_exact / B.totals.votes_2026, 1)} % všech hlasů.
       GPT spočítal přesné minimum ${RV.int(K.lb_gpt)}, Claude o kousek slabší, ale také platnou mez ${RV.int(K.lb_claude)}. Přesnou hodnotu jsme ověřili nezávislým výpočtem.`),
    card("oba modely", "tag-model", `Zhruba ${RV.int(Math.round(K.total.band[0] / 100) * 100)}–${RV.int(Math.round(K.total.band[1] / 100) * 100)} osobních křížků celkem`,
      `To je asi čtvrtina všech hlasů (${rng(K.total.band[0] / B.totals.votes_2026, K.total.band[1] / B.totals.votes_2026)}). Rozmezí je průnik 90% intervalů obou modelů;
       každý sám o sobě odhaduje jiný střed.`, both(`≈ ${RV.int(K.total.cl[1])}`, `≈ ${RV.int(K.total.gp[1])}`)),
    card("oba modely", "tag-model", "Terezie Červená je největší osobnost voleb",
      `Z 10. místa ŠANCE dostala zhruba třikrát víc osobních křížků, než odpovídá její pozici – nejvíc ze všech 120 kandidátů v obou analýzách.
       Jistě jich bylo nejméně ${tcC.lb}.`, both(`≈ ${tcC.C} · ${xFmt(tcC.eff)}`, `≈ ${tcG.C} · ${xFmt(tcG.eff)}`)),
    card("oba modely", "tag-model", "Další výrazné osobnosti",
      `V první desítce podle osobního efektu mají oba modely shodně ${effNames.map((r) => `${RV.esc(r.name)} (${RV.esc(r.party)}, ${r.position}.)`).join(", ")}.
       Většina z nich byla na kandidátce hodně nízko – a přesto je voliči hledali.`),
    card("oba modely", "tag-model", "Nejvíc osobních křížků v absolutním počtu",
      `V první desítce obou modelů jsou ${K.top_C.slice(0, 6).map((r) => `${RV.esc(r.name)} (${RV.esc(r.party)})`).join(", ")} a další.
       Jsou to hlavně lídři a známé tváře – pozice nahoře pomáhá i u osobních křížků. U Martiny Štěpánkové se ale modely liší v tom, kolik přesně (viz níže).`),
    card("oba modely", "tag-model", "Malé kandidátky žijí z osobností, velké ze stranických křížků",
      `${sameParty ? "Oba modely seřadily kandidátky podle podílu osobních křížků naprosto stejně." : ""}
       Nejvíc mají ${RV.esc(partyOrder[0].party)} (${rng(partyOrder[0].gp, partyOrder[0].cl)}) a ${RV.esc(partyOrder[1].party)} (${rng(partyOrder[1].gp, partyOrder[1].cl)}),
       nejméně vítězné ${RV.esc(partyOrder[7].party)} (${rng(partyOrder[7].gp, partyOrder[7].cl)}).`),
    card("oba modely", "tag-model", `Nejvíc se křížkuje v okrsku ${pcOrder[0].id}, nejméně v okrsku ${pcOrder[3].id}`,
      `${samePc ? "Pořadí okrsků je v obou analýzách stejné" : "Pořadí okrsků se v analýzách mírně liší"}: ${pcOrder.map((p) => p.id).join(" > ")}.
       Rozdíly mezi okrsky jsou ale malé – osobní křížky tvoří všude zhruba čtvrtinu hlasů.`),
    card("oba modely", "tag-model", "Většina stranických voličů jinde nekřížkuje",
      `Kdo zakřížkuje celou kandidátku, většinou už nikomu z jiné strany křížek nedá: podle modelů jde o ${rng(GP.headline.p_k0, CL.headline.p_k0)} takových voličů.`,
      both(pct(CL.headline.p_k0), pct(GP.headline.p_k0))),
  ].join(""));

  /* =========================================================== 2 kandidát po kandidátovi */
  const P = S.pairs;
  const diff = P.filter((p) => !p.overlap);
  set("pairs-intro", `Shoda odhadů osobních křížků je velmi vysoká: korelace ${RV.fmt(ST.pearson_C, 2)}, shoda pořadí ${RV.fmt(ST.spearman_C, 2)} (1 = dokonalá).
    U <strong>${ST.overlap_n} ze ${ST.n}</strong> kandidátů se 90% intervaly obou modelů překrývají. Výjimkou ${diff.length === 1 ? "je" : "jsou"} ${diff.map((p) => RV.esc(p.name)).join(" a ")}.
    GPT přitom odhaduje celkově asi o ${RV.fmt(100 * (1 - ST.sum_gp / ST.sum_cl), 0)} % méně osobních křížků než Claude.`);
  set("agree-stats", `<h3>Shoda v číslech</h3><dl class="kv" style="margin-top:10px">
    <div><dt>Korelace odhadů</dt><dd>${RV.fmt(ST.pearson_C, 2)}</dd></div>
    <div><dt>Shoda pořadí</dt><dd>${RV.fmt(ST.spearman_C, 2)}</dd></div>
    <div><dt>Překryv intervalů</dt><dd>${ST.overlap_n}<small> / ${ST.n}</small></dd></div>
    <div><dt>Společně v top 10 (křížky)</dt><dd>${ST.top10_common}<small> / 10</small></dd></div>
    <div><dt>Společně v top 10 (osobnosti)</dt><dd>${ST.top10_eff_common}<small> / 10</small></dd></div>
    <div><dt>Shoda osobního efektu</dt><dd>${RV.fmt(ST.spearman_eff, 2)}</dd></div></dl>`);

  RV.plot("#pairs-chart", (w) => {
    const narrow = w < 560;
    const max = Math.max(...P.map((p) => Math.max(p.cl, p.gp))) * 1.08;
    const traces = RV.PARTY_ORDER.map((party) => {
      const rows = P.filter((p) => p.party === party);
      return {
        type: "scatter", mode: "markers", name: party, x: rows.map((p) => p.cl), y: rows.map((p) => p.gp),
        marker: { size: rows.map((p) => (p.elected ? 13 : 9)), color: RV.color(party), opacity: 1, line: { color: surface(), width: 1.5 } },
        customdata: rows.map((p) => [p.name, p.party, p.position, p.cl_lo, p.cl_hi, p.gp_lo, p.gp_hi, p.overlap ? "překrývají se" : "NEpřekrývají se"]),
        hovertemplate: "<b>%{customdata[0]}</b> (%{customdata[1]}, %{customdata[2]}.)<br>Claude ≈ %{x} (%{customdata[3]}–%{customdata[4]})<br>GPT ≈ %{y} (%{customdata[5]}–%{customdata[6]})<br>intervaly %{customdata[7]}<extra></extra>",
      };
    });
    return {
      data: traces,
      layout: {
        height: narrow ? 460 : 560, margin: { l: 6, r: 10, t: 10, b: 44 }, showlegend: true,
        legend: { orientation: "h", y: -0.14, x: 0, font: { size: 12, color: ink2() } },
        xaxis: { range: [0, max], title: { text: "Claude – osobní křížky" } }, yaxis: { range: [0, max], title: { text: "GPT – osobní křížky" }, scaleanchor: "x" },
        shapes: [{ type: "line", x0: 0, y0: 0, x1: max, y1: max, line: { color: RV.token("line-strong"), width: 1.5 }, layer: "below" }],
        annotations: diff.map((p) => ({ x: p.cl, y: p.gp, text: surname(p.name), showarrow: true, arrowhead: 0, ax: narrow ? -46 : 34, ay: narrow ? 26 : 22, arrowcolor: ink2(), font: { size: 12, color: ink() } }))
          .concat([{ x: max * 0.92, y: max * 0.92, text: "stejný odhad", showarrow: false, textangle: -45, font: { size: 11, color: muted() }, yshift: 10 }]),
      },
    };
  });

  RV.plot("#total-chart", () => {
    const rows = [{ y: "GPT", v: K.total.gp, c: cGp() }, { y: "Claude", v: K.total.cl, c: cCl() }];
    return {
      data: rows.map((r) => ({
        type: "scatter", mode: "lines+markers", y: [r.y, r.y, r.y], x: [r.v[0], r.v[1], r.v[2]],
        line: { color: RV.alpha(r.c, 0.55), width: 6 }, marker: { size: [0, 15, 0], color: r.c, line: { color: surface(), width: 2 } },
        hovertemplate: `${r.y}: medián ${RV.int(r.v[1])}, 90 % ${RV.int(r.v[0])}–${RV.int(r.v[2])}<extra></extra>`,
      })),
      layout: {
        height: 220, margin: { l: 6, r: 14, t: 28, b: 40 },
        xaxis: { range: [2000, 9000], title: { text: "osobní křížky celkem" } }, yaxis: { tickfont: { color: ink(), size: 13.5 } },
        shapes: [
          { type: "rect", x0: K.total.band[0], x1: K.total.band[1], yref: "paper", y0: 0, y1: 1, fillcolor: RV.alpha(RV.token("accent"), 0.1), line: { width: 0 }, layer: "below" },
          { type: "line", x0: K.lb_exact, x1: K.lb_exact, yref: "paper", y0: 0, y1: 1, line: { color: RV.token("accent"), width: 2 } },
        ],
        annotations: [
          { x: K.lb_exact, y: 1, yref: "paper", yanchor: "bottom", showarrow: false, text: `minimum ${RV.int(K.lb_exact)}`, font: { size: 11.5, color: RV.token("accent") } },
          { x: (K.total.band[0] + K.total.band[1]) / 2, y: 1, yref: "paper", yanchor: "bottom", showarrow: false, text: "shoda obou", font: { size: 11.5, color: RV.token("accent") } },
        ],
      },
    };
  });

  const dotPairs = (rows, label, fCl, fGp, fmt, axis) => ({
    data: [{
      type: "scatter", mode: "markers", name: "Claude", y: rows.map(label), x: rows.map(fCl),
      marker: { size: 12, color: cCl(), line: { color: surface(), width: 2 } }, hovertemplate: `Claude: %{customdata}<extra></extra>`, customdata: rows.map((r) => fmt(fCl(r))),
    }, {
      type: "scatter", mode: "markers", name: "GPT", y: rows.map(label), x: rows.map(fGp),
      marker: { size: 12, color: cGp(), line: { color: surface(), width: 2 } }, hovertemplate: `GPT: %{customdata}<extra></extra>`, customdata: rows.map((r) => fmt(fGp(r))),
    }],
    layout: {
      height: rows.length * 36 + 90, margin: { l: 6, r: 14, t: 6, b: 40 }, showlegend: true,
      legend: { orientation: "h", y: -0.18, x: 0, font: { size: 12.5, color: ink2() } },
      xaxis: axis, yaxis: { tickfont: { color: ink(), size: 13 } },
      shapes: rows.map((r) => ({ type: "line", x0: fCl(r), x1: fGp(r), y0: label(r), y1: label(r), line: { color: RV.token("line-strong"), width: 3 }, layer: "below" })),
    },
  });
  RV.plot("#party-chart", () => dotPairs(K.parties.slice().sort((a, b) => (a.cl + a.gp) - (b.cl + b.gp)), (r) => r.party,
    (r) => 100 * r.cl, (r) => 100 * r.gp, (v) => RV.pct(v, 0), { range: [0, 60], ticksuffix: " %" }));
  RV.plot("#eff-chart", (w) => dotPairs(K.top_eff.slice().reverse(), (r) => (w < 500 ? surname(r.name) : r.name) + ` <span style="color:${muted()}">${r.party}</span>`,
    (r) => r.cl, (r) => r.gp, (v) => xFmt(v), { range: [1, 3.4], tickvals: [1, 1.5, 2, 2.5, 3], ticktext: ["×1", "×1,5", "×2", "×2,5", "×3"] }));

  /* =========================================================== 3 rozdíl */
  const st = P.find((p) => p.name === "Martina Štěpánková"), uh = P.find((p) => p.name === "Michal Uhlík");
  const pos1 = S.by_position[0], tail = S.by_position.slice(10).reduce((a, r) => ({ cl: a.cl + r.cl, gp: a.gp + r.gp }), { cl: 0, gp: 0 });
  set("diff-text", `
    <p><strong>Co se liší:</strong> u lídrů DOBŘE se 90% intervaly obou modelů nepřekrývají. Martině Štěpánkové přisuzuje Claude ≈&nbsp;${st.cl}
      osobních křížků (${st.cl_lo}–${st.cl_hi}), GPT jen ≈&nbsp;${st.gp} (${st.gp_lo}–${st.gp_hi}); Michalu Uhlíkovi ≈&nbsp;${uh.cl} oproti ≈&nbsp;${uh.gp}.
      Menší, ale stejným směrem jdoucí rozdíl je u lídrů ŠANCE a Perspektivy. U kandidátů na 11.–15. místech se modely skoro shodují
      (${RV.int(tail.cl)} vs. ${RV.int(tail.gp)} křížků), na 1. místech už ne (${RV.int(pos1.cl)} vs. ${RV.int(pos1.gp)}).</p>
    <p><strong>Proč:</strong> modely se liší v tom, <em>kolik voličů zakřížkovalo celou kandidátku</em>. Claude využil počet platných lístků
      (1&nbsp;679), který dohledal v otevřených datech ČSÚ, a odhaduje asi ${RV.int(ballotsCl)} stranických lístků. GPT tento údaj považoval
      za neznámý a odhaduje jich asi ${RV.int(ballotsGp)}. Víc stranických lístků znamená víc „automatických“ hlasů pro horní pozice velkých
      kandidátek – a tedy méně osobních křížků u jejich lídrů.</p>
    <p><strong>Kdo má pravdu:</strong> z dodaných čísel to rozhodnout nejde – oba rozklady jsou s výsledky voleb slučitelné.
      Claude má v tomhle bodě o jednu skutečnou informaci víc, GPT zase lépe obstál v testech na simulovaných volbách.
      Rozhodl by počet platných lístků v jednotlivých okrscích nebo anonymní vzorek vyplněných lístků. Pro lídry velkých kandidátek
      proto berte jako realistické celé rozpětí obou modelů.</p>`);
  RV.plot("#pos-chart", () => {
    const r = S.by_position;
    return {
      data: [
        { type: "bar", name: "Claude", x: r.map((p) => p.position), y: r.map((p) => p.cl), marker: { color: cCl() }, hovertemplate: "%{x}. místo – Claude: %{y}<extra></extra>" },
        { type: "bar", name: "GPT", x: r.map((p) => p.position), y: r.map((p) => p.gp), marker: { color: cGp() }, hovertemplate: "%{x}. místo – GPT: %{y}<extra></extra>" },
      ],
      layout: {
        barmode: "group", bargap: 0.25, bargroupgap: 0.08, barcornerradius: 3, height: 360, margin: { l: 6, r: 6, t: 10, b: 44 }, showlegend: true,
        legend: { orientation: "h", y: 1.08, x: 0, font: { size: 12.5, color: ink2() } },
        xaxis: { dtick: 1, title: { text: "pozice na kandidátce" } }, yaxis: { title: { text: "osobní křížky (součet 8 kandidátek)" } },
      },
    };
  });

  /* =========================================================== 4 hodnocení */
  const recCl = CL.recovery.filter((r) => r.true >= r.lo && r.true <= r.hi).length, recGp = GP.recovery.filter((r) => r.true >= r.lo && r.true <= r.hi).length;
  const okGp = GP.sensitivity.filter((s) => !s.main && s.ok).length, nGp = GP.sensitivity.filter((s) => !s.main).length;
  const rows = [
    ["Dokazatelná dolní mez", `${RV.int(CL.headline.lb_budget)} – spojitá relaxace; platí, ale není nejtěsnější`, `${RV.int(GP.headline.lb_budget)} – přesné minimum a k němu sestavené platné lístky`, "gpt"],
    ["Využití dostupných údajů", "použil i počet platných lístků (1 679), dohledaný v otevřených datech ČSÚ", "počet platných lístků nepoužil, považoval ho za neznámý", "claude"],
    ["Test na simulovaných volbách", `pravda uvnitř intervalu ve ${recCl} ze ${CL.recovery.length} testů; intervaly kandidátů spíš příliš úzké`, `pravda uvnitř intervalu ve ${recGp} ze ${GP.recovery.length} testů; pokrytí kandidátů 97,5&nbsp;%`, "gpt"],
    ["Kvalita výpočtu (MCMC)", "hlavní model R̂ 1,014 a 1 divergence; některé varianty výrazně hůř (R̂ až 1,06)", `hlavní model prošel (R̂ 1,009); varianty hraniční, ${okGp} z ${nGp} prošlo`, "gpt"],
    ["Šíře prověření předpokladů", `${CL.sensitivity.length - 1} variant modelu (${RV.int(CL.headline.sens_min)}–${RV.int(CL.headline.sens_max)})`, `${GP.sensitivity.length - 1} variant modelu (${RV.int(GP.headline.sens_min)}–${RV.int(GP.headline.sens_max)})`, "claude"],
    ["Předpověď vynechaného okrsku", "stejně dobrá jako jednoduchý odhad z ostatních okrsků", "nepatrně lepší než jednoduchý odhad", "tie"],
    ["Reprodukovatelnost a kontroly", "pevné seedy, uložené fity, skript sestavující notebook", "navíc jednotkové testy, otisky dat a kontrola 2 800 rozkladů na platné lístky", "gpt"],
    ["Srozumitelnost výstupů", "osobní efekt srovnatelný napříč kandidátkami, souhrn s označením fakt / mez / model", "efekt jen uvnitř kandidátky, souhrn s označením typu tvrzení", "tie"],
  ];
  const badge = (w) => w === "claude" ? `<span class="tag" style="background:var(--warm-soft);color:var(--warm)">Claude</span>` :
    w === "gpt" ? `<span class="tag" style="background:var(--river-soft);color:var(--river)">GPT</span>` : `<span class="tag">remíza</span>`;
  set("score", `<table class="data"><thead><tr><th>Kritérium</th><th>Claude</th><th>GPT</th><th>Lépe</th></tr></thead><tbody>` +
    rows.map((r) => `<tr><td><strong>${r[0]}</strong></td><td class="ink-2">${r[1]}</td><td class="ink-2">${r[2]}</td><td>${badge(r[3])}</td></tr>`).join("") + `</tbody></table>`);
  const nG = rows.filter((r) => r[3] === "gpt").length, nC = rows.filter((r) => r[3] === "claude").length, nT = rows.length - nG - nC;
  set("verdict", [
    `<div class="card reveal in"><span class="tag" style="background:var(--river-soft);color:var(--river)">verdikt</span><h3 style="margin-top:10px">Celkově o něco lépe GPT</h3>
      <p class="ink-2" style="margin:0">Skóre ${nG} : ${nC} (${nT}× remíza). GPT odvedl matematicky pečlivější práci: přesnou dolní mez, lépe kalibrované intervaly,
      čistší výpočet a víc kontrol. Jeho odhady jsou spíš opatrnější.</p></div>`,
    `<div class="card reveal in"><span class="tag" style="background:var(--warm-soft);color:var(--warm)">silná stránka Claude</span><h3 style="margin-top:10px">Víc informací, širší prověření</h3>
      <p class="ink-2" style="margin:0">Claude dohledal a zapojil počet platných lístků, prověřil víc variant modelu a jeho osobní efekt lze porovnávat napříč kandidátkami.
      Jeho intervaly ale bývají příliš úzké.</p></div>`,
    `<div class="card reveal in"><span class="tag tag-model">pro čtenáře</span><h3 style="margin-top:10px">Čemu věřit</h3>
      <p class="ink-2" style="margin:0">Tomu, na čem se oba shodnou: pořadí kandidátů, osobnosti voleb, rozdíly mezi kandidátkami a okrsky. U celkového počtu
      a u lídrů velkých kandidátek berte celé rozpětí obou modelů.</p></div>`,
  ].join(""));

  /* =========================================================== 5 tabulka */
  const sorted = P.slice().sort((a, b) => (b.cl + b.gp) - (a.cl + a.gp));
  function renderTable(n) {
    set("pairs-table", `<table class="data"><thead><tr><th>#</th><th>Kandidát</th><th class="r">Hlasy</th><th class="r">Jisté min.</th><th class="r">Claude</th><th class="r">GPT</th><th>Shoda</th></tr></thead><tbody>` +
      sorted.slice(0, n).map((p, i) => `<tr${p.overlap ? "" : ' class="is-hl"'}><td class="muted">${i + 1}</td><td>${RV.esc(p.name)}${p.elected ? " ✓" : ""}<br><span class="muted" style="font-size:12.5px">${RV.partyLabel(p.party)} · ${p.position}. místo</span></td>` +
        `<td class="r">${RV.int(p.votes)}</td><td class="r">${RV.int(p.lb)}</td>` +
        `<td class="r"><strong>${RV.int(p.cl)}</strong><br><span class="muted" style="font-size:12px">${p.cl_lo}–${p.cl_hi}</span></td>` +
        `<td class="r"><strong>${RV.int(p.gp)}</strong><br><span class="muted" style="font-size:12px">${p.gp_lo}–${p.gp_hi}</span></td>` +
        `<td>${p.overlap ? '<span class="delta-up">✓ shoda</span>' : '<span class="delta-down">✗ liší se</span>'}</td></tr>`).join("") + `</tbody></table>`);
  }
  renderTable(20);
  RV.seg("#tab-n", (v) => renderTable(+v));
})();
