
#!/usr/bin/env python3
"""Enrichissement via l'API iTunes pour freedom.db."""

import sqlite3, requests, time, os, sys, unicodedata
from datetime import datetime

DOSSIER = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(DOSSIER, 'freedom.db')
LOG = os.path.join(DOSSIER, 'enrichir.log')
LOCK = os.path.join(DOSSIER, '.enrichir.lock')
SEUIL_TITRE = 0.75
PAUSE = 0.5


def log(m):
    h = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    l = "[" + h + "] " + m
    print(l, flush=True)
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(l + '\n')
    except Exception:
        pass


def verrou():
    if os.path.exists(LOCK):
        try:
            with open(LOCK) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return False
        except Exception:
            try:
                os.remove(LOCK)
            except Exception:
                pass
    with open(LOCK, 'w') as f:
        f.write(str(os.getpid()))
    return True


def deverrou():
    try:
        os.remove(LOCK)
    except FileNotFoundError:
        pass


def norm(t):
    if not t:
        return ''
    t = t.lower()
    t = unicodedata.normalize('NFKD', t)
    t = ''.join(c for c in t if not unicodedata.combining(c))
    t = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in t)
    return ' '.join(t.split())


def simil(a, b):
    ma, mb = set(norm(a).split()), set(norm(b).split())
    if not ma:
        return 0.0
    return len(ma & mb) / len(ma)


_cache = {}


def chercher_itunes(titre, limite=15):
    if titre in _cache:
        return _cache[titre]
    try:
        r = requests.get(
            "https://itunes.apple.com/search",
            params={"term": titre, "entity": "musicTrack",
                    "limit": limite, "country": "FR"},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        data = r.json().get('results', [])
    except Exception as e:
        log("! iTunes : " + str(e))
        data = []
    _cache[titre] = data
    return data


def choisir(cands, duree, titre, artiste_radio=None):
    if not cands:
        return None, None, None
    ok = [c for c in cands if simil(titre, c.get('trackName', '')) >= SEUIL_TITRE]
    if not ok:
        ok = [c for c in cands if simil(titre, c.get('trackName', '')) >= 0.5]
    if not ok:
        return None, None, None
    if artiste_radio:
        def score(c):
            s_art = simil(artiste_radio, c.get('artistName', ''))
            dur_i = c.get('trackTimeMillis', 0) // 1000
            ecart = abs(dur_i - (duree or 0)) if duree else 0
            return (-s_art, ecart)
        ok.sort(key=score)
    b = ok[0]
    dur_i = b.get('trackTimeMillis', 0) // 1000
    e = abs(dur_i - (duree or 0)) if duree else None
    return b, e, 'titre'


def enrichir(limite=None, verbeux=True):
    if not verrou():
        log("Verrou actif, arret.")
        return 0
    try:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        q = """SELECT uid, titre, duree_sec, artistes, radio FROM diffusions
               WHERE artistes IS NULL OR artistes=''
                  OR album IS NULL OR album=''
               ORDER BY start_ts DESC"""
        if limite:
            q += " LIMIT " + str(int(limite))
        rows = c.execute(q).fetchall()
        if not rows:
            if verbeux:
                log("Aucun morceau a enrichir.")
            conn.close()
            return 0
        log("A enrichir : " + str(len(rows)))
        n = 0
        for uid, titre, duree, artiste_radio, radio_id in rows:
            cands = chercher_itunes(titre)
            bon, ecart, conf = choisir(cands, duree, titre, artiste_radio)
            if bon is None:
                if verbeux:
                    log("  x " + titre[:50])
                time.sleep(PAUSE)
                continue
            artiste = (bon.get('artistName') or '').strip()
            titre_d = (bon.get('trackName') or '').strip()
            album = (bon.get('collectionName') or '').strip() or None
            cover = (bon.get('artworkUrl100') or '').strip() or None
            if cover:
                cover = cover.replace('100x100bb', '600x600bb')
                cover = cover.replace('100x100', '600x600')
            preview = (bon.get('previewUrl') or '').strip() or None
            date_rel = (bon.get('releaseDate') or '')[:4]
            annee = int(date_rel) if date_rel.isdigit() else None

            # Verifier si un autre uid a deja ce titre+artiste
            doublon = c.execute("""
                SELECT uid FROM diffusions
                WHERE radio = ? AND LOWER(titre) = LOWER(?)
                  AND LOWER(artistes) = LOWER(?)
                  AND uid != ?
            """, (radio_id, titre_d, artiste, uid)).fetchone()

            try:
                if doublon:
                    # Supprimer le doublon (garder l'autre)
                    c.execute("DELETE FROM diffusions WHERE uid = ?", (uid,))
                    conn.commit()
                    if verbeux:
                        log("  = doublon supprime : " + titre_d)
                else:
                    c.execute("""UPDATE diffusions SET
                        artistes=?, titre=?, album=?, cover_deezer=?,
                        preview_mp3=?, annee=? WHERE uid=?""",
                        (artiste, titre_d, album, cover, preview, annee, uid))
                    conn.commit()
                    n += 1
                    if verbeux:
                        log("  OK " + titre[:35] + " -> " + artiste + " - " + titre_d)
            except sqlite3.Error as e:
                log("  ! " + str(e))

            time.sleep(PAUSE)

        conn.close()
        log("Termine - " + str(n) + " enrichis sur " + str(len(rows)))
        return n
    finally:
        deverrou()


if __name__ == '__main__':
    lim = None
    for a in sys.argv[1:]:
        if a.startswith('--limite='):
            lim = int(a.split('=', 1)[1])
    enrichir(lim, True)
