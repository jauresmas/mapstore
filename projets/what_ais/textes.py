"""Textes affichés dans MapStore : présentation des ressources (français, puis anglais)."""

DEPOT = "https://github.com/jauresmas/what-ais-doesnt-show"
STYLE = ("font-family:Segoe UI,Arial,sans-serif;font-size:14px;line-height:1.55;color:#1d1d1b")


def _chiffres(lignes):
    corps = "".join(
        f'<tr><td style="padding:3px 12px 3px 0;text-align:right;font-weight:700;font-size:16px;'
        f'color:{c};white-space:nowrap">{n}</td><td style="padding:3px 0">{lib}</td></tr>' for n, lib, c in lignes)
    return f'<table style="border-collapse:collapse;margin:8px 0 14px">{corps}</table>'


PRESENTATION_CARTE = f"""
<div style="{STYLE}">
<p style="margin:0;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#8a877f">AIS côtier · données ouvertes</p>
<h2 style="margin:4px 0 2px;font-size:22px">Ce que l'AIS ne montre pas</h2>
<p style="margin:0 0 12px;color:#52514e">Détroits danois et bassin de Bornholm · 13–19 octobre 2026</p>
<p>Où le réseau AIS côtier perd réellement les navires, quels silences rien d'ordinaire n'explique, et ce
qu'un radar satellitaire voit que l'AIS ne montre pas.</p>
{_chiffres([
    ("2 894", "navires de classe A suivis", "#1d1d1b"),
    ("3 880", "silences AIS de 2 heures ou plus", "#1d1d1b"),
    ("496", "dus aux trous de réception côtière", "#5f7d95"),
    ("11", "inexpliqués : transits silencieux en eaux bien couvertes", "#eb6834"),
    ("10", "navires dont le MMSI est partagé par deux émetteurs", "#4a3aa7"),
    ("121", "passages lents au-dessus d'un câble ou d'un pipeline", "#2a78d6"),
    ("47", "rencontres en mer de 2 heures ou plus", "#1baf7a"),
    ("210", "détections radar sans AIS (hors parcs éoliens)", "#52514e"),
])}
<h3 style="font-size:15px;margin:14px 0 4px">Lire la carte</h3>
<ul style="padding-left:18px;margin:0">
<li><b>Signaux</b> : les cinq écarts au comportement attendu, allumés par défaut. Un clic ouvre leur fiche.</li>
<li><b>Indicateurs</b> : densité du trafic et zones de mauvaise réception ; couverture mesurée et indice de
vigilance en vues d'analyse.</li>
<li><b>Quatre semaines</b> : angles morts chroniques et silences inexpliqués récurrents.</li>
<li>Les <b>signets</b> (loupe, recherche par signet) mènent aux zones commentées : rade de Skagen, bassin d'Arkona…</li>
</ul>
<h3 style="font-size:15px;margin:14px 0 4px">Méthode, en bref</h3>
<p style="margin:0">La couverture est mesurée à partir du trafic lui-même, par maille H3 : part des minutes reçues et
part des navires attendus perdus en traversant. Un silence n'est rangé « inexpliqué » que si le navire est resté dans
des eaux bien couvertes, si le réseau recevait ses voisins heure par heure, et s'il n'avait pas le temps de sortir de
la couverture et d'y revenir.</p>
<p style="margin:12px 0;padding:8px 10px;background:#f6f4f0;border-left:3px solid #8a877f;font-size:12.5px">
Projet personnel de démonstration, sur données ouvertes uniquement. Les indicateurs signalent des écarts au
comportement attendu, pas des infractions : aucun navire n'est nommé ni mis en cause, les navires sont
pseudonymisés.</p>
<p style="font-size:12px;color:#52514e;margin:0">Sources : Autorité maritime danoise (AIS) ; Marine Regions (CC BY 4.0) ;
Eurostat GISCO (© EuroGeographics) ; EMODnet et BSH (CC BY 4.0) ; TeleGeography (CC BY-NC-SA 3.0) ;
© contributeurs OpenStreetMap (ODbL) ; détections radar Powered by Global Fishing Watch (CC BY-NC 4.0).<br>
Code, méthode et rapport qualité : <a href="{DEPOT}" target="_blank" rel="noopener">{DEPOT.replace("https://", "")}</a></p>
<hr style="border:0;border-top:1px solid #e3e0da;margin:16px 0">
<p style="margin:0;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#8a877f">English</p>
<h3 style="font-size:16px;margin:4px 0">What AIS doesn't show</h3>
<p style="margin:0">Danish Straits &amp; Bornholm Basin, 13–19 October 2026. Where the shore AIS network actually
loses vessels, which silences nothing ordinary explains, and what satellite radar sees that AIS does not show.
Of 3,880 AIS silences of two hours or more, 496 are due to shore reception gaps and 11 remain unexplained: silent
transits in well-covered waters. Indicators flag departures from expected behaviour, not offences; vessels are
pseudonymised. Switch the interface language from the settings menu to read layer titles in English.</p>
</div>
"""

PRESENTATION_TABLEAU = f"""
<div style="{STYLE}">
<h2 style="margin:0 0 4px;font-size:20px">Tableau de bord · Ce que l'AIS ne montre pas</h2>
<p style="margin:0 0 10px;color:#52514e">Les chiffres de la semaine d'étude (13–19 octobre 2026) et des trois
semaines qui la précèdent, calculés par le GeoServer de l'installation à partir des couches publiées.</p>
<p style="font-size:12px;color:#52514e">Méthode et sources : <a href="{DEPOT}" target="_blank" rel="noopener">{DEPOT.replace("https://", "")}</a></p>
</div>
"""
