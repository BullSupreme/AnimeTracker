import unittest
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo
from unittest.mock import Mock, patch

from scripts.airing_window import is_paused_past_season


class AiringWindowTests(unittest.TestCase):
    def test_one_piece_return_next_year(self):
        anime = {'status': 'RELEASING', 'next_airing_date': '2027-01-03', 'next_episode_number': 1181}
        self.assertTrue(is_paused_past_season(anime, date(2026, 10, 12)))
        self.assertTrue(is_paused_past_season(anime, date(2026, 12, 31)))
        self.assertFalse(is_paused_past_season(anime, date(2027, 1, 1)))

    def test_raw_api_timestamp_matches_snapshot(self):
        timestamp = datetime(2027, 1, 3, 9, tzinfo=ZoneInfo('America/New_York')).timestamp()
        anime = {'status': 'RELEASING', 'nextAiringEpisode': {'episode': 1181, 'airingAt': timestamp}}
        self.assertTrue(is_paused_past_season(anime, date(2026, 10, 12)))

    def test_regular_airing_and_last_day_stay(self):
        for next_date in ('2026-10-19', '2026-12-31'):
            self.assertFalse(is_paused_past_season(
                {'status': 'RELEASING', 'next_airing_date': next_date}, date(2026, 10, 12)))

    def test_other_season_boundary(self):
        anime = {'status': 'RELEASING', 'next_airing_date': '2026-07-01'}
        self.assertTrue(is_paused_past_season(anime, date(2026, 6, 30)))
        self.assertFalse(is_paused_past_season(anime, date(2026, 7, 1)))

    def test_missing_dates_and_non_releasing_entries_stay(self):
        for anime in ({'status': 'RELEASING'}, {'status': 'RELEASING', 'next_airing_date': 'TBD'},
                      {'status': 'NOT_YET_RELEASED', 'next_airing_date': '2027-01-03'},
                      {'status': 'FINISHED', 'next_airing_date': '2027-01-03'}):
            self.assertFalse(is_paused_past_season(anime, date(2026, 10, 12)))

    def test_legacy_ongoing_snapshot(self):
        self.assertTrue(is_paused_past_season(
            {'next_episode_number': 1181, 'next_airing_date': '2027-01-03'}, date(2026, 10, 12)))

    def test_fetch_filter_runs_before_long_running_exceptions(self):
        # The filter test never reaches the HTTP client.
        with patch.dict(sys.modules, {'requests': Mock()}):
            from scripts.fetch_anime_data import process_anime_data
        year = datetime.now(ZoneInfo('America/New_York')).year + 1
        timestamp = datetime(year, 1, 3, 9, tzinfo=ZoneInfo('America/New_York')).timestamp()
        anime = {'id': 21, 'status': 'RELEASING', 'title': {'romaji': 'ONE PIECE'},
                 'nextAiringEpisode': {'episode': 1181, 'airingAt': timestamp}}
        self.assertEqual(process_anime_data({'data': {'Page': {'media': [anime]}}}), [])


if __name__ == '__main__':
    unittest.main()
