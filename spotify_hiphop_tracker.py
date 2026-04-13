#!/usr/bin/env python3
"""
Spotify Hip-Hop / Rap — Daily New Releases Tracker
==================================================
Fetches hip-hop and rap albums released today and exports them to CSV files
that can be committed by GitHub Actions and imported into Google Sheets.

Required environment variables:
  SPOTIFY_CLIENT_ID      — Spotify app Client ID
  SPOTIFY_CLIENT_SECRET  — Spotify app Client Secret
"""

from __future__ import annotations

import base64
import csv
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests


TIMEZONE = ZoneInfo("Europe/Paris")
LATEST_CSV_PATH = Path("releases.csv")
HISTORY_CSV_PATH = Path("releases_history.csv")
CSV_HEADERS = [
    "discovery_date",
    "release_date",
    "artists",
    "album",
    "album_type",
    "total_tracks",
    "spotify_url",
    "image_url",
    "spotify_id",
    "artist_genres",
]

GENRE_KEYWORDS = [
    "hip hop",
    "hip-hop",
    "rap",
    "r&b",
    "rnb",
    "rhythm and blues",
]

SEARCH_QUERIES = [
    'genre:"hip hop" tag:new',
    'genre:rap tag:new',
    'genre:"r&b" tag:new',
    'genre:rnb tag:new',
]


def get_spotify_token(client_id: str, client_secret: str) -> str:
    """Get a Spotify API token using the Client Credentials flow."""
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {auth}"},
        data={"grant_type": "client_credentials"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_json(url: str, token: str, params: dict | None = None) -> dict:
    """Perform a Spotify GET request and return JSON."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def fetch_new_releases(token: str, target_date: str) -> list[dict]:
    """Best-effort fetch of today's new releases via the Search API."""
    albums_found: list[dict] = []
    albums_seen: set[str] = set()

    for query in SEARCH_QUERIES:
        offset = 0

        while offset <= 100:
            data = get_json(
                "https://api.spotify.com/v1/search",
                token,
                params={"q": query, "type": "album", "limit": 10, "offset": offset},
            )
            items = data["albums"]["items"]
            if not items:
                break

            for album in items:
                if album.get("release_date") != target_date:
                    continue

                album_id = album["id"]
                if album_id in albums_seen:
                    continue

                albums_seen.add(album_id)
                albums_found.append(album)

            if data["albums"]["next"] is None:
                break
            offset += 10

    return albums_found


def get_artists_genres(token: str, artist_ids: list[str]) -> dict[str, list[str]]:
    """Fetch genres for artists one by one using Spotify artist metadata."""
    genres_by_artist: dict[str, list[str]] = {}

    for artist_id in artist_ids:
        artist = get_json(f"https://api.spotify.com/v1/artists/{artist_id}", token)
        genres_by_artist[artist_id] = artist.get("genres", [])

    return genres_by_artist


def album_matches_target_genres(album: dict, genres_by_artist: dict[str, list[str]]) -> tuple[bool, list[str]]:
    """Return whether any contributing artist matches the target genre list."""
    matched: set[str] = set()

    for artist in album.get("artists", []):
        for genre in genres_by_artist.get(artist["id"], []):
            normalized = genre.lower()
            if any(keyword in normalized for keyword in GENRE_KEYWORDS):
                matched.add(genre)

    return bool(matched), sorted(matched)


def search_new_hiphop_albums(token: str, target_date: str) -> list[dict[str, str]]:
    """Fetch today's new releases and keep only albums whose artists match target genres."""
    raw_albums = fetch_new_releases(token, target_date)
    artist_ids = sorted({artist["id"] for album in raw_albums for artist in album.get("artists", [])})
    genres_by_artist = get_artists_genres(token, artist_ids)

    albums_found: list[dict[str, str]] = []
    for album in raw_albums:
        matches, matched_genres = album_matches_target_genres(album, genres_by_artist)
        if not matches:
            continue

        albums_found.append(
            {
                "discovery_date": target_date,
                "release_date": album.get("release_date", ""),
                "artists": ", ".join(artist["name"] for artist in album["artists"]),
                "album": album["name"],
                "album_type": album.get("album_type", "").capitalize(),
                "total_tracks": str(album.get("total_tracks", 0)),
                "spotify_url": album["external_urls"].get("spotify", ""),
                "image_url": album["images"][0]["url"] if album.get("images") else "",
                "spotify_id": album["id"],
                "artist_genres": ", ".join(matched_genres),
            }
        )

    return sorted(albums_found, key=lambda album: (album["artists"].lower(), album["album"].lower()))


def read_existing_history(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    """Load existing history rows indexed by discovery date and Spotify ID."""
    if not path.exists():
        return {}

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = {}
        for row in reader:
            spotify_id = row.get("spotify_id")
            discovery_date = row.get("discovery_date")
            if spotify_id and discovery_date:
                rows[(discovery_date, spotify_id)] = {header: row.get(header, "") for header in CSV_HEADERS}
        return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    """Write rows to a CSV file with a stable header."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def update_history(path: Path, todays_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Merge today's rows into the cumulative history without duplicates."""
    history_rows = read_existing_history(path)

    for row in todays_rows:
        history_rows[(row["discovery_date"], row["spotify_id"])] = row

    merged_rows = sorted(
        history_rows.values(),
        key=lambda row: (row["discovery_date"], row["artists"].lower(), row["album"].lower()),
    )
    write_csv(path, merged_rows)
    return merged_rows


def main() -> None:
    now_in_paris = datetime.now(TIMEZONE)
    target_date = now_in_paris.strftime("%Y-%m-%d")

    print(f"Searching for new hip-hop / rap albums released on {target_date} (Europe/Paris)...")

    client_id = os.environ["SPOTIFY_CLIENT_ID"]
    client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]

    token = get_spotify_token(client_id, client_secret)
    todays_albums = search_new_hiphop_albums(token, target_date)

    write_csv(LATEST_CSV_PATH, todays_albums)
    all_history = update_history(HISTORY_CSV_PATH, todays_albums)

    print(f"Found {len(todays_albums)} album(s) for today.")
    print(f"Wrote {LATEST_CSV_PATH} and {HISTORY_CSV_PATH} ({len(all_history)} total row(s)).")

    if todays_albums:
        print("\nAlbums found today:")
        for album in todays_albums:
            print(f" - {album['artists']} — {album['album']} ({album['album_type']})")
    else:
        print("No hip-hop / rap albums found for today.")


if __name__ == "__main__":
    main()
