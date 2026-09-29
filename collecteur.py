
#!/usr/bin/env python3
"""
Collecteur Free Dom 2 via Playwright.
Scrape la playlist sur freedom.fr/free-dom-2/ et stocke dans SQLite.
Normalisation de la casse pour eviter les doublons.
"""

import sqlite3, time, os, sys, re
from datetime import datetime
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import RADIOS

DOSSIER = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(DOSSIER, 'freedom.db')
LOG = os.path.join(DOSSIER, 'collecteur.log')
INTERVALLE = 120


def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS diffusions (
        uid INTEGER PRIMARY KEY AUTOINCREMENT,
        radio TEXT NOT NULL, radio_nom TEXT,
        titre TEXT NOT NULL, artistes TEXT, duree_sec INTEGER,
        start_ts INTEGER NOT NULL, end_ts INTEGER, duree INTEGER,
        date TEXT, heure INTEGER,
        album TEXT, cover_deezer TEXT, cover_uri TEXT,
        annee INTEGER, preview_mp3 TEXT, deezer_rank INTEGER,
        explicit_lyrics INTEGER, likes INTEGER DEFAULT 0,
        type TEXT DEFAULT 'record', collecte INTEGER,
        UNIQUE(radio, titre, artistes))''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_radio ON diffusions(radio)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_start_ts ON diffusions(start_ts)')
    conn.commit()
    return conn


def log(msg):
    h = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    l = "[" + h + "] " + msg
    print(l, flush=True)
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(l + '\n')
    except Exception:
        pass


def extraire_playlist(page, url):
    """Charge la page et extrait les morceaux de la playlist."""
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)

    conteneur = page.query_selector("[class*='playlist']")
    if not conteneur:
        return []

    texte = conteneur.inner_text()
    lignes = [l.strip() for l in texte.split('\n') if l.strip()]

    morceaux = []
    i = 0
    while i < len(lignes) - 2:
        titre = lignes[i]
        artiste = lignes[i + 1]
        duree_str = lignes[i + 2]

        m = re.match(r'^(\d{1,2}):(\d{2})$', duree_str)
        if m:
            duree_sec = int(m.group(1)) * 60 + int(m.group(2))
            # Normalisation de la casse
            titre_norm = titre.title().strip()
            artiste_norm = artiste.title().strip()
            morceaux.append({
                'titre': titre_norm,
                'artiste': artiste_norm,
                'duree_sec': duree_sec,
            })
            i += 3
        else:
            i += 1

    # Dedupliquer dans le lot courant
    vus = set()
    uniques = []
    for m in morceaux:
        cle = (m['titre'].lower(), m['artiste'].lower())
        if cle not in vus:
            vus.add(cle)
            uniques.append(m)
    return uniques


def test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for radio in RADIOS:
            log("Test " + radio['nom'] + "...")
            page = browser.new_page(user_agent="Mozilla/5.0 (X11; Linux x86_64)")
            morceaux = extraire_playlist(page, radio['url'])
            page.close()
            log("  " + str(len(morceaux)) + " morceaux uniques")
            for m in morceaux[:10]:
                log("    " + m['artiste'] + " - " + m['titre'] + " (" + str(m['duree_sec']) + "s)")
        browser.close()


def boucle():
    conn = init_db()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        log("Demarrage - " + str(len(RADIOS)) + " radios")
        while True:
            try:
                for radio in RADIOS:
                    page = browser.new_page(user_agent="Mozilla/5.0 (X11; Linux x86_64)")
                    morceaux = extraire_playlist(page, radio['url'])
                    page.close()

                    if not morceaux:
                        log("[" + radio['id'] + "] aucun morceau")
                        continue

                    now = int(time.time())
                    dt = datetime.fromtimestamp(now)
                    c = conn.cursor()
                    nouveaux = 0

                    for m in morceaux:
                        # Verifier si ce morceau existe deja (insensible a la casse)
                        existe = c.execute("""
                            SELECT uid FROM diffusions
                            WHERE radio = ? AND LOWER(titre) = LOWER(?)
                              AND LOWER(artistes) = LOWER(?)
                        """, (radio['id'], m['titre'], m['artiste'])).fetchone()

                        if not existe:
                            try:
                                c.execute('''INSERT INTO diffusions
                                    (radio, radio_nom, titre, artistes, duree_sec,
                                     start_ts, date, heure, type, collecte)
                                    VALUES (?,?,?,?,?,?,?,?, 'record', ?)''',
                                    (radio['id'], radio['nom'], m['titre'], m['artiste'],
                                     m['duree_sec'], now, dt.strftime('%Y-%m-%d'),
                                     dt.hour, now))
                                nouveaux += 1
                            except sqlite3.IntegrityError:
                                pass

                    conn.commit()
                    if nouveaux > 0:
                        log("[" + radio['id'] + "] +" + str(nouveaux) + " nouveaux")
                    else:
                        log("[" + radio['id'] + "] rien de nouveau")

            except Exception as e:
                log("Erreur : " + str(e))

            time.sleep(INTERVALLE)

        browser.close()
    conn.close()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test()
    else:
        boucle()
