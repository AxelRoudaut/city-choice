#!/usr/bin/env python3
"""Critère 16 — Transports en commun, via les GTFS de transport.data.gouv.fr.

Deux mesures :
  couverture — part des communes de l'EPCI ayant au moins un arrêt ;
  qualité    — hiérarchie des modes, un métro ne vaut pas un bus.

PIÈGE : plusieurs réseaux publient plusieurs GTFS (urbain seul, suburbain seul,
réseau complet). Prendre le premier venu donne un Montpellier sans tram. On
retient donc le GTFS offrant le plus de modes distincts.
"""
import sys, pathlib, json, csv, io, zipfile, collections
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import VILLES, curl, curl_bytes, curl_json, ecrire, RACINE

CATALOGUE = "https://transport.data.gouv.fr/api/datasets"
CACHE = RACINE / ".cache" / "gtfs"
# route_type GTFS, y compris les types étendus les plus courants
MODES = {"0": "tram", "1": "métro", "2": "train", "3": "bus", "4": "ferry",
         "5": "tram-câble", "6": "câble", "7": "funiculaire", "11": "trolleybus", "12": "monorail",
         "700": "bus", "900": "tram", "1000": "ferry", "1300": "câble", "1400": "funiculaire"}
# Poids de qualité : un mode guidé en site propre transporte plus et plus vite.
QUALITE = {"métro": 3, "train": 2, "tram": 2, "funiculaire": 1, "câble": 1, "ferry": 1}


def dans(point, geom):
    def anneau(pt, ring):
        x, y = pt
        dedans = False
        for i in range(len(ring)):
            x1, y1 = ring[i]
            x2, y2 = ring[(i + 1) % len(ring)]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                dedans = not dedans
        return dedans

    def poly(pt, p):
        return bool(p) and anneau(pt, p[0]) and not any(anneau(pt, t) for t in p[1:])

    c = geom["coordinates"]
    return poly(point, c) if geom["type"] == "Polygon" else any(poly(point, p) for p in c)


def cadre(geom):
    xs, ys, pile = [], [], [geom["coordinates"]]
    while pile:
        i = pile.pop()
        if isinstance(i, (list, tuple)) and i and isinstance(i[0], (int, float)):
            xs.append(i[0]); ys.append(i[1])
        elif isinstance(i, (list, tuple)):
            pile += list(i)
    return min(xs), min(ys), max(xs), max(ys)


def gtfs_du_reseau(catalogue, ville):
    """Toutes les URL GTFS des jeux « public-transit » citant la ville."""
    urls = []
    for jeu in catalogue:
        if jeu.get("type") != "public-transit":
            continue
        titre = jeu.get("title", "")
        if ville.lower()[:5] not in titre.lower() and not _reseau_connu(titre, ville):
            continue
        pile, plat = list(jeu.get("resources") or []), []
        while pile:
            i = pile.pop()
            if isinstance(i, dict):
                plat.append(i)
            elif isinstance(i, list):
                pile += i
        for r in plat:
            if (r.get("format") or "").upper() == "GTFS":
                urls.append((titre, r.get("original_url") or r.get("url")))
    return urls


RESEAUX = {"Rennes": ("réseau urbain star",), "Grenoble": ("réseau urbain tag",),
           "Chambéry": ("synchro bus",), "Montpellier": ("tam",),
           "Toulon": ("mistral",), "Paris": ("île-de-france mobilités",)}


def _reseau_connu(titre, ville):
    return any(k in titre.lower() for k in RESEAUX.get(ville, ()))


def lire_gtfs(url, ville, etiquette):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{ville}_{abs(hash(url)) % 10**8}.zip"
    if not f.exists() or f.stat().st_size < 10000:
        f.write_bytes(curl_bytes(url, timeout=900))
    try:
        z = zipfile.ZipFile(f)
    except Exception:
        return None
    noms = {n.split("/")[-1]: n for n in z.namelist()}
    lire = lambda n: (list(csv.DictReader(io.TextIOWrapper(z.open(noms[n]), encoding="utf-8-sig")))
                      if n in noms else [])
    arrets = []
    for s in lire("stops.txt"):
        if s.get("location_type") not in (None, "", "0"):
            continue
        try:
            arrets.append((float(s["stop_lon"]), float(s["stop_lat"])))
        except (TypeError, ValueError, KeyError):
            pass
    modes = collections.Counter(MODES.get((r.get("route_type") or "").strip(), "autre")
                                for r in lire("routes.txt"))
    return {"arrets": arrets, "modes": dict(modes), "lignes": len(lire("routes.txt")),
            "source": etiquette, "url": url}


def main():
    catalogue = curl_json(CATALOGUE, timeout=120)
    res = {}
    for v, meta in VILLES.items():
        communes = curl_json(f"https://geo.api.gouv.fr/epcis/{meta['epci']}/communes"
                             f"?fields=nom,code,population&format=geojson&geometry=contour",
                             timeout=120).get("features", [])
        if not communes:
            print(f"  {v:12} EPCI {meta['epci']} introuvable")
            continue
        zones = [{"nom": c["properties"]["nom"], "pop": c["properties"].get("population") or 0,
                  "g": c["geometry"], "bb": cadre(c["geometry"]), "n": 0} for c in communes]
        # On garde le GTFS le plus riche en modes : cf. le piège Montpellier.
        meilleur = None
        for etiquette, url in gtfs_du_reseau(catalogue, v):
            d = lire_gtfs(url, v, etiquette)
            if d and (meilleur is None or len(d["modes"]) > len(meilleur["modes"])):
                meilleur = d
        if not meilleur:
            print(f"  {v:12} aucun GTFS exploitable")
            continue
        for p in meilleur["arrets"]:
            for z in zones:
                x0, y0, x1, y1 = z["bb"]
                if x0 <= p[0] <= x1 and y0 <= p[1] <= y1 and dans(p, z["g"]):
                    z["n"] += 1
                    break
        couvertes = [z for z in zones if z["n"] > 0]
        pop_c = sum(z["pop"] for z in couvertes)
        pop_t = sum(z["pop"] for z in zones)
        modes = meilleur["modes"]
        qualite = sum(poids for mode, poids in QUALITE.items() if modes.get(mode))
        res[v] = {
            "reseau": meilleur["source"],
            "communes_epci": len(zones), "communes_couvertes": len(couvertes),
            "couverture_communes_pct": round(100 * len(couvertes) / len(zones), 1),
            "couverture_population_pct": round(100 * pop_c / pop_t, 1) if pop_t else None,
            "arrets": len(meilleur["arrets"]), "lignes": meilleur["lignes"],
            "modes": modes, "indice_qualite_reseau": qualite,
        }
        r = res[v]
        print(f"  {v:12} {r['communes_couvertes']:>3}/{r['communes_epci']:<3} communes "
              f"({r['couverture_communes_pct']:>5.1f}%) · {r['arrets']:>5} arrêts · "
              f"qualité {qualite} · " + ", ".join(f"{k}:{n}" for k, n in sorted(modes.items(), key=lambda x: -x[1])[:4]))
    ecrire("transports", res, "transport.data.gouv.fr — GTFS des réseaux urbains",
           "https://transport.data.gouv.fr/datasets?type=public-transit", unite="% et indice",
           methode="Couverture : part des communes de l'EPCI ayant au moins un arrêt. "
                   "Qualité : somme des poids des modes présents (métro 3, tram et train 2, "
                   "funiculaire, câble et ferry 1). Le GTFS retenu est celui offrant le plus "
                   "de modes distincts, pour éviter un réseau partiel.")


if __name__ == "__main__":
    main()
