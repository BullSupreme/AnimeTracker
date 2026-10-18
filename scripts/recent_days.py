"""Build a rolling seven-day lineup without projecting historical next-airing dates."""
from datetime import date, timedelta


def build_recent_days(history, live, today):
    if isinstance(today, str):
        today = date.fromisoformat(today)
    days = {(today - timedelta(days=offset)).isoformat(): {} for offset in range(7)}

    def add(anime, release, episode=None, replace=False):
        if release not in days:
            return
        key = anime.get('id') or anime.get('name')
        if key in days[release] and not replace:
            return
        entry = dict(anime, release_date=release)
        if episode is not None:
            entry['episode'] = episode
        days[release][key] = entry

    for anime in history:
        add(anime, anime.get('release_date'))
    for anime in live:
        release = anime.get('release_date')
        add(anime, release, replace=release == today.isoformat())
        release = anime.get('next_airing_date')
        if release == today.isoformat():
            add(anime, release, anime.get('next_episode_number'), replace=True)

    return [dict(date=day, anime=sorted(entries.values(), key=lambda a: -(a.get('popularity') or 0)))
            for day, entries in days.items()]
