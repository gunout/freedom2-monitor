<div align="center">

# 📻 Freedom Monitor

**Collecteur & Dashboard de la programmation musicale de Free Dom 2**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com/)
[![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Made with ❤️](https://img.shields.io/badge/Made%20with-%E2%9D%A4%EF%B8%8F-red?style=for-the-badge)](https://github.com/gunout)
[![Maintained](https://img.shields.io/badge/Maintained-yes-success?style=for-the-badge)](https://github.com/gunout/freedom2-monitor)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](https://github.com/gunout/freedom2-monitor/pulls)

---

*Scraping Playwright · Enrichissement iTunes · Dashboard interactif · Analyse complète*

</div>

---

## 📖 Table des matières

- [Aperçu](#-aperçu)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#️-architecture)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Automatisation](#-automatisation)
- [Sources de données](#-sources-de-données)
- [Contribuer](#-contribuer)
- [Licence](#-licence)

---

## 🎯 Aperçu

**Freedom Monitor** est un pipeline complet qui :

1. **Scrape** en temps réel la playlist diffusée sur Free Dom 2 via `freedom.fr/free-dom-2/`
2. **Enrichit** automatiquement chaque morceau (album, année, pochette, extrait audio) via l'API publique iTunes
3. **Analyse** les données pour produire des CSV et un JSON
4. **Affiche** le tout dans un dashboard HTML interactif

Idéal pour suivre la programmation musicale de Free Dom 2, découvrir la scène musicale réunionnaise et internationale, ou analyser les tendances.


<img width="1683" height="3585" alt="Screenshot 2026-09-29 at 09-59-13 Free Dom 2 — Monitor" src="https://github.com/user-attachments/assets/a5506720-e4d5-4cc8-a06a-0423c7867fd6" />


---

## ✨ Fonctionnalités

### 🎧 Collecte & Enrichissement

- [x] Scraping de la playlist via Playwright (navigateur headless)
- [x] Extraction des morceaux (artiste + titre + durée)
- [x] Détection anti-doublons (insensible à la casse)
- [x] Stockage incrémental dans une base SQLite
- [x] Enrichissement iTunes : album, année, pochette 600×600, extrait audio 30s
- [x] Calcul de la durée de diffusion

### 📊 Analyses

- [x] Volume global (diffusions, artistes, titres, heures)
- [x] Top artistes (temps d'antenne)
- [x] Top titres (nombre de diffusions)
- [x] Répartition horaire (24h)
- [x] Répartition journalière (évolution par date)
- [x] Artistes récurrents (multi-jours)
- [x] Artistes diversifiés
- [x] Répartition par année de sortie
- [x] Ratio Clean / Explicit
- [x] Top albums

### 🎨 Dashboard

- [x] Design aux couleurs de Free Dom (bleu marine, blanc, noir)
- [x] Bandeau « On Air » avec pochette et extrait audio
- [x] Graphiques interactifs Plotly
- [x] Auto-refresh toutes les 2 minutes
- [x] Responsive (mobile / desktop)

---

## 🏗️ Architecture

| Fichier | Rôle |
|---------|------|
| `config.py` | Configuration de la radio Free Dom 2 |
| `collecteur.py` | Scraping Playwright + stockage SQLite |
| `enrichir.py` | Enrichissement via l'API iTunes |
| `analyser.py` | Génération des CSV d'analyse |
| `export_json.py` | Génération du JSON pour le dashboard |
| `index.html` | Dashboard interactif |
| `freedom.db` | Base SQLite |
| `resultats/` | CSV générés |
| `data.json` | JSON pour le dashboard |

**Flux de données :**

1. Le collecteur lance Chromium en arrière-plan (Playwright)
2. Il charge la page de Free Dom 2 et extrait la playlist
3. Il détecte les nouveaux morceaux et les insère dans `freedom.db`
4. `enrichir.py` complète les métadonnées via iTunes
5. `analyser.py` produit les CSV
6. `export_json.py` produit `data.json`
7. `index.html` lit le JSON et affiche les graphiques

---

## 🚀 Installation

### Prérequis

- Python 3.10 ou supérieur
- pip

### Cloner le dépôt

Ouvrez un terminal et tapez :

`git clone https://github.com/gunout/freedom2-monitor.git`

Puis :

`cd freedom2-monitor`

### Installer les dépendances

`pip install requests pandas playwright`

### Installer le navigateur Chromium

`playwright install chromium`

---

## 🎮 Utilisation

### Étape 1 — Lancer le collecteur

`python3 collecteur.py`

Le collecteur scrape la playlist toutes les 2 minutes et enregistre les morceaux.

**Pour le lancer en arrière-plan :**

`nohup python3 collecteur.py > /dev/null 2>&1 &`

### Étape 2 — Enrichir les morceaux

`python3 enrichir.py`

### Étape 3 — Générer les analyses

`python3 analyser.py`

Produit les CSV dans le dossier `resultats/`.

### Étape 4 — Générer le JSON

`python3 export_json.py`

Produit `data.json`.

### Étape 5 — Lancer le dashboard

`python3 -m http.server 8007`

Puis ouvrez dans votre navigateur :

[http://localhost:8007/index.html](http://localhost:8007/index.html)

---

## ⏰ Automatisation

Pour régénérer les analyses et le JSON automatiquement toutes les minutes, éditez votre crontab avec :

`crontab -e`

Puis ajoutez la ligne suivante :

`* * * * * cd /chemin/vers/freedom2-monitor && /usr/bin/python3 analyser.py && /usr/bin/python3 export_json.py >> cron.log 2>&1`

---

## 🌐 Sources de données

| Source | Endpoint | Authentification |
|--------|----------|------------------|
| Free Dom 2 | `https://freedom.fr/free-dom-2/` | ❌ Aucune |
| iTunes Search | `https://itunes.apple.com/search` | ❌ Aucune |

---

## 🤝 Contribuer

Les contributions sont les bienvenues !

1. Fork le projet
2. Créez une branche : `git checkout -b feature/ma-fonctionnalite`
3. Committez : `git commit -m "feat: ajoute ma fonctionnalité"`
4. Pushez : `git push origin feature/ma-fonctionnalite`
5. Ouvrez une Pull Request

### Convention de commit

- `feat:` nouvelle fonctionnalité
- `fix:` correction de bug
- `docs:` documentation
- `chore:` tâches diverses

---

## 📄 Licence

Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## ⚠️ Avertissement

- Le scraping est effectué sur une page publique de `freedom.fr` dans un but éducatif.
- Ce projet est destiné à un **usage personnel et éducatif**.
- Les données musicales collectées restent la propriété de leurs ayants droit respectifs.
- L'auteur n'est pas affilié à Free Dom ni à sa maison mère.

---

<div align="center">

**⭐ Si ce projet vous plaît, mettez-lui une étoile ! ⭐**

[🔝 Retour en haut](#-freedom-monitor)

</div>
