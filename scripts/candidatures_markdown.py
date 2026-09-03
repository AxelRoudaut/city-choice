#!/usr/bin/env python3
"""Met en forme candidatures/devops-grenoble.json en liste de candidature spontanée.

La sélection ci-dessous est un tri éditorial : les entreprises retenues sont
désignées par un fragment de leur raison sociale, et le script échoue si ce
fragment ne correspond pas à exactement une entreprise du JSON. Aucun nom,
aucun effectif, aucune commune n'est saisi à la main.
"""
import json, pathlib, sys, datetime

RACINE = pathlib.Path(__file__).resolve().parents[1]

# Écosystèmes locaux, par bassin : ce qui ne se trouve pas dans un registre.
ECOSYSTEMES = {
    "grenoble":
        "Inovallée (technopole Meylan / Montbonnot), le campus GIANT–Minatec (CEA, ST, Soitec), "
        "la French Tech Grenoble Alpes, le cluster Digital League",
    "montpellier":
        "Cap Oméga (l'incubateur du BIC de la métropole), le cluster Digital 113, "
        "la French Tech Méditerranée, le quartier Cambacérès et son écosystème de studios",
}

# Adjectif du lieu, pour les phrases où « le site local » sonne creux.
GENTILE = {"grenoble": ("grenoblois", "grenobloise"),
           "montpellier": ("montpelliérain", "montpelliéraine")}

# (fragment de raison sociale, commentaire éditorial)
# Le commentaire est une lecture personnelle, pas une donnée : voir l'avertissement.
SELECTION_GRENOBLE = [
 ("Cœur de cible — infra, cloud, hébergement",
  "Des boîtes dont le métier *est* l'exploitation : le poste DevOps y est structurel, pas un à-côté.",
  [("VATES", "éditeur de XCP-ng / Xen Orchestra, virtualisation open source"),
   ("AGARIK", "hébergeur infogéreur (groupe Bouygues Telecom)"),
   ("ALPILINK CLOUD", "hébergeur régional, datacenter local"),
   ("ALPILINK", "opérateur / intégrateur réseau régional"),
   ("NEPTUNE INTERNET SERVICES", "hébergement et infogérance, historique grenoblois"),
   ("DCS EASYWARE", "infogérance et services managés"),
   ("JILITI", "maintenance et infogérance d'infrastructures"),
   ("ECONOCOM APPS", "entité cloud & data d'Econocom"),
   ("SPIE ICS", "infrastructures et services numériques"),
   ("NXO FRANCE", "intégrateur réseau, télécoms, sécurité"),
   ("T-SYSTEMS", "infogérance, filiale Deutsche Telekom"),
   ("KOESIO MANAGED SERVICES", "services managés"),
   ("SOPRA STERIA INFRASTRUCTURE", "l'entité infra & sécurité du groupe, présente à Grenoble"),
   ("WORLDLINE", "paiement — production critique 24/7"),
   ("RAYNET", "gestion d'installations informatiques"),
   ("VMWARE", "site grenoblois historique (virtualisation)"),
   ("TIBCO", "intégration et middleware")]),

 ("Éditeurs et produits — DevOps sur son propre système",
  "Le cas le plus confortable : une seule plateforme, qu'on connaît, qu'on fait grandir.",
  [("ENALEAN", "éditeur de Tuleap, open source"),
   ("BONITASOFT", "éditeur BPM open source"),
   ("LEDGER", "sécurité crypto — site grenoblois de R&D"),
   ("CRITEO TECHNOLOGY", "adtech, très forte culture infra et données"),
   ("CEGID", "ERP et paie en SaaS"),
   ("SAGE", "logiciels de gestion"),
   ("SBS SOFTWARE", "logiciels bancaires, ex-Sopra Banking"),
   ("EASYVISTA", "ITSM — éditeur né à Grenoble"),
   ("QUESTEL", "propriété intellectuelle, plateforme SaaS"),
   ("ATEME", "compression et diffusion vidéo"),
   ("CORYS", "simulateurs industriels temps réel"),
   ("DIABELOOP", "dispositif médical connecté (pancréas artificiel)"),
   ("KBRW", "plateforme commerce/logistique"),
   ("CITYWAY", "information voyageur et mobilité"),
   ("BASSETTI", "logiciel de gestion des connaissances techniques"),
   ("HORIZONTAL SOFTWARE", "SIRH SaaS"),
   ("WIZBII", "plateforme emploi jeunes"),
   ("ELOQUANT", "relation client SaaS"),
   ("DIGIMIND", "veille et social listening"),
   ("KELKOO", "comparateur — trafic et volumétrie"),
   ("SOGELINK ENGINEERING", "logiciels réseaux et travaux publics"),
   ("SEPTEO REAL ESTATE", "logiciels immobilier"),
   ("WEBMECANIK", "marketing automation open source"),
   ("KOSMOS", "plateformes pour l'enseignement"),
   ("ARC INFORMATIQUE", "éditeur de PcVue (SCADA)"),
   ("METROLOGIC GROUP", "logiciels de métrologie 3D"),
   ("ALLEGRO DVT", "IP vidéo pour semi-conducteurs"),
   ("74SOFTWARE", "éditeur (ex-Berger-Levrault Software)"),
   ("TALENTIA SOFTWARE", "finance et RH"),
   ("SILVACO", "EDA — simulation de semi-conducteurs"),
   ("COMARCH R&D", "centre de R&D à Montbonnot"),
   ("MOODY'S ANALYTICS", "risque financier"),
   ("INFOR (FRANCE) SAS", "ERP"),
   ("PING IDENTITY", "gestion d'identité"),
   ("UNITY TECHNOLOGIES", "moteur 3D"),
   ("INTEL CORPORATION", "site de R&D"),
   ("ORACLE FRANCE", "site de R&D et de services"),
   ("SALESFORCE", "site de R&D"),
   ("DATADOG", "observabilité — l'outillage même du métier"),
   ("GOOGLE FRANCE", "site local — effectif groupe, pas grenoblois"),
   ("COMPAGNIE IBM", "site d'Eybens, historique"),
   ("DASSAULT SYSTEMES", "site de R&D"),
   ("SIEMENS ELECTRONIC DESIGN", "EDA, ex-Mentor Graphics"),
   ("SYNOPSYS", "EDA — émulation et vérification"),
   ("ANSYS", "simulation numérique"),
   ("AUTODESK", "site de R&D"),
   ("PARAMETRIC TECHNOLOGY", "PTC — PLM et CAO")]),

 ("Semi-conducteurs, instrumentation, énergie",
  "Le tissu industriel grenoblois. Postes DevOps/IT côté CI, fermes de calcul, chaînes de test.",
  [("STMICROELECTRONICS (CROLLES 2)", "l'usine de Crolles"),
   ("STMICROELECTRONICS FRANCE", "siège français, Grenoble"),
   ("STMICROELECTRONICS (GRENOBLE 2)", "R&D Grenoble"),
   ("STMICROELECTRONICS (ALPS)", "R&D Grenoble"),
   ("SOITEC", "substrats SOI — siège à Grenoble, usine à Bernin"),
   ("LYNRED", "détecteurs infrarouges"),
   ("ALEDIA", "micro-LED — scale-up deeptech"),
   ("TELEDYNE E2V SEMICONDUCTORS", "imageurs et composants spatiaux"),
   ("NXP SEMICONDUCTORS", "R&D Grenoble"),
   ("QUALCOMM FRANCE", "R&D Grenoble"),
   ("ARM FRANCE", "R&D Grenoble"),
   ("FEI", "microscopie électronique (Thermo Fisher), Crolles"),
   ("SCHNEIDER ELECTRIC FRANCE", "premier employeur industriel de la métropole"),
   ("SCHNEIDER ELECTRIC ENERGY", "entité énergie du groupe"),
   ("GRID SOLUTIONS", "réseaux électriques (GE Vernova)"),
   ("SOCOMEC", "onduleurs et coupure"),
   ("HAGER ELECTRO", "appareillage électrique"),
   ("HORIBA FRANCE", "instrumentation de mesure"),
   ("CAMECA", "instrumentation scientifique"),
   ("SERCEL", "instrumentation géophysique"),
   ("CHAUVIN ARNOUX", "mesure électrique"),
   ("BIO LOGIC", "instrumentation électrochimie"),
   ("C-TEC CONSTELLIUM", "centre de recherche aluminium")]),

 ("Recherche publique et grands instruments",
  "Beaucoup d'ingénierie système, de HPC et de stockage. Recrutement par concours ou CDD de projet : "
  "la candidature spontanée y marche moins bien qu'une veille sur leurs portails emploi.",
  [("COMMISSARIAT A L' ENERGIE ATOMIQUE", "CEA Grenoble — Leti, Liten"),
   ("INSTITUT NATIONAL DE RECHERCHE EN INFORMATIQ", "Inria, centre de Grenoble"),
   ("CENTRE NATIONAL DE LA RECHERCHE SCIENTIFIQUE", "CNRS, délégation Alpes"),
   ("EUROPEAN SYNCHROTRON", "ESRF — synchrotron, gros volumes de données"),
   ("INSTITUT MAX VON LAUE", "ILL — réacteur à neutrons"),
   ("INSTITUT NATIONAL DE LA SANTE", "Inserm, La Tronche"),
   ("INSTITUT NATIONAL DE RECHERCHE POUR L'AGRICU", "INRAE, Saint-Martin-d'Hères"),
   ("CTRE SCIENTIFIQUE TECHNIQUE DU BATIMENT", "CSTB"),
   ("BRGM", "géosciences"),
   ("CETIM", "centre technique des industries mécaniques"),
   ("AGENCE MUTUALISATION UNIVERSITES", "AMUE — SI des universités, Gières")]),

 ("ESN et conseil",
  "Le volume est ici, et la candidature spontanée y est la norme. Contrepartie : la mission est chez "
  "le client, et la qualité du poste dépend entièrement du compte sur lequel on est placé.",
  [("ZENIKA", "conseil et formation, forte culture technique"),
   ("SMILE", "open source"),
   ("HARDIS GROUPE", "ESN grenobloise historique + éditeur (Reflex WMS)"),
   ("VISEO", "ESN née à Grenoble"),
   ("ALTECA", "ESN régionale"),
   ("SULLY GROUP", ""),
   ("COEXYA", ""),
   ("NORSYS", "ESN à gouvernance atypique"),
   ("KAIZEN SOLUTIONS", "ESN grenobloise"),
   ("AVISTO", ""),
   ("ADENTIS", ""),
   ("AMARIS", ""),
   ("EXAKIS NELITE", "écosystème Microsoft/Azure"),
   ("CLOUDITY", "intégrateur Salesforce"),
   ("VIVERIS SYSTEMES", ""),
   ("VIVERIS TECHNOLOGIES", ""),
   ("SOGILIS", "petite structure, exigence technique revendiquée"),
   ("ECEDI", "web et services publics"),
   ("PROBAYES", "IA appliquée"),
   ("BLUEBEARSIT", ""),
   ("WIDIP", ""),
   ("IT - NEWVISION", ""),
   ("NEVERHACK FRANCE", "cybersécurité"),
   ("CAPGEMINI TECHNOLOGY SERVICES", ""),
   ("SOPRA STERIA GROUP", ""),
   ("ATOS FRANCE", ""),
   ("EVIDEN FRANCE", "ex-Atos Big Data & Security"),
   ("BULL SAS", "HPC, entité du groupe"),
   ("EVIDIAN", "gestion d'identité"),
   ("CGI FRANCE", ""),
   ("INETUM", ""),
   ("ALTEN", ""),
   ("ALTRAN TECHNOLOGIES", ""),
   ("AKKODIS DIGITAL", ""),
   ("OPEN", ""),
   ("ASTEK FRANCE", ""),
   ("THALES SERVICES NUMERIQUES", ""),
   ("ORANGE BUSINESS SERVICES", ""),
   ("SOCIETE POUR L'INFORMATIQUE INDUSTRIELLE", "le groupe SII"),
   ("EXPERIS FRANCE", ""),
   ("RANDSTAD DIGITAL", ""),
   ("COGNIZANT", ""),
   ("CS GROUP", "systèmes critiques"),
   ("WORLDGRID", "systèmes pour l'énergie"),
   ("SEGULA", ""),
   ("EXPLEO", ""),
   ("SERMA INGENIERIE", "sécurité et électronique"),
   ("BERTIN TECHNOLOGIES", "systèmes et instrumentation"),
   ("ELSYS DESIGN", "conception électronique"),
   ("EASII IC", "conception électronique"),
   ("MEDIANE SYSTEME", "embarqué"),
   ("KICKMAKER", "industrialisation produit")]),
]

SELECTION_MONTPELLIER = [
 ("Cœur de cible — infra, cloud, hébergement",
  "Des boîtes dont le métier *est* l'exploitation. Montpellier a une vraie densité d'hébergeurs "
  "et d'infogéreurs, et deux directions informatiques bancaires qui pèsent lourd.",
  [("ITS INTEGRA", "hébergeur, agréé données de santé"),
   ("IPGARDE", "cloud et infogérance"),
   ("BEEMO TECHNOLOGIE", "sauvegarde et PRA en ligne"),
   ("ADISTA", "opérateur et hébergeur"),
   ("FREE PRO", "ex-Jaguar Network — opérateur et datacenters"),
   ("SEWAN", "opérateur télécom et cloud"),
   ("EUROFIBER FRANCE", "opérateur d'infrastructure fibre"),
   ("CHEOPS TECHNOLOGY FRANCE", "intégrateur et infogéreur"),
   ("SEA TPI", "infogérance et centre de services"),
   ("DCS EASYWARE", "infogérance et services managés"),
   ("JILITI", "maintenance et infogérance d'infrastructures"),
   ("ECONOCOM APPS, CLOUD & DATA", "entité cloud & data d'Econocom"),
   ("ITS GROUP", "infrastructures et services"),
   ("KYNDRYL FRANCE", "ex-infogérance IBM — le site de Montpellier est historique"),
   ("CREDIT AGRICOLE-GROUP INFRASTRUCTURE PLATFORM", "CA-GIP : l'infrastructure du groupe"),
   ("CREDIT AGRICOLE TECHNOLOGIES ET SERVICES", "l'informatique du Crédit Agricole"),
   ("EURO INFORMATION DEVELOPPEMENTS", "le développement du groupe Crédit Mutuel"),
   ("SOPRA STERIA INFRASTRUCTURE & SECURITY SERVICES", "l'entité infra & sécurité du groupe"),
   ("WORLDLINE", "paiement — production critique 24/7"),
   ("DOCAPOSTE BPO", "traitement de données, groupe La Poste"),
   ("NXO FRANCE", "intégrateur réseau, télécoms, sécurité"),
   ("SYSTELCOM", "Axians — intégration réseau"),
   ("HID GLOBAL SAS", "identité et contrôle d'accès")]),

 ("Éditeurs et produits — DevOps sur son propre système",
  "Le cas le plus confortable : une seule plateforme, qu'on connaît, qu'on fait grandir. "
  "Montpellier en compte beaucoup, dont deux plateformes à très fort trafic.",
  [("TEADS FRANCE", "publicité vidéo — l'infrastructure la plus lourde de la ville"),
   ("DAILYMOTION", "plateforme vidéo"),
   ("ZENDESK FRANCE", "ex-We Are Cloud (Bime) — relation client SaaS"),
   ("BOOKING.COM (FRANCE) SAS", "site de développement"),
   ("CODERPAD FRANCE", "plateforme d'entretiens techniques"),
   ("DOCKER FRANCE", "oui, à Sète — l'outil au cœur du métier"),
   ("LEDGER", "sécurité crypto"),
   ("DATADOG FRANCE", "observabilité — l'outillage même du métier"),
   ("GOOGLE FRANCE", "site local — effectif groupe, pas montpelliérain"),
   ("INTEL CORPORATION SAS", "site de R&D"),
   ("DASSAULT SYSTEMES", "site de R&D"),
   ("SYNOPSYS EMULATION AND VERIFICATION", "EDA — émulation et vérification"),
   ("COMPAGNIE IBM FRANCE", "site historique"),
   ("SAGE", "logiciels de gestion"),
   ("CEGID", "ERP et paie en SaaS"),
   ("SBS SOFTWARE", "logiciels bancaires, ex-Sopra Banking"),
   ("SOPRA HR SOFTWARE", "SIRH"),
   ("BERGER LEVRAULT", "logiciels du secteur public"),
   ("SEPTEO SOLUTIONS NOTAIRES", "groupe Septeo — logiciels métier, siège à Lattes"),
   ("SEPTEO HOSPITALITY SOLUTIONS", "groupe Septeo — hôtellerie"),
   ("SEPTEO IT SOLUTIONS", "groupe Septeo — l'entité infrastructure"),
   ("IVALUA", "achats en SaaS"),
   ("QUESTEL", "propriété intellectuelle"),
   ("EQUASENS", "logiciels pour la pharmacie"),
   ("ESRI FRANCE", "SIG — ArcGIS"),
   ("SILAE", "paie en SaaS"),
   ("SMAG", "logiciels agricoles"),
   ("HOROQUARTZ", "gestion des temps"),
   ("LUNDIMATIN", "caisse et commerce"),
   ("TECLIB", "éditeur de GLPI — open source"),
   ("TIXEO", "visioconférence chiffrée, qualifiée par l'ANSSI"),
   ("IOTEROP", "IoT — piles LwM2M"),
   ("PRADEO SECURITY SYSTEMS", "sécurité mobile"),
   ("DEVENSYS", "cybersécurité"),
   ("SOPHIA GENETICS", "analyse génomique — calcul lourd"),
   ("INTRASENSE", "imagerie médicale"),
   ("COMPUGROUP MEDICAL SOLUTIONS", "logiciels de santé"),
   ("MEDINCELL", "biotech"),
   ("TALKSPIRIT", "réseau social d'entreprise"),
   ("AGILITATION", "Axeptio — gestion du consentement"),
   ("NUMALIS", "vérification d'IA"),
   ("WEFIGHT", "santé, assistant virtuel"),
   ("ODIGO", "centre de contact en SaaS"),
   ("ALTARES - D & B", "données d'entreprises"),
   ("GROUPE LA CENTRALE", "La Centrale, Caradisiac — trafic important"),
   ("DIGITAL CLASSIFIEDS FRANCE", "petites annonces en ligne"),
   ("CHAPSVISION", "traitement de données souverain"),
   ("OCEASOFT", "Dickson — capteurs connectés"),
   ("HORIBA ABX SAS", "diagnostic in vitro — Horiba Medical"),
   ("TAGEOS", "étiquettes RFID"),
   ("CORTUS", "processeurs embarqués"),
   ("SEMCO TECHNOLOGIES", "équipements pour semi-conducteurs")]),

 ("Jeu vidéo",
  "La particularité montpelliéraine, sans équivalent à Grenoble. Un studio, c'est des fermes de "
  "build, du stockage massif et des pipelines : le DevOps y a un nom différent, pas un métier "
  "différent. Attention aux codes NAF — Ubisoft Montpellier est déclaré en post-production "
  "audiovisuelle, pas en édition de jeux.",
  [("UBISOFT MONTPELLIER", "le plus gros studio de la ville"),
   ("NACON", "éditeur et studios"),
   ("SANDFALL INTERACTIVE", "studio monté en 2020"),
   ("PLAYDIGIOUS", "portage et édition"),
   ("MAGIC DESIGN STUDIOS", "studio indépendant"),
   ("MIDGAR STUDIO", "studio indépendant"),
   ("VOODOO", "jeu mobile — très gros volumes"),
   ("BUILD A ROCKET BOY FRANCE", "antenne française du studio britannique"),
   ("DIGIXART ENTERTAINMENT", "studio indépendant"),
   ("ARTISAN STUDIOS", "studio indépendant"),
   ("GAME SOURCE STUDIO", "prestation pour studios")]),

 ("Recherche publique et instituts",
  "Montpellier est un pôle mondial d'agronomie et d'environnement : beaucoup de données, de "
  "calcul et de stockage. Recrutement par concours ou CDD de projet — la veille sur leurs "
  "portails emploi marche mieux que la candidature spontanée.",
  [("CENTRE NATIONAL DE LA RECHERCHE SCIENTIFIQUE", "CNRS, délégation Occitanie Est"),
   ("INSTITUT NATIONAL DE RECHERCHE POUR L'AGRICULTURE L'ALIMENTATION ET L'ENVIRONNEMENT", "INRAE"),
   ("CTRE COOP INTERNAT RECHERCHE AGRO DEV", "CIRAD — agronomie tropicale"),
   ("INSTITUT DE RECHERCHE POUR LE DEVELOPPEMENT", "IRD"),
   ("INSTITUT NATIONAL DE LA SANTE ET DE LA RECHERCHE MEDICALE", "Inserm"),
   ("INSTITUT FRANCAIS DE RECHERCHE POUR L EXPLOITATION DE LA MER", "Ifremer"),
   ("BRGM", "géosciences"),
   ("AGENCE NATIONALE DE SECURITE SANITAIRE DE L ALIMENTATION DE L ENVIRONNEMENT ET DU TRAVAIL",
    "Anses — sécurité sanitaire"),
   ("SANOFI-AVENTIS RECHERCHE ET DEVELOPPEMENT", "R&D pharmaceutique"),
   ("AGENCE MUTUALISATION UNIVERSITES", "AMUE — SI des universités"),
   ("AGENCE BIBLIOGRAPHIQUE DE L'ENSEIGNEMENT SUPERIEUR", "ABES — infrastructure documentaire nationale")]),

 ("ESN et conseil",
  "Le volume est ici, et la candidature spontanée y est la norme. Contrepartie : la mission est "
  "chez le client, et la qualité du poste dépend entièrement du compte sur lequel on est placé.",
  [("SMILE", "open source"),
   ("SQLI", ""),
   ("KEYRUS", "données et BI"),
   ("CONSERTO", "ESN régionale"),
   ("MERITIS", ""),
   ("KLANIK", ""),
   ("DAVIDSON PACA", "l'entité sud de Davidson"),
   ("CELAD", ""),
   ("CATAMANIA", ""),
   ("ALTECA", ""),
   ("AMARIS FRANCE SAS", ""),
   ("VIVERIS TECHNOLOGIES", ""),
   ("IT LINK FRANCE", "systèmes embarqués et connectés"),
   ("HENIX", "test et qualification logicielle"),
   ("INSIDE", ""),
   ("ABSYS CYBORG", "écosystème Microsoft"),
   ("PRODWARE SA", ""),
   ("FIDUCIAL INFORMATIQUE", ""),
   ("ACELYS SERVICES NUMERIQUES", "ESN locale"),
   ("KALIOP FRANCE", "web et applicatif"),
   ("ANTADIS", "e-commerce open source"),
   ("AISI", "infrastructure et cloud"),
   ("NEXT DECISION", "données"),
   ("SOFTWAREONE FRANCE SAS", "licences et cloud"),
   ("EXTIA", ""),
   ("EPSYL", "ingénierie, groupe Alcen"),
   ("ORANGE CYBERDEFENSE FRANCE", "cybersécurité"),
   ("CAPGEMINI TECHNOLOGY SERVICES", ""),
   ("SOPRA STERIA GROUP", ""),
   ("CGI FRANCE", ""),
   ("ATOS FRANCE", ""),
   ("EVIDEN FRANCE", "ex-Atos Big Data & Security"),
   ("BULL SAS", "HPC, entité du groupe"),
   ("INETUM", ""),
   ("ALTEN", ""),
   ("ALTRAN TECHNOLOGIES", ""),
   ("AKKODIS I&S SAS", ""),
   ("ASTEK FRANCE", ""),
   ("SOCIETE POUR L'INFORMATIQUE INDUSTRIELLE", "le groupe SII"),
   ("RANDSTAD DIGITAL FRANCE", ""),
   ("EXPERIS FRANCE", ""),
   ("ORANGE BUSINESS SERVICES", ""),
   ("SEGULA ENGINEERING", "")]),
]

SELECTIONS = {"grenoble": SELECTION_GRENOBLE, "montpellier": SELECTION_MONTPELLIER}


def trouve(entreprises, fragment):
    """Un fragment doit désigner une entreprise et une seule, sinon on s'arrête :
    c'est ce qui garantit qu'aucun nom de la liste n'a été écrit à la main."""
    frag = fragment.upper().strip()
    # « SOITEC » attrape aussi « SOITEC LAB », « BASSETTI » aussi « BASSETTI TALENT
    # POOL » : la raison sociale exacte, parenthèses d'enseigne retirées, tranche.
    exact = [e for e in entreprises if (e["nom"] or "").split(" (")[0].upper() == frag]
    m = exact or [e for e in entreprises if frag in (e["nom"] or "").upper()]
    if len(m) != 1:
        raise SystemExit(f"« {fragment} » → {len(m)} correspondance(s) : "
                         + ", ".join(x["nom"] for x in m[:6]))
    return m[0]


def commune(nom):
    """MEYLAN → Meylan, SAINT-MARTIN-D'HERES → Saint-Martin-d'Heres.
    Les accents manquent à la source : on ne les invente pas."""
    t = (nom or "").title()
    for p in ("-D'", "-Le-", "-La-", "-Les-", "-Sur-", "-En-", "-De-"):
        t = t.replace(p, p.lower())
    return t


def main():
    slug = (sys.argv[1] if len(sys.argv) > 1 else "grenoble").lower()
    if slug not in SELECTIONS:
        raise SystemExit(f"bassin inconnu : {slug} — choisir parmi {', '.join(SELECTIONS)}")
    src = RACINE / "candidatures" / f"devops-{slug}.json"
    dest = RACINE / "candidatures" / f"devops-{slug}.md"
    d = json.loads(src.read_text())
    ents = d["entreprises"]
    retenus, out = set(), []
    A = out.append

    A(f"# Candidature spontanée DevOps — {d['bassin']}\n")
    A(f"*Liste établie le {datetime.date.today().strftime('%d/%m/%Y')} à partir de l'annuaire "
      "des entreprises (API Recherche d'entreprises, data.gouv.fr). "
      f"Régénérable : `just candidatures {slug}`.*\n")

    A("## Ce que cette liste est, et ce qu'elle n'est pas\n")
    A("**Les colonnes chiffrées viennent d'une source publique** : raison sociale, commune "
      "d'implantation, tranche d'effectif Insee et SIREN sortent tels quels de l'annuaire des "
      "entreprises. Aucun nom n'a été inventé, aucun effectif estimé.\n")
    A("**Les commentaires en italique sont ma lecture**, pas une donnée : ils disent pourquoi "
      "l'entreprise m'a semblé intéressante pour un poste DevOps. À vérifier avant d'écrire.\n")
    A("Trois limites à garder en tête :\n")
    masc, fem = GENTILE[slug]
    A(f"- **La tranche d'effectif est celle de l'entreprise entière, pas du site {masc}.** "
      "Datadog ou Google pèsent des milliers de salariés dont une poignée ici. "
      f"Inversement, un « 20-49 » local est parfois une équipe entièrement {fem}.\n"
      "- **L'annuaire recense des entreprises domiciliées, pas des postes ouverts.** C'est une "
      "carte du bassin d'emploi, pas un fil d'offres.\n"
      "- **Le code NAF est déclaratif** et parfois à côté de la plaque. Le filtre a retenu "
      "l'informatique, l'édition de logiciels et de jeux, les semi-conducteurs, l'ingénierie, "
      "la R&D et les télécoms ; "
      f"il en reste **{len(ents)} entreprises** de 20 salariés et plus, dont la sélection "
      "ci-dessous est un extrait.\n")
    A("Périmètre : " + ", ".join(d["epci"].values()) + ".\n")

    A("## Sélection\n")
    for titre, chapo, items in SELECTIONS[slug]:
        A(f"### {titre}\n")
        A(chapo + "\n")
        A("| Entreprise | Commune | Effectif (groupe) | Fiche | |")
        A("|---|---|---|---|---|")
        for frag, note in items:
            e = trouve(ents, frag)
            if e["siren"] in retenus:
                raise SystemExit(f"« {frag} » : {e['nom']} est déjà dans la liste")
            A(f"| **{e['nom']}** | {commune(e['commune'])} | {e['effectif']} | "
              f"[{e['siren']}]({e['annuaire']}) | {f'*{note}*' if note else ''} |")
            retenus.add(e["siren"])
        A("")

    A("## Comment s'y prendre\n")
    A("1. **Le SIREN est la clé de vérification.** La fiche liée donne le siège, les "
      "établissements, la date de création et les dirigeants — de quoi savoir à qui on écrit et "
      f"si le site {masc} est un vrai centre ou une adresse commerciale.\n"
      f"2. **Viser l'établissement local, pas le siège.** Beaucoup de ces entreprises ont leur "
      "siège à Paris ou Lyon ; la décision d'embauche d'un DevOps se prend souvent au niveau du "
      "site, auprès du responsable technique.\n"
      f"3. **Écosystèmes locaux à explorer en parallèle** : {ECOSYSTEMES[slug]}. Leurs annuaires "
      "d'adhérents recoupent utilement cette liste et exposent des structures trop petites pour "
      "le filtre des 20 salariés.\n"
      "4. **Les très petites structures sont hors liste par construction.** Le filtre commence à "
      "20 salariés ; en dessous, l'annuaire remonte surtout des indépendants. Pour viser plus "
      "petit, relancer le collecteur en abaissant `TRANCHES` dans "
      "`scripts/candidatures_devops.py`.\n")

    reste = [e for e in ents if e["siren"] not in retenus]
    A("## Annexe — les autres entreprises du filtre\n")
    A(f"Les {len(reste)} entreprises restantes, non triées : beaucoup de bureaux d'études "
      "bâtiment et de sociétés hors sujet, mais aussi des noms que je ne connais pas et qui "
      f"méritent un coup d'œil. Le fichier `devops-{slug}.json` contient les mêmes données "
      "avec les adresses complètes.\n")
    A("| Entreprise | Commune | Effectif | Activité | Fiche |")
    A("|---|---|---|---|---|")
    for e in reste:
        A(f"| {e['nom']} | {commune(e['commune'])} | {e['effectif']} | {e['naf_libelle']} | "
          f"[{e['siren']}]({e['annuaire']}) |")
    A("")
    A(f"---\n\nSource : {d['source']} — {d['url']} · collecte du {d['collecte']}.  \n"
      f"Méthode : {d['methode']}\n")

    dest.write_text("\n".join(out))
    print(f"  {len(retenus)} entreprises sélectionnées, {len(reste)} en annexe → "
          f"{dest.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
