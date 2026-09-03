#!/usr/bin/env python3
"""Critère 3 — Logement, via la Carte des loyers (DHUP / data.gouv).

Le jeu couvre les 34 900 communes : le rayon de 15 km est calculé pour de vrai,
pas approximé par la ville-centre. Paris est publié par arrondissement, moyenné
ici au prorata du nombre d'annonces.
PIÈGE : CSV en latin-1, séparateur « ; », décimales à la virgule.
"""
import sys, pathlib, csv, io, math, json, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import VILLES, curl_bytes, curl_json, ecrire

DATASET = ("https://www.data.gouv.fr/api/1/datasets/"
           "carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2025/")
RAYON_KM = 15


def url_csv():
    for r in curl_json(DATASET).get("resources", []):
        t = (r.get("title") or "").lower()
        if r.get("format") == "csv" and "appartement" in t and "1 ou 2" not in t and "3 pièces" not in t:
            return r["url"]
    raise SystemExit("ressource « Indicateurs de loyer appartement » introuvable")


def f(x):
    try:
        return float(str(x).replace(",", "."))
    except (TypeError, ValueError):
        return None


def dist_km(a, b):
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180
    return 12742 * math.asin(math.sqrt(
        0.5 - math.cos((la2 - la1) * p) / 2
        + math.cos(la1 * p) * math.cos(la2 * p) * (1 - math.cos((lo2 - lo1) * p)) / 2))


def centres():
    """Centroïdes de toutes les communes, pour le rayon."""
    d = curl_json("https://geo.api.gouv.fr/communes?fields=code,centre&format=json", timeout=180)
    return {c["code"]: (c["centre"]["coordinates"][1], c["centre"]["coordinates"][0])
            for c in d if c.get("centre")}


def main():
    brut = curl_bytes(url_csv())
    lignes = list(csv.DictReader(io.StringIO(brut.decode("latin-1")), delimiter=";"))
    par_insee = {l["INSEE_C"].strip(): l for l in lignes}
    geo = centres()
    res = {}
    for v, meta in VILLES.items():
        insee = meta["insee"]
        # Paris : moyenne des arrondissements pondérée par le nombre d'annonces
        cibles = [c for c in par_insee if c.startswith("751")] if insee == "75056" else [insee]
        num = den = 0.0
        for c in cibles:
            l = par_insee.get(c)
            if not l:
                continue
            p, n = f(l["loypredm2"]), f(l["nbobs_com"]) or 1
            if p:
                num += p * n
                den += n
        ville_loyer = round(num / den, 2) if den else None
        # rayon de 15 km : moyenne simple des communes dont le centroïde est dans le rayon
        ici = (meta["lat"], meta["lon"])
        autour = [f(par_insee[c]["loypredm2"]) for c, pos in geo.items()
                  if c in par_insee and dist_km(ici, pos) <= RAYON_KM]
        autour = [x for x in autour if x]
        res[v] = {
            "loyer_ville_eur_m2": ville_loyer,
            f"loyer_moyen_{RAYON_KM}km_eur_m2": round(sum(autour) / len(autour), 2) if autour else None,
            "communes_dans_le_rayon": len(autour),
        }
        print(f"  {v:12} ville {ville_loyer} €/m² · rayon {RAYON_KM} km "
              f"{res[v][f'loyer_moyen_{RAYON_KM}km_eur_m2']} €/m² sur {len(autour)} communes")
    ecrire("logement", res, "Carte des loyers — indicateurs de loyers d'annonce (DHUP)",
           DATASET, unite="€/m²",
           methode=f"Loyer d'annonce prédit appartement. Ville : valeur communale (Paris : "
                   f"moyenne des arrondissements pondérée par le nombre d'annonces). "
                   f"Rayon : moyenne des communes dont le centroïde est à moins de {RAYON_KM} km.")


if __name__ == "__main__":
    main()
