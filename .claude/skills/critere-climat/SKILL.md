---
name: critere-climat
description: Collecte et calcule le critère 8 (Climat) à partir des données climatologiques de base de Météo-France. À utiliser pour rafraîchir les normales, changer la période, ou corriger le choix de station d'une ville.
---

# Critère : climat

## Lancer

```bash
python3 scripts/fetch/climat.py
```

Écrit `_data/climat.json`, avec pour chaque ville la valeur, la source, la méthode et la
date de collecte.

Le collecteur est **indépendant de la liste de villes** : il parcourt
`VILLES` dans [scripts/fetch/_common.py](../../../scripts/fetch/_common.py).
Ajouter une ville au panel, c'est ajouter une entrée à ce dictionnaire (code
INSEE, département, EPCI, coordonnées) — aucun code à modifier.

## Source

Météo-France, données climatologiques de base (fichiers mensuels MENS par département, bucket ouvert sur data.gouv), sans clé

**Ce qui est mesuré.** Normales 1991-2020 : température moyenne, précipitations, ensoleillement, jours au-dessus de 30 °C et de 25 °C.

## De la donnée à la note

Appréciation : le climat est une préférence personnelle. Préférer les jours au-dessus de 30 °C à la température moyenne pour parler d'inconfort réel.

La note est une lecture argumentée, pas une donnée : la formule doit rester
écrite dans `_data/criteres.yml` (champ `methode`) et affichée en fin de
critère dans le rapport.

## Pièges vérifiés

1. **`INST` (ensoleillement) est en MINUTES**, pas en heures. Oublier la division par 60 donne des valeurs absurdes (105 690 « heures » par an).
2. **Le choix de station est le vrai piège.** « La plus complète du département » donne l'Alpe-d'Huez pour Grenoble (1860 m) ; « la plus proche » donne Autrans (1069 m) pour une ville à 212 m. Le script combine distance, écart au fond de vallée (altitude minimale des postes à moins de 40 km) et présence d'une série d'ensoleillement.
3. L'heuristique reste faillible : `_data/villes.yml` accepte une clé **`station_meteo`** par ville pour imposer un poste. Vérifier toujours la station retenue et sa distance dans la sortie.
4. Le CSV est en latin-1, gzippé, séparateur `;`.

## Après collecte

```bash
just donnees     # réinjecte les notes dans le bloc JS du rapport
just artifact    # régénère report.body.html
```
