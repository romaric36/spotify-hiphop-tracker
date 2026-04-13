# Setup Guide — Spotify Hip-Hop Daily Tracker

Ce setup n'utilise plus l'API Google Sheets. Le script génère des fichiers CSV dans GitHub, et Google Sheets les lit directement via `IMPORTDATA`.

## Structure du repo

```text
ton-repo-github/
├── spotify_hiphop_tracker.py
├── requirements.txt
├── releases.csv
├── releases_history.csv
└── .github/
    └── workflows/
        └── daily_hiphop_releases.yml
```

## Ce que fait le projet

- `releases.csv` contient uniquement les sorties détectées pour le jour courant.
- `releases_history.csv` conserve l'historique cumulé des sorties trouvées au fil des exécutions.
- GitHub Actions lance le script chaque nuit et commit automatiquement les CSV mis à jour.
- Google Sheets lit ensuite le CSV publié sur GitHub avec une simple formule.

## Étape 1 — Spotify Developer

Vérifie que ton application Spotify Developer dispose bien de :

- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`

On utilise le flow `Client Credentials`, donc aucun scope OAuth utilisateur n'est nécessaire.

## Étape 2 — Secrets GitHub

Dans ton repo GitHub :

1. Va dans `Settings` → `Secrets and variables` → `Actions`
2. Clique sur `New repository secret`
3. Ajoute seulement ces 2 secrets :

| Nom | Valeur |
|---|---|
| `SPOTIFY_CLIENT_ID` | Ton Client ID Spotify |
| `SPOTIFY_CLIENT_SECRET` | Ton Client Secret Spotify |

## Étape 3 — Repo public recommandé

Pour que Google Sheets puisse lire directement le CSV avec `IMPORTDATA`, le repo doit être **public**.

Si le repo reste privé :

- `raw.githubusercontent.com` ne sera pas lisible par Google Sheets
- il faudra passer par une autre méthode d'exposition du CSV

## Étape 4 — Premier lancement GitHub Actions

1. Ouvre l'onglet `Actions`
2. Clique sur `🎵 Daily Hip-Hop Releases Tracker`
3. Clique sur `Run workflow`
4. Attends la fin du job

Après ce premier run, tu devrais voir apparaître dans le repo :

- `releases.csv`
- `releases_history.csv`

## Étape 5 — Connecter Google Sheets

Crée un Google Sheet puis colle dans une cellule vide :

```text
=IMPORTDATA("https://raw.githubusercontent.com/romaric36/spotify-hiphop-tracker/main/releases_history.csv")
```

Si tu préfères n'afficher que les sorties du jour :

```text
=IMPORTDATA("https://raw.githubusercontent.com/romaric36/spotify-hiphop-tracker/main/releases.csv")
```

## Colonnes du CSV

| discovery_date | release_date | artists | album | album_type | total_tracks | spotify_url | image_url | spotify_id |
|---|---|---|---|---|---|---|---|---|

## Planification

Le workflow est planifié avec :

```yaml
- cron: '0 23 * * *'
```

Cela correspond à :

- `01:00` à Paris en heure d'été
- `00:00` à Paris en heure d'hiver

Le script, lui, calcule toujours la date avec le fuseau `Europe/Paris`, donc les lignes écrites restent cohérentes avec l'heure française.

## Limites à connaître

- Spotify ne fournit pas un filtre parfait "toutes les sorties rap du jour".
- Le script repose sur `tag:new` + plusieurs genres (`hip-hop`, `rap`, `trap`, `drill`) puis filtre sur la date du jour.
- Certaines sorties peuvent apparaître avec un léger décalage selon leur disponibilité régionale.

## Dépannage

- `401` Spotify : vérifie les deux secrets GitHub
- aucun CSV après le run : regarde les logs du workflow dans l'onglet `Actions`
- `IMPORTDATA` vide : vérifie que le repo est bien public et que le fichier existe sur la branche `main`
