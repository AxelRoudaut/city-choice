#!/usr/bin/env python3
"""Critère 15 — Affinité politique, via les résultats officiels des municipales.

Le RNE donne les maires mais PAS leur étiquette : la nuance politique vient des
résultats du ministère de l'Intérieur. Indicateur retenu : part des sièges de
gauche au conseil municipal.
Préférence déclarée du rapport : favoriser la gauche.
"""
import sys, pathlib, csv, io
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import VILLES, curl_bytes, curl_json, ecrire

DATASET = ("https://www.data.gouv.fr/api/1/datasets/"
           "elections-municipales-2026-resultats-du-second-tour/")
# Nuances officielles du ministère de l'Intérieur classées à gauche.
GAUCHE = {"LUG", "LFI", "LDVG", "LVEC", "LECO", "LSOC", "LCOM", "LEXG", "LRDG"}
BLOC = 13   # colonnes par liste candidate


def url_communes():
    for r in curl_json(DATASET).get("resources", []):
        t = r.get("title") or ""
        if "Résultats - Communes_" in t and "Polynésie" not in t:
            return r["url"]
    raise SystemExit("ressource « Résultats - Communes » introuvable")


def pct(x):
    try:
        return float(x.replace("%", "").replace(",", ".").strip())
    except (AttributeError, ValueError):
        return None


def main():
    brut = curl_bytes(url_communes(), timeout=180)
    try:
        txt = brut.decode("utf-8-sig")
    except UnicodeDecodeError:
        txt = brut.decode("latin-1")
    lignes = list(csv.reader(io.StringIO(txt), delimiter=";"))
    par_insee = {l[2].strip(): l for l in lignes[1:] if len(l) > 3}
    res = {}
    for v, meta in VILLES.items():
        r = par_insee.get(meta["insee"])
        if not r:
            print(f"  {v:12} absent du second tour (élu au premier ?)")
            continue
        listes, i = [], 18
        while i + 12 < len(r) and r[i].strip():
            listes.append({
                "candidat": f"{r[i+2].strip()} {r[i+1].strip()}",
                "nuance": r[i+4].strip(), "liste": r[i+6].strip(),
                "pct_exprimes": pct(r[i+9]),
                "sieges": int(r[i+11]) if r[i+11].strip().isdigit() else 0,
            })
            i += BLOC
        listes.sort(key=lambda x: -(x["pct_exprimes"] or 0))
        total = sum(l["sieges"] for l in listes)
        gauche = sum(l["sieges"] for l in listes if l["nuance"] in GAUCHE)
        res[v] = {
            "tete": listes[0]["candidat"] if listes else None,
            "nuance_tete": listes[0]["nuance"] if listes else None,
            "sieges_total": total, "sieges_gauche": gauche,
            "part_gauche_pct": round(100 * gauche / total, 1) if total else None,
            "listes": listes,
        }
        print(f"  {v:12} {res[v]['tete'][:24]:26} [{res[v]['nuance_tete']:<5}] "
              f"gauche {gauche:>3}/{total:<3} = {res[v]['part_gauche_pct']}%")
    ecrire("politique", res, "Ministère de l'Intérieur — municipales 2026, second tour",
           DATASET, unite="% des sièges au conseil municipal",
           methode="Part des sièges détenus par des listes de nuance officielle de gauche "
                   f"({', '.join(sorted(GAUCHE))}). Préférence déclarée : favoriser la gauche.")


if __name__ == "__main__":
    main()
