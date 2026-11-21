// Captures d'écran des pages publiées (docs/images/*.png), pour la documentation.
//
//   node outils/captures.mjs                     toutes les pages
//   node outils/captures.mjs tableau-de-bord     une seule
//
// Lit les adresses écrites par « python projets/what_ais/03_publier_mapstore.py » (adresses.json).
// Pilote Edge ou Chrome sans fenêtre par le protocole DevTools ; aucune dépendance (Node 22 : fetch et
// WebSocket intégrés). Navigateur : variable NAVIGATEUR, sinon Edge puis Chrome aux emplacements habituels.
import { spawn } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const RACINE = join(dirname(fileURLToPath(import.meta.url)), "..");
const DEST = join(RACINE, "docs", "images");
const ADRESSES = join(RACINE, "projets", "what_ais", "adresses.json");
const LARGEUR = 1440, HAUTEUR = 900, PORT = 9333;

if (!existsSync(ADRESSES)) {
  console.error("adresses.json absent : lancer d'abord python projets/what_ais/03_publier_mapstore.py adresses");
  process.exit(1);
}
const { base, pages } = JSON.parse(readFileSync(ADRESSES, "utf-8"));
// Une étape de récit en plus de la couverture de la GeoStory
if (pages.geostory) pages["geostory-etape"] = pages.geostory + "/section/silence/column/silence_3";
const demandees = process.argv.slice(2);

const NAVIGATEURS = [
  process.env.NAVIGATEUR,
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "/usr/bin/microsoft-edge", "/usr/bin/google-chrome", "/usr/bin/chromium",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
].filter(Boolean);
const navigateur = NAVIGATEURS.find((p) => existsSync(p));
if (!navigateur) { console.error("Edge ou Chrome introuvable : renseigner NAVIGATEUR"); process.exit(1); }

const pause = (ms) => new Promise((r) => setTimeout(r, ms));
const profil = mkdtempSync(join(tmpdir(), "mapstore-captures-"));
const processus = spawn(navigateur, ["--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars",
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${profil}`, `--window-size=${LARGEUR},${HAUTEUR}`,
  "about:blank"], { stdio: "ignore" });

try {
  let cible;
  for (let i = 0; i < 40 && !cible; i++) {
    await pause(500);
    try {
      cible = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page");
    } catch { /* le navigateur démarre */ }
  }
  if (!cible) throw new Error("protocole DevTools injoignable");

  const ws = new WebSocket(cible.webSocketDebuggerUrl);
  await new Promise((ok, ko) => { ws.onopen = ok; ws.onerror = ko; });
  let n = 0;
  const attentes = new Map(), enCours = new Set();
  let dernierReseau = Date.now();
  ws.onmessage = (m) => {
    const msg = JSON.parse(m.data);
    if (msg.method === "Network.requestWillBeSent") { enCours.add(msg.params.requestId); dernierReseau = Date.now(); }
    if (msg.method === "Network.loadingFinished" || msg.method === "Network.loadingFailed") {
      enCours.delete(msg.params.requestId); dernierReseau = Date.now();
    }
    if (msg.id && attentes.has(msg.id)) {
      const { ok, ko } = attentes.get(msg.id);
      attentes.delete(msg.id);
      msg.error ? ko(new Error(JSON.stringify(msg.error))) : ok(msg.result);
    }
  };
  const cdp = (method, params = {}) => new Promise((ok, ko) => {
    const id = ++n;
    attentes.set(id, { ok, ko });
    ws.send(JSON.stringify({ id, method, params }));
  });
  // Page prête : réseau au repos depuis 3 s (au moins 8 s, au plus 90 s ; tuiles et graphiques WPS)
  const repos = async () => {
    const debut = Date.now();
    await pause(8000);
    while (Date.now() - debut < 90000 && (enCours.size || Date.now() - dernierReseau < 3000)) await pause(250);
    await pause(1500); // fondu des tuiles
    return Math.round((Date.now() - debut) / 1000);
  };

  await cdp("Page.enable");
  await cdp("Network.enable");
  await cdp("Emulation.setDeviceMetricsOverride", { width: LARGEUR, height: HAUTEUR, deviceScaleFactor: 1, mobile: false });

  // Avis de confidentialité marqué comme lu (clé et format de MapStore 2026.03), pour qu'il ne masque pas la page
  const config = await (await fetch(base + "configs/localConfig.json")).json();
  if (config.privacy?.enabled) {
    await cdp("Page.navigate", { url: base + "configs/localConfig.json" });
    await pause(1000);
    const p = config.privacy;
    await cdp("Runtime.evaluate", { expression: `(() => { const t = Date.now();
      localStorage.setItem("mapstore.privacy.notice", JSON.stringify({ version: 1,
        policyVersion: ${JSON.stringify(p.policyVersion)}, dismissedAt: t,
        expiresAt: t + 864e5 * ${(p.retentionDays || 180) - 1} })); })()` });
  }

  mkdirSync(DEST, { recursive: true });
  for (const [nom, ancre] of Object.entries(pages)) {
    if (demandees.length && !demandees.includes(nom)) continue;
    await cdp("Page.navigate", { url: "about:blank" });
    enCours.clear();
    await cdp("Page.navigate", { url: base + ancre });
    const duree = await repos();
    const { data } = await cdp("Page.captureScreenshot", { format: "png" });
    writeFileSync(join(DEST, `${nom}.png`), Buffer.from(data, "base64"));
    console.log(`docs/images/${nom}.png (${duree} s)`);
  }
  ws.close();
} finally {
  processus.kill();
  await pause(1000);
  try { rmSync(profil, { recursive: true, force: true }); } catch { /* profil encore verrouillé */ }
}
