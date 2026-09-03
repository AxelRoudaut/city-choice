#!/usr/bin/env python3
"""Critère 14 — Eau du robinet, via Hub'Eau (contrôle sanitaire ARS).

Moyenne des nitrates sur 12 mois glissants : un prélèvement isolé varie trop
(trois relevés rennais consécutifs : 14,9 / 15,7 / 18,6 mg/L).
Sans clé. Limite réglementaire : 50 mg/L.
"""
import sys, pathlib, datetime, statistics
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import VILLES, curl_json, ecrire

API = "https://hubeau.eaufrance.fr/api/v1/qualite_eau_potable/resultats_dis"
NITRATES = "1340"
LIMITE = 50.0


def main():
    depuis = (datetime.date.today() - datetime.timedelta(days=365)).isoformat()
    res = {}
    for v, meta in VILLES.items():
        vals, distributeurs, conformes, total = [], set(), 0, 0
        for page in range(1, 4):
            d = curl_json(f"{API}?code_commune={meta['insee']}&code_parametre={NITRATES}"
                          f"&date_min_prelevement={depuis}&size=1000&page={page}", timeout=120)
            data = d.get("data") or []
            for r in data:
                if r.get("resultat_numerique") is not None:
                    vals.append(r["resultat_numerique"])
                    distributeurs.add(r.get("nom_distributeur") or "?")
                c = r.get("conclusion_conformite_prelevement") or ""
                total += 1
                if c.lower().startswith("eau d'alimentation conforme"):
                    conformes += 1
            if not d.get("next") or not data:
                break
        if not vals:
            print(f"  {v:12} aucun relevé")
            continue
        res[v] = {
            "nitrates_moy_12_mois": round(statistics.mean(vals), 1),
            "nitrates_min": min(vals), "nitrates_max": max(vals),
            "releves": len(vals),
            "conformite_pct": round(100 * conformes / total, 1) if total else None,
            "distributeurs": sorted(distributeurs),
            "limite_reglementaire": LIMITE,
        }
        print(f"  {v:12} {res[v]['nitrates_moy_12_mois']:>5.1f} mg/L "
              f"(min {min(vals)}, max {max(vals)}, {len(vals)} relevés) · "
              f"{res[v]['conformite_pct']}% conformes · {', '.join(sorted(distributeurs))[:34]}")
    ecrire("eau_potable", res, "Hub'Eau — contrôle sanitaire de l'eau distribuée (ARS)",
           "https://hubeau.eaufrance.fr/page/api-qualite-eau-potable", unite="mg/L de nitrates",
           methode="Moyenne des nitrates (paramètre 1340) sur 12 mois glissants, "
                   "tous réseaux desservant la commune. Limite réglementaire : 50 mg/L.")


if __name__ == "__main__":
    main()
