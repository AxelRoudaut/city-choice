---
name: critere-logement
description: Collecte et calcule le critère 3 (Logement dans un rayon de 15 km) à partir de la Carte des loyers de la DHUP. À utiliser pour rafraîchir les loyers, changer le rayon, ou ajouter une ville.
---

# Critère : logement

## Lancer

```bash
python3 scripts/fetch/logement.py
```

Écrit `_data/logement.json`, avec pour chaque ville la valeur, la source, la méthode et la
date de collecte.

Le collecteur est **indépendant de la liste de villes** : il parcourt
`VILLES` dans [scripts/fetch/_common.py](../../../scripts/fetch/_common.py).
Ajouter une ville au panel, c'est ajouter une entrée à ce dictionnaire (code
INSEE, département, EPCI, coordonnées) — aucun code à modifier.

## Source

Carte des loyers — indicateurs de loyers d'annonce par commune (DHUP), sur data.gouv

**Ce qui est mesuré.** Loyer d'annonce prédit pour un appartement, en €/m², pour la commune et en moyenne dans un rayon de 15 km.

## De la donnée à la note

Note inversée : 0 pour 35 €/m², 10 pour 12 €/m².

La note est une lecture argumentée, pas une donnée : la formule doit rester
écrite dans `_data/criteres.yml` (champ `methode`) et affichée en fin de
critère dans le rapport.

## Pièges vérifiés

1. Le CSV est en **latin-1**, séparateur `;`, décimales à la **virgule**. Le décoder en UTF-8 lève une `UnicodeDecodeError`. Utiliser `curl_bytes`, pas `curl`.
2. **Paris est publié par arrondissement**, pas sous 75056 : le script moyenne les 20 arrondissements au prorata du nombre d'annonces.
3. Toujours afficher l'intervalle de confiance (`lwr.IPm2`, `upr.IPm2`) : la valeur seule donne une fausse précision.
4. Le jeu couvre les 34 900 communes : le rayon de 15 km est calculé pour de vrai à partir des centroïdes de geo.api.gouv.fr, pas approximé par la ville-centre.

## Après collecte

```bash
just donnees     # réinjecte les notes dans le bloc JS du rapport
just artifact    # régénère report.body.html
```
