---
name: critere-transports
description: Collecte et calcule le critère 16 (Transports en commun) à partir des GTFS de transport.data.gouv.fr. À utiliser pour mesurer la couverture d'une agglomération par son réseau et la qualité des modes offerts.
---

# Critère : transports

## Lancer

```bash
python3 scripts/fetch/transports.py
```

Écrit `_data/transports.json`, avec pour chaque ville la valeur, la source, la méthode et la
date de collecte.

Le collecteur est **indépendant de la liste de villes** : il parcourt
`VILLES` dans [scripts/fetch/_common.py](../../../scripts/fetch/_common.py).
Ajouter une ville au panel, c'est ajouter une entrée à ce dictionnaire (code
INSEE, département, EPCI, coordonnées) — aucun code à modifier.

## Source

transport.data.gouv.fr — GTFS des réseaux urbains, sans clé

**Ce qui est mesuré.** Couverture : part des communes de l'EPCI ayant au moins un arrêt. Qualité : hiérarchie des modes (métro 3, tram et train 2, funiculaire, câble et ferry 1).

## De la donnée à la note

0,06 × couverture en % + 1,3 × indice de qualité, plafonné à 10.

La note est une lecture argumentée, pas une donnée : la formule doit rester
écrite dans `_data/criteres.yml` (champ `methode`) et affichée en fin de
critère dans le rapport.

## Pièges vérifiés

1. **Un réseau publie souvent plusieurs GTFS** : urbain seul, suburbain seul, réseau complet. Prendre le premier venu donne un Montpellier **sans tram**. Le script retient le GTFS offrant le plus de modes distincts — vérifier toujours le champ `modes` de la sortie.
2. Les `route_type` étendus (700 bus, 900 tram, 1400 funiculaire) doivent être traduits, sinon ils tombent en « autre ».
3. Le GTFS d'Île-de-France Mobilités pèse environ 115 Mo : le script met les archives en cache dans `.cache/gtfs/`.
4. Le rattachement d'un arrêt à une commune se fait par point-dans-polygone sur les contours de geo.api.gouv.fr, sans dépendance externe (ni shapely ni pandas).
5. La couverture en population est presque toujours proche de 100 % : c'est la couverture en **communes** qui discrimine (Chambéry 79 %, Paris 100 %).

## Après collecte

```bash
just donnees     # réinjecte les notes dans le bloc JS du rapport
just artifact    # régénère report.body.html
```
