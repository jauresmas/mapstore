# « Ce que l'AIS ne montre pas » dans MapStore

Chaîne de publication du projet [What AIS doesn't show](https://github.com/jauresmas/what-ais-doesnt-show)
dans la pile MapStore de ce dépôt : une carte, une application dédiée, un tableau de bord et une
GeoStory, servis par le GeoServer de la pile depuis PostGIS (base `what_ais_carto`, schéma `carto`).

Le dépôt What AIS n'est que **lu** (chemin `WHAT_AIS_DEPOT` du `.env`, par défaut à côté de ce dépôt) : les
GeoPackages pseudonymisés `carto.gpkg` et `traces.gpkg`, les bilans `carte/donnees/*.json` et le fichier
des pays GISCO. Aucune donnée à MMSI réel n'est chargée.

Le fonctionnement de chaque étape est décrit dans [docs/publication.md](../../docs/publication.md).

## Ce qui est publié

| Ressource | Adresse | Contenu |
|---|---|---|
| Application dédiée | `#/context/what-ais-doesnt-show/<id carte>` | la carte avec le bandeau du projet, présentation à l'ouverture, fiches au clic, signets, légendes, interface FR/EN |
| Carte | `#/viewer/<id>` | 23 couches en 8 groupes, 5 fonds (fond du projet, CARTO, Esri, OSM, vide) |
| Tableau de bord | `#/dashboard/<id>` | 8 compteurs, carte des signaux, causes des silences, quatre semaines, validation radar, tableau des 11 silences inexpliqués |
| GeoStory | `#/geostory/<id>` | quatre récits (angle mort confirmé par satellite, navire de pêche silencieux, identité partagée, quatre semaines), une carte par étape |

Les identifiants dépendent de l'instance : `03_publier_mapstore.py` affiche les adresses complètes à la
fin, et `python 03_publier_mapstore.py adresses` les réaffiche. Toutes les ressources sont en lecture pour
tous (visiteurs anonymes compris) et en écriture pour `admin`.

## Chaîne de publication

Python 3.10+ (bibliothèque standard). Après `python configurer.py`, `python configurer.py bases` et
`docker compose up -d` à la racine du dépôt :

```powershell
python projets\what_ais\01_charger_postgis.py
```

```powershell
python projets\what_ais\02_publier_geoserver.py
```

```powershell
python projets\what_ais\03_publier_mapstore.py
```

| Étape | Fait | Relancer quand |
|---|---|---|
| `01_charger_postgis.py` | charge les GeoPackages dans `what_ais_carto.carto` (ogr2ogr de QGIS), la terre élargie GISCO, les libellés français (`libelles_fr.sql`), les bilans du tableau de bord (`donnees_tableau.py`) et les cas des récits (`donnees_recit.py`) | le dépôt a régénéré ses données |
| `02_publier_geoserver.py` | espace `what_ais`, entrepôt PostGIS `carto`, 31 styles SLD, toutes les couches avec titres et résumés FR/EN | un style, un titre ou une couche a changé |
| `03_publier_mapstore.py` | carte, application, tableau de bord, GeoStory, avec présentation et vignette | la mise en page a changé ; `carte`, `tableau` ou `recit` en argument pour n'en publier qu'une |

Les trois scripts sont idempotents : relancer met à jour sans dupliquer (les ressources MapStore sont
retrouvées par catégorie et par nom, leurs identifiants ne changent pas).

## Fichiers

| Fichier | Contenu |
|---|---|
| `commun.py` | chemins (lus dans `.env`, avec détection de QGIS et psql), connexions, client REST (GeoServer, MapStore/GeoStore) |
| `catalogue.py` | couches de la carte : groupes, titres et résumés FR/EN, fiches d'information, signets |
| `styles.py` | styles SLD de la carte (palette et symboles du projet QGIS du dépôt) |
| `libelles_fr.sql` | colonnes françaises mises en forme (dates, durées, distances) et vues des signaux |
| `carte.py` | configuration de la carte MapStore (format version 2) |
| `contexte.py` | application dédiée : outils, thème, logotype, légende |
| `textes.py` | textes de présentation (carte, tableau de bord) |
| `donnees_tableau.py`, `tableau_de_bord.py` | tables des bilans et widgets du tableau de bord |
| `donnees_recit.py`, `recit.py` | couches et styles des récits, GeoStory |
| `ressources.py` | création et mise à jour des ressources MapStore, droits, présentation, vignettes |

## Limites connues

- Les titres de widgets du tableau de bord et les textes de la GeoStory ne suivent pas la langue de
  l'interface (MapStore ne les traduit pas) : ils sont en français, avec un résumé anglais en italique.
- L'impression PDF n'est pas installée dans l'image MapStore : l'outil est retiré de l'application.
- Les graphiques du tableau de bord portent sur toute l'aire d'étude ; ils ne sont pas liés à l'emprise de
  la carte du tableau de bord.
- Les détections radar Global Fishing Watch sont sous licence CC BY-NC 4.0 : usage non commercial.
