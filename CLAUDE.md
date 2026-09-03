# Maintenir « Cinq villes au banc d'essai »

Rapport de décision comparant **Rennes, Grenoble, Chambéry, Montpellier, Toulon**
sur 15 critères, avec pondération réglable. Publié en Jekyll sur GitHub Pages, et
en fragment autonome (`report.body.html`) comme Artifact Claude.

---

## Règle d'or

> **Aucun chiffre ne peut venir d'une estimation de LLM.**

Chaque valeur affichée doit être rattachable à un jeu de données public, avec sa
source, sa date de collecte et sa méthode de calcul. Une note sur 10 n'est pas
une donnée : c'est une lecture argumentée *de* données citées — la formule qui
transforme la donnée en note doit être écrite en commentaire à côté du tableau
de notes.

Si une donnée n'existe pas dans une source publique, deux options : renoncer au
critère, ou l'assumer explicitement comme préférence personnelle (c'est le cas
du critère 15, Affinité politique). **Jamais de valeur plausible inventée.**

Un précédent : le commit `d3509a1` a ajouté trois critères avec des notes
inventées, dont une pour une seule ville sur cinq → `NaN` dans tout le
classement. Voir « Invariants du classement » plus bas.

---

## Architecture

GitHub Pages sert du statique : **aucun appel API depuis le navigateur**
(CORS bloquant, et toute clé serait lisible dans le source de la page).

```
scripts/fetch/*.py  →  _data/*.json  →  scripts/notes.py  →  _data/criteres.yml
                                                                    ↓
                                                    scripts/build_donnees.py
                                                                    ↓
                                              bloc JS de _includes/report-body.html
```

La pondération et les notes vivent dans **`_data/criteres.yml`**, pas dans le
HTML. Le bloc JS est *généré*, jamais rendu par Liquid : c'est ce qui préserve
l'invariant « aucun Liquid dans le corps ».

```
just collecte    # rejoue tous les collecteurs (réseau requis)
just notes       # recalcule les notes depuis _data/*.json
just donnees     # réinjecte _data/criteres.yml dans le bloc JS
just artifact    # régénère report.body.html
```

Un **skill par critère outillé** documente la méthode, les pièges vérifiés et
la commande : voir `.claude/skills/critere-*/`.

Le barème est **relatif au panel classé** : les notes s'étalent de 1 à 10 sur
les seules villes en lice, les villes de référence étant placées sur la même
échelle. Changer la liste de villes recalibre tout automatiquement.

Chaque entrée de `_data/` doit porter : la valeur, l'URL de la source, la date
de collecte, et l'unité.

### Fichiers

| Fichier | Rôle |
|---|---|
| `_includes/report-body.html` | **source unique** du corps + du `<script>` |
| `_includes/report-head.html` | `<title>`, polices, CSS |
| `_layouts/report.html` | assemble les deux pour Jekyll |
| `index.html` | front matter + `{% include report-body.html %}` |
| `report.body.html` | **généré** par `just artifact` — ne jamais l'éditer à la main |

Ne pas introduire de Liquid (`{{`, `{%`) dans `report-body.html` : le fichier
n'en contient aucun, ce qui garantit que le JS traverse Jekyll intact et que le
fragment Artifact reste identique au site.

### Commandes

```
just init      # dépendances système + gems + polices
just serve     # http://localhost:4000, livereload
just build     # _site/, comme GitHub Pages
just artifact  # régénère report.body.html   ← après toute édition des includes
```

---

## Invariants du classement

Le `<script>` en fin de `report-body.html` porte trois garde-fous. Ne pas les
retirer :

1. **Identifiants de critère uniques** — deux critères partageant un `id`
   écrasent mutuellement leur poids et génèrent des `id` DOM en double. Lève une
   erreur au chargement.
2. **Note manquante signalée** — `console.warn` pour chaque couple
   ville × critère sans note.
3. **`render()` ignore les critères non renseignés** et normalise sur les poids
   effectivement appliqués, au lieu de propager un `NaN`.

Après toute modification du script : `node --check` sur le contenu du `<script>`,
puis vérifier que les cinq villes affichent un score numérique.

### Ajouter un critère — checklist

1. Identifier la source publique **avant** d'écrire la section.
2. Ajouter la section HTML **avant** la Synthèse et la Conclusion (les critères
   14 et 15 ont été insérés après : à corriger).
3. `CRITERES` : un `id` neuf, unique, et un poids par défaut.
4. `VILLES` : une note pour **les cinq villes**, sans exception.
5. Documenter la formule donnée → note en commentaire au-dessus de `VILLES`.
6. Mettre à jour le nombre de critères (chapô, byline, `index.html`,
   `_config.yml`) et les scores du verdict.
7. Ajouter la source au bloc « Sources » en fin de rapport.
8. `just artifact`.

---

## Catalogue des sources vérifiées

Toutes testées de bout en bout. Codes INSEE du panel :
Rennes **35238** (35) · Grenoble **38185** (38) · Chambéry **73065** (73) ·
Montpellier **34172** (34) · Toulon **83137** (83).

### Climat — Météo-France, données climatologiques de base
Bucket S3 ouvert, sans clé. Mensuelles par département :
```
https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/BASE/MENS/MENSQ_<dep>_previous-1950-2024.csv.gz
https://object.files.data.gouv.fr/meteofrance/data/synchro_ftp/BASE/MENS/MENSQ_<dep>_latest-2025-2026.csv.gz
```
CSV `;`, colonnes `NUM_POSTE;NOM_USUEL;LAT;LON;ALTI;AAAAMM;RR;…;TM;TX;…`.
Vérifié : Rennes-St Jacques 1991-2020 → 12,4 °C, 691 mm/an, 1762 h de soleil —
identique aux normales publiées par Infoclimat, mais depuis la source officielle.

- Préférer `NBJTX30`, `NBJTX35`, nuits tropicales à une simple moyenne : plus
  décisif pour un déménagement.
- **Piège : `INST` (ensoleillement) est en minutes**, pas en heures.
- Filtrer sur une station de référence par ville, pas sur tout le département.

### Qualité de l'air — Geod'air / LCSQA
Clé obligatoire (header `apikey`). **La documentation du site donne de fausses
routes** ; le spec réel est à `https://www.geodair.fr/api-ext/swagger.yaml`.
Export en deux temps :
```
GET https://www.geodair.fr/api-ext/statistique/export
    ?departement=35&polluant=39&type_donnee=a7
    &date_debut=01/01/2025 00:00&date_fin=31/12/2025 23:00     → renvoie un id
GET https://www.geodair.fr/api-ext/download?id=<id>            → CSV
```
Codes utiles — statistique : `a7` moyenne annuelle, `a2` moyenne journalière,
`a10` max journalier horaire. Polluants : `39` PM2.5, `03` NO2, `24` PM10.
Référentiels : `api-ext/polluant/export`, `api-ext/type-donnees/export?codes_polluants=39`.

- Le CSV donne le **type d'influence** (Fond / Trafic) et d'implantation
  (Urbaine / Périurbaine) : ne comparer que des stations **de fond urbaines**.
- Moyenne sur 3 ans plutôt qu'une année isolée.
- Le producteur demande **une seule requête par date, polluant et statistique** :
  mise en cache dans `_data/` obligatoire, pas d'appel à chaque build.

### Emploi — API Recherche d'entreprises
Sans clé, sans quota déclaré.
```
GET https://recherche-entreprises.api.gouv.fr/search
    ?activite_principale=62.01Z&code_commune=35238&etat_administratif=A&per_page=1
```
Lire `total_results`. Filtres utiles : `code_commune` (accepte une **liste
séparée par des virgules** → périmètre EPCI), `activite_principale` (NAF),
`est_association=true` (statut associatif, avec le n° RNA dans
`complements.identifiant_association`), `etat_administratif=A` (actifs).

Croisements pertinents pour ce rapport :
- DevOps : `62.01Z` programmation, `62.02A` conseil en systèmes, `63.11Z` traitement de données.
- CIP : `88.99B` action sociale sans hébergement, et son croisement avec
  `est_association=true` — l'insertion est majoritairement portée par des associations.

- **Raisonner à l'échelle de l'EPCI, pas de la commune** : un bassin d'emploi
  déborde largement la ville-centre.
- **Normaliser par habitant** : sinon on mesure la taille de la ville.
- **Piège : `total_results` plafonne à 10 000.** Au-delà, affiner les filtres ou
  afficher « > 10 000 ».
- Compte des entreprises **domiciliées**, pas des offres d'emploi : c'est un
  indicateur de densité de bassin, pas de tension du marché.

### Eau potable — Hub'Eau
Sans clé.
```
GET https://hubeau.eaufrance.fr/api/v1/qualite_eau_potable/resultats_dis
    ?code_commune=35238&code_parametre=1340&size=100&sort=desc
```
`1340` = nitrates. Champs : `date_prelevement`, `resultat_numerique`,
`libelle_unite`, `nom_distributeur`, `conclusion_conformite_prelevement`.

- **Ne jamais afficher un prélèvement isolé** : trois relevés rennais
  consécutifs donnent 14,9 / 15,7 / 18,6 mg/L. Utiliser une moyenne glissante
  12 mois, plus le taux de conformité sur la période.
- Une commune peut être desservie par plusieurs réseaux : le préciser.

### Logement — Carte des loyers (DHUP / data.gouv)
Couvre les 34 900 communes, ce qui permet de calculer un vrai rayon de 15 km au
lieu de l'approximer par la ville-centre.
```
GET https://www.data.gouv.fr/api/1/datasets/carte-des-loyers-indicateurs-de-loyers-dannonce-par-commune-en-2025/
→ ressource CSV « Indicateurs de loyer appartement »
```
Colonnes : `INSEE_C;LIBGEO;EPCI;DEP;REG;loypredm2;lwr.IPm2;upr.IPm2;nbobs_com`.

- **Piège : encodage `latin-1`**, séparateur `;`, décimales à la **virgule**.
- Toujours afficher l'intervalle de confiance (`lwr`/`upr`) : la prédiction seule
  donne une fausse précision.
- Centroïdes pour le rayon : `https://geo.api.gouv.fr/communes?code=<insee>&fields=nom,centre,population,surface`.

### Élus — RNE (data.gouv)
```
GET https://www.data.gouv.fr/api/1/datasets/repertoire-national-des-elus-1/
→ ressource « elus-maires-mai.csv »
```
Vérifié : les cinq maires du panel, mandats du 22/03/2026. Clé de jointure :
`Code du département` + `Code de la commune` (à zéro-padder en code INSEE).

- **Le RNE ne contient pas l'étiquette politique.** Elle doit venir des
  résultats officiels des municipales, ou être assumée comme lecture personnelle.

### Risques — Géorisques
```
GET https://georisques.gouv.fr/api/v1/gaspar/risques?code_insee=38185
```
Sans clé. Liste les risques recensés par commune.

---

## Sources écartées

| Source | Raison |
|---|---|
| **API Entreprise** | réservée aux administrations — accès non ouvert |
| **La Grande Carte** | clé distincte, impossible à protéger sur un site statique public |
| **API Melodi (Insee)** | nécessite un compte portail-api.insee.fr — à évaluer si besoin de données socio-éco |
| **BAN, RGE, Réf. organisation administrative** | sans rapport avec les 15 critères |
| **HelloWork, Indeed, PAP, blogs immobiliers** | sources secondaires non reproductibles → à remplacer par les jeux officiels ci-dessus |
| **Wikipédia (monuments historiques)** | acceptable en attendant la base Mérimée, mais à citer comme source secondaire |

---

## Secrets

**Aucune clé API dans le dépôt.** La clé Geod'air se lit depuis
l'environnement :

- en local : `.env.local` (git-ignoré), variable `GEODAIR_API_KEY` ;
- en CI : GitHub Secret `GEODAIR_API_KEY`, injecté dans le workflow.

Une clé qui a été écrite en clair dans un fichier du dépôt, un message ou un log
est compromise : la faire tourner sur https://www.geodair.fr/donnees/api.

---

## État des critères

| # | Critère | Source actuelle | Cible |
|---|---|---|---|
| 1-2 | Emploi DevOps / CIP | HelloWork, Indeed | Recherche d'entreprises (EPCI, par habitant) |
| 3 | Logement 15 km | blogs, observatoires locaux | Carte des loyers DHUP + rayon réel |
| 4-5 | Piéton, vie de centre | villes.plus, Wikipédia, presse | à consolider |
| 6-7 | Vélo, embouteillages | Baromètre FUB, TomTom | acceptables (méthodo publiée) |
| 8 | Climat | Infoclimat | **Météo-France MENS** |
| 9 | Qualité de l'air | Geod'air (manuel) | **Geod'air automatisé, `a7`, station de fond** |
| 10-12 | Environnement, falaise, mer & lac | PNR, Oblyk, FFME, tourisme | à consolider |
| 13 | Risques | Géorisques (manuel) | **API GASPAR** |
| 14 | Eau du robinet | Hub'Eau, prélèvement unique | **moyenne 12 mois + conformité** |
| 15 | Affinité politique | RNE + lecture personnelle | RNE (vérifié) + résultats municipales |

---

## Hors rapport — listes de candidature

Deux listes d'employeurs vivent dans `candidatures/`, produites par des scripts,
jamais écrites à la main. Elles ne sont pas publiées par Jekyll et n'entrent dans
aucun critère : c'est un usage personnel du même outillage.

| Commande | Sortie | Source |
|---|---|---|
| `just candidatures grenoble` | `candidatures/devops-grenoble.{json,md}` | API Recherche d'entreprises, 3 EPCI × 17 codes NAF, ≥ 20 salariés |
| `just candidatures montpellier` | `candidatures/devops-montpellier.{json,md}` | idem, 6 EPCI (métropole + couronne) |
| `just remote` | `candidatures/devops-remote.{json,md}` | 7 places de marché du travail à distance (~3 min, Himalayas cadence à 1 req/s) |

Ajouter un bassin : une entrée dans `BASSINS` (`scripts/candidatures_devops.py`),
une sélection dans `SELECTIONS` et une ligne dans `ECOSYSTEMES`
(`scripts/candidatures_markdown.py`). Les codes NAF sont communs aux deux villes,
`59.12Z` compris : **Ubisoft Montpellier est déclaré en post-production
audiovisuelle**, pas en édition de jeux — le code NAF est déclaratif.

La règle d'or s'applique : `scripts/candidatures_markdown.py` désigne les
entreprises par un fragment de raison sociale et **échoue** si le fragment ne
correspond pas à exactement une entreprise du JSON — impossible d'ajouter un nom
qui ne serait pas dans la source. Le tri éditorial et les commentaires en
italique sont assumés comme tels dans l'en-tête des fichiers.

Différence entre les deux : le registre des entreprises est stable, les offres
d'emploi tournent en quelques semaines. Les annotations de
`scripts/candidatures_remote_markdown.py` sont donc *facultatives* — appliquées
si l'entreprise est encore dans le flux, ignorées sinon.
