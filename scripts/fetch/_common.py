"""Socle commun aux collecteurs de données du comparatif.

Chaque collecteur écrit un JSON dans _data/ contenant, pour chaque ville :
la valeur mesurée, l'unité, la source et la date de collecte. Aucun chiffre
n'est estimé : voir CLAUDE.md, « Règle d'or ».
"""
import json, os, subprocess, sys, time, datetime, pathlib

RACINE = pathlib.Path(__file__).resolve().parents[2]
DATA = RACINE / "_data"

# Les listes de candidature sont personnelles et ne sont pas publiées : le dépôt
# est public, elles vivent à côté des lettres de motivation. Surchargeable par
# CANDIDATURES_DIR. Voir CLAUDE.md, « Hors rapport ».
CANDIDATURES = pathlib.Path(
    os.environ.get("CANDIDATURES_DIR", RACINE.parent / "Cover_Letters" / "candidatures")
).expanduser()

# Panel. Paris est une ligne de référence : il figure dans les tableaux mais
# ne concourt pas au classement pondéré (voir README).
VILLES = {
    "Rennes":      {"insee": "35238", "dep": "35", "epci": "243500139", "lat": 48.1159, "lon": -1.6884, "reference": False},
    "Grenoble":    {"insee": "38185", "dep": "38", "epci": "200040715", "lat": 45.1885, "lon":  5.7245, "reference": False},
    "Chambéry":    {"insee": "73065", "dep": "73", "epci": "200069110", "lat": 45.5646, "lon":  5.9178, "reference": False},
    "Montpellier": {"insee": "34172", "dep": "34", "epci": "243400017", "lat": 43.6109, "lon":  3.8772, "reference": False},
    "Toulon":      {"insee": "83137", "dep": "83", "epci": "248300543", "lat": 43.1258, "lon":  5.9304, "reference": False},
    "Paris":       {"insee": "75056", "dep": "75", "epci": "200054781", "lat": 48.8589, "lon":  2.3470, "reference": True},
}

# Paris est découpée en arrondissements dans plusieurs référentiels : l'API
# Recherche d'entreprises ne connaît pas 75056 et renvoie 0. Voir CLAUDE.md.
ARRONDISSEMENTS_PARIS = [f"751{i:02d}" for i in range(1, 21)]


def curl(url, *args, timeout=60, retries=3, pause=20):
    """GET avec réessais. Renvoie le corps en texte, ou "" après échec."""
    for essai in range(retries):
        p = subprocess.run(["curl", "-sSL", "-m", str(timeout), *args, url],
                           capture_output=True, text=True)
        if p.returncode == 0 and p.stdout:
            return p.stdout
        if essai < retries - 1:
            print(f"    réessai {essai + 1}/{retries} sur {url[:60]}", file=sys.stderr, flush=True)
            time.sleep(pause)
    return ""


def curl_bytes(url, *args, timeout=180, retries=3, pause=20):
    """Comme curl(), mais renvoie des octets : indispensable pour les CSV
    qui ne sont pas en UTF-8 (la Carte des loyers est en latin-1)."""
    for essai in range(retries):
        p = subprocess.run(["curl", "-sSL", "-m", str(timeout), *args, url],
                           capture_output=True)
        if p.returncode == 0 and p.stdout:
            return p.stdout
        if essai < retries - 1:
            time.sleep(pause)
    return b""


def curl_json(url, *args, **kw):
    txt = curl(url, *args, **kw)
    try:
        return json.loads(txt)
    except Exception:
        return {}


def ecrire(nom, valeurs, source, url, unite=None, methode=None):
    """Écrit _data/<nom>.json avec la traçabilité exigée par CLAUDE.md."""
    DATA.mkdir(exist_ok=True)
    doc = {
        "source": source,
        "url": url,
        "collecte": datetime.date.today().isoformat(),
        "unite": unite,
        "methode": methode,
        "villes": valeurs,
    }
    chemin = DATA / f"{nom}.json"
    chemin.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"→ {chemin.relative_to(RACINE)}  ({len(valeurs)} villes)")
    return doc


def station_meteo(ville):
    """Station Météo-France imposée pour une ville, si _data/villes.yml en déclare
    une (clé « station_meteo »). Le choix de station est un jugement : la config
    doit pouvoir corriger l'heuristique du collecteur."""
    fichier = DATA / "villes.yml"
    if not fichier.exists():
        return None
    try:
        import yaml
        conf = yaml.safe_load(fichier.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    return (conf.get(ville) or {}).get("station_meteo")


def cle_api(nom):
    """Lit une clé dans .env.local (local) ou l'environnement (CI)."""
    if nom in os.environ:
        return os.environ[nom]
    env = RACINE / ".env.local"
    if env.exists():
        for ligne in env.read_text(encoding="utf-8").splitlines():
            if ligne.startswith(f"{nom}="):
                return ligne.split("=", 1)[1].strip()
    raise SystemExit(f"Clé {nom} absente : voir CLAUDE.md > Secrets")
