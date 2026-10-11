"""Backfill AniList content metadata without refreshing schedules or rankings."""
import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

try:
    from .content_warnings import content_metadata
except ImportError:
    from content_warnings import content_metadata

FILES = [
    'anime_data.json', 'other_anime_sorted.json', 'recently_finished_anime.json',
    'upcoming_seasonal_anime.json', 'calendar_history.json', 'all_anime_catalog.json',
]
QUERY = '''query ($ids: [Int], $page: Int) {
    Page(page: $page, perPage: 50) {
        media(id_in: $ids, type: ANIME) { id isAdult genres tags { name rank } }
    }
}'''


def fetch_metadata(ids):
    payload = json.dumps({'query': QUERY, 'variables': {'ids': ids, 'page': 1}}).encode()
    for attempt in range(4):
        try:
            request = Request('https://graphql.anilist.co', data=payload,
                              headers={'Content-Type': 'application/json', 'User-Agent': 'AnimeTracker/3.3'})
            with urlopen(request, timeout=30) as response:
                data = json.load(response)
            if data.get('errors'):
                raise RuntimeError(data['errors'])
            return data['data']['Page']['media']
        except HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise
            time.sleep(min(int(error.headers.get('Retry-After', 30)), 60))
    raise RuntimeError('AniList request failed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--all', action='store_true', help='Also refresh all historical catalog entries')
    args = parser.parse_args()
    datasets = {}
    for name in FILES:
        path = Path('data') / name
        if path.exists():
            datasets[path] = json.loads(path.read_text(encoding='utf-8'))
    ids = sorted({entry['id'] for path, entries in datasets.items()
                  if args.all or path.name != 'all_anime_catalog.json' for entry in entries})
    refreshed = {}
    for offset in range(0, len(ids), 50):
        for media in fetch_metadata(ids[offset:offset + 50]):
            refreshed[media['id']] = content_metadata(media)
        print(f'Refreshed {min(offset + 50, len(ids))}/{len(ids)} titles', flush=True)
        time.sleep(2)
    # Write only after every batch succeeds, preserving all unrelated fields.
    for path, entries in datasets.items():
        count = 0
        for entry in entries:
            if entry['id'] in refreshed:
                entry.update(refreshed[entry['id']])
                count += 1
        if count:
            path.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(f'Updated {count} entries in {path}', flush=True)


if __name__ == '__main__':
    main()
