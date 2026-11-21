"""Étape 1 : charge les couches d'affichage pseudonymisées dans PostGIS (base what_ais_carto, schéma carto).

Source : les GeoPackages produits par la chaîne du dépôt (06_export_gpkg.py). Relancer ce script
remplace les tables : à refaire après une régénération des données.
"""
import os
import shutil
import subprocess
import sys

import donnees_recit
import donnees_tableau
from commun import CARTO_GPKG, GISCO, ICI, PG, PSQL, QGIS, TRACES_GPKG, env, geoserver, verifier_depot

# Couches de carto.gpkg utilisées par la carte (les variantes propres à l'atlas QGIS sont laissées de côté)
COUCHES = [
    "terre", "lieu", "zone_etude", "zee", "limite_zee", "mer_territoriale", "station_ais",
    "trafic", "couverture", "lacunes_reception", "indice_vigilance", "recurrence_couverture",
    "foyer_inexpliquees", "inexpliquee_semaines", "infrastructure", "parc_eolien", "mouillage",
    "silence_ais", "saut_position", "stationnement_infra", "rencontre", "detection_radar", "zone_fiche",
]


def ogr2ogr(source, couches, *options):
    environnement = dict(os.environ, PGPASSWORD=env()["WHAT_AIS_DB_PASSWORD"], PGCLIENTENCODING="UTF8")
    if QGIS:
        # ogr2ogr de QGIS (Windows) : ses DLL, données GDAL et PROJ
        environnement.update(PATH=f"{QGIS / 'bin'}{os.pathsep}{os.environ['PATH']}",
                             GDAL_DATA=str(QGIS / "apps" / "gdal" / "share" / "gdal"),
                             PROJ_LIB=str(QGIS / "share" / "proj"))
        programme = str(QGIS / "bin" / "ogr2ogr.exe")
    else:
        programme = shutil.which("ogr2ogr") or sys.exit("ogr2ogr introuvable : installer QGIS ou GDAL, "
                                                         "ou renseigner QGIS_DIR dans .env")
    cible = f"PG:host={PG['host']} port={PG['port']} dbname={PG['dbname']} user={PG['user']}"
    commande = [programme, "-f", "PostgreSQL", cible, str(source), *couches,
                "-overwrite", "-lco", f"SCHEMA={PG['schema']}", "-lco", "GEOMETRY_NAME=geom",
                "-lco", "FID=fid", "-lco", "SPATIAL_INDEX=GIST", "-lco", "PRECISION=NO",
                "--config", "PG_USE_COPY", "YES", *options]
    print(f"ogr2ogr {source.name} -> {PG['dbname']}.{PG['schema']} ({len(couches)} couches)")
    subprocess.run(commande, env=environnement, check=True)


def psql(sql):
    environnement = dict(os.environ, PGPASSWORD=env()["WHAT_AIS_DB_PASSWORD"], PGCLIENTENCODING="UTF8")
    # SQL envoyé par l'entrée standard, en UTF-8 : un argument -c passerait par la page de code
    # Windows et abîmerait les accents
    r = subprocess.run([str(PSQL), "-h", PG["host"], "-p", str(PG["port"]), "-U", PG["user"], "-d", PG["dbname"],
                        "-v", "ON_ERROR_STOP=1", "-At", "-q", "-f", "-"],
                       input=sql, env=environnement, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        sys.exit(r.stderr)
    return r.stdout.strip()


EMPRISE_FOND = ("2", "51", "26", "62")  # ouest, sud, est, nord
VUES = ["signal_silence_inexplique", "signal_mmsi_partage", "signal_radar_sans_ais", "foyer_recurrent",
        "indice_signale", "bilan_etude", "tableau_silences_inexpliques", "recit_radar_validation"]


def terre_large():
    """Fond de carte : terres GISCO sur une emprise large, fondues en un seul polygone, pour que le fond ne
    s'arrête pas au cadre de carto.gpkg quand on dézoome."""
    ogr2ogr(GISCO, [], "-nln", "terre_large_brut", "-nlt", "MULTIPOLYGON", "-select", "CNTR_ID",
            "-spat", *EMPRISE_FOND, "-clipsrc", "spat_extent")
    psql(f"""SET search_path = {PG['schema']}, public;
DROP TABLE IF EXISTS terre_large;
CREATE TABLE terre_large AS
SELECT 1 AS fid, ST_Multi(ST_UnaryUnion(ST_Collect(ST_MakeValid(geom))))::geometry(MultiPolygon, 4326) AS geom
FROM terre_large_brut;
ALTER TABLE terre_large ADD PRIMARY KEY (fid);
CREATE INDEX ON terre_large USING gist (geom);
DROP TABLE terre_large_brut;""")


def main():
    verifier_depot()
    # les vues de libelles_fr.sql empêcheraient ogr2ogr de remplacer leurs tables
    psql(";".join(f"DROP VIEW IF EXISTS {PG['schema']}.{v}" for v in VUES))
    ogr2ogr(CARTO_GPKG, COUCHES)
    ogr2ogr(TRACES_GPKG, ["trace"])
    terre_large()
    # Libellés français et valeurs mises en forme pour les fiches d'information et les graphiques
    psql((ICI / "libelles_fr.sql").read_text(encoding="utf-8"))
    # Bilans chiffrés du dépôt pour le tableau de bord (compteurs, graphiques, tableau)
    psql(donnees_tableau.sql())
    # Cas racontés par la GeoStory (carte/donnees/recits.json du dépôt)
    psql(donnees_recit.sql())
    print(psql("SELECT string_agg(relname || '=' || n_live_tup, ', ' ORDER BY relname) "
               "FROM pg_stat_user_tables WHERE schemaname = 'carto'"))
    # Les tables ont été remplacées : GeoServer doit oublier ses connexions et schémas en cache
    # (sinon les premiers graphiques WPS du tableau de bord peuvent échouer)
    try:
        geoserver().requete("POST", "/reset", ok=(200,))
        print("cache GeoServer vidé")
    except (OSError, RuntimeError):
        print("GeoServer injoignable : cache non vidé (normal avant le premier « docker compose up »)")


if __name__ == "__main__":
    main()
