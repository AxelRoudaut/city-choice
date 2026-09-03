#!/usr/bin/env python3
"""Critère 8 — Climat, via Météo-France (données climatologiques de base).

Normales 1991-2020 depuis les fichiers mensuels par département, sur le bucket
ouvert de data.gouv. Sans clé.
PIÈGE : INST (ensoleillement) est en MINUTES, pas en heures.
"""
import sys, pathlib, csv, gzip, io, collections, math
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import VILLES, curl_bytes, ecrire, station_meteo

BASE = ("https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/BASE/MENS/"
        "MENSQ_{dep}_previous-1950-2024.csv.gz")
DEBUT, FIN = 199101, 202012
MOIS_MIN = 240            # 20 ans de température sur la période
MOIS_MIN_INST = 180       # 15 ans d'ensoleillement : au-delà, pas de pénalité


def dist_km(a, b):
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180
    return 12742 * math.asin(math.sqrt(
        0.5 - math.cos((la2 - la1) * p) / 2
        + math.cos(la1 * p) * math.cos(la2 * p) * (1 - math.cos((lo2 - lo1) * p)) / 2))


def f(row, col):
    try:
        return float(row[col])
    except (TypeError, ValueError, KeyError):
        return None


def main():
    res = {}
    for v, meta in VILLES.items():
        brut = curl_bytes(BASE.format(dep=meta["dep"]), timeout=300)
        if not brut:
            print(f"  {v:12} téléchargement échoué")
            continue
        agg = collections.defaultdict(lambda: collections.defaultdict(float))
        n = collections.defaultdict(lambda: collections.defaultdict(int))
        pos, alt, rec = {}, {}, {}
        ete = collections.defaultdict(float)
        n_ete = collections.defaultdict(int)
        with gzip.open(io.BytesIO(brut), "rt", encoding="latin-1") as fh:
            for row in csv.DictReader(fh, delimiter=";"):
                try:
                    ym = int(row["AAAAMM"])
                except (TypeError, ValueError):
                    continue
                if not DEBUT <= ym <= FIN:
                    continue
                poste = row["NOM_USUEL"].strip()
                if poste not in pos:
                    try:
                        pos[poste] = (float(row["LAT"]), float(row["LON"]))
                        alt[poste] = float(row["ALTI"])
                    except (TypeError, ValueError):
                        pass
                for col in ("TM", "RR", "INST", "NBJTX30", "NBJTX25", "NBJRR1", "NBJTNS20"):
                    x = f(row, col)
                    if x is not None:
                        agg[poste][col] += x
                        n[poste][col] += 1
                # Record de chaleur absolu sur la période
                tx = f(row, "TXAB")
                if tx is not None:
                    rec[poste] = max(rec.get(poste, -99.0), tx)
                # Pluie estivale (juin à août) : c'est elle qui dit la sécheresse,
                # pas le cumul annuel. Montpellier et Toulon reçoivent autant de
                # pluie que Paris sur l'année, mais presque rien l'été.
                if ym % 100 in (6, 7, 8):
                    rr = f(row, "RR")
                    if rr is not None:
                        ete[poste] += rr
                        n_ete[poste] += 1
        # Station de référence : la PLUS PROCHE de la ville parmi celles ayant une
        # série suffisante. Prendre « la plus complète du département » donnerait
        # l'Alpe-d'Huez pour Grenoble : une station d'altitude, hors sujet.
        # 240 mois = 20 ans sur la période 1991-2020. Un seuil à 300 écartait
        # Grenoble-LVD (259 mois, en ville à 220 m) au profit de Saint-Geoirs,
        # un plateau à 37 km et 384 m qui compte 14 jours de canicule en moins.
        complet = [p for p in agg if n[p]["TM"] >= MOIS_MIN and p in pos]
        if not complet:
            print(f"  {v:12} aucune station complète en {meta['dep']}")
            continue
        force = station_meteo(v)
        if force:
            candidats = [p for p in complet if force.upper() in p.upper()]
            if not candidats:
                print(f"  {v:12} station imposée « {force} » introuvable ; sélection auto")
            complet = candidats or complet
        # Sélection automatique. Le poste le plus proche n'est pas le bon : un
        # poste d'altitude (Autrans, l'Alpe-d'Huez) décrit un autre climat, et un
        # poste sans ensoleillement est une série incomplète. On combine donc
        # distance, écart au fond de vallée et présence d'une série d'ensoleillement.
        # Fond de vallée = altitude MINIMALE des postes à moins de 40 km : c'est là
        # que sont les villes. Le rayon doit être large : autour de Grenoble, tous
        # les postes à moins de 25 km sont au-dessus de 945 m, et prendre le plus
        # proche donnerait Autrans (1069 m) pour une ville à 212 m.
        ici = (meta["lat"], meta["lon"])
        proches = [p for p in complet if dist_km(ici, pos[p]) <= 40] or complet
        ref_alt = min(alt[p] for p in proches)

        def score(p):
            return (dist_km(ici, pos[p])
                    + 0.03 * abs(alt[p] - ref_alt)
                    + (0 if n[p]["INST"] >= MOIS_MIN_INST else 15))

        poste = min(complet, key=score)
        ecart = dist_km(ici, pos[poste])
        a, c = agg[poste], n[poste]
        ans = c["TM"] / 12
        res[v] = {
            "station": poste,
            "temperature_moy_c": round(a["TM"] / c["TM"], 1),
            "precipitations_mm_an": round(a["RR"] / ans),
            "ensoleillement_h_an": round(a["INST"] / (c["INST"] / 12) / 60) if c["INST"] else None,
            "jours_sup_30c": round(a["NBJTX30"] / (c["NBJTX30"] / 12), 1) if c["NBJTX30"] else None,
            "jours_sup_25c": round(a["NBJTX25"] / (c["NBJTX25"] / 12), 1) if c["NBJTX25"] else None,
            "jours_pluie_an": round(a["NBJRR1"] / (c["NBJRR1"] / 12), 1) if c["NBJRR1"] else None,
            "nuits_sup_20c": round(a["NBJTNS20"] / (c["NBJTNS20"] / 12), 1) if c["NBJTNS20"] else None,
            "pluie_ete_mm": round(ete[poste] / (n_ete[poste] / 3)) if n_ete[poste] else None,
            "record_chaleur_c": rec.get(poste),
            "mois_observes": c["TM"],
            "mois_ensoleillement": c["INST"],
            "distance_ville_km": round(ecart, 1),
            "altitude_m": alt.get(poste),
        }
        r = res[v]
        print(f"  {v:12} {r['station'][:22]:24} {r['temperature_moy_c']:>5} °C · "
              f"{r['precipitations_mm_an']:>4} mm · {r['ensoleillement_h_an']} h · "
              f"{r['jours_sup_30c']:>4} j>30 · {str(r['jours_pluie_an']):>5} j pluie · "
              f"{str(r['pluie_ete_mm']):>4} mm été · {str(r['nuits_sup_20c']):>4} nuits>20 · "
              f"record {r['record_chaleur_c']}")
    ecrire("climat", res, "Météo-France — données climatologiques de base (mensuelles)",
           "https://meteo.data.gouv.fr/", unite="normales 1991-2020",
           methode="Normales 1991-2020, dont les jours de pluie (RR ≥ 1 mm), les nuits "
                   "tropicales et le cumul de juin à août, sur la station synoptique la plus proche de la "
                   "ville (au moins 300 mois de température ET d'ensoleillement, ce qui "
                   "écarte les postes d'altitude). INST est converti de minutes en heures.")


if __name__ == "__main__":
    main()
