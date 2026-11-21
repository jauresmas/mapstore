# Notes techniques : scripter MapStore 2026.03

Ce qu'il a fallu découvrir pour tout publier par scripts, sans passer par l'interface. Utile pour adapter
la chaîne ou diagnostiquer après une mise à jour de MapStore.

## API GeoStore (`/mapstore/rest/geostore`)

MapStore enregistre cartes, contextes, tableaux de bord et GeoStory comme des **ressources** GeoStore :
une catégorie (`MAP`, `CONTEXT`, `DASHBOARD`, `GEOSTORY`, `DETAILS`, `THUMBNAIL`), un nom unique par
catégorie, des données (le JSON de la configuration) et des attributs. Authentification Basic avec un
compte administrateur.

| Opération | Requête | Piège |
|---|---|---|
| Retrouver par nom | `GET /misc/category/name/{CAT}/resource/name/{nom}` | 404 si absente ; réponse `{"Resource": {"id": …}}` en JSON |
| Créer | `POST /resources`, corps **XML** (`<Resource>` avec `<store><data><![CDATA[…]]></data></store>` et `<Attributes>`), `Content-Type: application/xml` | données en CDATA (couper une éventuelle séquence `]]>`) ; l'identifiant revient en texte brut (`Accept: text/plain`) |
| Modifier nom et description | `PUT /resources/resource/{id}`, XML | répond 406 si `Accept: application/json` : envoyer `Accept: */*` |
| Remplacer les données | `PUT /data/{id}` avec le JSON brut | |
| Écrire un attribut | `PUT /resources/resource/{id}/attributes/` avec `{"restAttribute": {"name": …, "value": …}}` | `restattribute` en minuscules donne 400, le XML donne 415 |
| Droits | `POST /resources/resource/{id}/permissions`, XML `<SecurityRuleList>` | répond **204** en cas de succès |

Droits utilisés : lecture pour le groupe `everyone` (visiteurs anonymes compris), lecture et écriture
pour `admin`.

Attributs reconnus par MapStore :

- `thumbnail` : adresse d'une vignette, ici `rest/geostore/data/{id}/raw?decode=datauri` d'une ressource
  `THUMBNAIL` qui contient une image en data URI ;
- `details` et `detailsSettings` : présentation HTML (ressource `DETAILS`) et
  `{"showAsModal": false, "showAtStartup": true}` pour l'ouvrir au chargement ;
- `title` d'un contexte : titre affiché dans les listes.

## Carte (format version 2)

- Une couche WMS de GeoServer : `type: "wms"`, `url` vers `/geoserver/wms` (même origine), `name`
  `espace:couche`, `title` en objet `{"default", "fr-FR", "en-US"}` pour suivre la langue de l'interface.
- Les fiches d'information se configurent par couche (`featureInfo`), avec des champs et des libellés.
- Les fonds sont des couches du groupe `background` (`tileprovider`, `osm`, `empty`, ou WMS).

## Contexte (application dédiée)

- Le contexte embarque une configuration de carte (`mapConfig`) et sa liste d'outils
  (`plugins.desktop`). Partir de `plugins.desktop` de `localConfig.json` de la version installée garde
  la compatibilité, puis retirer ce qui ne sert pas.
- Logotype : `BrandNavbar.cfg.logo.src` accepte une image en data URI (SVG en base64).
- Thème : `theme.variables` (`ms-primary`, `ms-main-color`…) avec `customVariablesEnabled: true`.
- Adresse : `#/context/{nom}/{idCarte}`.

## Tableau de bord

- Grille `cols: {md: 6, xxs: 1}` et lignes de 150 px ; chaque widget a sa position dans `layouts`.
- Compteur : widget `counter`, unité dans `options.seriesOptions[0].uom`.
- Graphiques : traces Plotly, tri par la valeur agrégée avec `sortBy: "aggregation"`. Les options d'axe
  passent par `type`, `angle`, `nTicks`, `fontFamily`, `fontSize` (`dtick` n'est pas transmis).
- Compteurs et graphiques sont calculés par GeoServer en **WPS** (`gs:Aggregate`) : sans l'extension
  WPS, ils restent en erreur.
- Tableau : les en-têtes de colonnes viennent de `layer.fields[{name, alias}]`.
- Widget carte : `maps: [{…carte, mapId}]` et `selectedMapId`.
- Widget texte : les sauts de ligne du HTML deviennent des `<br>` ; écrire le HTML sur une seule ligne.
- Les titres de widgets ne suivent pas la langue de l'interface.

## GeoStory

- Les cartes de fond d'une section sont cadrées sur leur `bbox` : donner une emprise explicite plutôt
  qu'un centre et un zoom (le zoom fractionnaire est arrondi et décadre).
- Pour une colonne de texte à gauche, élargir l'emprise à l'ouest d'environ la largeur de la colonne.
- Apparence : `settings.theme.general` et `settings.theme.overlay` ; un contenu avec `theme: ""` prend le
  thème général.
- Lien vers une étape : `#/geostory/{id}/section/{section}/column/{colonne}`.

## Configuration de MapStore (`localConfig.json.patch`)

- Le patch est un JSON Patch (RFC 6902) appliqué à `localConfig.json` au démarrage. Les `remove` portent
  sur des **positions** de liste : les revérifier à chaque version.
- Avis de confidentialité : `privacy.links` (cookie, privacy, terms, une adresse par langue) supprime
  l'avertissement « à configurer » ; changer `privacy.policyVersion` redemande l'accord des visiteurs.
- L'accord du visiteur est conservé dans le `localStorage` sous `mapstore.privacy.notice`
  (`{version: 1, policyVersion, dismissedAt, expiresAt}`).
- MapStore est une application monopage : changer seulement le `#` de l'adresse ne recharge pas la
  configuration. Après une modification de `localConfig`, recharger complètement la page.

## GeoServer

- Entrepôt PostGIS : hôte `host.docker.internal` depuis le conteneur.
- Après un remplacement de tables par ogr2ogr, `POST /geoserver/rest/reset` vide les caches de schéma et
  de connexions.
- Polices des étiquettes : dossier monté sur `/opt/additional_fonts`, lu au démarrage.
- L'image officielle installe les extensions au démarrage avec `INSTALL_EXTENSIONS=true` et
  `STABLE_EXTENSIONS=wps` ; le volume `/opt/additional_libs` évite de les retélécharger.
