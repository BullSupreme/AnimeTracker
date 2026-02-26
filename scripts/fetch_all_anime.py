#!/usr/bin/env python3
"""
Fetch all anime catalog from AniList API.

Modes:
  --full      Full historical scan from 1990 to today (run locally once to build initial catalog)
  (default)   Incremental mode: fetch previous + current month only, merge into existing catalog

Uses AniList `id` as deduplication key — safe to run multiple times.
"""
import json
import requests
import time
import argparse
import os
from datetime import datetime, timedelta, date
from calendar import monthrange

ANILIST_API_URL = "https://graphql.anilist.co"
CATALOG_FILE = "data/all_anime_catalog.json"

QUERY_BY_DATE = '''
query ($page: Int, $perPage: Int, $startDate: FuzzyDateInt, $endDate: FuzzyDateInt) {
    Page(page: $page, perPage: $perPage) {
        pageInfo { hasNextPage currentPage total }
        media(
            type: ANIME,
            format_in: [TV, ONA, TV_SHORT],
            sort: [START_DATE],
            startDate_greater: $startDate,
            startDate_lesser: $endDate,
            isAdult: false
        ) {
            id idMal
            title { romaji english }
            averageScore popularity genres episodes format status
            season seasonYear
            coverImage { large }
            siteUrl
            startDate { year month day }
        }
    }
}
'''



def make_request(query, variables, retry_count=5):
    """Make AniList API request with retries and rate-limit handling."""
    for attempt in range(retry_count):
        try:
            response = requests.post(
                ANILIST_API_URL,
                json={'query': query, 'variables': variables},
                timeout=20
            )
            # Check rate limit headers
            remaining = int(response.headers.get('X-RateLimit-Remaining', 10))
            if remaining <= 2:
                # Proactively slow down before hitting the limit
                print(f"  Rate limit low ({remaining} remaining), pausing 15s...")
                time.sleep(15)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"  Rate limited. Waiting {retry_after}s...")
                time.sleep(retry_after + 2)
            elif response.status_code >= 500:
                wait = 5 * (attempt + 1)
                print(f"  Server error {response.status_code}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"  HTTP error {response.status_code}: {response.text[:200]}")
                return None
        except requests.RequestException as e:
            wait = 5 * (attempt + 1)
            print(f"  Request error: {e}. Retrying in {wait}s...")
            time.sleep(wait)
    print("  Failed after all retries.")
    return None


def fuzzy_date(year, month, day=1):
    """Convert to AniList FuzzyDateInt format: YYYYMMDD"""
    return int(f"{year}{month:02d}{day:02d}")


def process_anime(raw):
    """Extract relevant fields from raw AniList media object."""
    start = raw.get('startDate', {})
    if start and start.get('year') and start.get('month') and start.get('day'):
        start_date = f"{start['year']}-{start['month']:02d}-{start['day']:02d}"
    elif start and start.get('year') and start.get('month'):
        start_date = f"{start['year']}-{start['month']:02d}"
    elif start and start.get('year'):
        start_date = str(start['year'])
    else:
        start_date = None

    poster = raw.get('coverImage', {})
    poster_url = poster.get('large') or poster.get('medium') or ''

    return {
        'id': raw['id'],
        'mal_id': raw.get('idMal'),
        'name': raw['title']['romaji'],
        'english_title': raw['title'].get('english'),
        'poster_url': poster_url,
        'site_url': raw.get('siteUrl', f"https://anilist.co/anime/{raw['id']}"),
        'anilist_score': raw.get('averageScore'),
        'popularity': raw.get('popularity', 0),
        'genres': raw.get('genres', []),
        'season': raw.get('season'),
        'season_year': raw.get('seasonYear'),
        'format': raw.get('format'),
        'episodes': raw.get('episodes'),
        'status': raw.get('status'),
        'start_date': start_date,
    }


def fetch_by_date_range(start_fuzzy, end_fuzzy, label=""):
    """Fetch all pages of anime within a fuzzy date range."""
    results = []
    page = 1
    per_page = 50

    while True:
        variables = {
            'page': page,
            'perPage': per_page,
            'startDate': start_fuzzy,
            'endDate': end_fuzzy,
        }
        data = make_request(QUERY_BY_DATE, variables)

        if not data or 'data' not in data or not data['data']['Page']['media']:
            break

        page_data = data['data']['Page']
        media = page_data['media']
        results.extend(media)

        if not page_data['pageInfo']['hasNextPage']:
            break

        page += 1
        time.sleep(1)

    if label and results:
        print(f"  {label}: fetched {len(results)} anime")

    return [process_anime(a) for a in results]



def merge_into_catalog(catalog, new_anime):
    """Merge new_anime into catalog using id as dedup key (upsert)."""
    catalog_dict = {a['id']: a for a in catalog}
    updated = 0
    added = 0

    for anime in new_anime:
        if anime['id'] in catalog_dict:
            updated += 1
        else:
            added += 1
        catalog_dict[anime['id']] = anime

    print(f"  Merged: {added} new, {updated} updated, total {len(catalog_dict)}")
    return list(catalog_dict.values())


def load_catalog():
    """Load existing catalog or return empty list."""
    if os.path.exists(CATALOG_FILE):
        with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"Loaded existing catalog: {len(data)} anime")
            return data
    print("No existing catalog found, starting fresh.")
    return []


def save_catalog(catalog):
    """Save catalog sorted by popularity descending."""
    catalog.sort(key=lambda x: x.get('popularity', 0), reverse=True)
    os.makedirs('data', exist_ok=True)
    with open(CATALOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)
    print(f"Saved catalog: {len(catalog)} anime to {CATALOG_FILE}")


def run_full_scan():
    """
    Full historical scan from 1990 to today (for local initial build).
    Uses 2-year windows with 1s between pages and 2s between windows.
    Checkpoints to disk after each window so progress is never lost.
    """
    print("=== FULL HISTORICAL SCAN ===")
    print("Fetches all TV/ONA anime from 1990 to present in 2-year windows.")
    print("Progress is saved after each window — safe to re-run if interrupted.\n")

    catalog = load_catalog()
    existing_ids = {a['id'] for a in catalog}
    today = date.today()

    year = 1990
    while year <= today.year:
        year_end = min(year + 1, today.year)
        start_fuzzy = fuzzy_date(year, 1, 1)
        end_fuzzy = fuzzy_date(year_end, 12, 31)
        label = f"{year}" if year == year_end else f"{year}-{year_end}"

        print(f"\n[{label}]")
        page = 1
        window_results = []

        while True:
            variables = {
                'page': page,
                'perPage': 50,
                'startDate': start_fuzzy,
                'endDate': end_fuzzy,
            }
            data = make_request(QUERY_BY_DATE, variables)

            if not data or 'data' not in data:
                print(f"  Request failed on page {page}, saving and continuing...")
                break

            page_data = data['data']['Page']
            media = page_data['media']
            if not media:
                break

            new_in_page = [process_anime(a) for a in media]
            window_results.extend(new_in_page)
            print(f"  page {page} — {len(window_results)} fetched this window")

            if not page_data['pageInfo']['hasNextPage'] or page >= 50:
                break

            page += 1
            time.sleep(1)

        if window_results:
            catalog = merge_into_catalog(catalog, window_results)
            save_catalog(catalog)
            print(f"  Checkpoint: {len(catalog)} total anime in catalog")

        year += 2
        time.sleep(2)

    print(f"\n=== COMPLETE: {len(catalog)} anime in catalog ===")
    save_catalog(catalog)


def run_incremental():
    """Incremental mode: fetch previous + current month and merge."""
    print("=== INCREMENTAL UPDATE ===")
    today = date.today()
    catalog = load_catalog()

    # Current month
    current_start = fuzzy_date(today.year, today.month, 1)
    current_last_day = monthrange(today.year, today.month)[1]
    current_end = fuzzy_date(today.year, today.month, current_last_day)

    # Previous month
    if today.month == 1:
        prev_year, prev_month = today.year - 1, 12
    else:
        prev_year, prev_month = today.year, today.month - 1

    prev_start = fuzzy_date(prev_year, prev_month, 1)
    prev_last_day = monthrange(prev_year, prev_month)[1]
    prev_end = fuzzy_date(prev_year, prev_month, prev_last_day)

    print(f"\nFetching {prev_year}-{prev_month:02d}...")
    prev_anime = fetch_by_date_range(prev_start, prev_end, label=f"{prev_year}-{prev_month:02d}")
    if prev_anime:
        catalog = merge_into_catalog(catalog, prev_anime)

    time.sleep(1)

    print(f"\nFetching {today.year}-{today.month:02d}...")
    curr_anime = fetch_by_date_range(current_start, current_end, label=f"{today.year}-{today.month:02d}")
    if curr_anime:
        catalog = merge_into_catalog(catalog, curr_anime)

    save_catalog(catalog)
    print("=== INCREMENTAL UPDATE COMPLETE ===")


def main():
    parser = argparse.ArgumentParser(description='Fetch all anime catalog from AniList')
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run full historical scan (use locally to build initial catalog)'
    )
    args = parser.parse_args()

    if args.full:
        run_full_scan()
    else:
        run_incremental()


if __name__ == '__main__':
    main()
