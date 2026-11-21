"""Création et mise à jour des ressources MapStore (GeoStore) : carte, contexte, tableau de bord,
GeoStory, avec leur fiche de présentation (DETAILS), leur vignette (THUMBNAIL) et une lecture
publique. Les ressources sont retrouvées par catégorie et par nom : relancer met à jour.
"""
import base64
import json
import urllib.parse
import urllib.request

from xml.sax.saxutils import escape

from commun import ESPACE, GEOSERVER


def cdata(texte):
    """Section CDATA ; une éventuelle séquence ]]> est coupée en deux sections."""
    return "<![CDATA[" + texte.replace("]]>", "]]]]><![CDATA[>") + "]]>"


class Ressources:
    def __init__(self, ms):
        self.ms = ms
        groupes = ms.json("GET", "/usergroups?all=true")["UserGroupList"]["UserGroup"]
        groupes = groupes if isinstance(groupes, list) else [groupes]
        self.tout_le_monde = next(g["id"] for g in groupes if g["groupName"] == "everyone")
        self.admin = ms.json("GET", "/users/user/details")["User"]["id"]

    def chercher(self, categorie, nom):
        statut, texte = self.ms.requete(
            "GET", f"/misc/category/name/{categorie}/resource/name/{urllib.parse.quote(nom)}", ok=None)
        return json.loads(texte)["Resource"]["id"] if statut == 200 else None

    def attributs(self, rid):
        r = self.ms.json("GET", f"/resources/resource/{rid}?full=true")["Resource"]
        a = (r.get("Attributes") or {}).get("attribute") or []
        a = a if isinstance(a, list) else [a]
        return {x["name"]: x.get("value") for x in a}

    def enregistrer(self, categorie, nom, description, donnees, attributs=None):
        """Crée ou met à jour une ressource ; renvoie son identifiant."""
        texte = donnees if isinstance(donnees, str) else json.dumps(donnees, ensure_ascii=False)
        rid = self.chercher(categorie, nom)
        if rid is None:
            attrs = "".join(f"<attribute><name>{escape(k)}</name><type>STRING</type><value>{escape(v)}</value>"
                            f"</attribute>" for k, v in (attributs or {}).items())
            xml = (f"<Resource><description>{escape(description)}</description><metadata></metadata>"
                   f"<name>{escape(nom)}</name><category><name>{categorie}</name></category>"
                   f"<store><data>{cdata(texte)}</data></store>"
                   f"{'<Attributes>' + attrs + '</Attributes>' if attrs else ''}</Resource>")
            _, rid = self.ms.requete("POST", "/resources", xml, type_contenu="application/xml", accepter="text/plain")
            rid = int(rid)
        else:
            self.ms.requete("PUT", f"/resources/resource/{rid}",
                            f"<Resource><description>{escape(description)}</description>"
                            f"<name>{escape(nom)}</name></Resource>", type_contenu="application/xml",
                            accepter="*/*", ok=(200, 201, 204))
            self.ms.requete("PUT", f"/data/{rid}", texte,
                            type_contenu="application/json" if not isinstance(donnees, str) else "text/plain",
                            accepter="*/*", ok=(200, 201, 204))
            for k, v in (attributs or {}).items():
                self.ms.requete("PUT", f"/resources/resource/{rid}/attributes/",
                                {"restAttribute": {"name": k, "value": v}},
                                accepter="*/*", ok=(200, 201, 204))
        self.public(rid)
        return rid

    def public(self, rid):
        """Lecture pour tous (groupe everyone, visiteurs anonymes compris), écriture pour l'administrateur."""
        xml = ("<SecurityRuleList>"
               f"<SecurityRule><canRead>true</canRead><canWrite>true</canWrite>"
               f"<user><id>{self.admin}</id><name>admin</name></user></SecurityRule>"
               f"<SecurityRule><canRead>true</canRead><canWrite>false</canWrite>"
               f"<group><id>{self.tout_le_monde}</id><groupName>everyone</groupName></group></SecurityRule>"
               "</SecurityRuleList>")
        self.ms.requete("POST", f"/resources/resource/{rid}/permissions", xml, type_contenu="application/xml",
                        accepter="*/*", ok=(200, 201, 204))

    def lien_donnees(self, rid):
        return f"rest/geostore/data/{rid}/raw?decode=datauri"

    def presentation(self, nom, html, a_l_ouverture=True):
        """Fiche de présentation (catégorie DETAILS) ; renvoie les attributs à poser sur la ressource."""
        rid = self.enregistrer("DETAILS", f"{nom} · présentation", "", html)
        return {"details": self.lien_donnees(rid),
                "detailsSettings": json.dumps({"showAsModal": False, "showAtStartup": a_l_ouverture})}

    def vignette(self, nom, couches, bbox=(9.0, 53.9, 16.5, 58.2), largeur=640, hauteur=400):
        """Vignette de la ressource : rendu WMS du GeoServer de la pile, stocké en data URI."""
        q = {"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "STYLES": "", "SRS": "EPSG:4326",
             "LAYERS": ",".join(f"{ESPACE}:{c}" for c in couches), "BBOX": ",".join(map(str, bbox)),
             "WIDTH": largeur, "HEIGHT": hauteur, "FORMAT": "image/png", "TRANSPARENT": "false",
             "BGCOLOR": "0xEDF1F3", "FORMAT_OPTIONS": "antialiasing:full"}
        with urllib.request.urlopen(f"{GEOSERVER}/wms?{urllib.parse.urlencode(q)}", timeout=120) as r:
            png = r.read()
        uri = "data:image/png;base64," + base64.b64encode(png).decode()
        rid = self.enregistrer("THUMBNAIL", f"{nom} · vignette", "", uri)
        return {"thumbnail": self.lien_donnees(rid)}
