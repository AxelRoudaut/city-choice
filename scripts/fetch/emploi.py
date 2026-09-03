#!/usr/bin/env python3
"""Critères 1-2 — Emploi DevOps et CIP, via l'API Recherche d'entreprises.

Compte les établissements actifs par code NAF, rapportés à la population.
Sans clé. Fonctionne pour n'importe quelle commune française.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import VILLES, ARRONDISSEMENTS_PARIS, curl_json, ecrire

API = "https://recherche-entreprises.api.gouv.fr/search"
NAF_DEVOPS = ["62.01Z", "62.02A", "63.11Z"]   # programmation, conseil SI, hébergement/données
NAF_CIP = ["88.99B"]                          # action sociale sans hébergement
PLAFOND = 10000                               # l'API tronque total_results à 10 000


def communes(v):
    """Paris n'existe pas sous 75056 dans ce référentiel : il faut ses arrondissements."""
    return ARRONDISSEMENTS_PARIS if VILLES[v]["insee"] == "75056" else [VILLES[v]["insee"]]


def compte(naf, codes, association=None):
    """Somme commune par commune pour ne jamais heurter le plafond de 10 000."""
    total, tronque = 0, False
    for code in codes:
        args = ["-G", "--data-urlencode", f"activite_principale={naf}",
                "--data-urlencode", f"code_commune={code}",
                "--data-urlencode", "etat_administratif=A",
                "--data-urlencode", "per_page=1"]
        if association:
            args += ["--data-urlencode", "est_association=true"]
        n = curl_json(API, *args).get("total_results", 0)
        if n >= PLAFOND:
            tronque = True
        total += n
    return total, tronque


def population(v):
    d = curl_json(f"https://geo.api.gouv.fr/communes/{VILLES[v]['insee']}?fields=population")
    return d.get("population") or 0


def main():
    res = {}
    for v in VILLES:
        codes = communes(v)
        pop = population(v)
        devops = sum(compte(n, codes)[0] for n in NAF_DEVOPS)
        cip, _ = compte(NAF_CIP[0], codes, association=True)
        res[v] = {
            "population": pop,
            "devops_etablissements": devops,
            "devops_pour_1000_hab": round(1000 * devops / pop, 2) if pop else None,
            "cip_associations": cip,
            "cip_pour_1000_hab": round(1000 * cip / pop, 2) if pop else None,
            "naf_devops": NAF_DEVOPS, "naf_cip": NAF_CIP,
        }
        print(f"  {v:12} DevOps {devops:>6} ({res[v]['devops_pour_1000_hab']}/1000 hab) · "
              f"CIP assoc. {cip:>5} ({res[v]['cip_pour_1000_hab']}/1000 hab)")
    ecrire("emploi", res, "API Recherche d'entreprises",
           "https://recherche-entreprises.api.gouv.fr/", unite="établissements actifs",
           methode="Établissements actifs par code NAF, sommés commune par commune "
                   "(plafond API de 10 000 par requête), rapportés à la population Insee.")


if __name__ == "__main__":
    main()
