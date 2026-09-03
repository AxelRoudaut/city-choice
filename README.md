# Cinq villes au banc d'essai

Comparatif de **Rennes, Grenoble, Chambéry, Montpellier et Toulon** pour préparer
un déménagement, avec **Paris en ligne de référence**. Seize critères, des
pondérations réglables en direct, et — c'est le point — des chiffres qui viennent
tous de jeux de données publics traçables.

Le rapport se lit comme un article : chaque critère expose ses données, sa
source et sa méthode, puis un classement pondéré se recalcule à mesure que vous
déplacez les curseurs.

## Ce que compare le rapport

| # | Critère | Ce qui est mesuré |
|---|---|---|
| 1-2 | Emploi DevOps / CIP | densité d'entreprises du secteur dans le bassin |
| 3 | Logement | loyer d'annonce €/m² dans un rayon de 15 km |
| 4-5 | Centre piéton, vie de centre-ville | surfaces piétonnes, monuments, commerce |
| 6-7 | Vélo, embouteillages | aménagements cyclables, congestion |
| 8 | Climat | normales 1991-2020, jours de chaleur |
| 9 | Qualité de l'air | PM2.5 et NO2, moyennes annuelles |
| 10 | Environnement | espaces naturels, pression urbaine |
| 11 | Falaise | sites d'escalade avec corde à moins de 50 km |
| 12 | Mer et lac | spots de baignade à moins de 30 km |
| 13 | Risques | risques naturels et technologiques recensés |
| 14 | Eau du robinet | nitrates, moyenne 12 mois glissants |
| 15 | Affinité politique | part des sièges de gauche au conseil municipal |
| 16 | Transports en commun | couverture de l'agglomération, qualité du réseau |

## Démarrage

Prérequis : `ruby`, `curl`, et [`just`](https://github.com/casey/just).

```bash
just init     # dépendances système, gems, polices
just serve    # http://localhost:4000
```

`just init` demande le mot de passe sudo pour installer les paquets système
manquants (Ruby, headers, build-essential). Si tout est déjà là, il n'installe
rien.

## Commandes

| Commande | Effet |
|---|---|
| `just serve` | sert le rapport en local avec rechargement automatique |
| `just build` | construit `_site/`, exactement comme GitHub Pages |
| `just artifact` | régénère `report.body.html`, le fragment publié en Artifact |
| `just fonts` | rapatrie les polices pour un rendu hors ligne |
| `just clean` | supprime les fichiers générés, gems et polices |

## Utiliser le rapport

**Les curseurs.** Chaque critère a un poids de 0 à 40. Le total est normalisé :
seule compte l'importance *relative* que vous donnez à chaque critère. Le
classement se recalcule à chaque mouvement. « Rétablir les poids par défaut »
revient à la pondération d'origine.

**Lire les notes.** Toutes les notes vont de 0 à 10 et se lisent dans le même
sens — une note haute est toujours favorable. Pour « Embouteillages », une note
haute signifie donc *peu* de congestion.

**Paris.** Paris figure dans tous les tableaux comme étalon, mais ne concourt
pas dans le classement pondéré : c'est un point de comparaison, pas une
destination candidate.

**Les notes ne sont pas des données.** Ce sont des lectures argumentées des
chiffres présentés, et la formule qui transforme la donnée en note est écrite à
côté du tableau de notes. Les curseurs existent précisément pour que vous
puissiez substituer votre jugement à celui de l'auteur.

## D'où viennent les chiffres

Aucun chiffre n'est estimé. Chaque valeur provient d'un jeu de données public,
avec sa source et sa date de collecte affichées en fin de critère.

| Source | Ce qu'elle alimente |
|---|---|
| Météo-France, données climatologiques de base | climat |
| Geod'air / LCSQA | qualité de l'air |
| Hub'Eau, contrôle sanitaire | eau du robinet |
| API Recherche d'entreprises | emploi, tissu associatif |
| Carte des loyers (DHUP) | logement |
| Ministère de l'Intérieur, municipales 2026 | affinité politique |
| Répertoire National des Élus | maires et mandats |
| Géorisques (GASPAR) | risques |
| OpenStreetMap | falaise, baignade |
| transport.data.gouv.fr (GTFS) | transports en commun |

Un seul critère repose encore sur une source privée : **les embouteillages**
(TomTom Traffic Index), faute d'équivalent en données ouvertes.

## Structure du dépôt

```
_includes/report-body.html   ← source unique : corps du rapport + script
_includes/report-head.html   ← titre, polices, CSS
_layouts/report.html         ← assemblage Jekyll
index.html                   ← page publiée
report.body.html             ← GÉNÉRÉ par `just artifact`, ne pas éditer
```

Le rapport a deux cibles depuis la même source : le site Jekyll publié sur
GitHub Pages, et un fragment HTML autonome publié comme Artifact Claude.

## Publication

Un push sur `main` déclenche le workflow GitHub Pages
([.github/workflows/pages.yml](.github/workflows/pages.yml)) qui construit le
site et le déploie.

## Contribuer

Avant toute modification, lisez [CLAUDE.md](CLAUDE.md) : il contient la règle de
sourcing, les points d'entrée d'API vérifiés avec leurs pièges, et la checklist
pour ajouter un critère sans casser le classement.

Deux règles suffisent à éviter l'essentiel des ennuis :

1. **Ne jamais inventer un chiffre.** Pas de source publique, pas de critère.
2. **Éditer `_includes/`, jamais `report.body.html`**, puis lancer
   `just artifact`.
