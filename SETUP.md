# Setup Guide — Spotify Hip-Hop Daily Tracker

Ce guide te permet de mettre en place le tracker en ~20 minutes.

---

## 📁 Structure des fichiers

```
ton-repo-github/
├── spotify_hiphop_tracker.py        ← script principal
├── requirements.txt
└── .github/
    └── workflows/
        └── daily_hiphop_releases.yml  ← tâche planifiée GitHub Actions
```

---

## Étape 1 — Spotify Developer Credentials

Tu as déjà un compte. Vérifie juste que ton app a bien :
- Le **Client ID** et **Client Secret** disponibles sur https://developer.spotify.com/dashboard
- Aucun scope OAuth n'est nécessaire (on utilise le flow Client Credentials, sans login utilisateur)

---

## Étape 2 — Google Sheets : créer un Service Account

1. Va sur https://console.cloud.google.com
2. Crée un nouveau projet (ou utilise un existant)
3. Active l'API **Google Sheets** :
   - Menu → APIs & Services → Library → cherche "Google Sheets API" → Enable
4. Crée un Service Account :
   - Menu → APIs & Services → Credentials → Create Credentials → Service Account
   - Donne-lui un nom (ex: `spotify-tracker`)
   - Clique sur "Done"
5. Génère une clé JSON :
   - Clique sur le service account créé → onglet "Keys" → Add Key → Create new key → JSON
   - Télécharge le fichier `.json` — **garde-le précieusement**

---

## Étape 3 — Créer et configurer le Google Spreadsheet

1. Crée un nouveau Google Spreadsheet sur https://sheets.google.com
2. Donne-lui un nom (ex: "Hip-Hop Releases Daily")
3. **Partage-le avec le service account** :
   - Bouton "Partager" → colle l'email du service account (format `xxx@xxx.iam.gserviceaccount.com`)
   - Donne-lui le rôle **Éditeur**
4. Copie l'**ID du Spreadsheet** depuis l'URL :
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_ICI/edit
   ```

---

## Étape 4 — Créer le repo GitHub et ajouter les secrets

1. Crée un nouveau repo GitHub (public ou privé)
2. Copie les 3 fichiers dedans : `spotify_hiphop_tracker.py`, `requirements.txt`, `.github/workflows/daily_hiphop_releases.yml`
3. Va dans **Settings → Secrets and variables → Actions → New repository secret**

   Ajoute ces 4 secrets :

   | Nom | Valeur |
   |-----|--------|
   | `SPOTIFY_CLIENT_ID` | Ton Client ID Spotify |
   | `SPOTIFY_CLIENT_SECRET` | Ton Client Secret Spotify |
   | `GOOGLE_SPREADSHEET_ID` | L'ID du spreadsheet (étape 3) |
   | `GOOGLE_SERVICE_ACCOUNT_JSON` | Le **contenu complet** du fichier JSON téléchargé (étape 2) |

   > ⚠️ Pour `GOOGLE_SERVICE_ACCOUNT_JSON` : ouvre le fichier JSON dans un éditeur texte, sélectionne tout le contenu et colle-le directement dans le champ valeur du secret.

---

## Étape 5 — Tester manuellement

1. Va dans l'onglet **Actions** de ton repo GitHub
2. Clique sur le workflow **"🎵 Daily Hip-Hop Releases Tracker"**
3. Clique sur **"Run workflow"** → Run
4. Vérifie les logs et contrôle ton Google Spreadsheet

---

## ⏰ Planning automatique

Le workflow tourne automatiquement à **01h00 heure de Paris (CEST)** chaque nuit.
Si tu veux changer l'heure, modifie la ligne `cron` dans le workflow :
```yaml
- cron: '0 23 * * *'   # 23:00 UTC = 01:00 CEST (été)
- cron: '0 0 * * *'    # 00:00 UTC = 01:00 CET  (hiver)
```

---

## 📊 Format du Google Spreadsheet

| Date découverte | Artiste(s) | Album | Type | Nb titres | Date de sortie | Spotify URL | Pochette URL | ID Spotify |
|---|---|---|---|---|---|---|---|---|
| 2026-04-10 | Drake | Some Album | Album | 16 | 2026-04-10 | https://... | https://... | abc123 |

---

## ⚠️ Note importante

Depuis février 2026, Spotify a supprimé l'endpoint `/browse/new-releases`.
Le script utilise l'API Search avec `tag:new` et filtre sur la date du jour.
Cette approche couvre les genres : **hip-hop, rap, trap, drill**.
Il est possible que quelques sorties très tardives dans la journée n'apparaissent qu'au lendemain.

---

## 🛠️ Dépannage

- **Erreur 401 Spotify** → vérifie `SPOTIFY_CLIENT_ID` et `SPOTIFY_CLIENT_SECRET`
- **Erreur 403 Google Sheets** → vérifie que le spreadsheet est bien partagé avec l'email du service account
- **0 résultats** → normal si aucune sortie hip-hop le jour J (rares les weekends). Tu peux tester un vendredi (jour habituel de sortie des albums).
