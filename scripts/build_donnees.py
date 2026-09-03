#!/usr/bin/env python3
"""Régénère le bloc de données JS du rapport depuis _data/criteres.yml.

Le corps du rapport ne contient volontairement aucun Liquid, pour que le JS
traverse Jekyll intact et que le fragment Artifact reste identique au site.
La pondération est donc injectée par génération, pas par rendu.
"""
import io, json, pathlib, sys, yaml

RACINE = pathlib.Path(__file__).resolve().parents[1]
CIBLE = RACINE / "_includes" / "report-body.html"
DEBUT = "  // <<< DONNÉES GÉNÉRÉES — source : _data/criteres.yml, via `just donnees`"
FIN = "  // >>> FIN DONNÉES GÉNÉRÉES"


# Critère → fichier _data/*.json qui porte sa date de collecte.
FICHIERS = {"devops": "emploi", "cip": "emploi", "immo": "logement", "climat": "climat",
            "pollution": "qualite_air", "falaise": "loisirs_nature", "eau": "loisirs_nature",
            "eaupot": "eau_potable", "politique": "politique", "transports": "transports"}
MOIS = ("janvier février mars avril mai juin juillet août septembre "
        "octobre novembre décembre").split()


def js(x):
    return json.dumps(x, ensure_ascii=False)


def echappe(t):
    return (t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def date_fr(iso):
    try:
        a, m, j = iso.split("-")
        return f"{int(j)} {MOIS[int(m) - 1]} {a}"
    except Exception:
        return iso


def collecte(cid):
    """Date de collecte lue dans le JSON du collecteur, si le critère en a un."""
    nom = FICHIERS.get(cid)
    if not nom:
        return None
    f = RACINE / "_data" / f"{nom}.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8")).get("collecte")
    except Exception:
        return None


def bloc_source(c):
    """Le bloc « Source » affiché en fin de critère, généré depuis _data."""
    calculee = c.get("notes_issues_de") == "calculee"
    date = collecte(c["id"])
    quand = f' · relevé le {date_fr(date)}' if date else ""
    genre = ("Note calculée depuis ces données"
             if calculee else "Note : lecture argumentée, non calculée")
    return (f'  <p class="crit-src">'
            f'<span class="src-lab">Source</span> '
            f'<strong>{echappe(c["source"])}</strong>{quand}'
            f'<span class="src-meth">{echappe(c.get("methode") or "")}</span>'
            f'<span class="src-genre">{genre}</span></p>')


def injecte_sources(src, criteres):
    """Remplit chaque marqueur <!-- SRC:id --> … <!-- /SRC -->."""
    par_id = {c["id"]: c for c in criteres}
    poses = 0
    for cid, c in par_id.items():
        marque = f"<!-- SRC:{cid} -->"
        if marque not in src:
            continue
        debut = src.index(marque)
        apres = debut + len(marque)
        fin_marque = "<!-- /SRC -->"
        if src[apres:apres + 400].find(fin_marque) != -1:
            fin = src.index(fin_marque, apres) + len(fin_marque)
        else:
            fin = apres
        src = src[:apres] + "\n" + bloc_source(c) + "\n  " + fin_marque + src[fin:]
        poses += 1
    return src, poses


def main():
    criteres = yaml.safe_load((RACINE / "_data" / "criteres.yml").read_text(encoding="utf-8"))
    villes = yaml.safe_load((RACINE / "_data" / "villes.yml").read_text(encoding="utf-8"))

    vus = set()
    for c in criteres:
        if c["id"] in vus:
            sys.exit(f"Critère en double dans _data/criteres.yml : {c['id']}")
        vus.add(c["id"])

    lignes = [DEBUT, "  var CRITERES = ["]
    for i, c in enumerate(criteres):
        virgule = "," if i < len(criteres) - 1 else ""
        lignes.append(f'    {{id:{js(c["id"])}, nom:{js(c["nom"])}, def:{c["poids_defaut"]}}}{virgule}')
    lignes.append("  ];")
    lignes.append("")
    lignes.append("  // Note sur 10, toujours dans le même sens : 10 est favorable. Pour")
    lignes.append("  // « Embouteillages », une note haute signifie donc peu de congestion.")
    lignes.append("  // Une ville sans note pour un critère en est écartée, jamais comptée zéro.")
    lignes.append("  var VILLES = [")
    noms = list(villes)
    for i, v in enumerate(noms):
        virgule = "," if i < len(noms) - 1 else ""
        notes = {c["id"]: c["notes"][v] for c in criteres if v in (c.get("notes") or {})}
        ref = ", reference:true" if villes[v].get("reference") else ""
        lignes.append(f'    {{nom:{js(v)}, dep:{js(villes[v].get("departement", ""))}'
                      f'{ref}, s:{js(notes)}}}{virgule}')
    lignes.append("  ];")
    lignes.append(FIN)
    bloc = "\n".join(lignes)

    src = io.open(CIBLE, encoding="utf-8").read()
    if DEBUT in src and FIN in src:
        avant = src[:src.index(DEBUT)]
        apres = src[src.index(FIN) + len(FIN):]
        src = avant + bloc + apres
    else:
        ancien = src[src.index("  var CRITERES = ["):src.index("  ];", src.index("var VILLES")) + 4]
        src = src.replace(ancien, bloc, 1)
    src, poses = injecte_sources(src, criteres)
    io.open(CIBLE, "w", encoding="utf-8").write(src)

    hors = [v for v in villes if villes[v].get("reference")]
    print(f"→ {CIBLE.relative_to(RACINE)}")
    print(f"  {len(criteres)} critères · {len(villes)} villes "
          f"(dont {len(hors)} en référence : {', '.join(hors)})")
    print(f"  {poses} blocs « Source » injectés en fin de critère")
    for c in criteres:
        manque = [v for v in villes if v not in (c.get("notes") or {})]
        if manque:
            print(f"  ⚠ {c['id']:11} sans note : {', '.join(manque)}")


if __name__ == "__main__":
    main()
