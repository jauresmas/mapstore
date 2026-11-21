# Installation pas à pas

Installation testée sous Windows 11 avec Docker Desktop. Sous Linux ou macOS, la pile Docker est la même ;
seuls changent l'installation de PostgreSQL et l'accès des conteneurs à la base (voir plus bas).

## 1. Prérequis

| Logiciel | Version testée | Sert à |
|---|---|---|
| Docker Desktop (WSL 2) | 4.x | MapStore, GeoServer, nginx |
| PostgreSQL + PostGIS | 15.10 + 3.5 (installeur EDB, puis Stack Builder pour PostGIS) | base des cartes MapStore et base des couches |
| QGIS | 3.34 LTR | son `ogr2ogr` charge les GeoPackages dans PostGIS (GDAL seul suffit aussi) |
| Python | 3.12 (3.10 minimum) | `configurer.py` et la chaîne de publication, bibliothèque standard seulement |
| Git | 2.x | cloner les deux dépôts |
| Node.js | 22 (facultatif) | captures d'écran de la documentation |

Mémoire : compter 3 Go libres pour la pile (MapStore environ 1,5 Go, GeoServer 1 Go de tas Java).

La pile publie sur **127.0.0.1:8097** : ce port doit être libre (sinon voir « Changer de port »).

## 2. Récupérer les deux dépôts

Cloner ce dépôt et, à côté, le dépôt du projet cartographié :

```powershell
git clone https://github.com/jauresmas/what-ais-doesnt-show.git
```

La chaîne de publication ne fait que **lire** ce dépôt. Elle a besoin de :

| Fichier | Origine |
|---|---|
| `donnees/produites/carto.gpkg` | versionné dans le dépôt |
| `carte/donnees/*.json` (bilans, récits) | versionnés dans le dépôt |
| `donnees/produites/traces.gpkg` | produit par la chaîne du dépôt (étape 06) |
| `donnees/brutes/referentiel/gisco_CNTR_RG_01M_2024_4326.geojson` | téléchargé par la chaîne du dépôt (étape 03) |

Les deux derniers ne sont pas versionnés : lancer une fois la chaîne du dépôt, qui a son propre README
(`python scripts/run_all.py --sans-semaines`, environ 40 minutes).

Si le dépôt n'est pas dans le même dossier parent que celui-ci, indiquer son chemin dans `.env`
(`WHAT_AIS_DEPOT`, avec des barres obliques `/`), après l'étape 3.

## 3. Configurer

```powershell
python configurer.py
```

Le script :

- crée `.env` à partir de `.env.example` et remplit chaque mot de passe vide par une valeur aléatoire
  (lettres et chiffres, 32 caractères). Les valeurs ne sont jamais affichées ; un `.env` existant est
  complété, jamais écrasé ;
- écrit `datadir/geostore-datasource-ovr.properties` (connexion de MapStore à sa base) à partir du modèle
  `.modele` et du mot de passe `MAPSTORE_DB_PASSWORD` ;
- copie la police Segoe UI de Windows dans `fonts/`, pour que les étiquettes et légendes de GeoServer
  aient la police du projet QGIS. Hors Windows, GeoServer prend sa police par défaut.

`.env` contient :

| Clé | Usage |
|---|---|
| `MAPSTORE_ADMIN_PASSWORD` | compte `admin` de MapStore, créé au premier démarrage ; utilisé par les scripts de publication |
| `MAPSTORE_DB_PASSWORD` | rôle PostgreSQL `mapstore` |
| `GEOSERVER_ADMIN_PASSWORD` | compte `admin` du GeoServer de la pile |
| `WHAT_AIS_DB_PASSWORD` | rôle PostgreSQL `what_ais`, lu par GeoServer et par les scripts |
| `WHAT_AIS_DEPOT` | chemin du dépôt What AIS (facultatif) |
| `QGIS_DIR`, `PSQL`, `PILE_URL` | facultatifs : détectés ou valeurs par défaut |

## 4. Créer les bases PostgreSQL

```powershell
python configurer.py bases
```

psql demande le mot de passe du superutilisateur `postgres` (tapé dans la console, jamais enregistré). Les
deux scripts de `sql/` lisent les mots de passe des rôles dans des variables d'environnement
(`\getenv`) et sont idempotents :

| Script | Crée |
|---|---|
| `sql/01_creer_base_mapstore.sql` | rôle `mapstore`, base `mapstore`, schéma `geostore`. MapStore y crée ses tables au premier démarrage (`hbm2ddl.auto=update`) |
| `sql/02_creer_base_what_ais_carto.sql` | rôle `what_ais`, base `what_ais_carto`, extension PostGIS, schéma `carto` |

### Accès des conteneurs à PostgreSQL

Les conteneurs joignent la base de la machine hôte par `host.docker.internal:5432`.

- **Docker Desktop (Windows, macOS)** : rien à faire, les connexions arrivent comme locales.
- **Linux** : `docker-compose.yml` déclare déjà `host.docker.internal:host-gateway`. Il faut en plus que
  PostgreSQL écoute sur l'interface du pont Docker (`listen_addresses = '*'` ou l'adresse du pont dans
  `postgresql.conf`) et l'autoriser dans `pg_hba.conf`, par exemple :

  ```
  host  mapstore        mapstore  172.16.0.0/12  scram-sha-256
  host  what_ais_carto  what_ais  172.16.0.0/12  scram-sha-256
  ```

## 5. Démarrer la pile

```powershell
docker compose up -d
```

| Conteneur | Image | Rôle |
|---|---|---|
| `mapstore` | `geosolutionsit/mapstore2:2026.03.00` | MapStore, avec `datadir/` monté comme dossier de configuration externe |
| `mapstore-geoserver` | `docker.osgeo.org/geoserver:2.28.6` | GeoServer avec l'extension WPS (graphiques du tableau de bord), installée au premier démarrage |
| `mapstore-proxy` | `nginx:alpine` | une seule adresse : `/mapstore/`, `/geoserver/`, `/pages/` |

Le premier démarrage prend quelques minutes (téléchargement des images, de l'extension WPS, création des
tables MapStore). Suivre avec :

```powershell
docker compose logs -f mapstore
```

### Ce que fait le dossier `datadir/`

MapStore lit au démarrage le dossier `/usr/local/tomcat/datadir` du conteneur, monté depuis `datadir/` :

- `geostore-datasource-ovr.properties` (généré) remplace la base H2 embarquée par PostgreSQL ;
- `configs/localConfig.json.patch` (JSON Patch appliqué à la configuration de MapStore) :
  - ajoute le GeoServer de la pile au catalogue et le sélectionne par défaut ;
  - configure l'avis de confidentialité : version de la politique et liens vers `pages/mentions.html`
    (sans ces liens, MapStore affiche un avertissement « politiques à configurer ») ;
  - retire le didacticiel automatique du tableau de bord et de la GeoStory.

## 6. Vérifier

| Vérification | Attendu |
|---|---|
| http://localhost:8097/mapstore/ | accueil MapStore ; connexion `admin` avec `MAPSTORE_ADMIN_PASSWORD` |
| http://localhost:8097/geoserver/web/ | GeoServer ; connexion `admin` avec `GEOSERVER_ADMIN_PASSWORD` |
| http://localhost:8097/geoserver/ows?service=WPS&request=GetCapabilities | XML des capacités WPS (sinon l'extension n'est pas installée) |
| http://localhost:8097/pages/mentions.html | page des mentions |

## 7. Publier le projet

Voir [publication.md](publication.md) : trois scripts chargent PostGIS, configurent GeoServer et créent
les ressources MapStore.

## Changer de port

Le port 8097 apparaît à trois endroits : `docker-compose.yml` (`127.0.0.1:8097:80`), les deux URL de
`datadir/configs/localConfig.json.patch`, et `PILE_URL` dans `.env` pour les scripts. Après le changement :
`docker compose up -d`, puis relancer `03_publier_mapstore.py`, car les cartes enregistrent l'adresse
de GeoServer.
