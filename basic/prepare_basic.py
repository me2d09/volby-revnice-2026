#!/usr/bin/env python3
"""Základní (model-free) statistiky komunálních voleb Řevnice 2026.

Čte jen ověřená vstupní data ze složky ``input/`` a vytváří
``basic/zakladni_data.json`` (+ několik přehledných CSV), ze kterých
čerpá jednoduchá, interaktivní část webu. Bez externích závislostí (jen stdlib).

Spuštění z kořene repozitáře:  python basic/prepare_basic.py
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INP = ROOT / "input" / "data"
OUT = Path(__file__).resolve().parent

SEATS = 15
THRESHOLD = 0.05            # 5% klauzule (§ 45 zákona č. 491/2001 Sb.)
PREF_RULE = 1.10            # přednostní pořadí: ≥ 110 % průměru hlasů na kandidáta strany
BALLOT_VOTES = 15           # zakřížkování celé kandidátky = 15 hlasů

# Údaje, které ve vstupních CSV nejsou: ČSÚ open data (vysledky_obec_539643.xml,
# 10. 10. 2026) a input/context/CO_UZ_VIME.md.
TURNOUT = {
    "registered_voters": 2819,
    "envelopes": 1690,
    "valid_ballots": 1679,
    "turnout_pct": 59.95,
    "turnout_2022_pct": 56.14,
}

# Krátké názvy, barvy (identita kandidátek z infografiky) a pořadí čísel na lístku.
PARTIES = {
    "ŠANCE Řevnice":                       dict(id=1, short="ŠANCE",        color="#e6b000"),
    "TOP 09 a nezávislí kandidáti":        dict(id=2, short="TOP 09",       color="#8256c4"),
    "DOBŘE - Dialog o budoucnosti Řevnic": dict(id=3, short="DOBŘE",        color="#3f9a3a"),
    "Hnutí Srdce Řevnic":                  dict(id=4, short="Srdce Řevnic", color="#946b4a"),
    "PRO Řevnice":                         dict(id=5, short="PRO",          color="#2d86d4"),
    "ODS a nezávislí":                     dict(id=6, short="ODS",          color="#1f3c80"),
    "Perspektiva pro město":               dict(id=7, short="Perspektiva",  color="#df4f97"),
    "Naše Řevnice":                        dict(id=8, short="Naše Řevnice", color="#e5601e"),
    "Řevnice SPOLEČNĚ":                    dict(id=9, short="SPOLEČNĚ",     color="#8f8c84"),
}
FULL_DISPLAY = {"DOBŘE - Dialog o budoucnosti Řevnic": "DOBŘE – Dialog o budoucnosti Řevnic"}

TITLES = {"Ing.", "arch.", "Mgr.", "MPA", "Ph.D.", "doc.", "MUDr.", "MgA.", "Bc.",
          "RNDr.", "Dr.", "MSc."}
# Víceslovná příjmení / jména, která nelze rozdělit pravidlem „první slovo = příjmení“.
NAME_OVERRIDES = {
    "Nappi Bursík Martina": "Martina Nappi Bursík",
    "Sedláčková Davidová Markéta": "Markéta Sedláčková Davidová",
    "Sedláčková Rytířová Helena": "Helena Sedláčková Rytířová",
    "Fasching Kronus Petra": "Petra Fasching Kronus",
}
FEMALE_FIRST = {"Martina", "Terezie", "Markéta"}   # stačí pro 15 zvolených (ověřeno ručně)


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def display_name(raw: str) -> str:
    words = [w for w in raw.split() if w not in TITLES]
    key = " ".join(words)
    if key in NAME_OVERRIDES:
        return NAME_OVERRIDES[key]
    return " ".join(words[1:] + words[:1])


def dhondt(votes: dict[str, int], seats: int = SEATS, threshold: float = THRESHOLD):
    """Vrátí (mandáty, seznam přidělených podílů v pořadí) podle § 45 zák. 491/2001 Sb."""
    total = sum(votes.values())
    qualified = {p: v for p, v in votes.items() if v >= threshold * total}
    # při rovnosti podílů rozhoduje vyšší celkový počet hlasů (§ 45 odst. 4)
    quotients = sorted(((v / d, p, d) for p, v in qualified.items() for d in range(1, seats + 1)),
                       key=lambda t: (-t[0], -qualified[t[1]]))
    result = {p: 0 for p in votes}
    for q, p, d in quotients[:seats]:
        result[p] += 1
    return result, quotients


def votes_to_gain(votes: dict[str, int], party: str) -> int | None:
    """Nejmenší počet NOVÝCH hlasů pro stranu, který jí přinese další mandát (ostatní beze změny)."""
    base = dhondt(votes)[0][party]
    for x in range(1, 6000):
        v = dict(votes); v[party] += x
        if dhondt(v)[0][party] > base:
            return x
    return None


def votes_to_lose(votes: dict[str, int], party: str) -> int | None:
    """Kolik hlasů by strana musela ztratit, aby přišla o mandát."""
    base = dhondt(votes)[0][party]
    if base == 0:
        return None
    for x in range(1, votes[party] + 1):
        v = dict(votes); v[party] -= x
        if dhondt(v)[0][party] < base:
            return x
    return None


def main() -> None:
    parties_2022_2026 = read_csv(INP / "raw" / "strany_2022_2026.csv")
    cands = read_csv(INP / "processed" / "city_candidates_2026.csv")
    prec_cands = read_csv(INP / "processed" / "precinct_candidates_2026.csv")
    prec_party = read_csv(INP / "raw" / "okrsky_2026_party.csv")
    elected_cmp = read_csv(INP / "raw" / "zvoleni_2026_a_srovnani_2022.csv")

    votes26 = {r["strana"]: int(r["hlasy_2026"]) for r in parties_2022_2026 if int(r["hlasy_2026"]) > 0}
    votes22 = {r["strana"]: int(r["hlasy_2022"]) for r in parties_2022_2026 if int(r["hlasy_2022"]) > 0}
    total26, total22 = sum(votes26.values()), sum(votes22.values())
    seats26, quotients = dhondt(votes26)
    seats22, _ = dhondt(votes22)

    # --- kontrola: kandidátské součty = stranické součty
    for p, v in votes26.items():
        assert sum(int(c["votes"]) for c in cands if c["party"] == p) == v, p
    assert total26 == 23939

    # --- kandidáti: přednostní hlasy a kdo získá mandát
    by_party: dict[str, list[dict]] = {}
    for c in cands:
        by_party.setdefault(c["party"], []).append(c)
    pc_votes = {}
    for r in prec_cands:
        pc_votes.setdefault((r["party"], int(r["position"])), {})[int(r["precinct"])] = int(r["votes"])

    candidates = []
    pref_thresholds = {}
    for p, lst in by_party.items():
        lst.sort(key=lambda c: int(c["position"]))
        thr = PREF_RULE * votes26[p] / len(lst)
        pref_thresholds[p] = thr
        pref = sorted([c for c in lst if int(c["votes"]) >= thr], key=lambda c: -int(c["votes"]))
        rest = [c for c in lst if c not in pref]
        order = pref + rest
        n = seats26[p]
        winners = {c["name"] for c in order[:n]}
        for c in lst:
            pos = int(c["position"])
            candidates.append({
                "party": PARTIES[p]["short"],
                "position": pos,
                "name": display_name(c["name"]),
                "name_full": c["name"],
                "age": int(c["age"]),
                "votes": int(c["votes"]),
                "votes_precincts": [pc_votes[(p, pos)][k] for k in (1, 2, 3, 4)],
                "share_of_party_pct": round(100 * int(c["votes"]) / votes26[p], 2),
                "preference": int(c["votes"]) >= thr,
                "elected": c["name"] in winners,
                "min_personal_marks": int(c["rigorous_min_personal_marks_sum_precincts"]),
            })
        # kontrola proti oficiálnímu výsledku
        official = {c["name"] for c in lst if c["elected_2026"] == "ANO"}
        assert official == winners, (p, official, winners)

    # --- zvolení a srovnání s rokem 2022
    cmp_by_name = {r["zastupitel"]: r for r in elected_cmp}
    elected = sorted((c for c in candidates if c["elected"]), key=lambda c: -c["votes"])
    elected_out = []
    for c in elected:
        key = c["name"]
        if c["name"] == "Petr Hartmann":
            key = "Petr Hartmann (Perspektiva)"
        if c["name"] == "Pavel Hartmann":
            key = "Pavel Hartmann (TOP 09)"
        r = cmp_by_name[key]
        v22 = int(r["hlasy_2022_pokud_zvolen_2022"]) if r["hlasy_2022_pokud_zvolen_2022"] else None
        elected_out.append({
            "name": c["name"], "party": c["party"], "position": c["position"], "votes": c["votes"],
            "age": c["age"], "female": c["name"].split()[0] in FEMALE_FIRST,
            "votes_2022": v22,
            "party_2022": PARTIES[r["strana_2022"]]["short"] if r["strana_2022"] else None,
            "jumped": c["position"] > seats26[next(k for k, v in PARTIES.items() if v["short"] == c["party"])],
        })

    # --- strany
    parties_out = []
    for r in parties_2022_2026:
        p = r["strana"]
        meta = PARTIES[p]
        parties_out.append({
            "id": meta["id"], "short": meta["short"], "name": FULL_DISPLAY.get(p, p), "color": meta["color"],
            "votes_2026": int(r["hlasy_2026"]), "share_2026": round(float(r["podil_2026_pct"]), 2),
            "votes_2022": int(r["hlasy_2022"]), "share_2022": round(float(r["podil_2022_pct"]), 2),
            "seats_2026": seats26.get(p, 0), "seats_2022": seats22.get(p, 0),
            "change_votes": int(r["zmena_hlasu"]), "change_pp": round(float(r["zmena_p_b"]), 2),
            "qualified_2026": p in votes26 and votes26[p] >= THRESHOLD * total26,
            "votes_to_next_seat": votes_to_gain(votes26, p) if p in votes26 else None,
            "votes_to_lose_seat": votes_to_lose(votes26, p) if p in votes26 else None,
            "pref_threshold": round(pref_thresholds[p], 1) if p in pref_thresholds else None,
            "avg_age": round(sum(c["age"] for c in candidates if c["party"] == meta["short"]) / 15, 1)
                       if p in votes26 else None,
        })
    parties_out.sort(key=lambda d: (-d["votes_2026"], -d["votes_2022"]))

    # --- d'Hondtovy podíly (prvních 22 – ukazují „hranu“ posledního mandátu)
    quot_out = [{"party": PARTIES[p]["short"], "divisor": d, "quotient": round(q, 2), "seat": i < SEATS}
                for i, (q, p, d) in enumerate(quotients[:22])]

    # --- okrsky
    precincts = []
    for k in (1, 2, 3, 4):
        rows = [r for r in prec_party if int(r["okrsek"]) == k]
        pv = {PARTIES[r["strana"]]["short"]: int(r["hlasy"]) for r in rows}
        tot = int(rows[0]["celkem_hlasu_v_okrsku"])
        assert sum(pv.values()) == tot
        winner = max(pv, key=pv.get)
        without = {PARTIES[p]["short"]: votes26[p] - pv[PARTIES[p]["short"]] for p in votes26}
        precincts.append({
            "id": k, "votes_total": tot, "turnout_pct": float(rows[0]["volebni_ucast_pct_podle_novinky"]),
            "votes": pv, "shares": {s: round(100 * v / tot, 2) for s, v in pv.items()},
            "winner": winner,
            "seats_if_only_this": {PARTIES[p]["short"]: s for p, s in
                                   dhondt({p: pv[PARTIES[p]["short"]] for p in votes26})[0].items()},
            "city_without": without,
            "winner_without": max(without, key=without.get),
        })
    precinct_labels = {1: "sever / u Berounky", 2: "západ / jihozápad", 3: "střed / jih", 4: "východ / jihovýchod"}
    for pr in precincts:
        pr["label"] = precinct_labels[pr["id"]]

    # --- rychlá čísla a zajímavosti
    unrepresented = sum(d["votes_2026"] for d in parties_out if d["votes_2026"] and not d["qualified_2026"])
    ods = next(d for d in parties_out if d["short"] == "ODS")
    ods_votes = ods["votes_2026"]
    need_new = math.ceil((THRESHOLD * total26 - ods_votes) / (1 - THRESHOLD))     # nové hlasy zvyšují i celkový počet
    need_moved = math.ceil(THRESHOLD * total26 - ods_votes)                        # přetažené od jiné strany
    dudova = next(c for c in candidates if c["name"] == "Renata Dudová")
    bobek = next(c for c in candidates if c["name"] == "Vladimír Bobek")
    ages = [c["age"] for c in candidates]
    youngest = [c for c in candidates if c["age"] == min(ages)]
    oldest = [c for c in candidates if c["age"] == max(ages)]
    top_votes = max(candidates, key=lambda c: c["votes"])

    data = {
        "meta": {
            "title": "Komunální volby 2026 – Řevnice",
            "election_dates": "9.–10. 10. 2026",
            "municipality_code": "539643",
            "seats": SEATS, "threshold_pct": 100 * THRESHOLD, "pref_rule": PREF_RULE,
            "source": "ČSÚ / volby.gov.cz (uživatelské CSV exporty), viz input/README.md",
        },
        "turnout": {**TURNOUT, "turnout_change_pp": round(TURNOUT["turnout_pct"] - TURNOUT["turnout_2022_pct"], 2)},
        "totals": {
            "votes_2026": total26, "votes_2022": total22, "change_votes": total26 - total22,
            "change_pct": round(100 * (total26 - total22) / total22, 2),
            "votes_per_ballot": round(total26 / TURNOUT["valid_ballots"], 2),
            "unused_votes": TURNOUT["valid_ballots"] * SEATS - total26,
            "unrepresented_votes": unrepresented,
            "unrepresented_pct": round(100 * unrepresented / total26, 2),
            "women_elected": sum(e["female"] for e in elected_out),
            "candidates": len(candidates),
            "avg_age_candidates": round(sum(ages) / len(ages), 1),
            "avg_age_elected": round(sum(e["age"] for e in elected_out) / len(elected_out), 1),
            "min_personal_marks_city": sum(int(c["rigorous_min_personal_marks_city"]) for c in cands),
            "min_personal_marks_precincts": sum(c["min_personal_marks"] for c in candidates),
        },
        "parties": parties_out,
        "dhondt": quot_out,
        "precincts": precincts,
        "candidates": candidates,
        "elected": elected_out,
        "facts": {
            "ods_threshold_votes_new": need_new,
            "ods_threshold_votes_moved": need_moved,
            "ods_share_pct": ods["share_2026"],
            "last_seat": quot_out[SEATS - 1],
            "first_loser": quot_out[SEATS],
            "dudova": {"votes": dudova["votes"], "threshold": next(d["pref_threshold"] for d in parties_out if d["short"] == "DOBŘE"),
                       "bobek_votes": bobek["votes"]},
            "youngest": [{k: c[k] for k in ("name", "party", "age")} for c in youngest],
            "oldest": [{k: c[k] for k in ("name", "party", "age")} for c in oldest],
            "top_candidate": {k: top_votes[k] for k in ("name", "party", "votes")},
        },
    }

    (OUT / "zakladni_data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    def write(name: str, rows: list[dict], cols: list[str]) -> None:
        with open(OUT / name, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, delimiter=";", extrasaction="ignore")
            w.writeheader(); w.writerows(rows)

    write("strany_mandaty.csv", parties_out, ["short", "name", "votes_2026", "share_2026", "seats_2026",
          "votes_2022", "share_2022", "seats_2022", "change_votes", "change_pp", "qualified_2026",
          "votes_to_next_seat", "votes_to_lose_seat", "pref_threshold", "avg_age"])
    write("dhondt_podily.csv", quot_out, ["party", "divisor", "quotient", "seat"])
    write("zvoleni.csv", elected_out, ["name", "party", "position", "votes", "age", "votes_2022", "party_2022", "jumped"])

    print(f"OK: {len(candidates)} kandidátů, {len(precincts)} okrsky, mandáty {dict((PARTIES[p]['short'], s) for p, s in seats26.items())}")
    print(f"ODS k 5 %: +{need_new} nových / {need_moved} přetažených hlasů; poslední mandát {quot_out[SEATS-1]}, první pod čarou {quot_out[SEATS]}")
    print({d["short"]: (d["votes_to_next_seat"], d["votes_to_lose_seat"]) for d in parties_out})


if __name__ == "__main__":
    main()
