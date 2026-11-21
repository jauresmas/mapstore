# De PostGIS à la carte : la chaîne de publication

Trois scripts Python, sans dépendance hors bibliothèque standard, dans `projets/what_ais/`. Chacun est
idempotent : le relancer met à jour sans dupliquer.

```powershell
python projets\what_ais\01_charger_postgis.py
```

```powershell
python projets\what_ais\02_publier_geoserver.py
```

```powershell
python projets\what_ais\03_publier_mapstore.py
```

```
carto.gpkg, traces.gpkg, GISCO, bilans JSON
        │ 01 : ogr2ogr, SQL
        ▼
PostGIS what_ais_carto.carto ── tables, vues des signaux, libellés français, bilans, cas des récits
        │ 02 : API REST de GeoServer
        ▼
GeoServer : espace what_ais, entrepôt PostGIS, 31 styles SLD, couches titrées FR/EN
        │ 03 : API REST GeoStore de MapStore
        ▼
MapStore : carte → application dédiée → tableau de bord → GeoStory
```

## Étape 1 : charger PostGIS

`01_charger_postgis.py` remplit la base `what_ais_carto`, schéma `carto` :

- les 23 couches d'affichage de `carto.gpkg` et les traces de `traces.gpkg`, par l'`ogr2ogr` de QGIS
  (index spatiaux, géométrie `geom`) ;
- `terre_large` : les pays GISCO découpés sur une emprise large et fondus en un seul polygone, pour que le
  fond de carte ne s'arrête pas au cadre de l'aire d'étude quand on dézoome ;
- `libelles_fr.sql` : colonnes mises en forme en français pour les fiches d'information (dates, durées,
  distances) et les vues des cinq signaux, avec les mêmes filtres que le projet QGIS du dépôt ;
- `donnees_tableau.py` : tables des bilans chiffrés (compteurs, causes, semaines, validation radar) tirées
  des fichiers JSON du dépôt ;
- `donnees_recit.py` : couches des cas racontés par la GeoStory (`carte/donnees/recits.json`).

Les tables sont remplacées à chaque passage ; le script vide ensuite le cache de GeoServer pour qu'il ne
garde pas l'ancien schéma.

## Étape 2 : configurer GeoServer

`02_publier_geoserver.py` passe par l'API REST de GeoServer (`/geoserver/rest`) :

- espace de travail `what_ais` et entrepôt PostGIS `carto`, qui se connecte à
  `host.docker.internal:5432` avec le rôle `what_ais` ;
- 31 styles SLD générés par `styles.py` et `donnees_recit.py`, qui reprennent la palette et les symboles du
  projet QGIS du dépôt (palette lisible par les daltoniens, épaisseurs converties des millimètres aux
  pixels) ;
- une couche par table ou vue, avec titre et résumé en français et en anglais (repris par le catalogue et
  la légende de MapStore).

## Étape 3 : créer les ressources MapStore

`03_publier_mapstore.py` écrit directement dans l'API GeoStore de MapStore
(`/mapstore/rest/geostore`), avec le compte `admin`. Les ressources sont retrouvées par catégorie et par
nom : leurs identifiants ne changent pas d'une publication à l'autre. Toutes sont en lecture pour tous
(visiteurs anonymes compris) et en écriture pour `admin`.

```powershell
python projets\what_ais\03_publier_mapstore.py carte
```

publie seulement la carte et l'application ; `tableau` ou `recit` publient l'un des deux autres, et
`adresses` affiche les adresses des pages déjà publiées.

### La carte (`carte.py`, `catalogue.py`)

Configuration MapStore au format version 2, générée entièrement :

- 23 couches WMS en 8 groupes (Repères, Signaux, Tous les silences AIS, Indicateurs, Quatre semaines,
  Infrastructures en mer, Limites, Traces des navires), avec titres FR/EN, ordre, visibilité initiale ;
- emprise de chaque couche lue dans GeoServer (zoom sur la couche) ;
- fiches d'information au clic : champs choisis et libellés en français (`catalogue.py`) ;
- 5 fonds : fond du projet (terres GISCO servies par GeoServer), CARTO Positron sans étiquettes,
  Esri Océans, OpenStreetMap, fond vide ;
- signets vers les zones commentées (rade de Skagen, bassin d'Arkona, Øresund…) ;
- une présentation (ressource liée de catégorie `DETAILS`) ouverte au chargement, et une vignette rendue
  par le WMS de GeoServer.

### L'application dédiée (`contexte.py`)

Un **contexte** MapStore : une application à l'adresse `#/context/what-ais-doesnt-show/<id>`, qui embarque
la carte et ses propres outils :

- les outils du visualiseur standard de la version installée, lus dans `localConfig.json`, moins ceux qui
  ne servent pas ici (impression, 3D, temps, annotations, enregistrement…) ;
- un logotype SVG dans le bandeau (symbole du silence inexpliqué et titre bilingue) ;
- les couleurs du projet (variables de thème, contrastes AA) et une légende WMS en Segoe UI ;
- fiches d'information sans édition, mesures sans annotation.

### Le tableau de bord (`tableau_de_bord.py`, `donnees_tableau.py`)

Grille de 6 colonnes (une sur mobile) :

- un texte de lecture (chiffres clés, résumé anglais en italique) ;
- 8 compteurs (navires suivis, silences, dus aux trous de réception, inexpliqués, MMSI partagés, passages
  lents sur câble, rencontres, détections radar sans AIS), calculés par GeoServer (WPS `gs:Aggregate`) ;
- une carte des signaux, reprise de la carte publiée ;
- 3 graphiques : causes des silences (échelle logarithmique, couleur par classe), quatre semaines de
  comparaison, validation par le radar Sentinel-1 ;
- le tableau des 11 silences inexpliqués, colonnes renommées en français.

### La GeoStory (`recit.py`, `donnees_recit.py`)

Une couverture, une introduction, quatre récits immersifs et une conclusion :

1. Un angle mort confirmé par satellite ;
2. Un navire de pêche silencieux et un écho radar ;
3. Une identité, deux émetteurs ;
4. Chronique ou ponctuel ? (quatre semaines).

Chaque étape a sa propre carte (ressource de la GeoStory) cadrée par une emprise explicite, élargie à
l'ouest pour laisser la place à la colonne de texte, avec seulement les couches utiles à l'étape et une
légende en HTML dans le texte.

## Adapter la chaîne à un autre projet

`projets/what_ais/` sert de modèle :

| À changer | Où |
|---|---|
| sources et tables chargées | `01_charger_postgis.py`, `libelles_fr.sql` |
| styles | `styles.py` (SLD générés en Python) |
| couches, groupes, fiches, signets | `catalogue.py` |
| outils et apparence de l'application | `contexte.py` |
| widgets du tableau de bord | `tableau_de_bord.py` |
| récits | `recit.py` |

`commun.py` (chemins, client REST) et `ressources.py` (création, mise à jour, droits, présentation et
vignettes des ressources MapStore) se réutilisent tels quels. Créer une base, un rôle et une clé de mot
de passe par projet, sur le modèle de `sql/02_…` et de `WHAT_AIS_DB_PASSWORD`.

## Captures d'écran

Les images de la documentation se refont après une publication :

```powershell
node outils\captures.mjs
```

Le script pilote Edge ou Chrome sans fenêtre (protocole DevTools), attend que le réseau soit au repos et
écrit `docs/images/*.png`.
