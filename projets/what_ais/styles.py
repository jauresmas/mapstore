"""Styles SLD 1.0 des couches, d'après scripts/07_projet_qgis.py du dépôt (même palette, lisible par
les daltoniens). Les épaisseurs QGIS en millimètres sont converties pour l'écran (1 mm ≈ 3,8 px),
puis légèrement renforcées : une carte web se lit à 100 %, pas sur une feuille A4.
Les titres des règles sont les libellés de la légende, en français.
"""
from xml.sax.saxutils import escape

# Palette du projet
MER, TERRE, COTE = "#edf1f3", "#e7e3db", "#b8b0a2"
ENCRE, ENCRE_2, ENCRE_3 = "#1d1d1b", "#52514e", "#8a877f"
ORANGE, VIOLET, BLEU, VERT_EAU = "#eb6834", "#4a3aa7", "#2a78d6", "#1baf7a"
POLICE = "Segoe UI"
FAMILLES = [("Cargo", "Cargo", "#2a78d6"), ("Pétrolier ou chimiquier", "Tanker", "#eb6834"),
            ("Passagers", "Passenger", "#1baf7a"), ("Pêche", "Fishing", "#eda100"),
            ("Service et autorités", "Service & authorities", "#e87ba4"),
            ("Autre ou inconnu", "Other / unknown", "#008300")]


# --- Briques -------------------------------------------------------------------------------
def css(nom, valeur):
    return f'<CssParameter name="{nom}">{valeur}</CssParameter>'


def trait(couleur, largeur, opacite=1.0, tirets=None, bout="butt"):
    p = css("stroke", couleur) + css("stroke-width", largeur) + css("stroke-linejoin", "round") + css("stroke-linecap", bout)
    if opacite < 1:
        p += css("stroke-opacity", opacite)
    if tirets:
        p += css("stroke-dasharray", tirets)
    return f"<Stroke>{p}</Stroke>"


def plein(couleur, opacite=1.0):
    return f"<Fill>{css('fill', couleur)}{css('fill-opacity', opacite) if opacite < 1 else ''}</Fill>"


def hachure_fill(couleur, ecart=8, largeur=1.0):
    return (f"<Fill><GraphicFill><Graphic><Mark><WellKnownName>shape://slash</WellKnownName>"
            f"{trait(couleur, largeur)}</Mark><Size>{ecart}</Size></Graphic></GraphicFill></Fill>")


def geometrie(fonction):
    if not fonction:
        return ""
    return (f'<Geometry><ogc:Function name="{fonction}"><ogc:PropertyName>geom</ogc:PropertyName>'
            f"</ogc:Function></Geometry>")


def polygone(fond=None, opacite=1.0, contour=None, largeur=0.5, tirets=None, opacite_contour=1.0, hachure=None):
    remplissage = hachure if hachure else (plein(fond, opacite) if fond else "")
    bord = trait(contour, largeur, opacite_contour, tirets) if contour else ""
    return f"<PolygonSymbolizer>{remplissage}{bord}</PolygonSymbolizer>"


def ligne(couleur, largeur, opacite=1.0, tirets=None, bout="butt"):
    return f"<LineSymbolizer>{trait(couleur, largeur, opacite, tirets, bout)}</LineSymbolizer>"


def marque(forme, taille, fond, contour="#ffffff", largeur=1.0, rotation=0, geom=None, opacite=1.0):
    rot = f"<Rotation>{rotation}</Rotation>" if rotation else ""
    return (f"<PointSymbolizer>{geometrie(geom)}<Graphic><Mark><WellKnownName>{forme}</WellKnownName>"
            f"{plein(fond, opacite)}{trait(contour, largeur) if contour else ''}</Mark>"
            f"<Size>{taille}</Size>{rot}</Graphic></PointSymbolizer>")


def texte(champ, taille, couleur, style="normal", poids="normal", halo=None, rayon_halo=1.5,
          ancre=(0.5, 0.5), decalage=(0, 0), priorite=None, espace=None, majuscules=False):
    police = (css("font-family", POLICE) + css("font-size", taille) + css("font-style", style)
              + css("font-weight", poids))
    etiquette = f"<ogc:PropertyName>{champ}</ogc:PropertyName>"
    if majuscules:
        etiquette = f'<ogc:Function name="strToUpperCase">{etiquette}</ogc:Function>'
    h = f"<Halo><Radius>{rayon_halo}</Radius>{plein(halo)}</Halo>" if halo else ""
    placement = (f"<LabelPlacement><PointPlacement><AnchorPoint><AnchorPointX>{ancre[0]}</AnchorPointX>"
                 f"<AnchorPointY>{ancre[1]}</AnchorPointY></AnchorPoint><Displacement>"
                 f"<DisplacementX>{decalage[0]}</DisplacementX><DisplacementY>{decalage[1]}</DisplacementY>"
                 f"</Displacement></PointPlacement></LabelPlacement>")
    # Priority doit précéder les VendorOption dans le schéma SLD
    prio = f"<Priority>{priorite}</Priority>" if priorite else ""
    vendeur = '<VendorOption name="conflictResolution">true</VendorOption>' + (
        f'<VendorOption name="charSpacing">{espace}</VendorOption>' if espace else "")
    return (f"<TextSymbolizer><Label>{etiquette}</Label><Font>{police}</Font>{placement}{h}"
            f"{plein(couleur)}{prio}{vendeur}</TextSymbolizer>")


# --- Filtres -------------------------------------------------------------------------------
def egal(champ, valeur):
    return (f"<ogc:PropertyIsEqualTo><ogc:PropertyName>{champ}</ogc:PropertyName>"
            f"<ogc:Literal>{escape(str(valeur))}</ogc:Literal></ogc:PropertyIsEqualTo>")


def entre(champ, mini=None, maxi=None):
    """mini inclus, maxi exclu (comme les classes graduées de QGIS, bornes contiguës)."""
    conds = []
    if mini is not None:
        conds.append(f"<ogc:PropertyIsGreaterThanOrEqualTo><ogc:PropertyName>{champ}</ogc:PropertyName>"
                     f"<ogc:Literal>{mini}</ogc:Literal></ogc:PropertyIsGreaterThanOrEqualTo>")
    if maxi is not None:
        conds.append(f"<ogc:PropertyIsLessThan><ogc:PropertyName>{champ}</ogc:PropertyName>"
                     f"<ogc:Literal>{maxi}</ogc:Literal></ogc:PropertyIsLessThan>")
    return conds[0] if len(conds) == 1 else f"<ogc:And>{''.join(conds)}</ogc:And>"


def regle(titre, *symboles, filtre=None, echelle_min=None, echelle_max=None):
    f = f"<ogc:Filter>{filtre}</ogc:Filter>" if filtre else ""
    mini = f"<MinScaleDenominator>{echelle_min}</MinScaleDenominator>" if echelle_min else ""
    maxi = f"<MaxScaleDenominator>{echelle_max}</MaxScaleDenominator>" if echelle_max else ""
    return f"<Rule><Name>{escape(titre)}</Name><Title>{escape(titre)}</Title>{f}{mini}{maxi}{''.join(symboles)}</Rule>"


def sld(nom, titre, *styles_de_rendu):
    """styles_de_rendu : listes de règles, une FeatureTypeStyle chacune (dessinées dans l'ordre)."""
    fts = "".join(f"<FeatureTypeStyle>{''.join(r)}</FeatureTypeStyle>" for r in styles_de_rendu)
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<StyledLayerDescriptor version="1.0.0" xmlns="http://www.opengis.net/sld" '
            'xmlns:ogc="http://www.opengis.net/ogc" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/sld '
            'http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">'
            f"<NamedLayer><Name>{nom}</Name><UserStyle><Name>{nom}</Name><Title>{escape(titre)}</Title>"
            f"{fts}</UserStyle></NamedLayer></StyledLayerDescriptor>")


# --- Styles des couches --------------------------------------------------------------------
def styles():
    s = {}

    s["wa_terre"] = sld("wa_terre", "Terres émergées", [regle("Terres émergées", polygone(TERRE, contour=COTE, largeur=0.6))])

    rampe = ["#e2e8ec", "#d4dde3", "#c2cfd7", "#aebfc9", "#97aab6"]
    bornes = [(None, 2, "moins de 2"), (2, 10, "2 à 10"), (10, 40, "10 à 40"), (40, 150, "40 à 150"), (150, None, "plus de 150")]
    s["wa_trafic"] = sld("wa_trafic", "Densité du trafic", [
        regle(f"{lib} heures-navire", polygone(col), filtre=entre("heures_navire", a, b))
        for (a, b, lib), col in zip(bornes, rampe)])

    s["wa_couverture"] = sld("wa_couverture", "Couverture AIS côtière", [
        regle("Fiable", polygone("#d5e5dd", contour="#ffffff", largeur=0.3), filtre=egal("classe", "Reliable")),
        regle("Dégradée", polygone("#f2c79b", contour="#ffffff", largeur=0.3), filtre=egal("classe", "Degraded")),
        regle("Mauvaise : navires perdus", polygone("#d8693f", contour="#ffffff", largeur=0.3), filtre=egal("classe", "Poor")),
        regle("Trafic insuffisant pour juger", polygone(hachure=hachure_fill("#bdbdb8", 7, 1.0)),
              filtre=egal("classe", "Not enough traffic")),
    ])

    s["wa_lacunes"] = sld("wa_lacunes", "Mauvaise réception AIS côtière", [
        regle("Mauvaise réception AIS côtière", polygone(hachure=hachure_fill("#6f6c66", 6, 0.9), contour="#6f6c66",
                                                         largeur=0.4, opacite_contour=0.5))])

    s["wa_indice"] = sld("wa_indice", "Indice de vigilance", [
        regle("Faible (1 à 15)", polygone("#fbd8c7", contour="#ffffff", largeur=0.4), filtre=entre("indice", 0.0001, 15)),
        regle("Moyen (15 à 30)", polygone("#f2a07a", contour="#ffffff", largeur=0.4), filtre=entre("indice", 15, 30)),
        regle("Élevé (plus de 30)", polygone("#c24f22", contour="#ffffff", largeur=0.4), filtre=entre("indice", 30)),
    ])

    s["wa_recurrence"] = sld("wa_recurrence", "Angles morts sur quatre semaines", [
        regle("Chronique : mauvaise 3 ou 4 semaines sur 4", polygone("#a63c14", contour="#ffffff", largeur=0.3), filtre=egal("statut", "Chronic")),
        regle("Récurrent : mauvaise 2 semaines", polygone("#e0784a", contour="#ffffff", largeur=0.3), filtre=egal("statut", "Recurring")),
        regle("Ponctuel : mauvaise une seule semaine", polygone("#f6cdb3", contour="#ffffff", largeur=0.3), filtre=egal("statut", "One-off")),
        regle("Jamais mauvaise", polygone("#dfe8e2", contour="#ffffff", largeur=0.3), filtre=egal("statut", "Never poor")),
    ])

    s["wa_foyers"] = sld("wa_foyers", "Silences inexpliqués récurrents", [
        regle("Silences inexpliqués au moins 2 semaines (zone de 250 km²)",
              polygone(ORANGE, 0.35, contour=ORANGE, largeur=1.6))])

    s["wa_infrastructure"] = sld("wa_infrastructure", "Câbles et pipelines sous-marins", [
        regle("Pipeline", ligne("#6f675d", 2.1), filtre=egal("categorie", "pipeline")),
        regle("Câble électrique", ligne("#8a8378", 1.2), filtre=egal("categorie", "câble électrique")),
        regle("Câble de télécommunication", ligne("#8a8378", 1.2, tirets="7 3.5"), filtre=egal("categorie", "câble de télécommunication")),
        regle("Câble, usage non précisé", ligne("#a39d93", 1.0, tirets="2 4"), filtre=egal("categorie", "câble (usage non précisé)")),
    ])

    s["wa_parc_eolien"] = sld("wa_parc_eolien", "Parcs éoliens en mer", [
        regle("Parc éolien en mer", polygone("#dde5d9", contour="#9fb39a", largeur=0.8))])
    s["wa_mouillage"] = sld("wa_mouillage", "Zones de mouillage", [
        regle("Zone de mouillage", polygone("#dfe9f1", 0.9, contour="#7c9cb6", largeur=0.9, tirets="4 2.5"))])

    s["wa_limite_zee"] = sld("wa_limite_zee", "Limites des ZEE", [
        regle("Limite de zone économique exclusive", ligne("#7f8c96", 1.2, tirets="8 4.5"))])
    s["wa_mer_territoriale"] = sld("wa_mer_territoriale", "Mer territoriale (12 milles)", [
        regle("Mer territoriale (12 milles)", polygone(contour="#a3adb4", largeur=0.8, tirets="1 3"))])
    s["wa_zone_etude"] = sld("wa_zone_etude", "Aire d'étude", [
        regle("Aire d'étude", polygone(contour=ENCRE, largeur=1.4))])
    s["wa_zone_fiche"] = sld("wa_zone_fiche", "Zones des fiches", [
        regle("Zone de fiche (aire d'étude ou part d'une ZEE)", polygone(contour=ENCRE_3, largeur=1.2, tirets="6 3"),
              texte("nom_fr", 12, ENCRE_2, poids="bold", halo="#ffffff", rayon_halo=2))])

    s["wa_station_ais"] = sld("wa_station_ais", "Stations AIS côtières", [
        regle("Station AIS côtière", marque("triangle", 9, "#3d3d3a", "#ffffff", 0.8))])

    # Silence inexpliqué : trajet supposé en tirets orange sur liseré blanc, début creux, fin pleine
    s["wa_silence_inexplique"] = sld("wa_silence_inexplique", "Silence AIS inexpliqué", [
        regle("Silence AIS inexpliqué : trajet supposé, du début (creux) à la fin (plein)",
              ligne("#ffffff", 4.5, 0.9, bout="round"), ligne(ORANGE, 2.2, tirets="6 4"),
              marque("circle", 10, "#ffffff", ORANGE, 1.8, geom="startPoint"),
              marque("circle", 10, ORANGE, "#ffffff", 1.2, geom="endPoint"))])

    gris = [("coupure inexpliquée", "Inexpliqué", ORANGE, 9),
            ("réception insuffisante probable", "Trou de réception côtière", "#5f7d95", 6),
            ("sortie de couverture possible", "Sortie de couverture possible", "#9aa7b1", 6),
            ("escale ou détour côtier possible", "Escale ou détour côtier possible", "#9aa7b1", 6),
            ("sortie de la zone", "Sortie de l'aire d'étude", "#b3b8bc", 5),
            ("arrêt au port ou au mouillage", "Arrêt au port ou au mouillage", "#c4c2bc", 5),
            ("navigation intérieure ou portuaire", "Navigation intérieure ou portuaire", "#c4c2bc", 5),
            ("navire de servitude ou d'État", "Navire de servitude ou d'État", "#c4c2bc", 5),
            ("position incohérente", "Position incohérente", "#c4c2bc", 5)]
    ordinaires = [regle(lib, marque("circle", t, col, "#ffffff", 0.7, geom="startPoint"), filtre=egal("categorie", cat))
                  for cat, lib, col, t in gris[1:]][::-1]
    cat, lib, col, t = gris[0]
    s["wa_silences_tous"] = sld("wa_silences_tous", "Tous les silences AIS (point de départ)", ordinaires,
                                [regle(lib, marque("circle", t, col, "#ffffff", 0.9, geom="startPoint"), filtre=egal("categorie", cat))])

    s["wa_mmsi_partage"] = sld("wa_mmsi_partage", "MMSI partagé par deux émetteurs", [
        regle("MMSI partagé : saut de position impossible entre deux émetteurs",
              ligne(VIOLET, 0.7, 0.32), marque("circle", 6, VIOLET, "#ffffff", 0.8, geom="startPoint"),
              marque("circle", 6, VIOLET, "#ffffff", 0.8, geom="endPoint"))])

    s["wa_stationnement"] = sld("wa_stationnement", "Passage lent au-dessus d'un câble ou pipeline", [
        regle("Passage lent (moins de 2 nœuds, 30 min ou plus) au-dessus d'un câble ou pipeline",
              marque("square", 9, BLEU, "#ffffff", 1.1, rotation=45))])

    s["wa_rencontre"] = sld("wa_rencontre", "Rencontre en mer", [
        regle("Rencontre en mer (moins de 500 m, 2 h ou plus)", marque("circle", 11, VERT_EAU, "#ffffff", 1.2))])

    s["wa_radar"] = sld("wa_radar", "Détection radar sans AIS", [
        regle("Détection radar Sentinel-1 sans AIS (hors parcs éoliens)", marque("square", 7, "#ffffff", ENCRE_2, 1.3))])

    semaines = [("1. Sem. du 22 sept.", "Semaine du 22 septembre", "#f6cdb3"),
                ("2. Sem. du 29 sept.", "Semaine du 29 septembre", "#f2a07a"),
                ("3. Sem. du 6 oct.", "Semaine du 6 octobre", "#e0784a"),
                ("4. Sem. du 13 oct. (étude)", "Semaine du 13 octobre (semaine d'étude)", "#a63c14")]
    s["wa_inexpliquee_semaines"] = sld("wa_inexpliquee_semaines", "Silences inexpliqués, quatre semaines", [
        regle(lib, marque("circle", 10, col, "#ffffff", 1.1), filtre=egal("semaine_fr", val)) for val, lib, col in semaines])

    s["wa_traces"] = sld("wa_traces", "Traces des navires", [
        regle(fr, ligne(col, 0.8, 0.5), filtre=egal("famille", en)) for fr, en, col in FAMILLES])

    s["wa_lieux"] = sld("wa_lieux", "Repères", [
        regle("Ville", marque("circle", 5, ENCRE_2, "#ffffff", 0.8),
              texte("nom_fr", 11, "#3d3d3a", halo="#ffffff", ancre=(0, 0.5), decalage=(6, 0), priorite=500),
              filtre=egal("nature", "ville")),
        regle("Mer", texte("nom_fr", 12.5, "#6c8495", style="italic", halo=MER, rayon_halo=2, priorite=900, espace=1),
              filtre=egal("nature", "mer")),
        regle("Pays", texte("nom_fr", 13, "#a39b8e", espace=4, priorite=1000), filtre=egal("nature", "pays")),
        regle("Île", texte("nom_fr", 11, "#7a7266", style="italic", halo=TERRE, priorite=700), filtre=egal("nature", "ile")),
    ])
    return s
