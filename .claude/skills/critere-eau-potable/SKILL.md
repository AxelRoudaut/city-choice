---
name: critere-eau-potable
description: Collecte et calcule le critère 14 (Eau du robinet) à partir de Hub'Eau, contrôle sanitaire des ARS. À utiliser pour rafraîchir les nitrates ou suivre un autre paramètre de qualité.
---

# Critère : eau potable

## Lancer

```bash
python3 scripts/fetch/eau_potable.py
```

Écrit `_data/eau_potable.json`, avec pour chaque ville la valeur, la source, la méthode et la
date de collecte.

Le collecteur est **indépendant de la liste de villes** : il parcourt
`VILLES` dans [scripts/fetch/_common.py](../../../scripts/fetch/_common.py).
Ajouter une ville au panel, c'est ajouter une entrée à ce dictionnaire (code
INSEE, département, EPCI, coordonnées) — aucun code à modifier.

## Source

Hub'Eau — qualité de l'eau potable (hubeau.eaufrance.fr), sans clé

**Ce qui est mesuré.** Nitrates (paramètre 1340), moyenne sur 12 mois glissants, plus le taux de conformité.

## De la donnée à la note

Note inversée : 0 à la limite réglementaire de 50 mg/L, 10 à 0 mg/L.

La note est une lecture argumentée, pas une donnée : la formule doit rester
écrite dans `_data/criteres.yml` (champ `methode`) et affichée en fin de
critère dans le rapport.

## Pièges vérifiés

1. **Ne jamais afficher un prélèvement isolé.** Trois relevés rennais consécutifs donnent 14,9 puis 15,7 puis 18,6 mg/L. Toujours une moyenne 12 mois, avec le nombre de relevés.
2. Une commune peut être desservie par **plusieurs réseaux** : le script collecte tous les distributeurs et les liste. Le préciser dans le texte du critère.
3. L'API pagine : réponse HTTP **206** et champ `next`. Ne pas s'arrêter à la première page.
4. Le volume varie énormément d'une ville à l'autre (Paris 1 007 relevés sur 12 mois, Grenoble 35) : afficher `releves` pour que le lecteur juge de la robustesse.

## Après collecte

```bash
just donnees     # réinjecte les notes dans le bloc JS du rapport
just artifact    # régénère report.body.html
```
