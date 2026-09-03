#!/usr/bin/env python3
"""Employeurs potentiels pour une candidature spontanée DevOps autour de Grenoble.

Aucune entreprise n'est inventée : la liste sort de l'API Recherche d'entreprises
(annuaire des entreprises, data.gouv.fr), filtrée par code NAF, EPCI et tranche
d'effectif. Chaque ligne est vérifiable par son SIREN. Voir CLAUDE.md, « Règle d'or ».

    python3 scripts/candidatures_devops.py [bassin]   → candidatures/devops-<bassin>.json
"""
import sys, pathlib, json, datetime
sys.path.insert(0, str(pathlib.Path(__file__).parent / "fetch"))
from _common import curl_json, RACINE

API = "https://recherche-entreprises.api.gouv.fr/search"

# Le périmètre est l'agglomération plus la couronne d'EPCI contiguës où se
# trouvent réellement des employeurs : un bassin d'emploi déborde la ville-centre.
BASSINS = {
    "grenoble": {
        "label": "bassin grenoblois",
        "epci": {
            "200040715": "Grenoble-Alpes Métropole",
            "200018166": "CC Le Grésivaudan",   # Montbonnot / Crolles, Inovallée
            "243800984": "CA du Pays Voironnais",
        },
    },
    "montpellier": {
        "label": "bassin montpelliérain",
        "epci": {
            "243400017": "Montpellier Méditerranée Métropole",
            "243400470": "CA du Pays de l'Or",          # Mauguio, Pérols
            "200022986": "CC du Grand Pic Saint-Loup",
            "200066355": "CA Sète Agglopôle Méditerranée",
            "243400694": "CC Vallée de l'Hérault",      # Gignac
            "243400520": "CA Lunel Agglo",
        },
    },
}

# Familles NAF où un poste DevOps / SRE / infra existe réellement.
NAF = {
    "62.01Z": ("Numérique", "Programmation informatique"),
    "62.02A": ("Numérique", "Conseil en systèmes et logiciels"),
    "62.02B": ("Numérique", "Tierce maintenance de systèmes"),
    "62.03Z": ("Numérique", "Gestion d'installations informatiques (infogérance)"),
    "62.09Z": ("Numérique", "Autres activités informatiques"),
    "63.11Z": ("Numérique", "Traitement de données, hébergement"),
    "63.12Z": ("Numérique", "Portails internet"),
    "58.21Z": ("Jeu vidéo", "Édition de jeux électroniques"),
    # Ubisoft Montpellier et DigixArt sont déclarés en 59.12Z, pas en 58.21Z :
    # le code NAF est déclaratif, il faut aller chercher là où les studios sont.
    "59.12Z": ("Jeu vidéo", "Post-production audiovisuelle"),
    "58.29A": ("Éditeur", "Édition de logiciels système et de réseau"),
    "58.29C": ("Éditeur", "Édition de logiciels applicatifs"),
    "26.11Z": ("Industrie / semi-conducteurs", "Fabrication de composants électroniques"),
    "26.51B": ("Industrie / semi-conducteurs", "Instrumentation scientifique et technique"),
    "27.12Z": ("Industrie / énergie", "Matériel de distribution et de commande électrique"),
    "71.12B": ("Ingénierie", "Ingénierie, études techniques"),
    "72.19Z": ("Recherche", "R&D en autres sciences physiques et naturelles"),
    "61.10Z": ("Télécoms", "Télécommunications filaires"),
}

# Tranches Insee retenues : 20 salariés et plus (en deçà, pas d'équipe infra).
TRANCHES = "12,21,22,31,32,41,42,51,52,53"
LIBELLE_TRANCHE = {
    "NN": "effectif non renseigné", "00": "0 salarié", "01": "1-2", "02": "3-5",
    "03": "6-9", "11": "10-19", "12": "20-49", "21": "50-99", "22": "100-199",
    "31": "200-249", "32": "250-499", "41": "500-999", "42": "1000-1999",
    "51": "2000-4999", "52": "5000-9999", "53": "10000 et plus",
}
RANG = {t: i for i, t in enumerate(
    ["NN", "00", "01", "02", "03", "11", "12", "21", "22", "31", "32", "41", "42", "51", "52", "53"])}


def cherche(naf, epci):
    """Toutes les pages d'un couple (NAF, EPCI). L'API plafonne à 10 000 résultats,
    hors d'atteinte ici grâce au filtre d'effectif."""
    out, page = [], 1
    while True:
        d = curl_json(API, "-G",
                      "--data-urlencode", f"activite_principale={naf}",
                      "--data-urlencode", f"epci={epci}",
                      "--data-urlencode", "etat_administratif=A",
                      "--data-urlencode", f"tranche_effectif_salarie={TRANCHES}",
                      "--data-urlencode", "per_page=25",
                      "--data-urlencode", f"page={page}")
        res = d.get("results") or []
        out += res
        if page >= (d.get("total_pages") or 0) or not res:
            return out
        page += 1


def etablissement_local(e, epci):
    """L'établissement de l'entreprise réellement implanté dans l'EPCI visé :
    c'est là qu'on postule, pas au siège social qui est souvent à Paris."""
    cands = [x for x in (e.get("matching_etablissements") or []) if x.get("epci") == epci]
    if not cands and (e.get("siege") or {}).get("epci") == epci:
        cands = [e["siege"]]
    return cands[0] if cands else (e.get("matching_etablissements") or [None])[0]


def main():
    slug = (sys.argv[1] if len(sys.argv) > 1 else "grenoble").lower()
    if slug not in BASSINS:
        raise SystemExit(f"bassin inconnu : {slug} — choisir parmi {', '.join(BASSINS)}")
    EPCI = BASSINS[slug]["epci"]

    vus, lignes = {}, []
    for naf, (famille, libelle) in NAF.items():
        for code_epci, nom_epci in EPCI.items():
            res = cherche(naf, code_epci)
            print(f"  {naf} {nom_epci:<26} {len(res):>3} entreprises", flush=True)
            for e in res:
                siren = e.get("siren")
                etab = etablissement_local(e, code_epci) or {}
                # Une entreprise peut ressortir sur plusieurs NAF/EPCI : on garde
                # la première occurrence et on note les EPCI supplémentaires.
                if siren in vus:
                    if nom_epci not in vus[siren]["epci"]:
                        vus[siren]["epci"].append(nom_epci)
                    continue
                ligne = {
                    "siren": siren,
                    "nom": e.get("nom_complet"),
                    "famille": famille,
                    "naf": naf,
                    "naf_libelle": libelle,
                    "effectif_code": e.get("tranche_effectif_salarie") or "NN",
                    "effectif": LIBELLE_TRANCHE.get(e.get("tranche_effectif_salarie") or "NN", "?"),
                    "annee_effectif": e.get("annee_tranche_effectif_salarie"),
                    "categorie": e.get("categorie_entreprise"),
                    "date_creation": e.get("date_creation"),
                    "commune": etab.get("libelle_commune"),
                    "adresse": etab.get("adresse"),
                    "epci": [nom_epci],
                    "annuaire": f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}",
                }
                vus[siren] = ligne
                lignes.append(ligne)

    lignes.sort(key=lambda l: (-RANG.get(l["effectif_code"], 0), l["nom"] or ""))
    sortie = {
        "bassin": BASSINS[slug]["label"], "slug": slug,
        "source": "API Recherche d'entreprises (annuaire des entreprises, data.gouv.fr)",
        "url": "https://recherche-entreprises.api.gouv.fr/",
        "collecte": datetime.date.today().isoformat(),
        "methode": f"Établissements actifs des EPCI {', '.join(EPCI.values())}, "
                   f"codes NAF {', '.join(NAF)}, tranches d'effectif 20 salariés et plus. "
                   "Effectif = tranche Insee de l'entreprise (tous sites), pas du site local.",
        "epci": EPCI, "naf": {k: v[1] for k, v in NAF.items()},
        "entreprises": lignes,
    }
    dest = RACINE / "candidatures" / f"devops-{slug}.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(sortie, ensure_ascii=False, indent=2) + "\n")
    print(f"\n  {len(lignes)} entreprises → {dest.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
