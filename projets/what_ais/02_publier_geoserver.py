"""Étape 2 : publie les couches de la base what_ais_carto dans le GeoServer de la pile MapStore.

Espace de travail what_ais, entrepôt PostGIS carto, un style SLD par couche (styles.py), titres et
résumés bilingues (catalogue.py). Idempotent : relancer met à jour sans dupliquer.
"""
from catalogue import COUCHES, FOND
import donnees_recit
from donnees_tableau import TABLES
from commun import ENTREPOT, ESPACE, NAMESPACE_URI, PG, PG_DEPUIS_DOCKER, env, geoserver
from styles import styles

MOTS_CLES = ["AIS", "maritime", "Danemark", "Baltique", "What AIS doesn't show"]


def espace(gs):
    if not gs.existe(f"/workspaces/{ESPACE}.json"):
        gs.requete("POST", "/namespaces", {"namespace": {"prefix": ESPACE, "uri": NAMESPACE_URI}})
    gs.requete("PUT", f"/namespaces/{ESPACE}", {"namespace": {"prefix": ESPACE, "uri": NAMESPACE_URI}})
    print(f"espace de travail {ESPACE}")


def entrepot(gs):
    parametres = {
        "dbtype": "postgis", "host": PG_DEPUIS_DOCKER, "port": str(PG["port"]), "database": PG["dbname"],
        "schema": PG["schema"], "user": PG["user"], "passwd": env()["WHAT_AIS_DB_PASSWORD"],
        "Expose primary keys": "true", "Loose bbox": "true", "Estimated extends": "false",
        "encode functions": "true", "Support on the fly geometry simplification": "true",
        "validate connections": "true", "max connections": "10", "min connections": "1",
    }
    corps = {"dataStore": {"name": ENTREPOT, "description": "Couches publiées de What AIS doesn't show (PostGIS)",
                           "enabled": True, "connectionParameters": {
                               "entry": [{"@key": k, "$": v} for k, v in parametres.items()]}}}
    chemin = f"/workspaces/{ESPACE}/datastores"
    if gs.existe(f"{chemin}/{ENTREPOT}.json"):
        gs.requete("PUT", f"{chemin}/{ENTREPOT}", corps)
    else:
        gs.requete("POST", chemin, corps)
    print(f"entrepôt {ENTREPOT} -> {PG['dbname']}.{PG['schema']} sur {PG_DEPUIS_DOCKER}")


def publier_styles(gs):
    chemin = f"/workspaces/{ESPACE}/styles"
    tous = {**styles(), **donnees_recit.styles()}
    for nom, sld in tous.items():
        if gs.existe(f"{chemin}/{nom}.json"):
            gs.requete("PUT", f"{chemin}/{nom}", sld, type_contenu="application/vnd.ogc.sld+xml")
        else:
            gs.requete("POST", f"{chemin}?name={nom}", sld, type_contenu="application/vnd.ogc.sld+xml")
    print(f"{len(tous)} styles")


def couche(gs, c):
    nom = c["nom"]
    ft = {"featureType": {
        "name": nom, "nativeName": nom, "enabled": True, "srs": "EPSG:4326", "projectionPolicy": "FORCE_DECLARED",
        "title": c["titre"][0], "abstract": c["resume"][0],
        "internationalTitle": {"fr": c["titre"][0], "en": c["titre"][1]},
        "internationalAbstract": {"fr": c["resume"][0], "en": c["resume"][1]},
        "keywords": {"string": MOTS_CLES},
    }}
    chemin = f"/workspaces/{ESPACE}/datastores/{ENTREPOT}/featuretypes"
    if gs.existe(f"{chemin}/{nom}.json"):
        gs.requete("PUT", f"{chemin}/{nom}?recalculate=nativebbox,latlonbbox", ft)
    else:
        gs.requete("POST", chemin, ft)
    gs.requete("PUT", f"/layers/{ESPACE}:{nom}", {"layer": {
        "defaultStyle": {"name": c["style"], "workspace": ESPACE},
        "attribution": {"title": "What AIS doesn't show · données ouvertes",
                        "href": "https://github.com/jauresmas/what-ais-doesnt-show"}}})


def main():
    gs = geoserver()
    espace(gs)
    entrepot(gs)
    publier_styles(gs)
    for c in COUCHES + [FOND] + TABLES + donnees_recit.TABLES:
        couche(gs, c)
        print(f"  couche {ESPACE}:{c['nom']} (style {c['style']})")


if __name__ == "__main__":
    main()
