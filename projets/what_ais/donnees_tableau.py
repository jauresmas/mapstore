"""Tables du tableau de bord : bilans chiffrés du dépôt (carte/donnees/*.json) chargés dans PostGIS pour que
les compteurs et graphiques MapStore les interrogent comme les autres couches (WFS + WPS gs:Aggregate).

Chaque ligne porte la géométrie de l'aire d'étude : GeoServer publie ainsi des couches ordinaires, et un
graphique lié à la carte du tableau de bord les garde tant que l'aire d'étude est visible.
"""
import json

from commun import DEPOT

DONNEES = DEPOT / "carte" / "donnees"

# Libellés des semaines : le préfixe garde l'ordre chronologique quand MapStore trie par libellé
SEMAINES_FR = {"2026-09-22": "1 · 22 sept.", "2026-09-29": "2 · 29 sept.",
               "2026-10-06": "3 · 6 oct.", "2026-10-13": "4 · 13 oct. (étude)"}
CLASSES_FR = {"Reliable": "Fiable", "Degraded": "Dégradée", "Not enough traffic": "Trafic insuffisant",
              "Poor": "Mauvaise"}
# Causes des silences (catégories du dépôt), en libellés courts pour l'axe des graphiques
CAUSES_FR = {
    "navire de servitude ou d'État": "Servitude, État",
    "navigation intérieure ou portuaire": "Port, eaux intérieures",
    "sortie de la zone": "Sortie de zone",
    "réception insuffisante probable": "Réception côtière",
    "arrêt au port ou au mouillage": "Port, mouillage",
    "escale ou détour côtier possible": "Escale, détour",
    "sortie de couverture possible": "Sortie de couverture",
    "coupure inexpliquée": "Inexpliqué",
    "position incohérente": "Position incohérente",
}

TABLES = [  # couches GeoServer propres au tableau de bord (absentes de la carte)
    {"nom": "bilan_semaines", "style": "wa_zone_etude", "groupe": None, "visible": False,
     "titre": ("Bilan des quatre semaines", "Four-week summary"),
     "resume": ("Chiffres clés de la semaine d'étude et des trois semaines précédentes, une ligne par semaine.",
                "Key figures for the study week and the three weeks before it, one row per week.")},
    {"nom": "bilan_etude", "style": "wa_zone_etude", "groupe": None, "visible": False,
     "titre": ("Bilan de la semaine d'étude", "Study week summary"),
     "resume": ("Chiffres clés du 13 au 19 octobre 2026 (une ligne).",
                "Key figures for 13–19 October 2026 (one row).")},
    {"nom": "validation_radar", "style": "wa_zone_etude", "groupe": None, "visible": False,
     "titre": ("Validation par le radar satellitaire", "Validation by satellite radar"),
     "resume": ("Part des navires vus par le radar Sentinel-1 et reçus par le réseau AIS côtier, selon la classe "
                "de couverture mesurée de la maille.",
                "Share of vessels seen by Sentinel-1 radar and received by the shore AIS network, by measured "
                "coverage class of the cell.")},
    {"nom": "tableau_silences_inexpliques", "style": "wa_silence_inexplique", "groupe": None, "visible": False,
     "titre": ("Silences inexpliqués (tableau)", "Unexplained silences (table)"),
     "resume": ("Les silences inexpliqués de la semaine d'étude, colonnes mises en forme pour le tableau de bord.",
                "Unexplained silences of the study week, columns formatted for the dashboard.")},
]


def _texte(v):
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"


def sql():
    chiffres = json.loads((DONNEES / "chiffres.json").read_text(encoding="utf-8"))
    semaines = json.loads((DONNEES / "semaines.json").read_text(encoding="utf-8"))["semaines"]
    etude = max(s["semaine"] for s in semaines)

    lignes_semaines = ",\n".join(
        f"({i}, DATE '{s['semaine']}', {_texte(SEMAINES_FR.get(s['semaine'], s['semaine']))}, "
        f"{'true' if s['semaine'] == etude else 'false'}, {s['nb_navires']}, {s['nb_silences']}, "
        f"{s['nb_reception']}, {s['nb_inexpliquees']}, {s['nav_inexpliquees']}, {s['nav_mmsi_partage']}, "
        f"{s['nb_stationnements']}, {s['nb_rencontres']}, {round(s['part_couverte'] * 100, 1)})"
        for i, s in enumerate(semaines, 1))
    lignes_radar = ",\n".join(
        f"({i}, {_texte(v['classe'])}, {_texte(CLASSES_FR.get(v['classe'], v['classe']))}, {v['n']}, "
        f"{v['recus']}, {round(v['part'] * 100, 1)})"
        for i, v in enumerate(chiffres.get("validation_radar", []), 1))
    causes = "\n".join(f"        WHEN {_texte(k)} THEN {_texte(v)}" for k, v in CAUSES_FR.items())

    return f"""
SET search_path = carto, public;
DROP VIEW IF EXISTS bilan_etude, tableau_silences_inexpliques;
DROP TABLE IF EXISTS bilan_semaines, validation_radar;

CREATE TABLE bilan_semaines (
    fid integer PRIMARY KEY, semaine date, semaine_fr text, etude boolean,
    nb_navires integer, nb_silences integer, nb_reception integer, nb_inexpliquees integer,
    nav_inexpliquees integer, nav_mmsi_partage integer, nb_stationnements integer, nb_rencontres integer,
    couverte_pct numeric(4,1), nb_radar_sans_ais integer, geom geometry(MultiPolygon, 4326));
INSERT INTO bilan_semaines (fid, semaine, semaine_fr, etude, nb_navires, nb_silences, nb_reception,
    nb_inexpliquees, nav_inexpliquees, nav_mmsi_partage, nb_stationnements, nb_rencontres, couverte_pct)
VALUES
{lignes_semaines};
UPDATE bilan_semaines SET nb_radar_sans_ais = {int(chiffres.get('nb_radar_sans_ais') or 0)} WHERE etude;
UPDATE bilan_semaines SET geom = (SELECT ST_Multi(ST_Union(geom))::geometry(MultiPolygon, 4326) FROM zone_etude);

CREATE TABLE validation_radar (
    fid integer PRIMARY KEY, classe text, classe_fr text, detections integer, recues integer,
    part_recue_pct numeric(4,1), geom geometry(MultiPolygon, 4326));
INSERT INTO validation_radar (fid, classe, classe_fr, detections, recues, part_recue_pct) VALUES
{lignes_radar};
UPDATE validation_radar SET geom = (SELECT ST_Multi(ST_Union(geom))::geometry(MultiPolygon, 4326) FROM zone_etude);

CREATE VIEW bilan_etude AS SELECT * FROM bilan_semaines WHERE etude;

ALTER TABLE silence_ais ADD COLUMN IF NOT EXISTS cause_fr text;
UPDATE silence_ais SET cause_fr = CASE categorie
{causes}
        ELSE categorie END;

CREATE VIEW tableau_silences_inexpliques AS
SELECT fid, navire, famille_fr AS type_navire, debut_txt AS debut_utc, fin_txt AS fin_utc, duree_txt AS duree,
       distance_txt AS distance, couverte_txt AS part_eaux_couvertes, debut, geom
FROM silence_ais WHERE categorie = 'coupure inexpliquée';

ANALYZE bilan_semaines; ANALYZE validation_radar; ANALYZE silence_ais;
"""
