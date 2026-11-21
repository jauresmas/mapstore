"""Paramètres et outils communs à la publication de « What AIS doesn't show » dans MapStore.

Bibliothèque standard uniquement. Les mots de passe sont lus dans le .env de la pile (racine du dépôt,
créé par configurer.py), jamais écrits dans ces scripts.
"""
import base64
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request
from functools import cache
from pathlib import Path

ICI = Path(__file__).resolve().parent
PILE = ICI.parents[1]                       # racine de la pile (docker-compose.yml, .env)


@cache
def env():
    """Variables du .env de la pile (KEY=valeur), sans les exporter."""
    fichier = PILE / ".env"
    if not fichier.exists():
        sys.exit(f"{fichier} absent : lancer d'abord « python configurer.py » à la racine de la pile")
    valeurs = {}
    for ligne in fichier.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if ligne and not ligne.startswith("#") and "=" in ligne:
            cle, val = ligne.split("=", 1)
            valeurs[cle.strip()] = val.strip()
    return valeurs


def parametre(cle, defaut=None):
    """Variable d'environnement, sinon valeur du .env, sinon valeur par défaut."""
    return os.environ.get(cle) or env().get(cle) or defaut


def _version(chemin):
    return [int(n) for n in re.findall(r"\d+", chemin.name)] or [0]


def _qgis():
    """Dossier QGIS (son ogr2ogr apporte le pilote GeoPackage et PROJ), ou None si ogr2ogr est au PATH."""
    if valeur := parametre("QGIS_DIR"):
        return Path(valeur)
    installes = sorted(Path(os.environ.get("ProgramFiles", r"C:\Program Files")).glob("QGIS 3*"), key=_version)
    return installes[-1] if installes else None


def _psql():
    if valeur := parametre("PSQL"):
        return Path(valeur)
    if chemin := shutil.which("psql"):
        return Path(chemin)
    racine = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "PostgreSQL"
    installes = sorted((p.parents[1] for p in racine.glob("*/bin/psql.exe")), key=_version)
    return installes[-1] / "bin" / "psql.exe" if installes else Path("psql")


# Clone local du dépôt What AIS doesn't show, lu seulement (par défaut à côté de la pile)
DEPOT = Path(parametre("WHAT_AIS_DEPOT", PILE.parent / "what-ais-doesnt-show"))
# Pays Eurostat GISCO 1:1 M (© EuroGeographics) téléchargés par la chaîne du dépôt (03_referentiel.py)
GISCO = DEPOT / "donnees" / "brutes" / "referentiel" / "gisco_CNTR_RG_01M_2024_4326.geojson"
CARTO_GPKG = DEPOT / "donnees" / "produites" / "carto.gpkg"
TRACES_GPKG = DEPOT / "donnees" / "produites" / "traces.gpkg"
CARTE_DONNEES = DEPOT / "carte" / "donnees"

QGIS = _qgis()
PSQL = _psql()

# Base des couches publiées (créée par sql/02_creer_base_what_ais_carto.sql)
PG = {"host": "localhost", "port": 5432, "dbname": "what_ais_carto", "user": "what_ais", "schema": "carto"}
# La même base vue depuis le conteneur GeoServer
PG_DEPUIS_DOCKER = "host.docker.internal"

BASE_URL = parametre("PILE_URL", "http://localhost:8097").rstrip("/")
GEOSERVER = f"{BASE_URL}/geoserver"
MAPSTORE = f"{BASE_URL}/mapstore"
ESPACE = "what_ais"                         # espace de travail GeoServer
ENTREPOT = "carto"                          # entrepôt PostGIS
NAMESPACE_URI = "https://github.com/jauresmas/what-ais-doesnt-show"


def verifier_depot():
    manquants = [f for f in (CARTO_GPKG, TRACES_GPKG, GISCO, CARTE_DONNEES) if not f.exists()]
    if manquants:
        sys.exit("Dépôt What AIS doesn't show introuvable (WHAT_AIS_DEPOT dans .env) ou données pas encore "
                 "produites (traces.gpkg et le fichier GISCO viennent de sa chaîne : "
                 "python scripts/run_all.py --sans-semaines). Manquent :\n  " + "\n  ".join(map(str, manquants)))


class Http:
    """Client REST minimal avec authentification Basic."""

    def __init__(self, base, utilisateur, mot_de_passe):
        self.base = base.rstrip("/")
        jeton = base64.b64encode(f"{utilisateur}:{mot_de_passe}".encode()).decode()
        self.entetes = {"Authorization": f"Basic {jeton}"}

    def requete(self, methode, chemin, corps=None, type_contenu="application/json", accepter="application/json",
                ok=(200, 201)):
        url = chemin if chemin.startswith("http") else f"{self.base}{chemin}"
        if isinstance(corps, (dict, list)):
            corps = json.dumps(corps, ensure_ascii=False)
        donnees = corps.encode("utf-8") if isinstance(corps, str) else corps
        entetes = dict(self.entetes, Accept=accepter)
        if donnees is not None:
            entetes["Content-Type"] = type_contenu
        req = urllib.request.Request(url, data=donnees, method=methode, headers=entetes)
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                texte = r.read().decode("utf-8", "replace")
                statut = r.status
        except urllib.error.HTTPError as e:
            texte, statut = e.read().decode("utf-8", "replace"), e.code
        if ok and statut not in ok:
            raise RuntimeError(f"{methode} {url} -> HTTP {statut}\n{texte[:1500]}")
        return statut, texte

    def json(self, methode, chemin, corps=None, **kw):
        statut, texte = self.requete(methode, chemin, corps, **kw)
        return json.loads(texte) if texte.strip().startswith(("{", "[")) else texte

    def existe(self, chemin):
        statut, _ = self.requete("GET", chemin, ok=None)
        return statut == 200


def geoserver():
    return Http(f"{GEOSERVER}/rest", "admin", env()["GEOSERVER_ADMIN_PASSWORD"])


def mapstore():
    return Http(f"{MAPSTORE}/rest/geostore", "admin", env()["MAPSTORE_ADMIN_PASSWORD"])
