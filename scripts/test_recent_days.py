import unittest

from scripts.recent_days import build_recent_days


class RecentDaysTests(unittest.TestCase):
    def test_rolling_days_cross_month_and_year(self):
        days = build_recent_days([], [], '2027-01-03')
        self.assertEqual([d['date'] for d in days], [
            '2027-01-03', '2027-01-02', '2027-01-01', '2026-12-31',
            '2026-12-30', '2026-12-29', '2026-12-28'])

    def test_history_does_not_project_next_airing(self):
        anime = dict(id=1, episode=5, release_date='2026-10-16', next_airing_date='2026-10-18')
        days = build_recent_days([anime], [], '2026-10-18')
        self.assertEqual(days[0]['anime'], [])
        self.assertEqual(days[2]['anime'][0]['episode'], 5)

    def test_past_snapshot_wins_over_live_estimate(self):
        history = [dict(id=1, episode=5, release_date='2026-10-16')]
        live = [dict(id=1, episode=6, release_date='2026-10-16')]
        self.assertEqual(build_recent_days(history, live, '2026-10-18')[2]['anime'][0]['episode'], 5)

    def test_today_uses_confirmed_episode_and_deduplicates(self):
        history = [dict(id=1, episode=5, release_date='2026-10-18')]
        live = [dict(id=1, episode=6, release_date='2026-10-11', next_airing_date='2026-10-18', next_episode_number=7)]
        days = build_recent_days(history, live * 2, '2026-10-18')
        self.assertEqual(len(days[0]['anime']), 1)
        self.assertEqual(days[0]['anime'][0]['episode'], 7)
        self.assertEqual(live[0]['episode'], 6)

    def test_outside_window_and_popularity(self):
        history = [dict(id=1, release_date='2026-10-11'), dict(id=2, release_date='2026-10-19'),
                   dict(id=3, release_date='2026-10-18', popularity=1),
                   dict(id=4, release_date='2026-10-18', popularity=10)]
        self.assertEqual([a['id'] for a in build_recent_days(history, [], '2026-10-18')[0]['anime']], [4, 3])


if __name__ == '__main__':
    unittest.main()
