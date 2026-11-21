"""Application dédiée (contexte MapStore) : les outils du visualiseur standard de cette version de
MapStore, sans ceux qui ne servent pas ici, avec le bandeau, les couleurs et la légende du projet.
"""
import base64
import json
import urllib.request

from commun import MAPSTORE

# Outils retirés : impression (module non installé), 3D, temps (aucune couche temporelle), tutoriel,
# annotations (remplacées par le dessin des vues de carte), téléchargement WPS (extension absente),
# enregistrement de la carte (l'application est en lecture ; l'administrateur garde la carte source)
RETIRES = {"Tutorial", "Print", "HelpLink", "Annotations", "GlobeViewSwitcher", "Timeline", "Playback",
           "LayerDownload", "CRSSelector", "Save", "SaveAs", "DeleteResource", "AutoMapUpdate"}

LEGENDE = {"WMSLegendOptions": "forceLabels:on;fontName:Segoe UI;fontSize:11;fontAntiAliasing:true;"
                               "fontColor:0x1D1D1B;dx:6;dy:0.2;mx:0.05;my:0.15;bgColor:0xFFFFFF",
           "scaleDependent": True, "legendWidth": 18, "legendHeight": 18}

# Couleurs de l'interface : encre et bleu de mer du projet, contrastes AA sur blanc
THEME = {"variables": {"ms-main-color": "#1d1d1b", "ms-main-bg": "#ffffff",
                       "ms-primary": "#1f5878", "ms-primary-contrast": "#ffffff",
                       "ms-success": "#167a57", "ms-success-contrast": "#ffffff"}}


def logo():
    """Logotype du bandeau : le symbole du silence inexpliqué et le titre bilingue."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="430" height="44" viewBox="0 0 430 44">
<g transform="translate(4 22)">
<line x1="6" y1="0" x2="34" y2="0" stroke="#ffffff" stroke-width="7" stroke-linecap="round"/>
<line x1="6" y1="0" x2="34" y2="0" stroke="#eb6834" stroke-width="3" stroke-dasharray="5 3.5"/>
<circle cx="6" cy="0" r="5" fill="#ffffff" stroke="#eb6834" stroke-width="2.4"/>
<circle cx="35" cy="0" r="5" fill="#eb6834" stroke="#ffffff" stroke-width="1.5"/></g>
<text x="52" y="20" font-family="Segoe UI, Arial, sans-serif" font-size="17" font-weight="700" fill="#1d1d1b">Ce que l'AIS ne montre pas</text>
<text x="52" y="37" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="#52514e" letter-spacing="0.4">What AIS doesn't show · détroits danois, 13–19 oct. 2026</text>
</svg>"""
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode()


def plugins_standard():
    with urllib.request.urlopen(f"{MAPSTORE}/configs/localConfig.json", timeout=60) as r:
        return json.load(r)["plugins"]["desktop"]


def adapter(p, carte_id=None):
    p = {"name": p} if isinstance(p, str) else json.loads(json.dumps(p))
    cfg = p.setdefault("cfg", {})
    if p["name"] == "TOC":
        cfg.setdefault("layerOptions", {})["legendOptions"] = LEGENDE
    elif p["name"] == "BrandNavbar":
        lien = "#/context/what-ais-doesnt-show" + (f"/{carte_id}" if carte_id else "")
        cfg["logo"] = {"src": logo(), "href": lien, "style": {"height": "2.4rem"}}
    elif p["name"] == "Identify":
        cfg["showEdit"] = False
        cfg["showHighlightFeatureButton"] = True
    elif p["name"] == "Measure":
        cfg.setdefault("defaultOptions", {})["showAddAsAnnotation"] = False
    if not cfg:
        p.pop("cfg")
    return p


def contexte(config_carte, carte_id=None):
    plugins = [adapter(p, carte_id) for p in plugins_standard()
               if (p if isinstance(p, str) else p["name"]) not in RETIRES]
    return {
        "windowTitle": "Ce que l'AIS ne montre pas · What AIS doesn't show",
        "mapConfig": config_carte,
        "theme": THEME,
        "customVariablesEnabled": True,
        "plugins": {"desktop": plugins},
        "userPlugins": [],
        "templates": [],
    }
