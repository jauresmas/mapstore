-- Champs d'affichage en français, ajoutés après chaque chargement (01_charger_postgis.py).
-- Les fiches d'information de MapStore et les graphiques des tableaux de bord affichent ces champs
-- tels quels : dates en heure UTC, nombres arrondis, libellés traduits. Les données sources ne
-- sont pas modifiées.
SET search_path TO carto, public;

CREATE OR REPLACE FUNCTION pg_temp.famille_fr(f text) RETURNS text LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE f WHEN 'Cargo' THEN 'Cargo' WHEN 'Tanker' THEN 'Pétrolier ou chimiquier'
        WHEN 'Passenger' THEN 'Passagers' WHEN 'Fishing' THEN 'Pêche'
        WHEN 'Service & authorities' THEN 'Service et autorités' WHEN 'Other / unknown' THEN 'Autre ou inconnu'
        ELSE f END $$;
CREATE OR REPLACE FUNCTION pg_temp.date_fr(t timestamptz) RETURNS text LANGUAGE sql IMMUTABLE AS $$
    SELECT to_char(t AT TIME ZONE 'UTC', 'DD/MM/YYYY HH24:MI') || ' UTC' $$;
CREATE OR REPLACE FUNCTION pg_temp.nombre_fr(x numeric, d int) RETURNS text LANGUAGE sql IMMUTABLE AS $$
    SELECT replace(round(x, d)::text, '.', ',') $$;
CREATE OR REPLACE FUNCTION pg_temp.couverture_fr(c text) RETURNS text LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE c WHEN 'Reliable' THEN 'Fiable' WHEN 'Degraded' THEN 'Dégradée'
        WHEN 'Poor' THEN 'Mauvaise (navires perdus)' WHEN 'Not enough traffic' THEN 'Trafic insuffisant pour juger'
        ELSE c END $$;

-- Signaux
ALTER TABLE silence_ais ADD COLUMN famille_fr text, ADD COLUMN debut_txt text, ADD COLUMN fin_txt text,
    ADD COLUMN duree_txt text, ADD COLUMN distance_txt text, ADD COLUMN couverte_txt text;
UPDATE silence_ais SET famille_fr = pg_temp.famille_fr(famille), debut_txt = pg_temp.date_fr(debut),
    fin_txt = pg_temp.date_fr(fin), duree_txt = pg_temp.nombre_fr(duree_h::numeric, 1) || ' h',
    distance_txt = pg_temp.nombre_fr(distance_nm::numeric, 1) || ' milles',
    couverte_txt = CASE WHEN part_couverte IS NULL THEN 'non calculée'
                        ELSE round(part_couverte::numeric * 100) || ' %' END;

ALTER TABLE saut_position ADD COLUMN debut_txt text, ADD COLUMN fin_txt text, ADD COLUMN distance_txt text,
    ADD COLUMN vitesse_txt text;
UPDATE saut_position SET debut_txt = pg_temp.date_fr(debut), fin_txt = pg_temp.date_fr(fin),
    distance_txt = pg_temp.nombre_fr(distance_nm::numeric, 1) || ' milles',
    vitesse_txt = round(vitesse_implicite::numeric) || ' nœuds';

ALTER TABLE stationnement_infra ADD COLUMN famille_fr text, ADD COLUMN debut_txt text, ADD COLUMN duree_txt text,
    ADD COLUMN distance_txt text;
UPDATE stationnement_infra SET famille_fr = pg_temp.famille_fr(famille), debut_txt = pg_temp.date_fr(debut),
    duree_txt = pg_temp.nombre_fr(duree_h::numeric, 1) || ' h',
    distance_txt = round(distance_min_m::numeric) || ' m';

ALTER TABLE rencontre ADD COLUMN famille_a_fr text, ADD COLUMN famille_b_fr text, ADD COLUMN debut_txt text,
    ADD COLUMN duree_txt text, ADD COLUMN distance_txt text;
UPDATE rencontre SET famille_a_fr = pg_temp.famille_fr(famille_a), famille_b_fr = pg_temp.famille_fr(famille_b),
    debut_txt = pg_temp.date_fr(debut), duree_txt = pg_temp.nombre_fr(duree_h::numeric, 1) || ' h',
    distance_txt = round(distance_moyenne_m::numeric) || ' m';

ALTER TABLE detection_radar ADD COLUMN instant_txt text, ADD COLUMN couverture_fr text, ADD COLUMN distance_txt text;
UPDATE detection_radar SET instant_txt = pg_temp.date_fr(instant), couverture_fr = pg_temp.couverture_fr(classe_couverture),
    distance_txt = CASE WHEN dist_ais_m IS NULL THEN '—' ELSE round(dist_ais_m::numeric) || ' m' END;

-- Indicateurs
ALTER TABLE couverture ADD COLUMN classe_fr text, ADD COLUMN reception_txt text, ADD COLUMN perte_txt text;
UPDATE couverture SET classe_fr = pg_temp.couverture_fr(classe),
    reception_txt = CASE WHEN taux_reception IS NULL THEN '—' ELSE round(taux_reception::numeric * 100) || ' %' END,
    perte_txt = CASE WHEN taux_perte IS NULL THEN '—' ELSE round(taux_perte::numeric * 100) || ' %' END;

ALTER TABLE recurrence_couverture ADD COLUMN statut_fr text;
UPDATE recurrence_couverture SET statut_fr = CASE statut
    WHEN 'Chronic' THEN 'Chronique (3 ou 4 semaines sur 4)' WHEN 'Recurring' THEN 'Récurrent (2 semaines)'
    WHEN 'One-off' THEN 'Ponctuel (1 semaine)' WHEN 'Never poor' THEN 'Jamais mauvaise'
    WHEN 'Not enough traffic' THEN 'Trafic insuffisant pour juger' ELSE statut END;

ALTER TABLE indice_vigilance ADD COLUMN indice_txt text, ADD COLUMN heures_txt text;
UPDATE indice_vigilance SET indice_txt = pg_temp.nombre_fr(indice::numeric, 1),
    heures_txt = round(heures_navire::numeric) || ' h';

ALTER TABLE trafic ADD COLUMN heures_txt text;
UPDATE trafic SET heures_txt = pg_temp.nombre_fr(heures_navire::numeric, CASE WHEN heures_navire < 10 THEN 1 ELSE 0 END) || ' h';

ALTER TABLE inexpliquee_semaines ADD COLUMN semaine_fr text, ADD COLUMN famille_fr text, ADD COLUMN debut_txt text,
    ADD COLUMN duree_txt text;
UPDATE inexpliquee_semaines SET famille_fr = pg_temp.famille_fr(famille), debut_txt = pg_temp.date_fr(debut),
    duree_txt = pg_temp.nombre_fr(duree_h::numeric, 1) || ' h',
    semaine_fr = CASE semaine::text
        WHEN '2026-09-22' THEN '1. Sem. du 22 sept.' WHEN '2026-09-29' THEN '2. Sem. du 29 sept.'
        WHEN '2026-10-06' THEN '3. Sem. du 6 oct.' WHEN '2026-10-13' THEN '4. Sem. du 13 oct. (étude)'
        ELSE semaine::text END;

ALTER TABLE trace ADD COLUMN famille_fr text;
UPDATE trace SET famille_fr = pg_temp.famille_fr(famille);

-- Infrastructures et contexte
ALTER TABLE infrastructure ADD COLUMN nom_txt text;
UPDATE infrastructure SET nom_txt = coalesce(nullif(nom, ''), 'sans nom');

ALTER TABLE parc_eolien ADD COLUMN etat_fr text;
UPDATE parc_eolien SET etat_fr = CASE etat WHEN 'Planned' THEN 'En projet' WHEN 'Production' THEN 'En production'
    WHEN 'Approved' THEN 'Autorisé' WHEN 'Dismantled' THEN 'Démantelé' WHEN 'Construction' THEN 'En construction'
    ELSE etat END;

ALTER TABLE zone_fiche ADD COLUMN nom_fr text, ADD COLUMN couverte_txt text;
UPDATE zone_fiche SET nom_fr = CASE nom
    WHEN 'Danish Straits & Bornholm Basin' THEN 'Aire d''étude' WHEN 'Danish EEZ' THEN 'ZEE danoise'
    WHEN 'Swedish EEZ' THEN 'ZEE suédoise' WHEN 'German EEZ' THEN 'ZEE allemande'
    WHEN 'Polish EEZ' THEN 'ZEE polonaise' ELSE nom END,
    couverte_txt = round(part_couverte::numeric * 100) || ' %';

ALTER TABLE lieu ADD COLUMN nom_fr text;
UPDATE lieu SET nom_fr = CASE nom
    WHEN 'Kattegat' THEN 'Cattégat' WHEN 'Great Belt' THEN 'Grand Belt' WHEN 'Fehmarn Belt' THEN 'Belt de Fehmarn'
    WHEN 'Arkona Basin' THEN 'Bassin d''Arkona' WHEN 'Bornholm Basin' THEN 'Bassin de Bornholm'
    WHEN 'Pomeranian Bay' THEN 'Baie de Poméranie' WHEN 'Baltic Sea' THEN 'Mer Baltique'
    WHEN 'DENMARK' THEN 'DANEMARK' WHEN 'SWEDEN' THEN 'SUÈDE' WHEN 'GERMANY' THEN 'ALLEMAGNE'
    WHEN 'POLAND' THEN 'POLOGNE' WHEN 'Gothenburg' THEN 'Göteborg' WHEN 'Copenhagen' THEN 'Copenhague'
    ELSE nom END;

ALTER TABLE station_ais ADD COLUMN messages_txt text;
UPDATE station_ais SET messages_txt = to_char(nb_messages, 'FM999G999G999');

-- Vues des signaux, avec les mêmes filtres que le projet QGIS : une couche GeoServer par signal,
-- dont le décompte est directement celui du rapport (11, 121, 47...). Supprimées avant chaque
-- rechargement par 01_charger_postgis.py, recréées ici.
CREATE VIEW signal_silence_inexplique AS
    SELECT * FROM silence_ais WHERE categorie = 'coupure inexpliquée';
CREATE VIEW signal_mmsi_partage AS
    SELECT * FROM saut_position WHERE mmsi_partage;
CREATE VIEW signal_radar_sans_ais AS
    SELECT * FROM detection_radar WHERE NOT apparie AND categorie <> 'structure fixe probable (parc éolien)';
CREATE VIEW foyer_recurrent AS
    SELECT * FROM foyer_inexpliquees WHERE nb_semaines >= 2;
CREATE VIEW indice_signale AS
    SELECT * FROM indice_vigilance WHERE indice > 0;

ANALYZE;
