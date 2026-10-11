/* Volby Řevnice 2026 – společný kód: hlavička, patička, režim, formátování, Plotly. */
(function () {
  "use strict";

  const REPO = "https://github.com/me2d09/volby-revnice-2026";
  const RV = (window.RV = window.RV || {});
  RV.REPO = REPO;
  RV.data = window.RV_DATA = window.RV_DATA || {};

  /* ---------- režim (světlý / tmavý) ---------- */
  const THEME_KEY = "rv-theme";
  function storedTheme() { try { return localStorage.getItem(THEME_KEY); } catch (e) { return null; } }
  function applyTheme(t) {
    if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t);
    else document.documentElement.removeAttribute("data-theme");
  }
  applyTheme(storedTheme());
  RV.isDark = function () {
    const t = document.documentElement.getAttribute("data-theme");
    if (t) return t === "dark";
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  };
  function toggleTheme() {
    const next = RV.isDark() ? "light" : "dark";
    applyTheme(next);
    try { localStorage.setItem(THEME_KEY, next); } catch (e) { /* bez úložiště */ }
    themeChanged();
  }
  if (window.matchMedia) {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    (mq.addEventListener ? mq.addEventListener.bind(mq, "change") : mq.addListener.bind(mq))(() => {
      if (!document.documentElement.getAttribute("data-theme")) themeChanged();
    });
  }

  /* ---------- tokeny ---------- */
  RV.token = function (name) {
    return getComputedStyle(document.documentElement).getPropertyValue("--" + name).trim();
  };
  const PARTY_SLUG = {
    "DOBŘE": "dobre", "ŠANCE": "sance", "Perspektiva": "perspektiva", "PRO": "pro",
    "Naše Řevnice": "nase", "TOP 09": "top09", "ODS": "ods", "Srdce Řevnic": "srdce", "SPOLEČNĚ": "spolecne",
  };
  RV.PARTY_ORDER = ["DOBŘE", "ŠANCE", "Perspektiva", "PRO", "Naše Řevnice", "TOP 09", "ODS", "Srdce Řevnic"];
  RV.slug = (p) => PARTY_SLUG[p] || "spolecne";
  RV.color = (p) => RV.token("p-" + RV.slug(p));
  RV.cssColor = (p) => "var(--p-" + RV.slug(p) + ")";
  /* průhledná varianta barvy pro „stranickou“ složku */
  RV.alpha = function (hex, a) {
    const h = hex.replace("#", "");
    const n = parseInt(h.length === 3 ? h.split("").map((c) => c + c).join("") : h, 16);
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
  };

  /* ---------- formátování (česky) ---------- */
  const nf0 = new Intl.NumberFormat("cs-CZ", { maximumFractionDigits: 0 });
  RV.fmt = (x, d = 0) => (x == null || isNaN(x)) ? "–" :
    new Intl.NumberFormat("cs-CZ", { minimumFractionDigits: d, maximumFractionDigits: d }).format(x);
  RV.int = (x) => nf0.format(Math.round(x));
  RV.pct = (x, d = 1) => RV.fmt(x, d) + " %";
  RV.pp = (x, d = 2) => (x > 0 ? "+" : x < 0 ? "−" : "") + RV.fmt(Math.abs(x), d) + " p. b.";
  RV.signed = (x, d = 0) => (x > 0 ? "+" : x < 0 ? "−" : "±") + RV.fmt(Math.abs(x), d);
  RV.plural = (n, one, few, many) => (n === 1 ? one : n >= 2 && n <= 4 ? few : many);
  RV.initials = (name) => name.split(" ").filter(Boolean).map((w) => w[0]).slice(0, 2).join("");
  RV.esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  RV.partyLabel = (p) => `<span class="party"><span class="sw" style="--c:${RV.cssColor(p)}"></span>${RV.esc(p)}</span>`;

  /* ---------- hlavička a patička ---------- */
  const NAV = [
    { href: "index.html", label: "Úvod", key: "uvod" },
    { href: "vysledky.html", label: "Výsledky v kostce", key: "vysledky" },
    { href: "souhrn.html", label: "Souhrn analýz", key: "souhrn" },
    { href: "krizky.html", label: "Analýza Claude", key: "krizky" },
    { href: "gpt.html", label: "Analýza GPT", key: "gpt" },
    { href: "notebooky.html", label: "Pro fajnšmekry", key: "notebooky" },
  ];
  const ICONS = {
    sun: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4"/></svg>',
    moon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z"/></svg>',
    menu: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
  };
  RV.ICONS = ICONS;
  const MARK = '<svg class="brand-mark" viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="9" fill="var(--accent)"/><path d="M3 21c4-6 7-9 10-9s5 4 8 4 5-3 8-6v19H3Z" fill="var(--bg)" opacity=".28"/><path d="M3 25c3-1.6 5.5-1.6 8.5 0s5.5 1.6 8.5 0 5.5-1.6 9 0" fill="none" stroke="var(--bg)" stroke-width="2.2" stroke-linecap="round"/><path d="m10 10.5 3 3 6.5-7" fill="none" stroke="var(--bg)" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  function header(active) {
    const el = document.querySelector("[data-site-header]");
    if (!el) return;
    el.className = "site-header";
    el.innerHTML =
      `<div class="wrap"><a class="brand" href="index.html">${MARK}<span>Volby Řevnice 2026<small>neoficiální analýza výsledků</small></span></a>` +
      `<button class="icon-btn menu-btn" type="button" aria-label="Menu" aria-expanded="false">${ICONS.menu}</button>` +
      `<nav class="nav" aria-label="Hlavní navigace">` +
      NAV.map((n) => `<a href="${n.href}"${n.key === active ? ' aria-current="page"' : ""}>${n.label}${n.soon ? '<span class="soon">brzy</span>' : ""}</a>`).join("") +
      `</nav><button class="icon-btn theme-btn" type="button" aria-label="Přepnout světlý / tmavý režim"></button></div>`;
    const tb = el.querySelector(".theme-btn");
    const setIcon = () => { tb.innerHTML = RV.isDark() ? ICONS.sun : ICONS.moon; };
    setIcon();
    tb.addEventListener("click", () => { toggleTheme(); setIcon(); });
    const mb = el.querySelector(".menu-btn"), nav = el.querySelector(".nav");
    mb.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      mb.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  function footer() {
    const el = document.querySelector("[data-site-footer]");
    if (!el) return;
    el.className = "site-footer";
    el.innerHTML = `<div class="wrap">
      <div>
        <h4>O projektu</h4>
        <p>Neoficiální analýza komunálních voleb v Řevnicích 9.–10. října 2026. Analýzy vytvořily jazykové modely
        <strong>Claude</strong> (Anthropic) a <strong>GPT</strong> (OpenAI); zadání a prompty připravil <strong>Petr Čermák</strong> (sám kandidoval za PRO Řevnice; data i kód jsou veřejné).</p>
        <p class="muted" style="margin:0">Oficiální výsledky najdete na <a href="https://www.volby.cz/" rel="noopener">volby.cz</a>.
        Modelové odhady nejsou změřená data – vždy jsou označené.</p>
      </div>
      <div>
        <h4>Kapitoly</h4>
        <ul>${NAV.map((n) => `<li><a href="${n.href}">${n.label}</a>${n.soon ? ' <span class="muted">(připravujeme)</span>' : ""}</li>`).join("")}</ul>
      </div>
      <div>
        <h4>Data a kód</h4>
        <ul>
          <li>Zdroj dat: <a href="https://www.volby.cz/" rel="noopener">ČSÚ / volby.cz</a></li>
          <li><a href="${REPO}" rel="noopener">Zdrojový kód na GitHubu</a></li>
          <li><a href="notebooky/claude.html">Notebook Claude</a> · <a href="notebooky/gpt.html">Notebook GPT</a></li>
          <li><a href="data/zakladni.json" download>Základní data (JSON)</a></li>
        </ul>
      </div>
    </div>`;
  }

  /* ---------- Plotly ---------- */
  const charts = [];
  RV.baseLayout = function () {
    const ink = RV.token("ink"), ink2 = RV.token("ink-2"), muted = RV.token("muted");
    const line = RV.token("line"), strong = RV.token("line-strong"), surface = RV.token("surface");
    const axis = {
      gridcolor: line, zerolinecolor: strong, linecolor: strong, tickcolor: strong,
      tickfont: { color: muted, size: 12 }, title: { font: { color: ink2, size: 13 } },
      automargin: true, fixedrange: true, showspikes: false, exponentformat: "none", separatethousands: true,
    };
    return {
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      font: { family: "Inter, system-ui, -apple-system, Segoe UI, sans-serif", size: 13, color: ink2 },
      margin: { l: 10, r: 16, t: 10, b: 10 },
      separators: ", ",
      showlegend: false,
      hovermode: "closest",
      hoverlabel: { bgcolor: surface, bordercolor: strong, font: { color: ink, size: 13, family: "Inter, system-ui, sans-serif" }, align: "left" },
      xaxis: Object.assign({}, axis), yaxis: Object.assign({}, axis),
      bargap: 0.28,
      dragmode: false,
    };
  };
  function merge(a, b) {
    const out = Array.isArray(a) ? a.slice() : Object.assign({}, a);
    for (const k in b) {
      if (b[k] && typeof b[k] === "object" && !Array.isArray(b[k]) && a && typeof a[k] === "object" && !Array.isArray(a[k])) out[k] = merge(a[k], b[k]);
      else out[k] = b[k];
    }
    return out;
  }
  RV.merge = merge;
  const CONFIG = { displayModeBar: false, responsive: true, scrollZoom: false, locale: "cs" };

  function draw(c) {
    if (!window.Plotly || !c.visible) return;
    const spec = c.fn(c.el.clientWidth || 600);
    if (!spec) return;
    const layout = merge(RV.baseLayout(), spec.layout || {});
    window.Plotly.react(c.el, spec.data, layout, CONFIG);
    if (spec.after) spec.after(c.el);
  }
  /** Zaregistruje graf. fn(width) vrací {data, layout}. Vrací funkci pro překreslení. */
  RV.plot = function (el, fn) {
    if (typeof el === "string") el = document.querySelector(el);
    if (!el) return () => {};
    const c = { el, fn, visible: false };
    charts.push(c);
    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver((entries) => {
        if (entries.some((e) => e.isIntersecting)) { c.visible = true; draw(c); io.disconnect(); }
      }, { rootMargin: "300px" });
      io.observe(el);
    } else { c.visible = true; draw(c); }
    return function redraw(newFn) { if (newFn) c.fn = newFn; draw(c); };
  };
  function themeChanged() { charts.forEach(draw); document.dispatchEvent(new CustomEvent("rv-theme")); }
  let rt = null, lastW = window.innerWidth;
  window.addEventListener("resize", () => {
    clearTimeout(rt);
    rt = setTimeout(() => { if (Math.abs(window.innerWidth - lastW) > 40) { lastW = window.innerWidth; charts.forEach(draw); } }, 200);
  });

  /* segmentové přepínače: <div class="seg" data-seg> <button data-v=..> */
  RV.seg = function (el, onChange) {
    if (typeof el === "string") el = document.querySelector(el);
    if (!el) return;
    const btns = Array.from(el.querySelectorAll("button"));
    btns.forEach((b) => b.addEventListener("click", () => {
      btns.forEach((x) => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
      onChange(b.dataset.v, b);
    }));
  };

  /* ---------- d'Hondt (stejná pravidla jako basic/prepare_basic.py) ---------- */
  RV.dhondt = function (votes, seats = 15, threshold = 0.05) {
    const total = Object.values(votes).reduce((a, b) => a + b, 0);
    const q = [];
    for (const p in votes) {
      if (votes[p] < threshold * total) continue;
      for (let d = 1; d <= seats; d++) q.push({ p, d, q: votes[p] / d });
    }
    q.sort((a, b) => (b.q - a.q) || (votes[b.p] - votes[a.p]));   // při rovnosti podílů rozhoduje vyšší počet hlasů
    const res = {};
    for (const p in votes) res[p] = 0;
    q.slice(0, seats).forEach((x) => { res[x.p] += 1; });
    return { seats: res, quotients: q, total };
  };

  /* ---------- zobrazení při scrollu ---------- */
  function reveal() {
    const els = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window)) { els.forEach((e) => e.classList.add("in")); return; }
    const io = new IntersectionObserver((entries) => entries.forEach((e) => {
      if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
    }), { rootMargin: "0px 0px -40px 0px" });
    els.forEach((e) => io.observe(e));
  }

  RV.init = function (active) {
    header(active);
    footer();
    reveal();
  };
})();
