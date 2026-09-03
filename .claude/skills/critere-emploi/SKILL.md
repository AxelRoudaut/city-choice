---
name: critere-emploi
description: Collecte et calcule les critères 1-2 (Emploi DevOps, Emploi CIP) du comparatif de villes à partir de l'API Recherche d'entreprises. À utiliser pour rafraîchir les données emploi, ajouter une ville au panel, ou changer les codes NAF retenus.
---

# Critère : emploi

## Lancer

```bash
python3 scripts/fetch/emploi.py
```

Écrit `_data/emploi.json`, avec pour chaque ville la valeur, la source, la méthode et la
date de collecte.

Le collecteur est **indépendant de la liste de villes** : il parcourt
`VILLES` dans [scripts/fetch/_common.py](../../../scripts/fetch/_common.py).
Ajouter une ville au panel, c'est ajouter une entrée à ce dictionnaire (code
INSEE, département, EPCI, coordonnées) — aucun code à modifier.

## Source

API Recherche d'entreprises (recherche-entreprises.api.gouv.fr), sans clé

**Ce qui est mesuré.** Établissements actifs par code NAF, rapportés à 1 000 habitants.

## De la donnée à la note

devops : 0 pour 0/1000 hab, 10 pour 13/1000.
cip : 0 pour 0,8/1000 hab, 10 pour 2,3/1000.

La note est une lecture argumentée, pas une donnée : la formule doit rester
écrite dans `_data/criteres.yml` (champ `methode`) et affichée en fin de
critère dans le rapport.

## Pièges vérifiés

1. `total_results` est **plafonné à 10 000**. Paris dépasse ce plafond sur 62.01Z : le script somme commune par commune pour le contourner. Ne jamais faire une requête unique sur un grand périmètre.
2. **Paris n'existe pas sous le code 75056** dans ce référentiel et renvoie 0. Il faut interroger les 20 arrondissements (75101 à 75120). Voir `ARRONDISSEMENTS_PARIS` dans `_common.py`.
3. Le compte porte sur les entreprises **domiciliées**, pas sur les offres d'emploi : c'est un indicateur de densité de bassin, pas de tension du marché. Le dire dans le texte du critère.
4. Normaliser par habitant est obligatoire : sans cela on mesure la taille de la ville.

## Après collecte

```bash
just donnees     # réinjecte les notes dans le bloc JS du rapport
just artifact    # régénère report.body.html
```
