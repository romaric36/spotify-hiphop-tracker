#!/usr/bin/env python3
"""
Spotify Hip-Hop / Rap — Daily New Releases Tracker
====================================================
Fetches new hip-hop and rap albums released today and logs them to Google Sheets.

Required environment variables:
  SPOTIFY_CLIENT_ID          — Spotify app Client ID
  SPOTIFY_CLIENT_SECRET      — Spotify app Client Secret
  GOOGLE_SPREADSHEET_ID      — ID of the target Google Spreadsheet
  GOOGLE_SERVICE_ACCOUNT_JSON — Full JSON content of the Google Service Account key
"""

import os
import json
import datetime
import requests
import base64

from googleapiclient.discovery import build
from google.oauth2 import service_account


# ── Spotify — Authentication ──────────────────────────────────────────────────

def get_spotify_token(client_id: str, client_secret: str) -> str:
    """Get a Spotify API token using the Client Credentials flow (no user login needed)."""
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {auth}"},
        data={"grant_type": "client_credentials"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


# ── Spotify — Search new hip-hop/rap releases ─────────────────────────────────

def search_new_hiphop_albums(token: str, today_str: str) -> list[dict]:
    """
    Search for new hip-hop/rap albums and filter by today's release date.
    Uses `tag:new` to target recently released content, then filters by exact date.

    Note: Spotify removed the /browse/new-releases endpoint in February 2026.
    This search-based approach is the recommended workaround.
    """
    headers = {"Authorization": f"Bearer {token}"}
    albums_seen = set()
    albums_found = []

    # Search across both hip-hop and rap genre tags
    queries = [
        "genre:hip-hop tag:new",
        "genre:rap tag:new",
        "genre:trap tag:new",
        "genre:drill tag:new",
    ]

    for query in queries:
        offset = 0

        while offset <= 200:  # Spotify caps search at 1000 results; 50*4=200 is a good ceiling
            params = {
                "q": query,
                "type": "album",
                "limit": 50,
                "offset": offset,
            }

            resp = requests.get(
                "https://api.spotify.com/v1/search",
                headers=headers,
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            items = data["albums"]["items"]
            if not items:
                break

            for album in items:
                release_date = album.get("release_date", "")

                # Only keep albums released today
                if release_date != today_str:
                    continue

                album_id = album["id"]
                if album_id in albums_seen:
                    continue

                albums_seen.add(album_id)
                albums_found.append({
                    "id": album_id,
                    "name": album["name"],
                    "artists": ", ".join(a["name"] for a in album["artists"]),
                    "release_date": release_date,
                    "album_type": album.get("album_type", ""),
                    "total_tracks": album.get("total_tracks", 0),
                    "spotify_url": album["external_urls"].get("spotify", ""),
                    "image_url": album["images"][0]["url"] if album.get("images") else "",
                })

            # Move to next page, or stop if no more results
            if data["albums"]["next"] is None:
                break
            offset += 50

    return albums_found


# ── Google Sheets ─────────────────────────────────────────────────────────────

def get_sheets_service(service_account_json: str):
    """Build the Google Sheets API service from a Service Account JSON string."""
    creds_info = json.loads(service_account_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = service_account.Credentials.from_service_account_info(creds_info, scopes=scopes)
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def ensure_header(service, spreadsheet_id: str) -> None:
    """Write the header row if the sheet is empty."""
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range="Sheet1!A1:I1")
        .execute()
    )

    if "values" not in result:
        headers = [[
            "Date découverte",
            "Artiste(s)",
            "Album",
            "Type",
            "Nb titres",
            "Date de sortie",
            "Spotify URL",
            "Pochette URL",
            "ID Spotify",
        ]]
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body={"values": headers},
        ).execute()
        print("✅ Header row created.")


def append_albums(service, spreadsheet_id: str, albums: list[dict], discovery_date: str) -> None:
    """Append album rows to the Google Sheet."""
    if not albums:
        print("ℹ️  No new albums to add today.")
        return

    rows = [
        [
            discovery_date,
            album["artists"],
            album["name"],
            album["album_type"].capitalize(),
            album["total_tracks"],
            album["release_date"],
            album["spotify_url"],
            album["image_url"],
            album["id"],
        ]
        for album in albums
    ]

    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range="Sheet1!A1",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()

    print(f"✅ {len(rows)} album(s) added to Google Sheets.")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")

    print(f"🎵 Searching for new hip-hop/rap albums released on {today_str}...")

    # Load credentials from environment variables
    client_id = os.environ["SPOTIFY_CLIENT_ID"]
    client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]
    spreadsheet_id = os.environ["GOOGLE_SPREADSHEET_ID"]
    service_account_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

    # Step 1 — Spotify search
    token = get_spotify_token(client_id, client_secret)
    albums = search_new_hiphop_albums(token, today_str)
    print(f"🔍 Found {len(albums)} album(s) released today.")

    # Step 2 — Write to Google Sheets
    sheets = get_sheets_service(service_account_json)
    ensure_header(sheets, spreadsheet_id)
    append_albums(sheets, spreadsheet_id, albums, today_str)

    # Summary
    if albums:
        print("\n📋 Albums logged:")
        for a in albums:
            print(f"   • {a['artists']} — {a['name']} ({a['album_type']}, {a['total_tracks']} tracks)")
    else:
        print("No hip-hop/rap albums found for today.")


if __name__ == "__main__":
    main()
