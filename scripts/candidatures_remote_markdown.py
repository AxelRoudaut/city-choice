#!/usr/bin/env python3
"""Met en forme candidatures/devops-remote.json en liste de candidature.

Contrairement à la liste grenobloise, adossée à un registre stable, les offres
d'emploi tournent d'une semaine à l'autre. Les annotations éditoriales sont donc
*facultatives* : elles s'appliquent si l'entreprise est encore dans le flux, et
sont ignorées sinon. Aucun nom n'est ajouté par elles.
"""
import json, pathlib, datetime, re, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from candidatures_remote import FRANCE, PAYS_EUROPE   # une seule définition des zones

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "fetch"))
from _common import CANDIDATURES

SRC = CANDIDATURES / "devops-remote.json"
DEST = CANDIDATURES / "devops-remote.md"

# Annotations appliquées si l'entreprise figure dans la collecte du jour.
NOTES = {
    "canonical": "éditeur d'Ubuntu — entreprise entièrement distribuée depuis sa création",
    "gitlab": "sans bureaux ; son manuel interne de fonctionnement à distance est public",
    "remote": "son métier est d'employer à distance pour le compte d'autres entreprises",
    "localstack": "émulateur AWS local — outil de la boîte à outils DevOps",
    "temporal technologies": "moteur d'orchestration open source",
    "circleci": "plateforme de CI/CD",
    "ashby": "logiciel de recrutement, équipe distribuée",
    "frontify": "SaaS suisse",
    "kraken": "place de marché crypto, équipe très distribuée",
    "tether operations limited": "équipe distribuée, offre explicitement « 100 % remote »",
    "opennebula systems": "éditeur open source d'un cloud privé",
    "proxify": "place de marché de freelances — mission, pas emploi",
    "lemon.io": "place de marché de freelances — mission, pas emploi",
    "a.team": "place de marché de freelances — mission, pas emploi",
    "gt": "place de marché de freelances — mission, pas emploi",
    "sosafe": "cybersécurité, Cologne",
    "nebius": "infrastructure GPU / cloud",
    "software mind": "société de services polonaise",
}
MARCHE = re.compile(r"place de marché de freelances")

INFRA = re.compile(r"devops|sre|site reliability|platform|infrastructure|cloud|"
                   r"kubernetes|sysadmin|système|systems eng|production eng|"
                   r"reliability|observability", re.I)


def offre_vitrine(e):
    """L'offre la plus parlante : celle qui porte un intitulé d'infra et la zone
    retenue pour l'entreprise, à défaut la plus récente."""
    cand = [o for o in e["offres"] if o["zone"] == e["zone"]] or e["offres"]
    return sorted(cand, key=lambda o: (not INFRA.search(o["poste"]), o["date"]),
                  reverse=False)[0]


def zone_courte(txt, n=4):
    """« Antigua and Barbuda, Argentina, … » sur 35 pays ne dit rien. On tronque,
    en remontant d'abord les pays qui concernent un candidat français."""
    parts = [p.strip() for p in (txt or "").split(",") if p.strip()]
    if not parts:
        return "non précisée"
    if len(parts) <= n:
        return ", ".join(parts)
    tri = sorted(parts, key=lambda p: (not FRANCE.search(p), not PAYS_EUROPE.search(p)))
    return ", ".join(tri[:n]) + f" … (+{len(parts) - n})"


def tableau(A, ents):
    A("| Entreprise | Offre repérée | Ouvert à | Offres | Vue sur | |")
    A("|---|---|---|---|---|---|")
    for e in ents:
        o = offre_vitrine(e)
        note = NOTES.get(e["entreprise"].lower(), "")
        A(f"| **[{e['entreprise']}]({o['url']})** | {o['poste']} | {zone_courte(o['zone_declaree'])} "
          f"| {e['nb_offres']} | {', '.join(e['sources'])} | {f'*{note}*' if note else ''} |")
    A("")


def main():
    d = json.loads(SRC.read_text())
    ents = d["entreprises"]
    france = [e for e in ents if e["zone"] == "france"]
    europe = [e for e in ents if e["zone"] == "europe"]
    monde = [e for e in ents if e["zone"] == "monde"]
    ailleurs = [e for e in ents if e["zone"] == "ailleurs"]
    marches = [e for e in france + europe + monde
               if MARCHE.search(NOTES.get(e["entreprise"].lower(), ""))]
    france = [e for e in france if e not in marches]
    europe = [e for e in europe if e not in marches]
    monde = [e for e in monde if e not in marches]

    out = []
    A = out.append
    A("# Candidature DevOps en télétravail intégral\n")
    A(f"*Collecte du {datetime.date.today().strftime('%d/%m/%Y')} sur sept places de marché "
      "du travail à distance. Régénérable : `just remote`.*\n")

    A("## Ce que cette liste prouve, et ce qu'elle ne prouve pas\n")
    A("Il n'existe **aucun registre public du « 100 % remote »**. Ce n'est pas un statut "
      "juridique comme le code NAF ou le SIREN : c'est une politique d'entreprise, révisable "
      "du jour au lendemain, et plusieurs de celles qui s'en réclamaient il y a trois ans ont "
      "rappelé leurs équipes depuis. Il n'y a donc rien à interroger qui fasse foi.\n")
    A("Ce qui est vérifiable, en revanche, c'est **qu'une entreprise a publié une offre en "
      "télétravail, sur un poste d'infrastructure, ouverte à telle zone, à telle date**. "
      "C'est la seule chose que ce fichier avance. Chaque nom ci-dessous est lié à l'offre qui "
      "l'a fait entrer dans la liste — si le lien est mort, l'entrée a fait son temps.\n")
    A(f"Sur **{d['nb_offres']} offres d'infrastructure** récoltées et regroupées en "
      f"**{len(ents)} entreprises**, la répartition est instructive :\n")
    A(f"- **{len(france)}** ouvertes à la France, à l'Europe entière ou à l'EMEA "
      f"(plus {len(marches)} places de marché de freelances) ;\n"
      f"- **{len(europe)}** ouvertes à un ou plusieurs pays européens **qui ne sont pas la "
      "France** — Pologne surtout, puis Royaume-Uni, Allemagne, Portugal ;\n"
      f"- **{len(monde)}** sans restriction géographique déclarée ;\n"
      f"- **{len(ailleurs)}** hors zone — Amérique du Nord, Inde, Amérique latine. "
      "C'est la majorité, et c'est le fait marquant : le remote annoncé est presque toujours "
      "un remote national ou régional.\n")
    citent = sorted({e["entreprise"] for e in ents for o in e["offres"]
                     if "france" in (o["zone_declaree"] or "").lower()})
    A(f"Le chiffre qui résume tout : sur ces {d['nb_offres']} offres, "
      + (f"**{len(citent)} entreprises seulement nomment la France** dans les pays où elles "
         f"acceptent d'employer — {', '.join(citent)}."
         if citent else "**aucune ne nomme la France** dans les pays où elle accepte d'employer.")
      + "\n")
    A("> **Le piège du mot « Europe ».** Une offre « remote, Europe » signifie le plus souvent "
      "« depuis un pays où nous avons une entité juridique ou un contrat de portage ». La France "
      "figure rarement dans cette liste — le coût de l'emploi y est élevé et le droit du travail "
      "peu compatible avec un contrat type. **À vérifier offre par offre, avant d'écrire** : la "
      "question à poser est « pouvez-vous employer un résident fiscal français, et sous quel "
      "contrat ? ». Les réponses possibles sont : entité française, portage salarial (EOR type "
      "Deel, Remote.com), ou statut d'indépendant facturant depuis la France.\n")

    A("## Ouvert à la France, à l'Europe ou à l'EMEA\n")
    A("Les entreprises dont au moins une offre nomme la France, l'Europe, l'EMEA ou un fuseau "
      "horaire européen. C'est ici qu'une candidature a le plus de chances d'aboutir — et c'est "
      "la seule section où le mot « Europe » a été pris au mot.\n")
    tableau(A, sorted(france, key=lambda e: -e["nb_offres"]))

    A("## Ouvert à un pays européen, mais pas à la France\n")
    A("Ces offres-là sont fermées : « remote Poland » veut dire contrat polonais. Elles restent "
      "un signal utile — ces entreprises **savent** employer à distance en Europe, elles ont "
      "déjà l'outillage juridique et les habitudes de travail. C'est précisément le genre "
      "d'entreprise où une candidature spontanée peut ouvrir un poste qui n'est pas affiché.\n")
    tableau(A, sorted(europe, key=lambda e: -e["nb_offres"]))

    A("## Sans restriction déclarée\n")
    A("« Anywhere in the World », « Worldwide ». Souvent sincère, parfois un raccourci pour "
      "« n'importe où, tant que vous êtes indépendant ». À creuser au cas par cas.\n")
    tableau(A, sorted(monde, key=lambda e: -e["nb_offres"]))

    if marches:
        A("## Places de marché de freelances\n")
        A("Elles publient beaucoup et recrutent en continu, mais la relation n'est pas un emploi : "
          "on y est mis en relation avec un client final, en facturant. À traiter comme un canal "
          "distinct de la candidature spontanée.\n")
        tableau(A, sorted(marches, key=lambda e: -e["nb_offres"]))

    A("## Où continuer à chercher\n")
    A("Les sept sources interrogées, toutes en accès libre — les réinterroger a plus de valeur "
      "que de conserver cette liste, qui vieillit en quelques semaines :\n")
    for s in d["sources"]:
        A(f"- {s}")
    A("")
    A("**Le marché français est absent de ces places de marché**, et c'est une limite réelle de "
      "cette liste : les entreprises françaises publient sur Welcome to the Jungle, l'APEC, "
      "Indeed ou HelloWork, dont aucune n'expose d'API ouverte. Pour un poste en télétravail "
      "intégral chez un employeur français — contrat de droit français, pas de question de "
      "portage — c'est là qu'il faut chercher, à la main, avec le filtre « télétravail total ». "
      "Les deux démarches sont complémentaires : celle-ci ouvre le marché international, l'autre "
      "évite tout le sujet du contrat.\n")

    if ailleurs:
        A("## Annexe — hors zone aujourd'hui\n")
        A(f"Ces {len(ailleurs)} entreprises recrutent des profils d'infrastructure en télétravail, "
          "mais l'offre repérée est réservée à une autre zone. Elles restent des employeurs "
          "distribués : une candidature spontanée peut y trouver une ouverture que l'offre "
          "publiée ne montre pas.\n")
        A(", ".join(f"[{e['entreprise']}]({offre_vitrine(e)['url']})"
                    for e in sorted(ailleurs, key=lambda e: e["entreprise"].lower())) + "\n")

    A("---\n")
    A(f"Collecte du {d['collecte']} · {d['nb_offres']} offres.  \n"
      f"Méthode : {d['methode']}  \n"
      f"Avertissement : {d['avertissement']}\n")

    DEST.write_text("\n".join(out))
    print(f"  {len(france)} France/Europe + {len(europe)} pays européen + {len(monde)} monde "
          f"+ {len(marches)} places de marché, "
          f"{len(ailleurs)} en annexe → {DEST}")


if __name__ == "__main__":
    main()
