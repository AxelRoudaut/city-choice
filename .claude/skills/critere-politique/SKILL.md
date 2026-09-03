---
name: critere-politique
description: Collecte et calcule le critère 15 (Affinité politique) à partir des résultats officiels des élections municipales. À utiliser pour rafraîchir les nuances politiques après une élection ou changer la préférence politique du rapport.
---

# Critère : politique

## Lancer

```bash
python3 scripts/fetch/politique.py
```

Écrit `_data/politique.json`, avec pour chaque ville la valeur, la source, la méthode et la
date de collecte.

Le collecteur est **indépendant de la liste de villes** : il parcourt
`VILLES` dans [scripts/fetch/_common.py](../../../scripts/fetch/_common.py).
Ajouter une ville au panel, c'est ajouter une entrée à ce dictionnaire (code
INSEE, département, EPCI, coordonnées) — aucun code à modifier.

## Source

Ministère de l'Intérieur — résultats des municipales, second tour, sur data.gouv

**Ce qui est mesuré.** Part des sièges au conseil municipal détenus par des listes de nuance officielle de gauche.

## De la donnée à la note

Part des sièges de gauche divisée par 10. Préférence déclarée du rapport : favoriser la gauche.

La note est une lecture argumentée, pas une donnée : la formule doit rester
écrite dans `_data/criteres.yml` (champ `methode`) et affichée en fin de
critère dans le rapport.

## Pièges vérifiés

1. **Le RNE ne contient PAS l'étiquette politique** : il donne les maires et leurs mandats, rien de plus. La nuance vient des résultats du ministère, colonne « Nuance liste ».
2. Les pourcentages portent un signe **`%`** et une virgule décimale : `float()` échoue sans nettoyage préalable.
3. Le fichier « Résultats - Communes » a **83 colonnes**, par blocs de 13 par liste candidate à partir de l'indice 18. La clé est le **code INSEE complet** en colonne 2, pas un suffixe.
4. Une commune élue **au premier tour** est absente du fichier du second tour : prévoir le repli sur le premier tour.
5. Les nuances retenues comme « de gauche » sont listées dans le script (`GAUCHE`). C'est un choix éditorial assumé : le modifier change le critère.

## Après collecte

```bash
just donnees     # réinjecte les notes dans le bloc JS du rapport
just artifact    # régénère report.body.html
```
