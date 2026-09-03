---
name: critere-qualite-air
description: Collecte et calcule le critère 9 (Qualité de l'air) à partir de l'API Geod'air du LCSQA. Nécessite une clé. À utiliser pour rafraîchir les moyennes annuelles PM2.5 et NO2 ou changer l'année de référence.
---

# Critère : qualite air

## Lancer

```bash
python3 scripts/fetch/qualite_air.py
```

Écrit `_data/qualite_air.json`, avec pour chaque ville la valeur, la source, la méthode et la
date de collecte.

Le collecteur est **indépendant de la liste de villes** : il parcourt
`VILLES` dans [scripts/fetch/_common.py](../../../scripts/fetch/_common.py).
Ajouter une ville au panel, c'est ajouter une entrée à ce dictionnaire (code
INSEE, département, EPCI, coordonnées) — aucun code à modifier.

## Source

Geod'air / LCSQA, clé requise (header `apikey`)

**Ce qui est mesuré.** Moyenne annuelle de PM2.5 et NO2 sur les stations de fond en implantation urbaine.

## De la donnée à la note

Note inversée sur les PM2.5 : 0 pour 15 µg/m³, 10 pour 5 µg/m³.

La note est une lecture argumentée, pas une donnée : la formule doit rester
écrite dans `_data/criteres.yml` (champ `methode`) et affichée en fin de
critère dans le rapport.

## Pièges vérifiés

1. **La documentation du site donne de fausses routes.** Le spec réel est `https://www.geodair.fr/api-ext/swagger.yaml`. Toute autre route renvoie « no Route matched ».
2. L'export se fait **en deux temps** : `api-ext/statistique/export` renvoie un identifiant, puis `api-ext/download?id=…` renvoie le CSV. Prévoir une pause entre les deux.
3. Codes : statistique `a7` = moyenne annuelle ; polluants `39` = PM2.5, `03` = NO2, `24` = PM10. Les référentiels sont à `api-ext/polluant/export` et `api-ext/type-donnees/export?codes_polluants=39`.
4. **Quota strict.** Le producteur demande une seule requête par date, polluant et statistique ; au-delà l'API répond « API rate limit exceeded ». Le script met les exports en cache dans `.cache/geodair/` — ne jamais le contourner.
5. Ne comparer que des stations de **fond** en implantation **urbaine** : le CSV donne les deux colonnes. Comparer une station trafic à une station de fond fausse tout.
6. La clé se lit dans `.env.local` ou la variable `GEODAIR_API_KEY`. Jamais dans le dépôt.

## Après collecte

```bash
just donnees     # réinjecte les notes dans le bloc JS du rapport
just artifact    # régénère report.body.html
```
