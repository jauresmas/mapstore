"""Tableau de bord MapStore « Ce que l'AIS ne montre pas » : compteurs, graphiques (WPS gs:Aggregate du
GeoServer de la pile), carte des signaux et tableau des silences inexpliqués.

Grille MapStore : 6 colonnes (disposition « md »), une colonne sur petit écran (« xxs »).
"""
import uuid

import carte
from catalogue import COUCHES
from commun import ESPACE
from donnees_tableau import CAUSES_FR, TABLES
from textes import PRESENTATION_TABLEAU

NOM = "What AIS doesn't show · tableau de bord"
ESPACE_NOMS = uuid.UUID("6c1d4f0e-5b7a-4a52-9a43-0a1f2b3c4d5e")  # identifiants stables d'une publication à l'autre

ORANGE, VIOLET, BLEU, VERT_EAU = "#eb6834", "#4a3aa7", "#2a78d6", "#1baf7a"
ENCRE, ENCRE_2, GRIS, ACIER = "#1d1d1b", "#52514e", "#b8b0a2", "#5f7d95"

# Couches allumées dans la carte du tableau de bord
VISIBLES = {"zone_etude", "limite_zee", "lacunes_reception", "infrastructure", "parc_eolien",
            "signal_silence_inexplique", "signal_mmsi_partage", "stationnement_infra", "rencontre",
            "signal_radar_sans_ais", "lieu"}


def ident(nom):
    return str(uuid.uuid5(ESPACE_NOMS, nom))


def couche(nom):
    """Couche WMS/WFS du GeoServer de la pile, au format attendu par les widgets."""
    c = next((x for x in COUCHES + TABLES if x["nom"] == nom), None)
    return {"type": "wms", "url": carte.WMS, "visibility": True, "dimensions": [], "name": f"{ESPACE}:{nom}",
            "id": f"{ESPACE}__{nom}", "title": c["titre"][0] if c else nom, "description": c["resume"][0] if c else "",
            "params": {}, "allowedSRS": {}, "links": [], "search": {"type": "wfs", "url": carte.WFS}}


def compteur(nom, titre, attribut, x, y):
    return {"id": ident(nom), "widgetType": "counter", "title": titre, "mapSync": False, "legend": False,
            "layer": couche("bilan_etude"), "url": carte.WMS, "geomProp": "geom",
            "options": {"aggregationAttribute": attribut, "aggregateFunction": "Sum"},
            "dataGrid": {"x": x, "y": y, "w": 1, "h": 1}}


def classes(couleurs, defaut):
    return {"method": "uniqueInterval", "intervals": 5, "reverse": False, "ramp": "viridis",
            "defaultColor": defaut, "defaultLabel": "",
            "classes": [{"id": ident("classe " + v), "title": v, "color": c, "value": v, "unique": v}
                        for v, c in couleurs.items()]}


def trace(nom, type_, nom_couche, groupe, attribut, fonction, style, libelle=None, tri=None, classement=None):
    t = {"id": "trace-" + ident(nom), "type": type_, "layer": couche(nom_couche), "geomProp": "geom",
         "options": {"groupByAttributes": groupe, "aggregationAttribute": attribut, "aggregateFunction": fonction},
         "style": style}
    if libelle:
        t["name"] = libelle
    if tri:
        t["sortBy"] = tri
    if classement:
        t["options"]["classificationAttribute"] = classement
    return t


POLICE_AXES = {"fontFamily": "Segoe UI, Arial, sans-serif", "fontSize": 11}


def graphique(nom, titre, traces, x, y, w, h, legende=False, axe_y=None, axe_x=None, description=""):
    cid = ident(nom + " graphique")
    return {"id": ident(nom), "widgetType": "chart", "title": titre, "description": description,
            "mapSync": False, "legend": legende, "dataGrid": {"x": x, "y": y, "w": w, "h": h},
            "selectedChartId": cid,
            "charts": [{"chartId": cid, "name": titre, "legend": legende, "cartesian": True, "barChartType": "group",
                        "xAxisOpts": [{"id": 0, "angle": 0, **POLICE_AXES, **(axe_x or {})}],
                        "yAxisOpts": [{"id": 0, "hide": False, **POLICE_AXES, **(axe_y or {})}],
                        "traces": traces}]}


def barre(couleur):
    return {"msMode": "simple", "marker": {"color": couleur, "line": {"color": couleur, "width": 0}}}


def texte(nom, titre, html, x, y, w, h):
    return {"id": ident(nom), "widgetType": "text", "title": titre, "text": html, "mapSync": False,
            "legend": False, "url": False, "dataGrid": {"x": x, "y": y, "w": w, "h": h}}


def widget_carte(e, x, y, w, h):
    conf = carte.config_carte(e, centre=(12.6, 55.95), zoom=7, visibles=VISIBLES)["map"]
    mid = ident("carte du tableau de bord")
    m = {k: conf[k] for k in ("projection", "units", "center", "zoom", "maxExtent", "mapOptions", "groups")}
    m["layers"] = [l for l in conf["layers"] if l.get("visibility")]
    m["mapId"] = mid
    m["version"] = 2
    return {"id": ident("carte"), "widgetType": "map", "title": "Les signaux sur la carte", "mapSync": True,
            "legend": False, "url": False, "layer": False, "maps": [m], "selectedMapId": mid,
            "dataGrid": {"x": x, "y": y, "w": w, "h": h}}


GUIDE = f"""<div style="font-family:Segoe UI,Arial,sans-serif;font-size:13px;line-height:1.5;color:{ENCRE}">
<p style="margin:0 0 6px"><b>Semaine du 13 au 19 octobre 2026</b>, détroits danois et bassin de Bornholm :
2 894 navires de classe A suivis.</p>
<p style="margin:0 0 6px">Sur <b>3 880 silences</b> AIS de 2 heures ou plus, presque tous ont une raison ordinaire
(port, sortie de zone, navire de servitude) ou tiennent au réseau côtier (<span style="color:{ACIER}"><b>496</b></span>).
Restent <span style="color:{ORANGE}"><b>11 silences inexpliqués</b></span> : des transits muets en eaux bien couvertes.</p>
<p style="margin:0;color:{ENCRE_2};font-size:12px">Indicateurs d'écart au comportement attendu, pas
d'infractions ; navires pseudonymisés. <i>Week of 13–19 Oct. 2026: of 3,880 AIS silences, 11 stay unexplained.</i></p>
</div>""".replace("\n", " ")


COLONNES = [("navire", "Navire (pseudonyme)", "Vessel (pseudonym)"), ("type_navire", "Type", "Type"),
            ("debut_utc", "Début", "Start"), ("fin_utc", "Fin", "End"), ("duree", "Durée", "Duration"),
            ("distance", "Distance", "Distance"), ("part_eaux_couvertes", "Eaux bien couvertes", "Well-covered water")]


def tableau_silences(x, y, w, h):
    c = couche("tableau_silences_inexpliques")
    c["fields"] = [{"name": n, "type": "string", "alias": carte.titre(fr, en)} for n, fr, en in COLONNES]
    return {"id": ident("tableau silences"), "widgetType": "table", "title": "Les 11 silences inexpliqués",
            "mapSync": False, "legend": False, "layer": c, "url": carte.WMS,
            "geomProp": "geom",
            "options": {"propertyName": [n for n, _fr, _en in COLONNES]},
            "dataGrid": {"x": x, "y": y, "w": w, "h": h}}


def widgets(e):
    couleurs_causes = {v: GRIS for v in CAUSES_FR.values()}
    couleurs_causes.update({"Inexpliqué": ORANGE, "Réception côtière": ACIER})
    couleurs_radar = {"Fiable": "#1f5878", "Dégradée": "#6f93ad", "Trafic insuffisant": "#a9b8c4",
                      "Mauvaise": ACIER}
    return [
        texte("guide", "Lire ce tableau", GUIDE, 0, 0, 2, 2),
        compteur("c navires", "Navires de classe A suivis", "nb_navires", 2, 0),
        compteur("c silences", "Silences AIS de 2 h ou plus", "nb_silences", 3, 0),
        compteur("c reception", "Dus aux trous de réception", "nb_reception", 4, 0),
        compteur("c inexpliques", "Silences inexpliqués", "nb_inexpliquees", 5, 0),
        compteur("c mmsi", "Navires au MMSI partagé", "nav_mmsi_partage", 2, 1),
        compteur("c passages", "Passages lents sur câble", "nb_stationnements", 3, 1),
        compteur("c rencontres", "Rencontres en mer", "nb_rencontres", 4, 1),
        compteur("c radar", "Détections radar sans AIS", "nb_radar_sans_ais", 5, 1),
        widget_carte(e, 0, 2, 3, 3),
        graphique("causes", "Pourquoi les AIS se taisent : les 3 880 silences par cause", [
            trace("causes", "bar", "silence_ais", "cause_fr", "fid", "Count",
                  {"msMode": "classification", "msClassification": classes(couleurs_causes, GRIS)},
                  libelle="Silences", tri="aggregation", classement="cause_fr")], 3, 2, 3, 3,
                  axe_y={"type": "log", "nTicks": 4}, axe_x={"angle": -30},
                  description="Échelle logarithmique : les 11 silences inexpliqués restent lisibles à côté des "
                              "1 121 silences de navires de servitude."),
        graphique("semaines", "Quatre semaines : silences inexpliqués et navires au MMSI partagé", [
            trace("semaines inexpliques", "bar", "bilan_semaines", "semaine_fr", "nb_inexpliquees", "Sum",
                  barre(ORANGE), libelle="Silences inexpliqués"),
            trace("semaines mmsi", "bar", "bilan_semaines", "semaine_fr", "nav_mmsi_partage", "Sum",
                  barre(VIOLET), libelle="Navires au MMSI partagé"),
        ], 0, 5, 3, 2, legende=True),
        graphique("radar", "Le radar Sentinel-1 confirme la mesure : part des navires reçus (%)", [
            trace("radar", "bar", "validation_radar", "classe_fr", "part_recue_pct", "Sum",
                  {"msMode": "classification", "msClassification": classes(couleurs_radar, ACIER)},
                  libelle="Part reçue (%)", tri="aggregation", classement="classe_fr")], 3, 5, 3, 2,
                  axe_y={"range": [0, 100]},
                  description="Navires vus par le radar et reçus par le réseau AIS côtier, selon la classe de "
                              "couverture mesurée : 99,3 % en zone fiable, 51,4 % en zone mauvaise."),
        tableau_silences(0, 7, 6, 2),
    ]


def dispositions(ws):
    md = [{"i": w["id"], **w["dataGrid"], "moved": False, "static": False} for w in ws]
    xxs, y = [], 0
    for w in sorted(ws, key=lambda w: (w["dataGrid"]["y"], w["dataGrid"]["x"])):
        h = w["dataGrid"]["h"] if w["widgetType"] in ("map", "chart", "table") else 1
        xxs.append({"i": w["id"], "x": 0, "y": y, "w": 1, "h": h, "moved": False, "static": False})
        y += h
    return {"md": md, "xxs": xxs}


def tableau(e):
    ws = widgets(e)
    return {"widgets": ws, "layouts": dispositions(ws),
            "catalogs": {"services": {"what_ais": {"url": f"/geoserver/{ESPACE}/wms", "type": "wms",
                                                   "title": "What AIS doesn't show (GeoServer)", "autoload": True}},
                         "selectedService": "what_ais"}}


def publier(r, e, carte_id=None):
    attributs = {**r.presentation(NOM, PRESENTATION_TABLEAU, a_l_ouverture=False),
                 **r.vignette(NOM, ["terre_large", "trafic", "lacunes_reception", "zone_etude", "signal_silence_inexplique"])}
    rid = r.enregistrer("DASHBOARD", NOM,
                        "Chiffres clés, causes des silences AIS, quatre semaines et validation radar.",
                        tableau(e), attributs)
    print(f"tableau de bord {rid} : #/dashboard/{rid}")
    return rid
