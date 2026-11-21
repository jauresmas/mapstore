"""GeoStory MapStore « Ce que l'AIS ne montre pas » : les récits de la carte web du dépôt (carte/recit.js),
une carte par étape, textes et chiffres repris du dépôt (français, résumé anglais en italique).

Chaque étape a sa propre ressource carte : couches, emprise et filtres y sont figés, sans dépendre de la
fusion des surcharges de carte par la GeoStory.
"""
import math
import zlib

import carte
from catalogue import COUCHES
from commun import ESPACE
import donnees_recit

NOM = "What AIS doesn't show · récits"
ORANGE, VIOLET, ACIER, ENCRE, ENCRE_2 = "#eb6834", "#4a3aa7", "#5f7d95", "#1d1d1b", "#52514e"
ZONE = [[8.6, 53.7], [16.9, 58.4]]

PAR_NOM = {c["nom"]: c for c in COUCHES + donnees_recit.TABLES}


# ---------- cartes des étapes ----------
def vue(cadre, largeur=1440, hauteur=820, colonne=470):
    """Centre et niveau de zoom pour voir le cadre à droite de la colonne de texte."""
    (o, s), (e, n) = cadre
    my = lambda lat: math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    utile_l, utile_h = largeur - colonne - 80, hauteur - 100
    zx = math.log2(utile_l * 360 / (256 * (e - o)))
    zy = math.log2(utile_h * 2 * math.pi / (256 * (my(n) - my(s))))
    z = max(5, math.floor(min(zx, zy) + 0.4))  # un léger rognage du cadre plutôt qu'un niveau de trop peu
    lat_c = math.degrees(2 * math.atan(math.exp((my(n) + my(s)) / 2)) - math.pi / 2)
    decalage = (colonne / 2) * 360 / (256 * 2 ** z)
    return ((o + e) / 2 - decalage, lat_c), z


def couche(nom, e, opacite=None, filtre=None, style=None):
    c = carte.couche_wms(PAR_NOM[nom], e, True)
    c["id"] = f"{ESPACE}__{nom}" + (f"__{zlib.crc32(filtre.encode()):08x}" if filtre else "")
    if opacite is not None:
        c["opacity"] = opacite
    if filtre:
        c["params"] = {"CQL_FILTER": filtre}
    if style:
        c["style"] = style
    c["featureInfo"] = {"format": "HIDDEN"}
    return c


def emprise(cadre, colonne=True, marge=0.08, part_texte=0.36):
    """Emprise à afficher : le cadre avec une marge, élargi vers l'ouest pour laisser la place à la colonne de
    texte (la GeoStory ajuste la carte sur cette emprise, quelle que soit la taille de l'écran)."""
    (o, s), (e, n) = cadre
    dx, dy = (e - o) * marge, (n - s) * marge
    o, s, e, n = o - dx, s - dy, e + dx, n + dy
    if colonne:
        o = e - (e - o) / (1 - part_texte)
    return {"crs": "EPSG:4326", "bounds": {"minx": o, "miny": s, "maxx": e, "maxy": n}}


def ressource(rid, e, cadre, couches, colonne=True):
    centre, zoom = vue(cadre, colonne=470 if colonne else 0)
    fond = carte.fonds()[0]
    fond["visibility"] = True
    m = carte.config_carte(e, centre=centre, zoom=zoom)["map"]
    m["layers"] = [fond] + couches + [couche("lieu", e)]
    m["groups"] = []
    m.pop("bookmark_search_config", None)
    m.pop("text_search_config", None)
    m["mapInfoControl"] = False
    m["bbox"] = emprise(cadre, colonne)
    return {"id": rid, "type": "map", "data": m}


# ---------- textes ----------
def carte_texte(titre, html, anglais, legende=None, etape=None):
    leg = ""
    if legende:
        leg = '<p style="margin:10px 0 0;font-size:12.5px;line-height:1.7;color:#52514e">' + "<br>".join(
            f'<span style="color:{c};font-size:15px">{s}</span>&nbsp;{lib}' for s, c, lib in legende) + "</p>"
    tete = (f'<p style="margin:0 0 2px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;'
            f'color:#8a877f">{etape}</p>') if etape else ""
    t = f'<h3 style="margin:0 0 6px;font-size:18px;color:{ENCRE}">{titre}</h3>' if titre else ""
    return (f'<div style="font-family:Segoe UI,Arial,sans-serif;font-size:15px;line-height:1.55;color:{ENCRE}">'
            f'{tete}{t}<p style="margin:0">{html}</p>{leg}'
            f'<p style="margin:10px 0 0;font-size:12.5px;font-style:italic;color:#6b6964">{anglais}</p></div>')


def colonne(cid, rid, html):
    return {"type": "column", "id": cid, "align": "left", "size": "small", "theme": "",
            "background": {"type": "map", "resourceId": rid, "fit": "cover", "size": "full", "align": "center"},
            "contents": [{"id": cid + "_texte", "type": "text", "html": html}]}


def immersive(sid, titre, etapes):
    return {"type": "immersive", "id": sid, "title": titre,
            "contents": [colonne(f"{sid}_{i}", rid, html) for i, (rid, html) in enumerate(etapes, 1)]}


# ---------- légendes ----------
L_COUV = [("■", "#d8693f", "couverture mauvaise : navires souvent perdus"), ("■", "#f2c79b", "dégradée"),
          ("■", "#d5e5dd", "fiable"), ("▨", "#bdbdb8", "trafic insuffisant pour juger")]
L_RADAR = [("●", "#8d9aa4", "vu par le radar, reçu par l'AIS côtier"),
           ("●", ORANGE, "vu et identifié par le radar, non reçu par l'AIS côtier")]
L_SIL = [("━", "#a8461f", "route reçue par l'AIS"), ("○", ORANGE, "dernière position avant le silence")]
L_SIL_PASSE = [("┅", ORANGE, "trajet supposé pendant le silence"),
               ("◌", ORANGE, "position attendue au passage (cercle de 5 km)"),
               ("●", "#8d9aa4", "écho radar d'un navire AIS"), ("●", ORANGE, "identifié, non reçu par l'AIS côtier"),
               ("□", ENCRE_2, "écho sans aucun AIS")]
L_MMSI = [("●", VIOLET, "position annoncée sous le MMSI"), ("━", VIOLET, "saut impossible")]
L_SEM = [("■", "#a63c14", "angle mort chronique (3 ou 4 semaines)"), ("■", "#e0784a", "récurrent (2 semaines)"),
         ("■", "#f6cdb3", "ponctuel (1 semaine)")]
L_FOYER = [("▢", ORANGE, "zone de 250 km² à silences deux semaines"),
           ("●", "#a63c14", "silence inexpliqué (plus foncé : plus récent)"), ("■", "#a63c14", "angle mort chronique")]


def recit(e):
    res, sections = [], []

    def r(rid, cadre, noms, **kw):
        couches = []
        for n in noms:
            if isinstance(n, tuple):
                couches.append(couche(n[0], e, **n[1]))
            else:
                couches.append(couche(n, e))
        res.append(ressource(rid, e, cadre, couches, **kw))
        return rid

    # Couverture
    s_couv = [[13.3, 54.05], [16.6, 56.05]]
    r("couv_1", s_couv, ["couverture"])
    r("couv_2", s_couv, ["couverture", "recit_radar_validation"])
    r("couv_3", ZONE, ["couverture", "recit_radar_validation"])
    # Silence
    cadre_sil = [[11.644, 56.019], [12.792, 56.691]]
    r("sil_1", cadre_sil, [("recit_silence_ligne", {"filtre": "partie = 'route'"}),
                           ("recit_silence_point", {"filtre": "role = 'muet'"})])
    r("sil_2", cadre_sil, [("couverture", {"opacite": 0.55}), ("recit_silence_ligne", {"filtre": "partie = 'route'"}),
                           ("recit_silence_point", {"filtre": "role = 'muet'"})])
    r("sil_3", cadre_sil, ["recit_silence_cercle", ("recit_silence_ligne", {"filtre": "partie <> 'retour'"}),
                           ("recit_silence_point", {"filtre": "role = 'muet'"}), "recit_silence_radar"])
    r("sil_4", cadre_sil, ["recit_silence_cercle", "recit_silence_ligne", "recit_silence_point",
                           ("recit_silence_radar", {"filtre": "etat >= 2"})])
    # Identité
    cadre_id = [[10.474, 54.981], [14.787, 57.767]]
    r("id_1", cadre_id, [("recit_identite_position", {"filtre": "minute < 60"})])
    r("id_2", cadre_id, [("recit_identite_saut", {"filtre": "minute <= 1620"}),
                         ("recit_identite_position", {"filtre": "minute <= 1620"})])
    r("id_3", cadre_id, ["recit_identite_saut", "recit_identite_position"])
    # Semaines
    r("sem_1", ZONE, ["couverture"])
    r("sem_2", ZONE, ["recurrence_couverture"])
    r("sem_3", [[11.8, 54.3], [16.4, 56.4]], [("recurrence_couverture", {"opacite": 0.4}), "foyer_recurrent",
                                              "inexpliquee_semaines"])
    # Couverture et page de titre
    r("titre", ZONE, [("trafic", {"opacite": 0.8}), "lacunes_reception", "signal_mmsi_partage", "stationnement_infra",
                      "rencontre", "signal_radar_sans_ais", "signal_silence_inexplique"], colonne=False)

    sections.append({"type": "title", "id": "titre", "title": "Ce que l'AIS ne montre pas", "cover": True,
                     "contents": [{"id": "titre_texte", "type": "text", "size": "large", "align": "center", "theme": "",
                                   "background": {"type": "map", "resourceId": "titre", "fit": "cover", "size": "full",
                                                  "align": "center"},
                                   "html": TITRE}]})
    sections.append({"type": "paragraph", "id": "introduction", "title": "Quatre récits",
                     "contents": [{"type": "column", "id": "introduction_colonne",
                                   "contents": [{"id": "introduction_texte", "type": "text", "html": INTRODUCTION}]}]})

    sections.append(immersive("couverture", "Un angle mort confirmé par satellite", [
        ("couv_1", carte_texte("Un angle mort confirmé par satellite",
            "Au sud de Bornholm et dans la baie de Poméranie, les stations côtières danoises sont loin. La couverture "
            "mesurée à partir du trafic lui-même y est mauvaise (mailles rouges) : les navires sont souvent perdus en "
            "traversant.",
            "South of Bornholm and in Pomeranian Bay, Danish shore stations are far away: the coverage measured from "
            "the traffic itself is poor, and vessels are often lost while crossing.", L_COUV, "Récit 1 · étape 1 sur 3")),
        ("couv_2", carte_texte(None,
            "Sentinel-1 voit les navires, qu'ils émettent ou non. Sur les <b>177</b> navires vus et identifiés par le "
            "satellite dans les mailles mal couvertes, <b style=\"color:#eb6834\">86</b> n'étaient pas reçus par le "
            "réseau côtier danois à cette minute (orange). Dans les mailles bien couvertes : <b>13</b> sur 1 775.",
            "Of 177 vessels the satellite saw and identified in poorly covered cells, 86 were not received by the "
            "Danish shore network at that minute. In reliably covered cells: 13 out of 1,775.",
            L_RADAR, "Récit 1 · étape 2 sur 3")),
        ("couv_3", carte_texte(None,
            "Sur toute la zone, la part reçue suit la carte de couverture : <b>99 %</b> dans les mailles fiables, "
            "<b style=\"color:#eb6834\">51 %</b> dans les mauvaises. Une source qui ne doit rien à l'AIS côtier "
            "confirme où il est en défaut, et c'est là qu'une détection indépendante apporte le plus.",
            "Across the area, the share received follows the coverage map: 99 % in reliable cells, 51 % in poor ones.",
            L_RADAR, "Récit 1 · étape 3 sur 3")),
    ]))
    sections.append(immersive("silence", "Un navire de pêche silencieux et un écho radar", [
        ("sil_1", carte_texte("Un navire de pêche silencieux et un écho radar",
            "Dimanche 18 octobre. Un navire de pêche (V-42B040) traverse le Cattégat, dans des eaux où les stations "
            "côtières reçoivent neuf voisins sur dix.",
            "Sunday 18 October. A fishing vessel (V-42B040) heads through the Kattegat, in waters where shore "
            "stations receive nine neighbours in ten.", L_SIL, "Récit 2 · étape 1 sur 4")),
        ("sil_2", carte_texte(None,
            "<b>11:46 UTC</b> : son AIS se tait. Les autres navires alentour restent reçus : ce n'est pas un trou de "
            "réception. La couverture mesurée est fiable tout autour.",
            "11:46 UTC: its AIS falls silent. Other vessels around keep being received, so it is not a reception gap.",
            L_SIL + [("■", "#d5e5dd", "couverture fiable")], "Récit 2 · étape 2 sur 4")),
        ("sil_3", carte_texte(None,
            "<b>17:00 UTC</b> : Sentinel-1 passe. Un écho ne correspond à aucun AIS, à moins de 5 km de l'endroit où "
            "le navire devrait se trouver sur sa route (cercle orange).",
            "17:00 UTC: Sentinel-1 passes over. One echo matches no AIS at all, less than 5 km from where the vessel "
            "should be on its way.", L_SIL_PASSE, "Récit 2 · étape 3 sur 4")),
        ("sil_4", carte_texte(None,
            "<b>18:40 UTC</b> : l'AIS revient <b>28 milles</b> plus loin, après <b>6,9 heures</b>. Aucune explication "
            "ordinaire ne justifie ce silence. Un émetteur défaillant reste possible : c'est un cas à examiner, pas "
            "une preuve.",
            "18:40 UTC: the AIS comes back 28 nautical miles further on, after 6.9 hours. A faulty transmitter remains "
            "possible: a case worth a closer look, not proof of anything.",
            [("●", ORANGE, "retour de l'AIS")] + L_SIL_PASSE[:2] + [("□", ENCRE_2, "écho sans aucun AIS")],
            "Récit 2 · étape 4 sur 4")),
    ]))
    sections.append(immersive("identite", "Une identité, deux émetteurs", [
        ("id_1", carte_texte("Une identité, deux émetteurs",
            "Sous un seul MMSI, un cargo (V-70E655) annonce sa position environ une fois par minute, comme l'AIS "
            "l'exige.",
            "Under a single MMSI, a cargo vessel (V-70E655) reports its position about once a minute, as AIS requires.",
            L_MMSI[:1], "Récit 3 · étape 1 sur 3")),
        ("id_2", carte_texte(None,
            "Puis une position à <b>125 milles</b> de là, une minute plus tard, et retour (traits violets) : "
            "<b>33 sauts impossibles</b> en 36 heures.",
            "Then a position 125 nautical miles away, a minute later, and back again: 33 impossible jumps in 36 hours.",
            L_MMSI, "Récit 3 · étape 2 sur 3")),
        ("id_3", carte_texte(None,
            "Aucun navire ne file 1 000 nœuds : deux émetteurs partagent une même identité, par erreur de "
            "configuration ou par copie délibérée. L'AIS seul ne dit pas quelle position est la vraie ; une "
            "géolocalisation indépendante, si.",
            "No ship sails at 1,000 knots: two transmitters share one identity. AIS alone cannot tell which position "
            "is genuine; an independent geolocation can.", L_MMSI, "Récit 3 · étape 3 sur 3")),
    ]))
    sections.append(immersive("semaines", "Chronique ou ponctuel ?", [
        ("sem_1", carte_texte("Chronique ou ponctuel ?",
            "Une semaine de couverture côtière, mesurée à partir du trafic lui-même (la semaine d'étude). Un angle "
            "mort vu une seule semaine peut tenir au hasard : météo, station en panne.",
            "One week of shore coverage, measured from the traffic itself. A blind spot seen in a single week may be "
            "bad luck: weather, a station down.", L_COUV, "Récit 4 · étape 1 sur 3")),
        ("sem_2", carte_texte(None,
            "Sur quatre semaines, <b>168 mailles</b> sont mauvaises au moins trois semaines sur quatre (rouge foncé), "
            "soit environ <b>5 120 km²</b> : 109 dans les eaux allemandes, 37 dans les eaux suédoises, 22 dans les "
            "eaux polonaises. Ce sont des manques durables du réseau côtier, là où une détection indépendante sert "
            "semaine après semaine.",
            "Over four weeks, 168 cells are poor at least three weeks out of four, about 5,120 km²: structural gaps of "
            "the shore network.", L_SEM, "Récit 4 · étape 2 sur 3")),
        ("sem_3", carte_texte(None,
            "Les silences inexpliqués, au contraire, ne reviennent pas : <b>33</b> en quatre semaines, venant de "
            "<b>30 navires</b> différents, et seules <b>4 zones</b> de 250 km² en ont vu deux semaines différentes "
            "(contour orange). S'ils tenaient à un défaut de la méthode, ils reviendraient aux mêmes endroits.",
            "Unexplained silences, on the contrary, do not come back: 33 in four weeks, from 30 different vessels, "
            "and only 4 areas saw one in two different weeks.", L_FOYER, "Récit 4 · étape 3 sur 3")),
    ]))
    sections.append({"type": "paragraph", "id": "conclusion", "title": "Pour aller plus loin",
                     "contents": [{"type": "column", "id": "conclusion_colonne",
                                   "contents": [{"id": "conclusion_texte", "type": "text", "html": CONCLUSION}]}]})

    return {"type": "cascade", "resources": res, "sections": sections,
            "settings": {"storyTitle": "Ce que l'AIS ne montre pas", "isTitleEnabled": True,
                         "isNavbarEnabled": True, "isLogoEnabled": False,
                         "theme": {"general": {"color": ENCRE, "backgroundColor": "#ffffff", "borderColor": "#e3e0da"},
                                   "overlay": {"backgroundColor": "rgba(255, 255, 255, 0.93)", "borderColor": "#e3e0da",
                                               "boxShadow": "0 6px 18px rgba(29, 29, 27, 0.18)", "color": ENCRE}}}}


TITRE = """<p style="margin:0;font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#52514e">AIS côtier · données ouvertes</p>
<h1 style="margin:6px 0 8px;font-size:44px;line-height:1.1;color:#1d1d1b">Ce que l'AIS ne montre pas</h1>
<p style="margin:0;font-size:18px;color:#1d1d1b">Détroits danois et bassin de Bornholm · 13–19 octobre 2026</p>
<p style="margin:10px 0 0;font-size:14px;font-style:italic;color:#52514e">What AIS doesn't show · four stories</p>""".replace("\n", "")

INTRODUCTION = """<div style="font-family:Segoe UI,Arial,sans-serif;font-size:16px;line-height:1.6;color:#1d1d1b">
<p>Le réseau AIS côtier suit <b>2 894 navires</b> de classe A dans les détroits danois. Sur une semaine, <b>3 880</b>
de leurs AIS se taisent deux heures ou plus. Presque toujours pour une raison ordinaire : un port, une sortie de zone,
un navire de servitude, ou une station côtière trop loin. Restent <b style="color:#eb6834">11 silences inexpliqués</b>.</p>
<p>Quatre récits, tirés de l'analyse : où le réseau perd les navires et comment un satellite radar le confirme ; un
navire de pêche qui se tait sept heures ; une identité partagée par deux émetteurs ; et ce qui revient, ou non,
d'une semaine sur l'autre.</p>
<p style="font-size:14px;font-style:italic;color:#52514e">Of 3,880 AIS silences in one week, 11 stay unexplained. Four
stories: a blind spot confirmed by satellite, a silent fishing vessel, one identity shared by two transmitters, and what
recurs over four weeks.</p></div>""".replace("\n", " ")

CONCLUSION = """<div style="font-family:Segoe UI,Arial,sans-serif;font-size:15px;line-height:1.6;color:#1d1d1b">
<p>Les indicateurs signalent des <b>écarts au comportement attendu</b>, pas des infractions : aucun navire n'est nommé ni
mis en cause, les navires sont pseudonymisés.</p>
<p>Explorer toutes les couches dans <a href="#/context/what-ais-doesnt-show/{carte}">la carte</a>, les chiffres dans
<a href="#/dashboard/{tableau}">le tableau de bord</a>, la méthode et le code dans
<a href="https://github.com/jauresmas/what-ais-doesnt-show" target="_blank" rel="noopener">le dépôt</a>.</p>
<p style="font-size:12.5px;color:#52514e">Sources : Autorité maritime danoise (AIS) ; Marine Regions (CC BY 4.0) ;
Eurostat GISCO (© EuroGeographics) ; EMODnet et BSH (CC BY 4.0) ; TeleGeography (CC BY-NC-SA 3.0) ; © contributeurs
OpenStreetMap (ODbL) ; détections radar Powered by Global Fishing Watch (CC BY-NC 4.0).</p></div>""".replace("\n", " ")


def publier(r, e, carte_id=None, tableau_id=None):
    donnees = recit(e)
    for s in donnees["sections"]:
        if s["id"] == "conclusion":
            c = s["contents"][0]["contents"][0]
            c["html"] = c["html"].replace("{carte}", str(carte_id or "")).replace("{tableau}", str(tableau_id or ""))
    attributs = r.vignette(NOM, ["terre_large", "couverture", "recit_radar_validation"], bbox=(12.6, 54.0, 16.8, 56.4))
    rid = r.enregistrer("GEOSTORY", NOM,
                        "Quatre récits : un angle mort confirmé par satellite, un navire de pêche silencieux, "
                        "une identité partagée, quatre semaines.", donnees, attributs)
    print(f"récits {rid} : #/geostory/{rid}")
    return rid
