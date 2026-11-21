"""Prépare la pile MapStore sur une nouvelle machine, sans jamais écrire ni afficher un mot de passe.

    python configurer.py          .env (mots de passe générés), connexion de MapStore à PostgreSQL, polices
    python configurer.py bases    crée les rôles et les bases PostgreSQL (psql demande le mot de passe de postgres)

Idempotent : un .env existant est complété, jamais écrasé ; les bases existantes ne sont pas recréées.
Bibliothèque standard uniquement.
"""
import os
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent
ENV = ICI / ".env"
EXEMPLE = ICI / ".env.example"
PROPRIETES = ICI / "datadir" / "geostore-datasource-ovr.properties"
MODELE = PROPRIETES.with_name(PROPRIETES.name + ".modele")
POLICES = ICI / "fonts"
SEGOE = ["segoeui.ttf", "segoeuib.ttf", "segoeuii.ttf", "segoeuisl.ttf"]

# Clés du .env remplies par un mot de passe aléatoire quand elles sont vides
MOTS_DE_PASSE = ["MAPSTORE_ADMIN_PASSWORD", "MAPSTORE_DB_PASSWORD", "GEOSERVER_ADMIN_PASSWORD",
                 "WHAT_AIS_DB_PASSWORD"]


def lire_env():
    valeurs = {}
    if ENV.exists():
        for ligne in ENV.read_text(encoding="utf-8").splitlines():
            ligne = ligne.strip()
            if ligne and not ligne.startswith("#") and "=" in ligne:
                cle, val = ligne.split("=", 1)
                valeurs[cle.strip()] = val.strip()
    return valeurs


def mot_de_passe():
    # Lettres et chiffres seulement : aucun caractère à échapper dans .env, psql, JDBC ou une URL
    return secrets.token_urlsafe(24).replace("-", "x").replace("_", "y")


def ancien_mot_de_passe_base():
    """Mot de passe de la base MapStore d'une installation antérieure à .env (fichier properties écrit à la
    main), pour ne pas casser une pile qui tourne déjà."""
    if PROPRIETES.exists():
        m = re.search(r"^geostoreDataSource\.password=(.+)$", PROPRIETES.read_text(encoding="utf-8"), re.M)
        if m and "{" not in m.group(1):
            return m.group(1).strip()
    return None


def preparer_env():
    if not ENV.exists():
        shutil.copyfile(EXEMPLE, ENV)
        print(".env créé à partir de .env.example")
    texte = ENV.read_text(encoding="utf-8")
    valeurs = lire_env()
    ajouts = []
    for cle in MOTS_DE_PASSE:
        if valeurs.get(cle):
            continue
        valeur = (cle == "MAPSTORE_DB_PASSWORD" and ancien_mot_de_passe_base()) or mot_de_passe()
        if re.search(rf"^{cle}=\s*$", texte, re.M):
            texte = re.sub(rf"^{cle}=\s*$", lambda _: f"{cle}={valeur}", texte, count=1, flags=re.M)
        else:
            texte = texte.rstrip("\n") + f"\n{cle}={valeur}\n"
        ajouts.append(cle)
    if ajouts:
        ENV.write_text(texte, encoding="utf-8")
        print(".env : mot de passe renseigné pour " + ", ".join(ajouts) + " (valeurs non affichées)")
    else:
        print(".env : complet")
    return lire_env()


def ecrire_proprietes(valeurs):
    texte = MODELE.read_text(encoding="utf-8").replace("{MAPSTORE_DB_PASSWORD}", valeurs["MAPSTORE_DB_PASSWORD"])
    if not PROPRIETES.exists() or PROPRIETES.read_text(encoding="utf-8") != texte:
        PROPRIETES.write_text(texte, encoding="utf-8")
        print(f"{PROPRIETES.relative_to(ICI)} écrit")
    else:
        print(f"{PROPRIETES.relative_to(ICI)} : à jour")


def copier_polices():
    """Segoe UI (police du projet QGIS) pour les étiquettes et légendes de GeoServer. Elle appartient à
    Microsoft : elle n'est pas versionnée, on la reprend de Windows. Sans elle, GeoServer prend sa police
    par défaut et la carte reste lisible."""
    POLICES.mkdir(exist_ok=True)
    source = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    manquantes = [f for f in SEGOE if not (POLICES / f).exists()]
    copiees = [f for f in manquantes if (source / f).exists()]
    for f in copiees:
        shutil.copyfile(source / f, POLICES / f)
    if copiees:
        print(f"fonts/ : {len(copiees)} police(s) Segoe UI copiée(s) depuis {source}")
    restantes = [f for f in manquantes if f not in copiees]
    if restantes:
        print("fonts/ : Segoe UI introuvable, GeoServer utilisera sa police par défaut")
    elif not manquantes:
        print("fonts/ : complet")


def trouver_psql():
    if os.environ.get("PSQL") or lire_env().get("PSQL"):
        return Path(os.environ.get("PSQL") or lire_env()["PSQL"])
    if chemin := shutil.which("psql"):
        return Path(chemin)
    racine = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "PostgreSQL"
    versions = sorted((p for p in racine.glob("*/bin/psql.exe")),
                      key=lambda p: [int(n) for n in re.findall(r"\d+", p.parent.parent.name)] or [0])
    if versions:
        return versions[-1]
    sys.exit("psql introuvable : l'ajouter au PATH ou renseigner PSQL dans .env")


def creer_bases():
    valeurs = preparer_env()
    psql = trouver_psql()
    environnement = dict(os.environ, PGCLIENTENCODING="UTF8",
                         MAPSTORE_DB_PASSWORD=valeurs["MAPSTORE_DB_PASSWORD"],
                         WHAT_AIS_DB_PASSWORD=valeurs["WHAT_AIS_DB_PASSWORD"])
    for script in sorted((ICI / "sql").glob("0*.sql")):
        print(f"psql -U postgres -f sql/{script.name}")
        subprocess.run([str(psql), "-h", "localhost", "-U", "postgres", "-d", "postgres", "-v", "ON_ERROR_STOP=1",
                        "-q", "-f", str(script)], env=environnement, check=True)
    print("bases prêtes : mapstore (schéma geostore), what_ais_carto (PostGIS, schéma carto)")


def main(quoi="pile"):
    if quoi == "bases":
        creer_bases()
    elif quoi == "pile":
        valeurs = preparer_env()
        ecrire_proprietes(valeurs)
        copier_polices()
        print("ensuite : python configurer.py bases, puis docker compose up -d")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(*sys.argv[1:2])
