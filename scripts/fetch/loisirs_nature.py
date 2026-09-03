#!/usr/bin/env python3
"""Critères 11-12 — Falaise et baignade, via OpenStreetMap (Overpass).

FALAISE : ne compter que l'escalade AVEC CORDE. Un simple comptage de sites
place Paris en tête grâce à Fontainebleau, qui est du bloc : il faut exiger un
marqueur de voie équipée (climbing:sport, trad, multipitch, longueur, cotation).

BAIGNADE : plages et zones de baignade, SURVEILLÉES OU NON. Le rapportage de la
saison balnéaire ne recense que les sites surveillés et manque donc les lacs et
criques, qui comptent autant.
"""
import sys, pathlib, json, time
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import VILLES, curl, ecrire

MIROIRS = ["https://overpass-api.de/api/interpreter",
           "https://overpass.kumi.systems/api/interpreter"]
RAYON_FALAISE = 50000
RAYON_BAIGNADE = 30000
CORDE = ("climbing:sport", "climbing:trad", "climbing:multipitch",
         "climbing:length:max", "climbing:grade:french:max", "climbing:length", "climbing:rock")


def overpass(requete):
    for i in range(5):
        txt = curl(MIROIRS[i % len(MIROIRS)], "-X", "POST", "-d", "data=" + requete,
                   timeout=150, retries=1)
        try:
            return json.loads(txt)["elements"]
        except Exception:
            time.sleep(20)
    return None


def main():
    res = {}
    for v, meta in VILLES.items():
        lat, lon = meta["lat"], meta["lon"]
        els = overpass(f'[out:json][timeout:120];'
                       f'(nwr(around:{RAYON_FALAISE},{lat},{lon})["sport"="climbing"];);out tags center;')
        if els is None:
            print(f"  {v:12} falaise : Overpass indisponible")
            continue
        corde = [e for e in els
                 if any(k in e.get("tags", {}) for k in CORDE)
                 and e.get("tags", {}).get("climbing") != "boulder"
                 and e.get("tags", {}).get("leisure") != "sports_centre"
                 and not e.get("tags", {}).get("building")]
        res.setdefault(v, {})["falaise"] = {
            "sites_avec_corde": len(corde),
            "sites_bruts": len(els),
            "rayon_km": RAYON_FALAISE // 1000,
        }
        print(f"  {v:12} falaise  {len(corde):>4} sites corde (sur {len(els)} bruts)")
        time.sleep(8)
    for v, meta in VILLES.items():
        lat, lon = meta["lat"], meta["lon"]
        els = overpass(f'[out:json][timeout:120];('
                       f'nwr(around:{RAYON_BAIGNADE},{lat},{lon})["natural"="beach"];'
                       f'nwr(around:{RAYON_BAIGNADE},{lat},{lon})["leisure"="swimming_area"];'
                       f'nwr(around:{RAYON_BAIGNADE},{lat},{lon})["sport"="swimming"]["natural"="water"];'
                       f');out tags center;')
        if els is None:
            print(f"  {v:12} baignade : Overpass indisponible")
            continue
        plages = [e for e in els if e.get("tags", {}).get("natural") == "beach"]
        res.setdefault(v, {})["baignade"] = {
            "spots": len(els), "plages": len(plages), "zones_baignade": len(els) - len(plages),
            "rayon_km": RAYON_BAIGNADE // 1000,
        }
        print(f"  {v:12} baignade {len(els):>4} spots ({len(plages)} plages)")
        time.sleep(8)
    ecrire("loisirs_nature", res, "OpenStreetMap via Overpass",
           "https://overpass-api.de/", unite="nombre de sites",
           methode=f"Falaise : sites sport=climbing à moins de {RAYON_FALAISE // 1000} km portant "
                   "un marqueur d'escalade avec corde ; le bloc et les salles sont exclus. "
                   f"Baignade : plages et zones de baignade à moins de {RAYON_BAIGNADE // 1000} km, "
                   "surveillées ou non.")


if __name__ == "__main__":
    main()
