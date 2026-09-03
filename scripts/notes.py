#!/usr/bin/env python3
"""Recalcule les notes sur 10 de _data/criteres.yml à partir des _data/*.json.

Barème RELATIF AU PANEL CLASSÉ. Une échelle absolue calibrée en incluant une
ville de référence atypique écrase les autres : avec Paris à 26,6 entreprises
pour 1 000 habitants, les cinq villes candidates tombaient toutes sous 6.
On étale donc de 1 à 10 sur les seules villes classées, puis on place les
villes de référence sur cette même échelle, bornées à [0, 10].

Conséquence voulue : le barème se recalibre tout seul si le panel change.
"""
import io, json, math, pathlib, yaml

RACINE = pathlib.Path(__file__).resolve().parents[1]
DATA = RACINE / "_data"
BAS, HAUT = 1.0, 10.0


def charger(nom):
    f = DATA / f"{nom}.json"
    return json.loads(f.read_text(encoding="utf-8"))["villes"] if f.exists() else {}


def valeurs(source, chemin):
    """Extrait une valeur par ville en suivant un chemin de clés."""
    out = {}
    for v, d in source.items():
        x = d
        for c in chemin:
            x = (x or {}).get(c) if isinstance(x, dict) else None
        if isinstance(x, (int, float)):
            out[v] = float(x)
    return out


def etaler(vals, classees, sens=1, transfo=None):
    """1 à 10 sur les villes classées ; les références suivent la même échelle."""
    if transfo:
        vals = {v: transfo(x) for v, x in vals.items()}
    ref = [x for v, x in vals.items() if v in classees]
    if len(ref) < 2:
        return {}
    lo, hi = min(ref), max(ref)
    if lo == hi:
        return {v: round((BAS + HAUT) / 2, 1) for v in vals}
    out = {}
    for v, x in vals.items():
        t = (x - lo) / (hi - lo)
        if sens < 0:
            t = 1 - t
        out[v] = round(max(0.0, min(10.0, BAS + t * (HAUT - BAS))), 1)
    return out


def main():
    criteres = yaml.safe_load((DATA / "criteres.yml").read_text(encoding="utf-8"))
    villes = yaml.safe_load((DATA / "villes.yml").read_text(encoding="utf-8"))
    classees = {v for v in villes if not villes[v].get("reference")}

    climat = charger("climat")
    emploi, logement = charger("emploi"), charger("logement")
    air, eau = charger("qualite_air"), charger("eau_potable")
    pol, tc, nat = charger("politique"), charger("transports"), charger("loisirs_nature")

    # Chaque entrée : (valeurs, sens, transfo, phrase décrivant la mesure).
    LIB = {
        "devops":     "Établissements actifs en NAF 62.01Z, 62.02A et 63.11Z rapportés à 1 000 habitants",
        "cip":        "Associations actives en NAF 88.99B rapportées à 1 000 habitants",
        "immo":       "Loyer d'annonce moyen dans un rayon de 15 km, en €/m²",
        "climat":     ("Beau temps sans sécheresse : ensoleillement (40 %), rareté des canicules "
                       "au-dessus de 30 °C (30 %) et rareté des jours de pluie (30 %), le tout "
                       "minoré si le cumul de juin à août tombe sous 120 mm"),
        "pollution":  "Moyenne annuelle de PM2.5 sur la station de fond urbaine de référence",
        "eaupot":     "Nitrates dans l'eau distribuée, moyenne sur 12 mois glissants",
        "politique":  "Part des sièges de gauche au conseil municipal, d'après les nuances officielles",
        "falaise":    "Sites d'escalade avec corde à moins de 50 km (racine carrée du décompte)",
        "eau":        "Spots de baignade à moins de 30 km, surveillés ou non (racine carrée du décompte)",
        "transports": "Couverture des communes de l'EPCI, plus huit points par mode lourd du réseau",
    }
    SENS = {"immo": "moins il est élevé, mieux c'est", "pollution": "moins il est élevé, mieux c'est",
            "eaupot": "moins il est élevé, mieux c'est"}

    def note_climat(conf):
        """Beau temps sans sécheresse : ensoleillement valorisé, canicules et
        jours de pluie pénalisés, malus si l'été est trop sec.

        Le cumul annuel ne dit rien de la sécheresse — Montpellier, Toulon et
        Paris reçoivent tous ~635 mm par an, mais 86, 47 et 169 mm entre juin
        et août. C'est la pluie estivale qui départage.
        """
        soleil = valeurs(climat, ["ensoleillement_h_an"])
        canicule = valeurs(climat, ["jours_sup_30c"])
        pluie = valeurs(climat, ["jours_pluie_an"])
        ete = valeurs(climat, ["pluie_ete_mm"])
        if not (soleil and canicule and pluie):
            return {}

        def norme(vals, sens):
            ref = [x for v, x in vals.items() if v in classees]
            lo, hi = min(ref), max(ref)
            if lo == hi:
                return {v: 0.5 for v in vals}
            return {v: max(0.0, min(1.0, ((x - lo) / (hi - lo)) if sens > 0
                                         else (1 - (x - lo) / (hi - lo))))
                    for v, x in vals.items()}

        ns, nc, np_ = norme(soleil, +1), norme(canicule, -1), norme(pluie, -1)
        seuil = conf.get("seuil_pluie_ete_mm", 120)
        plancher = conf.get("malus_secheresse_max", 0.60)
        out = {}
        for v in soleil:
            if v not in nc or v not in np_:
                continue
            base = (conf.get("poids_soleil", 0.40) * ns[v]
                    + conf.get("poids_canicule", 0.30) * nc[v]
                    + conf.get("poids_jours_pluie", 0.30) * np_[v])
            mm = ete.get(v)
            malus = 1.0
            if mm is not None and mm < seuil:
                malus = plancher + (1 - plancher) * (mm / seuil)
            out[v] = round(max(0.0, min(10.0, BAS + base * malus * (HAUT - BAS))), 1)
        return out

    calculs = {
        "devops":    etaler(valeurs(emploi, ["devops_pour_1000_hab"]), classees, +1),
        "cip":       etaler(valeurs(emploi, ["cip_pour_1000_hab"]), classees, +1),
        "immo":      etaler(valeurs(logement, ["loyer_moyen_15km_eur_m2"]), classees, -1),
        "pollution": etaler(valeurs(air, ["PM2.5", "valeur_ug_m3"]), classees, -1),
        "eaupot":    etaler(valeurs(eau, ["nitrates_moy_12_mois"]), classees, -1),
        "politique": etaler(valeurs(pol, ["part_gauche_pct"]), classees, +1),
        "falaise":   etaler(valeurs(nat, ["falaise", "sites_avec_corde"]), classees, +1, math.sqrt),
        "eau":       etaler(valeurs(nat, ["baignade", "spots"]), classees, +1, math.sqrt),
        "transports": etaler({v: d["couverture_communes_pct"] + 8 * d["indice_qualite_reseau"]
                              for v, d in tc.items()
                              if d.get("couverture_communes_pct") is not None}, classees, +1),
        "climat": note_climat(next((c.get("parametres") or {}
                                    for c in criteres if c["id"] == "climat"), {})),
    }

    for c in criteres:
        n = calculs.get(c["id"])
        if not n:
            continue
        c["notes"] = {v: n[v] for v in villes if v in n}
        c["notes_issues_de"] = "calculee"
        if c["id"] == "climat":
            c["methode"] = (f"{LIB['climat']}. Chaque composante est étalée sur les seules "
                            f"villes classées, les villes de référence étant placées sur la "
                            f"même échelle. Les poids sont réglables dans le champ "
                            f"« parametres » de ce fichier.")
        else:
            sens = SENS.get(c["id"], "plus il est élevé, mieux c'est")
            c["methode"] = (f"{LIB[c['id']]} ; {sens}. La note étale cet indicateur de "
                            f"{BAS:.0f} à {HAUT:.0f} sur les seules villes classées, "
                            f"les villes de référence étant placées sur la même échelle. "
                            f"Le barème se recalibre si le panel change.")
        manque = [v for v in villes if v not in n]
        etat = f"  ⚠ sans donnée : {', '.join(manque)}" if manque else ""
        print(f"  {c['id']:11} " + "  ".join(f"{v}:{n[v]}" for v in villes if v in n) + etat)

    entete = (DATA / "criteres.yml").read_text(encoding="utf-8").split("- id:")[0]
    (DATA / "criteres.yml").write_text(
        entete + yaml.dump(criteres, allow_unicode=True, sort_keys=False, width=100),
        encoding="utf-8")
    print("\n→ _data/criteres.yml mis à jour (barème relatif au panel classé)")


if __name__ == "__main__":
    main()
