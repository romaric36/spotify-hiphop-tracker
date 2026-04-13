# Setup Guide — Spotify Hip-Hop Weekly Tracker

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

- `releases.csv` contient uniquement les sorties détectées dans la fenêtre hebdomadaire courante.
- `releases_history.csv` conserve l'historique cumulé des sorties trouvées au fil des exécutions.
- GitHub Actions lance le script chaque vendredi matin et commit automatiquement les CSV mis à jour.
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
2. Clique sur `🎵 Weekly Hip-Hop Releases Tracker`
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

Si tu préfères n'afficher que la fenêtre hebdomadaire courante :

```text
=IMPORTDATA("https://raw.githubusercontent.com/romaric36/spotify-hiphop-tracker/main/releases.csv")
```

## Colonnes du CSV

| discovery_date | release_date | artists | album | album_type | total_tracks | spotify_url | image_url | spotify_id |
|---|---|---|---|---|---|---|---|---|

## Planification

Le workflow est planifié avec :

```yaml
- cron: '0 3 * * 5'
```

Cela correspond à :

- `05:00` à Paris en heure d'été le vendredi
- `04:00` à Paris en heure d'hiver le vendredi

Le script calcule une fenêtre de sortie du `samedi` précédent jusqu'au `vendredi` courant avec le fuseau `Europe/Paris`.

## Limites à connaître

- Spotify ne fournit pas un filtre parfait "toutes les sorties rap de la semaine".
- Le script repose sur `Search` + contrôle des genres artistes (`hip hop`, `rap`, `r&b`) puis filtre les dates entre le samedi précédent et le vendredi courant.
- Certaines sorties peuvent apparaître avec un léger décalage selon leur disponibilité régionale.

## Dépannage

- `401` Spotify : vérifie les deux secrets GitHub
- aucun CSV après le run : regarde les logs du workflow dans l'onglet `Actions`
- `IMPORTDATA` vide : vérifie que le repo est bien public et que le fichier existe sur la branche `main`
