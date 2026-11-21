-- Base interne de MapStore (cartes, contextes, tableaux de bord, GeoStory, utilisateurs), à la place
-- de la base H2 embarquée. Les données géographiques n'y vont pas : elles arrivent dans MapStore par GeoServer.
--
-- Lancé par « python configurer.py bases » en tant que postgres (psql demande son mot de passe).
-- Le mot de passe du rôle vient de la variable d'environnement MAPSTORE_DB_PASSWORD (fichier .env),
-- jamais écrit ici. Idempotent : relancer ne recrée rien.

\set ON_ERROR_STOP on
\getenv mdp MAPSTORE_DB_PASSWORD
\if :{?mdp}
\else
    \echo 'MAPSTORE_DB_PASSWORD absent : lancer « python configurer.py bases »'
    \quit
\endif

SELECT format('CREATE ROLE mapstore LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE', :'mdp')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'mapstore') \gexec

SELECT 'CREATE DATABASE mapstore OWNER mapstore'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mapstore') \gexec

\connect mapstore

CREATE SCHEMA IF NOT EXISTS geostore AUTHORIZATION mapstore;
ALTER ROLE mapstore IN DATABASE mapstore SET search_path TO geostore, public;
