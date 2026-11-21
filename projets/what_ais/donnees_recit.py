"""Couches propres à la GeoStory : les trois cas racontés par la carte web du dépôt
(carte/donnees/recits.json, navires pseudonymisés) et la validation radar point par point.

    recit_silence_ligne     route avant le silence, route après, trajet supposé pendant le silence
    recit_silence_point     dernière position avant le silence, première position au retour
    recit_silence_cercle    position attendue au passage du satellite (cercle de 5 km)
    recit_silence_radar     échos Sentinel-1 du passage, classés comme dans le dépôt
    recit_identite_position positions annoncées sous le MMSI partagé
    recit_identite_saut     sauts impossibles entre les deux émetteurs
    recit_radar_validation  navires vus et identifiés par le radar, reçus ou non par l'AIS côtier
"""
import json

from commun import DEPOT
from styles import ENCRE_2, ORANGE, VIOLET, egal, ligne, marque, polygone, regle, sld

RECITS = DEPOT / "carte" / "donnees" / "recits.json"

ETATS_RADAR = {0: "reçu par l'AIS côtier", 1: "identifié, non reçu par l'AIS côtier", 2: "aucun AIS",
               3: "aucun AIS, près du navire silencieux"}

TABLES = [
    {"nom": "recit_silence_ligne", "style": "wa_recit_silence_ligne",
     "titre": ("Récit : route du navire silencieux", "Story: silent vessel route"),
     "resume": ("Route reçue avant et après le silence, trajet supposé pendant le silence.",
                "Route received before and after the silence, assumed path during the silence.")},
    {"nom": "recit_silence_point", "style": "wa_recit_silence_point",
     "titre": ("Récit : début et fin du silence", "Story: start and end of the silence"),
     "resume": ("Dernière position reçue avant le silence et première position au retour de l'AIS.",
                "Last position received before the silence and first position when AIS returns.")},
    {"nom": "recit_silence_cercle", "style": "wa_recit_silence_cercle",
     "titre": ("Récit : position attendue au passage du satellite", "Story: expected position at the satellite pass"),
     "resume": ("Cercle de 5 km autour de la position attendue sur le trajet supposé, à l'heure du passage.",
                "5 km ring around the expected position on the assumed path, at the time of the pass.")},
    {"nom": "recit_silence_radar", "style": "wa_recit_radar",
     "titre": ("Récit : échos radar du passage", "Story: radar echoes of the pass"),
     "resume": ("Échos Sentinel-1 du passage, selon qu'ils correspondent ou non à un navire AIS.",
                "Sentinel-1 echoes of the pass, by whether they match an AIS vessel.")},
    {"nom": "recit_identite_position", "style": "wa_recit_identite_position",
     "titre": ("Récit : positions annoncées sous le MMSI partagé", "Story: positions reported under the shared MMSI"),
     "resume": ("Positions reçues sous un même MMSI, environ une par minute.",
                "Positions received under one MMSI, about one a minute.")},
    {"nom": "recit_identite_saut", "style": "wa_recit_identite_saut",
     "titre": ("Récit : sauts impossibles", "Story: impossible jumps"),
     "resume": ("Sauts d'une position à l'autre, d'un émetteur à l'autre, en une ou deux minutes.",
                "Jumps from one position to the other, one transmitter to the other, within a minute or two.")},
    {"nom": "recit_radar_validation", "style": "wa_recit_radar_validation",
     "titre": ("Récit : validation par le radar", "Story: validation by radar"),
     "resume": ("Navires vus et identifiés par Sentinel-1, reçus ou non par le réseau AIS côtier danois.",
                "Vessels seen and identified by Sentinel-1, received or not by the Danish shore AIS network.")},
]
for t in TABLES:
    t.update(groupe="recit", visible=True, fiche=None)


def _wkt_ligne(points):
    return "LINESTRING(" + ",".join(f"{p[0]} {p[1]}" for p in points) + ")"


def sql():
    r = json.loads(RECITS.read_text(encoding="utf-8"))
    s, m = r["silence"], r["identite"]
    avant = [p for p in s["trace"] if p[2] <= s["debut"]]
    apres = [p for p in s["trace"] if p[2] >= s["fin"]]
    d, f = avant[-1], apres[0]
    k = (s["passe"] - d[2]) / (f[2] - d[2])
    attendu = (d[0] + k * (f[0] - d[0]), d[1] + k * (f[1] - d[1]))

    lignes = [("route", _wkt_ligne(avant)), ("retour", _wkt_ligne(apres)), ("suppose", _wkt_ligne([d, f]))]
    radar = ",\n".join(f"({i}, {e}, '{ETATS_RADAR[e].replace(chr(39), chr(39) * 2)}', "
                       f"ST_SetSRID(ST_Point({x}, {y}), 4326))" for i, (x, y, e) in enumerate(s["radar"], 1))
    positions = ",\n".join(f"({i}, {p[2]}, ST_SetSRID(ST_Point({p[0]}, {p[1]}), 4326))"
                           for i, p in enumerate(m["positions"], 1))
    sauts = ",\n".join(f"({i}, {t}, ST_SetSRID(ST_MakeLine(ST_Point({x1}, {y1}), ST_Point({x2}, {y2})), 4326))"
                       for i, (x1, y1, x2, y2, t) in enumerate(m["sauts"], 1))
    return f"""
SET search_path = carto, public;
DROP VIEW IF EXISTS recit_radar_validation;
DROP TABLE IF EXISTS recit_silence_ligne, recit_silence_point, recit_silence_cercle, recit_silence_radar,
    recit_identite_position, recit_identite_saut;

CREATE TABLE recit_silence_ligne (fid integer PRIMARY KEY, partie text, navire text, geom geometry(LineString, 4326));
INSERT INTO recit_silence_ligne VALUES
{",".join(f"({i}, '{p}', '{s['navire']}', ST_GeomFromText('{w}', 4326))" for i, (p, w) in enumerate(lignes, 1))};

CREATE TABLE recit_silence_point (fid integer PRIMARY KEY, role text, minute integer, geom geometry(Point, 4326));
INSERT INTO recit_silence_point VALUES
(1, 'muet', {d[2]}, ST_SetSRID(ST_Point({d[0]}, {d[1]}), 4326)),
(2, 'retour', {f[2]}, ST_SetSRID(ST_Point({f[0]}, {f[1]}), 4326));

CREATE TABLE recit_silence_cercle (fid integer PRIMARY KEY, geom geometry(Polygon, 4326));
INSERT INTO recit_silence_cercle VALUES
(1, ST_Buffer(ST_SetSRID(ST_Point({attendu[0]}, {attendu[1]}), 4326)::geography, 5000, 32)::geometry(Polygon, 4326));

CREATE TABLE recit_silence_radar (fid integer PRIMARY KEY, etat integer, etat_fr text, geom geometry(Point, 4326));
INSERT INTO recit_silence_radar VALUES
{radar};

CREATE TABLE recit_identite_position (fid integer PRIMARY KEY, minute integer, geom geometry(Point, 4326));
INSERT INTO recit_identite_position VALUES
{positions};

CREATE TABLE recit_identite_saut (fid integer PRIMARY KEY, minute integer, geom geometry(LineString, 4326));
INSERT INTO recit_identite_saut VALUES
{sauts};

CREATE VIEW recit_radar_validation AS
SELECT fid, recu_par_reseau AS recu, classe_couverture, couverture_fr, instant_txt, geom
FROM detection_radar WHERE recu_par_reseau IS NOT NULL;

CREATE INDEX ON recit_identite_position USING gist (geom);
ANALYZE recit_silence_ligne; ANALYZE recit_silence_point; ANALYZE recit_silence_radar;
ANALYZE recit_identite_position; ANALYZE recit_identite_saut;
"""


def styles():
    """Symboles repris de la carte web du dépôt (récits)."""
    s = {}
    s["wa_recit_silence_ligne"] = sld("wa_recit_silence_ligne", "Route du navire silencieux", [
        regle("Route reçue par l'AIS", ligne("#a8461f", 2.2, 0.9, bout="round"),
              filtre=f"<ogc:Not>{egal('partie', 'suppose')}</ogc:Not>"),
        regle("Trajet supposé pendant le silence", ligne(ORANGE, 1.8, 0.85, tirets="2 4"),
              filtre=egal("partie", "suppose"))])
    s["wa_recit_silence_point"] = sld("wa_recit_silence_point", "Début et fin du silence", [
        regle("Dernière position reçue (l'AIS se tait)", marque("circle", 13, "#ffffff", ORANGE, 2.6),
              filtre=egal("role", "muet")),
        regle("Retour de l'AIS", marque("circle", 13, ORANGE, "#ffffff", 1.8), filtre=egal("role", "retour"))])
    s["wa_recit_silence_cercle"] = sld("wa_recit_silence_cercle", "Position attendue au passage", [
        regle("Position attendue au passage du satellite (cercle de 5 km)",
              polygone(ORANGE, 0.08, ORANGE, 1.6, tirets="4 3"))])
    s["wa_recit_radar"] = sld("wa_recit_radar", "Échos radar du passage", [
        regle(ETATS_RADAR[0], marque("circle", 7, "#8d9aa4", "#ffffff", 0.8), filtre=egal("etat", 0)),
        regle(ETATS_RADAR[1], marque("circle", 9, ORANGE, "#ffffff", 1.2), filtre=egal("etat", 1)),
        regle(ETATS_RADAR[2], marque("square", 9, "#ffffff", ENCRE_2, 1.6), filtre=egal("etat", 2)),
        regle(ETATS_RADAR[3], marque("square", 9, "#ffffff", ENCRE_2, 1.6),
              marque("circle", 28, "#ffffff", ORANGE, 2.5, opacite=0.0), filtre=egal("etat", 3))])
    s["wa_recit_identite_position"] = sld("wa_recit_identite_position", "Positions annoncées", [
        regle("Position annoncée sous le MMSI", marque("circle", 5, VIOLET, "#ffffff", 0.6, opacite=0.75))])
    s["wa_recit_identite_saut"] = sld("wa_recit_identite_saut", "Sauts impossibles", [
        regle("Saut impossible (une minute, plus de 100 milles)", ligne(VIOLET, 1.6, 0.7))])
    s["wa_recit_radar_validation"] = sld("wa_recit_radar_validation", "Validation par le radar", [
        regle("Vu par le radar, reçu par l'AIS côtier", marque("circle", 6, "#8d9aa4", "#ffffff", 0.7),
              filtre=egal("recu", "true"))], [
        regle("Vu et identifié par le radar, non reçu par l'AIS côtier", marque("circle", 9, ORANGE, "#ffffff", 1.2),
              filtre=egal("recu", "false"))])
    return s
