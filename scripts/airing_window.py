"""Exclude releasing shows whose confirmed return falls after this season."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def is_paused_past_season(anime, today):
    status = anime.get('status')
    next_episode = anime.get('nextAiringEpisode') or {}
    episode_number = next_episode.get('episode', anime.get('next_episode_number'))
    # Older snapshots may lack status; only infer ongoing when episodes already aired.
    if status != 'RELEASING' and not (
            status is None and isinstance(episode_number, int) and episode_number > 1):
        return False

    next_date = None
    timestamp = next_episode.get('airingAt')
    if isinstance(timestamp, (int, float)):
        try:
            next_date = datetime.fromtimestamp(timestamp, ZoneInfo('America/New_York')).date()
        except (ValueError, OverflowError, OSError):
            return False
    else:
        try:
            next_date = date.fromisoformat(anime.get('next_airing_date') or '')
        except (TypeError, ValueError):
            return False

    next_month = ((today.month - 1) // 3 + 1) * 3 + 1
    next_season = date(today.year + 1, 1, 1) if next_month == 13 else date(today.year, next_month, 1)
    return next_date > next_season - timedelta(days=1)
