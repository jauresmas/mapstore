"""Étape 3 : publie dans MapStore la carte, l'application dédiée (contexte), le tableau de bord et
la GeoStory de « What AIS doesn't show ». Idempotent : les ressources sont retrouvées par nom.

    python 03_publier_mapstore.py            tout
    python 03_publier_mapstore.py carte      seulement la carte et l'application (contexte)
    python 03_publier_mapstore.py tableau    seulement le tableau de bord
    python 03_publier_mapstore.py recit      seulement la GeoStory
    python 03_publier_mapstore.py adresses   affiche les adresses des pages déjà publiées
"""
import json
import sys

import carte
import contexte
from commun import ENTREPOT, ESPACE, ICI, MAPSTORE, geoserver, mapstore
from ressources import Ressources
from textes import PRESENTATION_CARTE

NOM_CARTE = "What AIS doesn't show · carte"
NOM_CONTEXTE = "what-ais-doesnt-show"
COUCHES_VIGNETTE = ["terre_large", "trafic", "lacunes_reception", "infrastructure", "parc_eolien", "zone_etude",
                    "limite_zee", "signal_mmsi_partage", "stationnement_infra", "rencontre", "signal_radar_sans_ais",
                    "signal_silence_inexplique"]


def emprises():
    """Emprise WGS84 de chaque couche, lue dans GeoServer (zoom sur la couche dans MapStore)."""
    gs, e = geoserver(), {}
    for c in carte.COUCHES:
        ft = gs.json("GET", f"/workspaces/{ESPACE}/datastores/{ENTREPOT}/featuretypes/{c['nom']}.json")["featureType"]
        b = ft["latLonBoundingBox"]
        e[c["nom"]] = (b["minx"], b["miny"], b["maxx"], b["maxy"])
    return e


def publier_carte(r, e):
    conf = carte.config_carte(e)
    attributs = {**r.presentation(NOM_CARTE, PRESENTATION_CARTE), **r.vignette(NOM_CARTE, COUCHES_VIGNETTE)}
    rid = r.enregistrer("MAP", NOM_CARTE,
                        "Angles morts du réseau AIS côtier et silences inexpliqués, détroits danois et bassin de "
                        "Bornholm, 13–19 octobre 2026.", conf, attributs)
    print(f"carte {rid} : #/viewer/{rid}")
    return rid, conf, attributs


def publier_contexte(r, conf, attributs_carte, carte_id):
    donnees = contexte.contexte(conf, carte_id)
    rid = r.enregistrer("CONTEXT", NOM_CONTEXTE,
                        "Application cartographique dédiée : Ce que l'AIS ne montre pas (What AIS doesn't show).",
                        donnees, {"thumbnail": attributs_carte["thumbnail"],
                                  "title": "Ce que l'AIS ne montre pas"})
    print(f"application {rid} : #/context/{NOM_CONTEXTE}/{carte_id}")
    return rid


def adresses(r):
    """Adresses des pages publiées (leurs identifiants dépendent de l'instance), affichées et écrites dans
    adresses.json pour l'outil de captures d'écran."""
    import recit
    import tableau_de_bord
    ids = {"carte": r.chercher("MAP", NOM_CARTE), "tableau": r.chercher("DASHBOARD", tableau_de_bord.NOM),
           "recit": r.chercher("GEOSTORY", recit.NOM)}
    pages = {"application": f"#/context/{NOM_CONTEXTE}/{ids['carte']}" if ids["carte"] else None,
             "carte": f"#/viewer/{ids['carte']}" if ids["carte"] else None,
             "tableau-de-bord": f"#/dashboard/{ids['tableau']}" if ids["tableau"] else None,
             "geostory": f"#/geostory/{ids['recit']}" if ids["recit"] else None}
    pages = {k: v for k, v in pages.items() if v}
    print("\nAdresses :")
    for nom, ancre in pages.items():
        print(f"  {nom:16} {MAPSTORE}/{ancre}")
    (ICI / "adresses.json").write_text(json.dumps({"base": f"{MAPSTORE}/", "pages": pages}, indent=2),
                                       encoding="utf-8")


def main(quoi="tout"):
    r = Ressources(mapstore())
    if quoi == "adresses":
        return adresses(r)
    e = emprises()
    if quoi in ("tout", "carte"):
        carte_id, conf, attributs = publier_carte(r, e)
        publier_contexte(r, conf, attributs, carte_id)
    else:
        carte_id = r.chercher("MAP", NOM_CARTE)
    import tableau_de_bord
    if quoi in ("tout", "tableau"):
        tableau_id = tableau_de_bord.publier(r, e, carte_id)
    else:
        tableau_id = r.chercher("DASHBOARD", tableau_de_bord.NOM)
    if quoi in ("tout", "recit"):
        import recit
        recit.publier(r, e, carte_id, tableau_id)
    adresses(r)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "tout")
