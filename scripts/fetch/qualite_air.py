#!/usr/bin/env python3
"""Critère 9 — Qualité de l'air, via Geod'air / LCSQA. CLÉ REQUISE.

ATTENTION : la documentation du site geodair.fr donne de fausses routes.
Le spec réel est https://www.geodair.fr/api-ext/swagger.yaml et l'export se
fait en deux temps : statistique/export renvoie un identifiant, download le
récupère.

Le producteur demande UNE SEULE requête par date, polluant et statistique :
les exports sont donc mis en cache sur disque.
"""
import sys, pathlib, csv, io, time, os, math
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import VILLES, curl, ecrire, cle_api, RACINE

BASE = "https://www.geodair.fr/api-ext"
POLLUANTS = {"39": "PM2.5", "03": "NO2"}
MOY_ANNUELLE = "a7"          # cf. api-ext/type-donnees/export?codes_polluants=39
ANNEE = 2025
RAYON_STATION_KM = 20        # au-delà, la station décrit une autre agglomération
CACHE = RACINE / ".cache" / "geodair"


def dist_km(a, b):
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180
    return 12742 * math.asin(math.sqrt(
        0.5 - math.cos((la2 - la1) * p) / 2
        + math.cos(la1 * p) * math.cos(la2 * p) * (1 - math.cos((lo2 - lo1) * p)) / 2))


def export(dep, polluant, cle):
    """Deux temps : demander l'export, puis le télécharger. Résultat mis en cache."""
    CACHE.mkdir(parents=True, exist_ok=True)
    fichier = CACHE / f"{dep}_{polluant}_{ANNEE}.csv"
    if fichier.exists() and fichier.stat().st_size > 200:
        return fichier.read_text(encoding="utf-8")
    entete = ["-H", f"apikey: {cle}"]
    for essai in range(4):
        ident = curl(f"{BASE}/statistique/export", *entete, "-G",
                     "--data-urlencode", f"departement={dep}",
                     "--data-urlencode", f"polluant={polluant}",
                     "--data-urlencode", f"type_donnee={MOY_ANNUELLE}",
                     "--data-urlencode", f"date_debut=01/01/{ANNEE} 00:00",
                     "--data-urlencode", f"date_fin=31/12/{ANNEE} 23:00",
                     retries=1).strip()
        if ident and not ident.startswith("{"):
            time.sleep(4)
            txt = curl(f"{BASE}/download?id={ident}", *entete, retries=1)
            if txt and not txt.lstrip().startswith("{"):
                fichier.write_text(txt, encoding="utf-8")
                return txt
        print(f"    quota Geod'air atteint, pause 45 s ({essai + 1}/4)", flush=True)
        time.sleep(45)
    return ""


def stations(txt, meta):
    """Stations de fond urbaines du CSV, avec leur distance à la ville."""
    out = {}
    for r in csv.DictReader(io.StringIO(txt.lstrip("\ufeff")), delimiter=";"):
        if r.get("type d'influence") != "Fond":
            continue
        if r.get("type d'implantation") != "Urbaine":
            continue
        try:
            d = dist_km((meta["lat"], meta["lon"]),
                        (float(r["Latitude"]), float(r["Longitude"])))
            v = float(r["valeur brute"])
        except (TypeError, ValueError, KeyError):
            continue
        if d <= RAYON_STATION_KM:
            out[r["nom site"]] = (d, v)
    return out


def main():
    cle = cle_api("GEODAIR_API_KEY")
    res = {}
    for v, meta in VILLES.items():
        par_polluant = {}
        for polluant, nom in POLLUANTS.items():
            txt = export(meta["dep"], polluant, cle)
            if txt:
                par_polluant[nom] = stations(txt, meta)
        if not par_polluant:
            print(f"  {v:12} export indisponible")
            continue
        # Une SEULE station de référence par ville, la plus proche présente pour
        # tous les polluants : comparer un PM2.5 et un NO2 mesurés à deux endroits
        # différents ne décrit pas le même air.
        communes_ = set.intersection(*(set(d) for d in par_polluant.values())) if par_polluant else set()
        if communes_:
            station = min(communes_, key=lambda s: par_polluant[list(par_polluant)[0]][s][0])
        else:
            toutes = {s: d for m in par_polluant.values() for s, (d, _) in m.items()}
            if not toutes:
                print(f"  {v:12} aucune station de fond à moins de {RAYON_STATION_KM} km")
                continue
            station = min(toutes, key=toutes.get)
        entree = {"station": station, "annee": ANNEE}
        for nom, m in par_polluant.items():
            if station in m:
                d, val = m[station]
                entree[nom] = round(val, 1)
                entree["distance_km"] = round(d, 1)
        entree["complet"] = all(n in entree for n in POLLUANTS.values())
        pm, no2 = entree.get("PM2.5"), entree.get("NO2")
        if pm is not None and no2 is not None:
            # Repère de comparaison, pas un indice réglementaire : lignes
            # directrices OMS 2021, 5 µg/m³ pour les PM2.5 et 10 pour le NO2.
            entree["indice_exposition"] = round(pm / 5 + no2 / 10, 2)
        res[v] = entree
        print(f"  {v:12} {station[:26]:28} PM2.5 {str(pm):>5} · NO2 {str(no2):>5} · "
              f"indice {entree.get('indice_exposition')} ({entree.get('distance_km')} km)")
        time.sleep(2)
    ecrire("qualite_air", res, "Geod'air / LCSQA — moyennes annuelles réglementaires",
           "https://www.geodair.fr/donnees/api", unite="µg/m³",
           methode=f"Moyenne annuelle {ANNEE} (type de donnée a7) sur une station unique par "
                   f"ville : la station de fond en implantation urbaine la plus proche, dans "
                   f"un rayon de {RAYON_STATION_KM} km, mesurant tous les polluants retenus. "
                   "Indice d'exposition = PM2.5/5 + NO2/10 (lignes directrices OMS 2021).")


if __name__ == "__main__":
    main()
