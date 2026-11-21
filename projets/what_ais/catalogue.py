"""Catalogue des couches publiées : nom GeoServer, style, titres et résumés bilingues, groupe dans
la carte MapStore, visibilité initiale et fiche d'information au clic (en français).

Une seule source pour GeoServer (02_publier_geoserver.py) et MapStore (03_publier_mapstore.py).
"""

GROUPES = [  # id, titre fr, titre en, déplié
    ("reperes", "Repères", "Landmarks", False),
    ("signaux", "Signaux", "Signals", True),
    ("silences", "Tous les silences AIS", "All AIS silences", False),
    ("indicateurs", "Indicateurs", "Indicators", True),
    ("semaines", "Quatre semaines", "Four weeks", False),
    ("infrastructures", "Infrastructures en mer", "Offshore infrastructure", False),
    ("limites", "Limites", "Boundaries", False),
    ("traces", "Traces des navires", "Vessel tracks", False),
]


def _ligne(libelle, champ):
    return (f'<tr><th style="text-align:left;font-weight:600;color:#52514e;padding:2px 10px 2px 0;'
            f'vertical-align:top;white-space:nowrap">{libelle}</th><td style="padding:2px 0">'
            f'${{properties.{champ}}}</td></tr>')


def fiche(titre, couleur, lignes, note=""):
    """Gabarit HTML d'une fiche d'information MapStore (format TEMPLATE)."""
    corps = "".join(_ligne(l, c) for l, c in lignes)
    n = f'<p style="margin:8px 0 0;font-size:11px;line-height:1.4;color:#8a877f">{note}</p>' if note else ""
    return (f'<div style="font-family:Segoe UI,Arial,sans-serif;font-size:13px;color:#1d1d1b;max-width:360px">'
            f'<div style="border-left:4px solid {couleur};padding-left:8px;margin-bottom:6px">'
            f'<strong style="font-size:14px">{titre}</strong></div>'
            f'<table style="border-collapse:collapse">{corps}</table>{n}</div>')


NAVIRE = ("Navire (pseudonyme)", "navire")

COUCHES = [
    # --- Repères
    dict(nom="lieu", style="wa_lieux", groupe="reperes", visible=True, fiche=None,
         titre=("Noms de lieux", "Place names"),
         resume=("Mers, pays, îles et villes de l'aire d'étude.", "Seas, countries, islands and cities of the study area.")),
    dict(nom="station_ais", style="wa_station_ais", groupe="reperes", visible=False,
         titre=("Stations AIS côtières", "AIS shore stations"),
         resume=("Stations du réseau AIS côtier danois et nombre de messages reçus pendant la semaine d'étude.",
                 "Danish shore AIS stations and number of messages received during the study week."),
         fiche=fiche("Station AIS côtière", "#3d3d3a", [("Station", "id_station"), ("Messages reçus", "messages_txt")])),

    # --- Signaux
    dict(nom="signal_silence_inexplique", style="wa_silence_inexplique", groupe="signaux", visible=True,
         titre=("Silence AIS inexpliqué", "Unexplained AIS silence"),
         resume=("Silences AIS de 2 heures ou plus qu'aucune explication ordinaire ne justifie : le navire est resté "
                 "dans des eaux bien couvertes, où le réseau recevait ses voisins. Trajet supposé entre la dernière et "
                 "la première position reçues.",
                 "AIS silences of 2 hours or more that no ordinary explanation accounts for: the vessel stayed in "
                 "well-covered waters where the network kept receiving its neighbours. Assumed path between the last "
                 "and next received positions."),
         fiche=fiche("Silence AIS inexpliqué", "#eb6834",
                     [NAVIRE, ("Type", "famille_fr"), ("Début", "debut_txt"), ("Fin", "fin_txt"), ("Durée", "duree_txt"),
                      ("Trajet supposé", "distance_txt"), ("En eaux bien couvertes", "couverte_txt")],
                     "Un signal n'est pas une infraction : il dit où regarder, pas ce qui s'est passé.")),
    dict(nom="signal_mmsi_partage", style="wa_mmsi_partage", groupe="signaux", visible=True,
         titre=("MMSI partagé par deux émetteurs", "MMSI shared by two transmitters"),
         resume=("Sauts de position impossibles (plus de 50 nœuds implicites) pour les navires qui en comptent trois "
                 "ou plus : deux émetteurs utilisent la même identité.",
                 "Impossible position jumps (implied speed over 50 knots) for vessels with three or more: two "
                 "transmitters share the same identity."),
         fiche=fiche("MMSI partagé par deux émetteurs", "#4a3aa7",
                     [NAVIRE, ("De", "debut_txt"), ("À", "fin_txt"), ("Distance du saut", "distance_txt"),
                      ("Vitesse implicite", "vitesse_txt")])),
    dict(nom="stationnement_infra", style="wa_stationnement", groupe="signaux", visible=True,
         titre=("Passage lent au-dessus d'un câble ou pipeline", "Slow passage over a cable or pipeline"),
         resume=("Navire à moins de 2 nœuds pendant 30 minutes ou plus, à moins de 750 m d'un câble ou d'un pipeline "
                 "sous-marin, hors ports et mouillages.",
                 "Vessel below 2 knots for 30 minutes or more within 750 m of a submarine cable or pipeline, outside "
                 "ports and anchorages."),
         fiche=fiche("Passage lent au-dessus d'une infrastructure", "#2a78d6",
                     [NAVIRE, ("Type", "famille_fr"), ("Début", "debut_txt"), ("Durée", "duree_txt"),
                      ("Infrastructure", "infrastructure"), ("Nom", "nom_infrastructure"),
                      ("Distance minimale", "distance_txt"), ("Source du tracé", "source")])),
    dict(nom="rencontre", style="wa_rencontre", groupe="signaux", visible=True,
         titre=("Rencontre en mer", "Ship-to-ship encounter"),
         resume=("Deux navires à moins de 500 m l'un de l'autre pendant 2 heures ou plus, hors ports et mouillages côtiers. "
                 "45 des 47 rencontres ont lieu en rade de Skagen.",
                 "Two vessels within 500 m of each other for 2 hours or more, outside ports and coastal anchorages. "
                 "45 of the 47 encounters take place in Skagen roads."),
         fiche=fiche("Rencontre en mer", "#1baf7a",
                     [("Navire A", "navire_a"), ("Type A", "famille_a_fr"), ("Navire B", "navire_b"),
                      ("Type B", "famille_b_fr"), ("Début", "debut_txt"), ("Durée", "duree_txt"),
                      ("Distance moyenne", "distance_txt")])),
    dict(nom="signal_radar_sans_ais", style="wa_radar", groupe="signaux", visible=True,
         titre=("Détection radar sans AIS", "Radar detection without AIS"),
         resume=("Navires vus par le radar Sentinel-1 sans aucun AIS correspondant (Global Fishing Watch), hors "
                 "structures fixes des parcs éoliens. Powered by Global Fishing Watch (CC BY-NC 4.0).",
                 "Vessels seen by Sentinel-1 radar with no matching AIS (Global Fishing Watch), excluding wind farm "
                 "structures. Powered by Global Fishing Watch (CC BY-NC 4.0)."),
         fiche=fiche("Détection radar sans AIS", "#52514e",
                     [("Passage du satellite", "instant_txt"), ("Lecture", "categorie"),
                      ("Couverture côtière de la maille", "couverture_fr"), ("Navire AIS le plus proche", "distance_txt")],
                     "Données radar : Powered by Global Fishing Watch (CC BY-NC 4.0).")),

    # --- Tous les silences
    dict(nom="silence_ais", style="wa_silences_tous", groupe="silences", visible=False,
         titre=("Silences AIS de 2 h ou plus, par cause", "AIS silences of 2 h or more, by cause"),
         resume=("Les 3 880 silences AIS de la semaine, au point où ils commencent, rangés en neuf catégories, "
                 "de la plus ordinaire à « inexpliqué ».",
                 "The week's 3,880 AIS silences, at their starting point, sorted into nine categories, from the most "
                 "ordinary to 'unexplained'."),
         fiche=fiche("Silence AIS", "#5f7d95",
                     [NAVIRE, ("Type", "famille_fr"), ("Cause retenue", "categorie"), ("Début", "debut_txt"),
                      ("Durée", "duree_txt"), ("Trajet supposé", "distance_txt")])),

    # --- Indicateurs
    dict(nom="indice_signale", style="wa_indice", groupe="indicateurs", visible=False,
         titre=("Indice de vigilance (mailles H3)", "Vigilance index (H3 cells)"),
         resume=("Combinaison des quatre signaux rapportée au trafic, par maille H3 de résolution 5 (environ 250 km²).",
                 "The four signals combined and weighted by traffic, per H3 resolution-5 cell (about 250 km²)."),
         fiche=fiche("Indice de vigilance", "#c24f22",
                     [("Indice", "indice_txt"), ("Signaux présents", "nb_signaux"), ("Navires", "nb_navires"),
                      ("Trafic", "heures_txt"), ("Navires en silence", "nav_coupures"),
                      ("Navires aux sauts impossibles", "nav_sauts"), ("Navires en passage lent", "nav_stationnements"),
                      ("Navires en rencontre", "nav_rencontres")])),
    dict(nom="lacunes_reception", style="wa_lacunes", groupe="indicateurs", visible=True, fiche=None,
         titre=("Mauvaise réception AIS côtière", "Poor shore AIS reception"),
         resume=("Mailles où le réseau côtier perd des navires attendus : fusion des mailles de couverture mauvaise.",
                 "Cells where the shore network loses expected vessels: merged poor-coverage cells.")),
    dict(nom="couverture", style="wa_couverture", groupe="indicateurs", visible=False,
         titre=("Couverture AIS côtière mesurée (mailles H3)", "Measured shore AIS coverage (H3 cells)"),
         resume=("Couverture calculée à partir du trafic lui-même : part des minutes reçues et part des navires attendus "
                 "perdus en traversant la maille (résolution 6, environ 36 km²).",
                 "Coverage computed from the traffic itself: share of minutes received and share of expected vessels "
                 "lost while crossing the cell (resolution 6, about 36 km²)."),
         fiche=fiche("Couverture AIS côtière", "#d8693f",
                     [("Classe", "classe_fr"), ("Minutes reçues", "reception_txt"), ("Navires perdus", "perte_txt"),
                      ("Navires", "nb_navires")])),
    dict(nom="trafic", style="wa_trafic", groupe="indicateurs", visible=True,
         titre=("Densité du trafic", "Shipping density"),
         resume=("Heures-navire par maille H3 pendant la semaine d'étude (navires de classe A).",
                 "Vessel-hours per H3 cell during the study week (class A vessels)."),
         fiche=fiche("Densité du trafic", "#97aab6",
                     [("Heures-navire", "heures_txt"), ("Navires", "nb_navires")])),

    # --- Quatre semaines
    dict(nom="foyer_recurrent", style="wa_foyers", groupe="semaines", visible=False,
         titre=("Silences inexpliqués récurrents", "Recurring unexplained silences"),
         resume=("Zones de 250 km² où des silences inexpliqués ont commencé au moins deux semaines différentes sur quatre.",
                 "250 km² areas where unexplained silences started in at least two different weeks out of four."),
         fiche=fiche("Silences inexpliqués récurrents", "#eb6834",
                     [("Semaines concernées", "nb_semaines"), ("Silences", "nb_silences"), ("Navires", "nb_navires")])),
    dict(nom="inexpliquee_semaines", style="wa_inexpliquee_semaines", groupe="semaines", visible=False,
         titre=("Silences inexpliqués des quatre semaines", "Unexplained silences over four weeks"),
         resume=("Début des 33 silences inexpliqués des semaines du 22 septembre au 13 octobre 2026.",
                 "Start of the 33 unexplained silences from the weeks of 22 September to 13 October 2026."),
         fiche=fiche("Silence inexpliqué", "#a63c14",
                     [("Semaine", "semaine_fr"), ("Type", "famille_fr"), ("Début", "debut_txt"), ("Durée", "duree_txt")])),
    dict(nom="recurrence_couverture", style="wa_recurrence", groupe="semaines", visible=False,
         titre=("Angles morts sur quatre semaines", "Blind spots over four weeks"),
         resume=("Nombre de semaines où chaque maille a été mal couverte : un angle mort chronique l'est au moins "
                 "trois semaines sur quatre.",
                 "Number of weeks each cell was poorly covered: a chronic blind spot is poor at least three weeks out of four."),
         fiche=fiche("Couverture sur quatre semaines", "#a63c14",
                     [("Statut", "statut_fr"), ("Semaines jugées", "nb_jugees"), ("Semaines mauvaises", "nb_mauvaises"),
                      ("Semaines dégradées", "nb_degradees"), ("Semaines fiables", "nb_fiables")])),

    # --- Infrastructures
    dict(nom="infrastructure", style="wa_infrastructure", groupe="infrastructures", visible=True,
         titre=("Câbles et pipelines sous-marins", "Submarine cables and pipelines"),
         resume=("Tracés publics combinés de trois sources (EMODnet et BSH, TeleGeography, OpenStreetMap) : indicatifs.",
                 "Public routes combined from three sources (EMODnet and BSH, TeleGeography, OpenStreetMap): indicative."),
         fiche=fiche("Câble ou pipeline", "#6f675d",
                     [("Catégorie", "categorie"), ("Nom", "nom_txt"), ("Source", "source")])),
    dict(nom="parc_eolien", style="wa_parc_eolien", groupe="infrastructures", visible=True,
         titre=("Parcs éoliens en mer", "Offshore wind farms"),
         resume=("Parcs éoliens en mer (EMODnet), quel que soit leur état d'avancement.",
                 "Offshore wind farms (EMODnet), whatever their stage."),
         fiche=fiche("Parc éolien en mer", "#9fb39a",
                     [("Nom", "nom"), ("Pays", "pays"), ("État", "etat_fr"), ("Puissance (MW)", "puissance_mw"),
                      ("Éoliennes", "nb_eoliennes")])),
    dict(nom="mouillage", style="wa_mouillage", groupe="infrastructures", visible=False,
         titre=("Zones de mouillage", "Anchorages"),
         resume=("Mouillages cartographiés et points de mouillage (rayon d'un mille), OpenStreetMap.",
                 "Mapped anchorages and anchorage points (one-mile radius), OpenStreetMap."),
         fiche=fiche("Mouillage", "#7c9cb6", [("Nom", "nom"), ("Nature", "nature")])),

    # --- Limites
    dict(nom="zone_etude", style="wa_zone_etude", groupe="limites", visible=True, fiche=None,
         titre=("Aire d'étude", "Study area"),
         resume=("Détroits danois et bassin de Bornholm.", "Danish Straits and Bornholm Basin.")),
    dict(nom="limite_zee", style="wa_limite_zee", groupe="limites", visible=True,
         titre=("Limites des zones économiques exclusives", "Exclusive economic zone boundaries"),
         resume=("Limites maritimes entre États (Marine Regions, CC BY 4.0).", "Maritime boundaries between states (Marine Regions, CC BY 4.0)."),
         fiche=fiche("Limite maritime", "#7f8c96", [("Limite", "nom"), ("Nature", "nature")])),
    dict(nom="mer_territoriale", style="wa_mer_territoriale", groupe="limites", visible=False, fiche=None,
         titre=("Mer territoriale (12 milles)", "Territorial sea (12 NM)"),
         resume=("Eaux territoriales de 12 milles marins (Marine Regions).", "12-nautical-mile territorial waters (Marine Regions).")),
    dict(nom="zone_fiche", style="wa_zone_fiche", groupe="limites", visible=False,
         titre=("Zones des fiches", "Zone sheets"),
         resume=("Aire d'étude et part de chaque ZEE qui s'y trouve, avec leurs chiffres clés.",
                 "Study area and the share of each EEZ within it, with their key figures."),
         fiche=fiche("Zone", "#8a877f",
                     [("Zone", "nom_fr"), ("Navires", "nb_navires"), ("Silences AIS", "nb_silences"),
                      ("… dus à la réception côtière", "nb_reception"), ("Silences inexpliqués", "nb_inexpliquees"),
                      ("Navires au MMSI partagé", "nav_mmsi_partage"), ("Passages lents sur infrastructure", "nb_stationnements"),
                      ("Rencontres", "nb_rencontres"), ("Détections radar sans AIS", "nb_radar_sans_ais"),
                      ("Trafic en eaux bien couvertes", "couverte_txt")])),

    # --- Traces
    dict(nom="trace", style="wa_traces", groupe="traces", visible=False,
         titre=("Traces des navires", "Vessel tracks"),
         resume=("Traces des navires de classe A pendant la semaine d'étude, par type de navire (pseudonymisées).",
                 "Class A vessel tracks during the study week, by vessel type (pseudonymised)."),
         fiche=fiche("Trace", "#2a78d6", [NAVIRE, ("Type", "famille_fr")])),
]

# Fond cartographique du projet (terres sur mer claire), publié aussi
FOND = dict(nom="terre_large", style="wa_terre", titre=("Terres émergées", "Land"),
            resume=("Terres émergées (Eurostat GISCO, © EuroGeographics).", "Land (Eurostat GISCO, © EuroGeographics)."))

# Signets : nom fr, nom en, ouest, sud, est, nord (WGS84), repris du projet QGIS
SIGNETS = [
    ("Aire d'étude", "Study area", 9.0, 53.9, 16.5, 58.2),
    ("Rade de Skagen (rencontres)", "Skagen roads (encounters)", 10.2, 57.45, 11.1, 57.9),
    ("Bassin d'Arkona", "Arkona Basin", 12.6, 54.6, 14.3, 55.4),
    ("Entrée du canal de Kiel", "Kiel Canal entrance", 9.8, 54.25, 10.4, 54.5),
    ("Belt de Fehmarn", "Fehmarn Belt", 10.9, 54.35, 11.7, 54.75),
    ("Øresund", "Øresund", 12.4, 55.5, 13.0, 56.15),
    ("Bornholm", "Bornholm", 14.5, 54.9, 15.4, 55.4),
    ("Baie de Poméranie (bord de couverture)", "Pomeranian Bay (coverage edge)", 13.5, 53.9, 14.7, 54.6),
]
