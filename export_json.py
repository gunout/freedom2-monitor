
#!/usr/bin/env python3
"""Exporte freedom.db en JSON pour GitHub Pages."""

import sqlite3, json, os
from datetime import datetime

DOSSIER = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(DOSSIER, 'freedom.db')
SORTIE = os.path.join(DOSSIER, 'data.json')

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()
L = lambda rows: [dict(r) for r in rows]

data = {
    'genere_le': datetime.now().isoformat(),
    'genere_ts': int(datetime.now().timestamp()),
}

data['volume'] = dict(c.execute("""
    SELECT COUNT(*) AS nb_diffusions,
           COUNT(DISTINCT artistes) AS nb_artistes,
           COUNT(DISTINCT titre) AS nb_titres,
           MIN(date) AS premiere_date,
           MAX(date) AS derniere_date,
           ROUND(SUM(duree_sec)/3600.0, 2) AS heures,
           ROUND(AVG(duree_sec), 1) AS duree_moy
    FROM diffusions WHERE artistes IS NOT NULL AND artistes != ''
""").fetchone() or {})

data['top_artistes'] = L(c.execute("""
    SELECT artistes, COUNT(*) AS nb_diffusions,
           ROUND(SUM(duree_sec)/60.0, 1) AS minutes
    FROM diffusions WHERE artistes IS NOT NULL AND artistes != ''
    GROUP BY artistes ORDER BY minutes DESC LIMIT 30
""").fetchall())

data['top_titres'] = L(c.execute("""
    SELECT artistes, titre, COUNT(*) AS nb_diffusions,
           ROUND(SUM(duree_sec)/60.0, 1) AS minutes
    FROM diffusions WHERE artistes IS NOT NULL AND artistes != ''
    GROUP BY artistes, titre ORDER BY nb_diffusions DESC LIMIT 30
""").fetchall())

data['heures'] = L(c.execute("""
    SELECT heure, COUNT(*) AS nb FROM diffusions
    WHERE heure IS NOT NULL GROUP BY heure ORDER BY heure
""").fetchall())

data['jours'] = L(c.execute("""
    SELECT date, COUNT(*) AS nb FROM diffusions
    WHERE date IS NOT NULL GROUP BY date ORDER BY date
""").fetchall())

data['semaine'] = L(c.execute("""
    SELECT CASE CAST(strftime('%w', date) AS INTEGER)
        WHEN 0 THEN 'Dimanche' WHEN 1 THEN 'Lundi' WHEN 2 THEN 'Mardi'
        WHEN 3 THEN 'Mercredi' WHEN 4 THEN 'Jeudi' WHEN 5 THEN 'Vendredi'
        WHEN 6 THEN 'Samedi' END AS jour,
        COUNT(*) AS nb FROM diffusions WHERE date IS NOT NULL
    GROUP BY strftime('%w', date)
    ORDER BY CAST(strftime('%w', date) AS INTEGER)
""").fetchall())

data['recurrents'] = L(c.execute("""
    SELECT artistes, COUNT(DISTINCT date) AS nb_jours,
           COUNT(*) AS nb_diffusions
    FROM diffusions WHERE artistes IS NOT NULL AND artistes != ''
    GROUP BY artistes HAVING nb_jours >= 2
    ORDER BY nb_jours DESC LIMIT 20
""").fetchall())

data['titres_recurrents'] = L(c.execute("""
    SELECT artistes, titre, COUNT(DISTINCT date) AS nb_jours,
           COUNT(*) AS nb_diffusions
    FROM diffusions WHERE artistes IS NOT NULL AND artistes != ''
    GROUP BY artistes, titre HAVING nb_jours >= 2
    ORDER BY nb_jours DESC LIMIT 20
""").fetchall())

data['diversifies'] = L(c.execute("""
    SELECT artistes, COUNT(DISTINCT titre) AS nb_titres,
           COUNT(*) AS nb
    FROM diffusions WHERE artistes IS NOT NULL AND artistes != ''
    GROUP BY artistes HAVING nb_titres >= 2
    ORDER BY nb_titres DESC LIMIT 20
""").fetchall())

data['annees'] = L(c.execute("""
    SELECT annee, COUNT(*) AS nb_diffusions FROM diffusions
    WHERE annee IS NOT NULL GROUP BY annee ORDER BY annee DESC
""").fetchall())

data['explicit'] = L(c.execute("""
    SELECT CASE explicit_lyrics WHEN 1 THEN 'Explicit'
        WHEN 0 THEN 'Clean' ELSE 'Inconnu' END AS type_contenu,
        COUNT(*) AS nb FROM diffusions
    WHERE explicit_lyrics IS NOT NULL GROUP BY explicit_lyrics
""").fetchall())

data['albums'] = L(c.execute("""
    SELECT album, artistes, COUNT(*) AS nb FROM diffusions
    WHERE album IS NOT NULL AND album != ''
    GROUP BY album ORDER BY nb DESC LIMIT 20
""").fetchall())

data['derniers_morceaux'] = L(c.execute("""
    SELECT titre, artistes, cover_deezer, cover_uri, preview_mp3,
           date, heure, album, annee, start_ts
    FROM diffusions ORDER BY start_ts DESC LIMIT 10
""").fetchall())

dernier = c.execute("""
    SELECT titre, artistes, cover_deezer, cover_uri, preview_mp3,
           date, heure, album, annee, start_ts, end_ts
    FROM diffusions ORDER BY start_ts DESC LIMIT 1
""").fetchone()
data['dernier_morceau'] = dict(dernier) if dernier else {}

conn.close()

with open(SORTIE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("data.json genere")
print("  Diffusions : " + str(data['volume'].get('nb_diffusions', 0)))
print("  Artistes   : " + str(data['volume'].get('nb_artistes', 0)))
print("  Titres     : " + str(data['volume'].get('nb_titres', 0)))
