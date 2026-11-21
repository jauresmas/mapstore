"""Configuration MapStore de la carte « What AIS doesn't show » (format de carte version 2).

Utilisée telle quelle par la ressource carte, par l'application dédiée (contexte) et, avec des
couches allumées ou éteintes selon l'étape, par la GeoStory.
"""
import copy
import urllib.parse

from catalogue import COUCHES, FOND, GROUPES, SIGNETS
from commun import ESPACE

WMS = "/geoserver/wms"
WFS = "/geoserver/wfs"
LANGUES = ("fr-FR", "en-US", "it-IT", "de-DE", "es-ES", "nl-NL")


def titre(fr, en):
    """Titre localisé MapStore : français par défaut, anglais pour l'interface en anglais."""
    t = {"default": fr}
    for langue in LANGUES:
        t[langue] = en if langue == "en-US" else fr
    return t


# Ordre d'affichage, du dessous vers le dessus ; chaque groupe reste d'un seul tenant dans la table des matières
ORDRE = ["traces", "indicateurs", "semaines", "infrastructures", "limites", "silences", "signaux", "reperes"]
DANS_GROUPE = {  # ordre interne, du dessous vers le dessus
    "indicateurs": ["trafic", "couverture", "lacunes_reception", "indice_signale"],
    "semaines": ["recurrence_couverture", "foyer_recurrent", "inexpliquee_semaines"],
    "infrastructures": ["mouillage", "parc_eolien", "infrastructure"],
    "limites": ["mer_territoriale", "zone_fiche", "zone_etude", "limite_zee"],
    "signaux": ["signal_radar_sans_ais", "stationnement_infra", "rencontre", "signal_mmsi_partage",
                "signal_silence_inexplique"],
    "reperes": ["station_ais", "lieu"],
}
OPACITE = {"trafic": 0.85, "couverture": 0.9, "recurrence_couverture": 0.9}


def couche_wms(c, emprises=None, visible=None):
    nom = c["nom"]
    couche = {
        "id": f"{ESPACE}__{nom}",
        "type": "wms",
        "url": WMS,
        "name": f"{ESPACE}:{nom}",
        "title": titre(*c["titre"]),
        "description": c["resume"][0],
        "group": c["groupe"],
        "visibility": c["visible"] if visible is None else visible,
        "opacity": OPACITE.get(nom, 1),
        "format": "image/png",
        "transparent": True,
        "tiled": True,
        "singleTile": False,
        "search": {"type": "wfs", "url": WFS},
        "featureInfo": {"format": "TEMPLATE", "template": c["fiche"]} if c.get("fiche") else {"format": "HIDDEN"},
        "params": {},
        "dimensions": [],
        "allowedSRS": {"EPSG:3857": True, "EPSG:900913": True, "EPSG:4326": True},
    }
    if emprises and nom in emprises:
        o, s, e, n = emprises[nom]
        couche["bbox"] = {"crs": "EPSG:4326", "bounds": {"minx": o, "miny": s, "maxx": e, "maxy": n}}
    return couche


def fonds():
    vignette = WMS + "?" + urllib.parse.urlencode({
        "SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "LAYERS": f"{ESPACE}:{FOND['nom']}", "STYLES": "",
        "SRS": "EPSG:4326", "BBOX": "8.5,53.5,17,58.5", "WIDTH": 120, "HEIGHT": 80, "FORMAT": "image/png",
        "TRANSPARENT": "false", "BGCOLOR": "0xEDF1F3"})
    return [
        {"id": "fond_projet", "type": "wms", "url": WMS, "name": f"{ESPACE}:{FOND['nom']}", "group": "background",
         "title": titre("Fond du projet (terres et mer)", "Project basemap (land and sea)"),
         "visibility": True, "format": "image/png", "transparent": False, "tiled": True,
         "params": {"BGCOLOR": "0xEDF1F3"}, "thumbURL": vignette, "featureInfo": {"format": "HIDDEN"},
         "dimensions": []},
        {"id": "carto_positron", "type": "tileprovider", "provider": "CartoDB.PositronNoLabels",
         "name": "PositronNoLabels", "source": "CartoDB", "group": "background",
         "title": titre("CARTO Positron (sans étiquettes)", "CARTO Positron (no labels)"), "visibility": False},
        {"id": "esri_ocean", "type": "tileprovider", "provider": "Esri.OceanBasemap", "name": "OceanBasemap",
         "source": "Esri", "group": "background", "title": titre("Esri Océans", "Esri Ocean"), "visibility": False},
        {"id": "osm", "type": "osm", "source": "osm", "name": "mapnik", "group": "background",
         "title": titre("OpenStreetMap", "OpenStreetMap"), "visibility": False},
        {"id": "fond_vide", "type": "empty", "source": "ol", "name": "empty", "group": "background",
         "title": titre("Fond vide", "Empty background"), "visibility": False},
    ]


def couches(emprises=None, visibles=None):
    """visibles : ensemble de noms de couches à allumer (les autres éteintes) ; None = état par défaut."""
    par_nom = {c["nom"]: c for c in COUCHES}
    liste = []
    for g in ORDRE:
        noms = DANS_GROUPE.get(g, [c["nom"] for c in COUCHES if c["groupe"] == g])
        for nom in noms:
            v = None if visibles is None else (nom in visibles)
            liste.append(couche_wms(par_nom[nom], emprises, v))
    return liste


def groupes():
    return [{"id": gid, "title": titre(fr, en), "expanded": deplie} for gid, fr, en, deplie in GROUPES]


def signets():
    return {"bookmarks": [{"options": {"west": o, "south": s, "east": e, "north": n}, "title": fr,
                           "layerVisibilityReload": False} for fr, _en, o, s, e, n in SIGNETS],
            "zoomOnSelect": True}


def config_carte(emprises=None, centre=(12.75, 56.05), zoom=8, visibles=None, fond="fond_projet"):
    fonds_ = fonds()
    for f in fonds_:
        f["visibility"] = f["id"] == fond
    return {
        "version": 2,
        "map": {
            "projection": "EPSG:900913",
            "units": "m",
            "center": {"x": centre[0], "y": centre[1], "crs": "EPSG:4326"},
            "zoom": zoom,
            "maxExtent": [-20037508.34, -20037508.34, 20037508.34, 20037508.34],
            "mapOptions": {},
            "layers": fonds_ + couches(emprises, visibles),
            "groups": groupes(),
            "backgrounds": [],
            "bookmark_search_config": signets(),
            "text_search_config": None,
        },
        "catalogServices": {
            "services": {
                "what_ais": {"url": f"/geoserver/{ESPACE}/wms", "type": "wms", "autoload": True,
                             "title": "What AIS doesn't show (GeoServer)"},
            },
            "selectedService": "what_ais",
        },
        "mapInfoConfiguration": {"trigger": "click", "infoFormat": "text/html", "showEmptyMessageGFI": False},
        "widgetsConfig": {"widgets": [], "layouts": {"md": [], "xxs": []}},
        "dimensionData": {},
        "timelineData": {},
    }


def copie(conf):
    return copy.deepcopy(conf)
