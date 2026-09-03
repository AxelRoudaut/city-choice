#!/usr/bin/env python3
"""Employeurs qui recrutent des profils DevOps en télétravail intégral.

Il n'existe aucun registre public du « 100 % remote » : ce n'est pas un statut
juridique, c'est une politique d'entreprise, révisable du jour au lendemain.
La seule preuve disponible est donc une offre publiée : telle entreprise
cherchait tel profil, en remote, ouvert à telle zone, à telle date.

Ce collecteur agrège sept places de marché du travail à distance, toutes sans
clé d'API, et n'en retient que les offres d'infrastructure ouvertes à l'Europe.
Aucun nom d'entreprise n'est saisi à la main.

    python3 scripts/candidatures_remote.py   → candidatures/devops-remote.json
"""
import sys, pathlib, json, re, time, datetime, xml.etree.ElementTree as ET
sys.path.insert(0, str(pathlib.Path(__file__).parent / "fetch"))
from _common import curl, curl_json, CANDIDATURES

UA = "Mozilla/5.0 (X11; Linux x86_64)"
# Himalayas n'expose aucun filtre par métier : il faut balayer le flux récent.
# Le paramètre `limit` n'est qu'un plafond — le service en renvoie parfois 20,
# parfois 100 — donc on compte les offres lues, pas les pages.
# Au-delà d'une requête par seconde, le service répond 429 : on cadence.
OFFRES_HIMALAYAS = 3000
REQUETES_HIMALAYAS = 150
PAUSE_HIMALAYAS = 1.2
PAGES_ARBEITNOW = 12      # 175 offres par page
TAGS_JOBICY = ("devops", "sre", "kubernetes", "cloud", "infrastructure", "linux",
               "docker", "terraform", "aws", "azure", "devsecops", "sysadmin")

# Intitulés qui désignent un poste d'infrastructure. Volontairement large en
# entrée : le tri fin se fait à la lecture.
POSTE = re.compile(r"""\b(
    devops | dev\s?ops | sre | site\s+reliability | platform\s+engineer
  | plateforme | infrastructure\s+(engineer|architect) | cloud\s+(engineer|architect|ops)
  | kubernetes | sysadmin | system[s]?\s+(engineer|administrator)
  | ingénieur\s+(système|systèmes|infrastructure|cloud|production)
  | administrateur\s+(système|systèmes) | production\s+engineer | ops\s+engineer
  | observability | ci/cd | reliability\s+engineer
)\b""", re.I | re.X)

# Un intitulé technique dans une rubrique « DevOps » suffit : les places de
# marché rangent sous cette rubrique des postes qui n'en portent pas le nom.
TECHNIQUE = re.compile(r"\b(engineer|engineering|developer|architect|administrator|"
                       r"ingénieur|ingénieure|développeur|technic|technique|ops)\b", re.I)


# Une rubrique DevOps contient aussi ceux qui la vendent : on les écarte.
NON_TECHNIQUE = re.compile(r"\b(sales|account\s+(executive|manager)|customer\s+success|"
                           r"marketing|recruit|instructor|writer|copywriter|teacher|"
                           r"gtm|business\s+development|pre-?sales|commercial|"
                           r"assistant|receptionist)\b", re.I)


def retenu(titre, rubrique_devops=False):
    """Garde-fou contre le bruit : une rubrique « DevOps » contient aussi des
    postes de vente et de rédaction. L'intitulé doit dire « infrastructure »,
    ou au moins « ingénieur » quand la rubrique, elle, dit DevOps."""
    titre = titre or ""
    if NON_TECHNIQUE.search(titre):
        return False
    return bool(POSTE.search(titre) or (rubrique_devops and TECHNIQUE.search(titre)))


# Une offre « remote Poland » est un remote européen, mais elle est fermée à un
# résident français : les deux cas ne se rangent pas ensemble.
FRANCE = re.compile(r"\b(france|français|europe|emea|eea|union européenne|"
                    r"cet|cest|utc[+\-]?[0-3])\b", re.I)
PAYS_EUROPE = re.compile(r"\b(united kingdom|uk|ireland|germany|deutschland|spain|"
                         r"portugal|italy|netherlands|belgium|poland|czechia|"
                         r"czech republic|slovakia|hungary|romania|bulgaria|croatia|"
                         r"slovenia|greece|cyprus|malta|austria|switzerland|sweden|"
                         r"norway|denmark|finland|estonia|latvia|lithuania|ukraine|"
                         r"serbia|albania|moldova|luxembourg|iceland|"
                         r"allemagne|royaume-uni)\b", re.I)
MONDE = re.compile(r"\b(worldwide|anywhere|global|international|n'importe)\b", re.I)


def get(url, *args):
    return curl(url, "-A", UA, *args)


def gjson(url, *args):
    try:
        return json.loads(get(url, *args) or "null")
    except Exception:
        return None


def zone(texte):
    """Classe la zone déclarée, du plus au moins actionnable depuis la France :

    'france'  — France, Europe, EMEA ou fuseau européen : candidature possible ;
    'europe'  — un ou plusieurs pays européens, mais pas la France ;
    'monde'   — aucune restriction annoncée ;
    'ailleurs'— une zone qui exclut l'Europe.
    """
    t = (texte or "").strip()
    if not t:
        return "monde"
    if FRANCE.search(t):
        return "france"
    if PAYS_EUROPE.search(t):
        return "europe"
    if MONDE.search(t):
        return "monde"
    return "ailleurs"


def offre(source, entreprise, poste, zone_txt, url, date):
    return {"source": source, "entreprise": (entreprise or "").strip(),
            "poste": (poste or "").strip(), "zone_declaree": (zone_txt or "").strip(),
            "zone": zone(zone_txt), "url": url, "date": date}


def remotive():
    """Remotive — catégorie DevOps déjà constituée, plus le tout-venant filtré."""
    out = []
    for cat in ("devops", "software-dev"):
        d = gjson(f"https://remotive.com/api/remote-jobs?category={cat}&limit=500")
        for j in (d or {}).get("jobs", []):
            if not retenu(j.get("title"), rubrique_devops=(cat == "devops")):
                continue
            out.append(offre("Remotive", j.get("company_name"), j.get("title"),
                             j.get("candidate_required_location"), j.get("url"),
                             (j.get("publication_date") or "")[:10]))
    return out


def remoteok():
    """Remote OK — les 100 dernières offres, tous métiers ; on filtre l'intitulé."""
    d = gjson("https://remoteok.com/api")
    out = []
    for j in (d or [])[1:]:
        titre = j.get("position") or ""
        tags = " ".join(j.get("tags") or [])
        if not retenu(titre, rubrique_devops=bool(POSTE.search(tags))):
            continue
        out.append(offre("Remote OK", j.get("company"), titre, j.get("location"),
                         j.get("url"), (j.get("date") or "")[:10]))
    return out


def weworkremotely():
    """We Work Remotely — flux RSS de la catégorie DevOps and Sysadmin."""
    xml = get("https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss")
    out = []
    if not xml:
        return out
    for it in ET.fromstring(xml).findall(".//item"):
        champ = {c.tag: (c.text or "") for c in it}
        titre = champ.get("title", "")
        entreprise, _, poste = titre.partition(": ")
        if not retenu(poste or titre, rubrique_devops=True):   # flux 100 % DevOps
            continue
        out.append(offre("We Work Remotely", entreprise or titre, poste or titre,
                         champ.get("region"), champ.get("link"),
                         champ.get("pubDate", "")[:16]))
    return out


def himalayas():
    """Himalayas — pas de filtre par métier côté API : on pagine le flux récent."""
    out, cursor, lues = [], None, 0
    for _ in range(REQUETES_HIMALAYAS):
        if lues >= OFFRES_HIMALAYAS:
            break
        url = "https://himalayas.app/jobs/api?limit=100" + (f"&cursor={cursor}" if cursor else "")
        d = gjson(url)
        if not d:      # 429 : le flux coupe, on garde ce qui a été lu
            print("    (flux Himalayas interrompu — limite de débit)", flush=True)
            break
        if not d.get("jobs"):
            break
        lues += len(d["jobs"])
        for j in d["jobs"]:
            cats = (" ".join(j.get("categories") or []) + " "
                    + " ".join(j.get("parentCategories") or [])).replace("-", " ")
            if not retenu(j.get("title"), rubrique_devops=bool(POSTE.search(cats))):
                continue
            zones = ", ".join(j.get("locationRestrictions") or [])
            # Pas de pays imposé mais un fuseau UTC 0 à +3 : c'est ouvert à l'Europe.
            tz = j.get("timezoneRestrictions") or []
            if not zones and any(0 <= float(t) <= 3 for t in tz):
                zones = "fuseaux UTC " + ", ".join(str(t) for t in tz)
            out.append(offre("Himalayas", j.get("companyName"), j.get("title"), zones,
                             j.get("applicationLink"),
                             datetime.datetime.fromtimestamp(int(j.get("pubDate") or 0)).date().isoformat()))
        cursor = d.get("nextCursor")
        if not cursor:
            break
        time.sleep(PAUSE_HIMALAYAS)
    print(f"    ({lues} offres lues sur le flux Himalayas)", flush=True)
    return out


def jobicy():
    """Jobicy — filtres géographique et thématique côté serveur."""
    out = []
    requetes = [f"geo={g}" for g in ("europe", "anywhere")] + \
               [f"tag={t}" for t in TAGS_JOBICY]
    for q in requetes:
        d = gjson(f"https://jobicy.com/api/v2/remote-jobs?count=100&{q}")
        for j in (d or {}).get("jobs", []):
            ind = " ".join(j.get("jobIndustry") or [])
            if not retenu(j.get("jobTitle"), rubrique_devops=bool(POSTE.search(ind))):
                continue
            out.append(offre("Jobicy", j.get("companyName"), j.get("jobTitle"),
                             j.get("jobGeo"), j.get("url"), (j.get("pubDate") or "")[:10]))
    return out


def workingnomads():
    """Working Nomads — flux public, catégorie et localisation déclarées."""
    d = gjson("https://www.workingnomads.com/api/exposed_jobs/") or []
    out = []
    for j in d:
        contexte = f"{j.get('tags', '')} {j.get('category_name', '')}"
        if not retenu(j.get("title"), rubrique_devops=bool(POSTE.search(contexte))):
            continue
        out.append(offre("Working Nomads", j.get("company_name"), j.get("title"),
                         j.get("location"), j.get("url"), (j.get("pub_date") or "")[:10]))
    return out


def arbeitnow():
    """Arbeitnow — marché européen (Allemagne surtout), champ `remote` explicite."""
    out = []
    for page in range(1, PAGES_ARBEITNOW + 1):
        d = gjson(f"https://www.arbeitnow.com/api/job-board-api?page={page}")
        for j in (d or {}).get("data", []):
            if not j.get("remote") or not retenu(j.get("title")):
                continue
            # Arbeitnow tient deux places, une allemande et une britannique :
            # l'offre relève du droit du travail du pays, pas de « l'Europe ».
            pays = "Royaume-Uni" if ".co.uk" in (j.get("url") or "") else "Allemagne"
            out.append(offre("Arbeitnow", j.get("company_name"), j.get("title"),
                             f"{pays} — {j.get('location') or 'télétravail'}", j.get("url"),
                             datetime.datetime.fromtimestamp(int(j.get("created_at") or 0)).date().isoformat()))
    return out


def main():
    offres = []
    for nom, f in [("Remotive", remotive), ("Remote OK", remoteok),
                   ("We Work Remotely", weworkremotely), ("Himalayas", himalayas),
                   ("Jobicy", jobicy), ("Working Nomads", workingnomads),
                   ("Arbeitnow", arbeitnow)]:
        try:
            r = f()
        except Exception as e:
            print(f"  {nom:<18} échec : {e}", flush=True)
            r = []
        print(f"  {nom:<18} {len(r):>4} offres d'infrastructure", flush=True)
        offres += r

    # Regroupement par entreprise : c'est l'employeur qu'on vise, pas l'offre.
    par_ent = {}
    for o in offres:
        if not o["entreprise"]:
            continue
        cle = re.sub(r"[^a-z0-9]", "", o["entreprise"].lower())
        e = par_ent.setdefault(cle, {"entreprise": o["entreprise"], "offres": [],
                                     "sources": set(), "zones": set()})
        e["offres"].append(o)
        e["sources"].add(o["source"])
        e["zones"].add(o["zone"])

    ents = []
    for e in par_ent.values():
        e["offres"].sort(key=lambda o: o["date"], reverse=True)
        # Une entreprise est classée sur sa meilleure offre : c'est celle-là
        # qui décide s'il y a une porte d'entrée.
        zone_ent = next(z for z in ("france", "europe", "monde", "ailleurs")
                        if z in e["zones"] or z == "ailleurs")
        ents.append({"entreprise": e["entreprise"], "zone": zone_ent,
                     "nb_offres": len(e["offres"]), "sources": sorted(e["sources"]),
                     "offres": e["offres"]})
    ents.sort(key=lambda e: (e["entreprise"].lower()))

    compte = {z: sum(1 for e in ents if e["zone"] == z)
              for z in ("france", "europe", "monde", "ailleurs")}
    print(f"\n  {len(ents)} entreprises — {compte['france']} ouvertes à la France ou à "
          f"l'Europe entière, {compte['europe']} à un autre pays européen, "
          f"{compte['monde']} sans restriction déclarée, {compte['ailleurs']} hors zone")

    dest = CANDIDATURES / "devops-remote.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({
        "sources": ["Remotive (remotive.com/api)", "Remote OK (remoteok.com/api)",
                    "We Work Remotely (flux RSS DevOps and Sysadmin)",
                    "Himalayas (himalayas.app/jobs/api)", "Jobicy (jobicy.com/api/v2)",
                    "Working Nomads (workingnomads.com/api/exposed_jobs)",
                    "Arbeitnow (arbeitnow.com/api/job-board-api)"],
        "collecte": datetime.date.today().isoformat(),
        "methode": "Offres en télétravail publiées sur sept places de marché, filtrées sur "
                   "l'intitulé de poste (DevOps, SRE, platform, cloud, systèmes) puis "
                   "regroupées par entreprise. La zone est celle déclarée dans l'offre.",
        "avertissement": "Une offre publiée prouve qu'une entreprise recrutait en remote à "
                         "cette date. Elle ne prouve pas que l'entreprise est « 100 % remote », "
                         "ni qu'elle peut employer un résident français.",
        "nb_offres": len(offres), "compte_par_zone": compte, "entreprises": ents,
    }, ensure_ascii=False, indent=2) + "\n")
    print(f"  {len(offres)} offres → {dest}")


if __name__ == "__main__":
    main()
