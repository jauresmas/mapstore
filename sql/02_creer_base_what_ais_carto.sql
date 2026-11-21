-- Base des couches publiées du projet What AIS doesn't show (lue par le GeoServer de la pile).
-- Elle ne contient que les couches d'affichage pseudonymisées du dépôt (carto.gpkg, traces.gpkg) et les
-- tables dérivées par projets/what_ais, jamais la base d'analyse à MMSI réels.
--
-- Lancé par « python configurer.py bases » en tant que postgres (psql demande son mot de passe).
-- Le mot de passe du rôle vient de la variable d'environnement WHAT_AIS_DB_PASSWORD (fichier .env).
-- Idempotent : relancer ne recrée rien.

\set ON_ERROR_STOP on
\getenv mdp WHAT_AIS_DB_PASSWORD
\if :{?mdp}
\else
    \echo 'WHAT_AIS_DB_PASSWORD absent : lancer « python configurer.py bases »'
    \quit
\endif

SELECT format('CREATE ROLE what_ais LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE', :'mdp')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'what_ais') \gexec

SELECT 'CREATE DATABASE what_ais_carto OWNER what_ais'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'what_ais_carto') \gexec

\connect what_ais_carto

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS carto AUTHORIZATION what_ais;
ALTER ROLE what_ais IN DATABASE what_ais_carto SET search_path TO carto, public;
