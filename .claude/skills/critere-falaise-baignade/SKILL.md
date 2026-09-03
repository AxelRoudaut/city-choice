---
name: critere-falaise-baignade
description: Collecte et calcule les critères 11-12 (Falaise, Mer et lac) à partir d'OpenStreetMap via Overpass. À utiliser pour compter les sites d'escalade avec corde et les spots de baignade autour d'une ville.
---

# Critère : falaise baignade

## Lancer

```bash
python3 scripts/fetch/loisirs_nature.py
```

Écrit `_data/loisirs_nature.json`, avec pour chaque ville la valeur, la source, la méthode et la
date de collecte.

Le collecteur est **indépendant de la liste de villes** : il parcourt
`VILLES` dans [scripts/fetch/_common.py](../../../scripts/fetch/_common.py).
Ajouter une ville au panel, c'est ajouter une entrée à ce dictionnaire (code
INSEE, département, EPCI, coordonnées) — aucun code à modifier.

## Source

OpenStreetMap via l'API Overpass, sans clé

**Ce qui est mesuré.** Falaise : sites d'escalade avec corde à moins de 50 km. Baignade : plages et zones de baignade à moins de 30 km, surveillées ou non.

## De la donnée à la note

Échelle racine : 10 × min(1, √(n / n_max)). Le rendement décroissant évite qu'une ville écrase les autres.

La note est une lecture argumentée, pas une donnée : la formule doit rester
écrite dans `_data/criteres.yml` (champ `methode`) et affichée en fin de
critère dans le rapport.

## Pièges vérifiés

1. **Ne jamais compter les sites d'escalade bruts.** Un comptage naïf place Paris en tête (1 035 sites) grâce à Fontainebleau, qui est du **bloc**, pas de la falaise. Exiger un marqueur de voie équipée : `climbing:sport`, `climbing:trad`, `climbing:multipitch`, `climbing:length:max`, `climbing:grade:french:max`. Le filtre fait tomber Paris à 39.
2. `climbing!=boulder` **ne suffit pas** : beaucoup de secteurs de bloc ne portent pas ce tag.
3. Exclure aussi `leisure=sports_centre` et tout objet avec `building` : ce sont des salles.
4. **Le rapportage de la saison balnéaire ne recense que les sites surveillés** et manque donc lacs et criques. OSM couvre les deux, c'est pourquoi il est préféré ici.
5. Le nombre de voies (`climbing:sport=N`) n'est renseigné que sur une petite minorité de sites : le **comptage de sites** est fiable, celui des voies ne l'est pas.
6. Overpass limite le débit (2 slots). Le script réessaie sur plusieurs miroirs et met les réponses en cache. Vérifier `https://overpass-api.de/api/status` en cas d'échec répété.
7. La complétude d'OSM varie : Chambéry ressort devant Grenoble sur la falaise, ce qui reflète peut-être le tagging autant que le terrain. À signaler dans le texte du critère.

## Après collecte

```bash
just donnees     # réinjecte les notes dans le bloc JS du rapport
just artifact    # régénère report.body.html
```
