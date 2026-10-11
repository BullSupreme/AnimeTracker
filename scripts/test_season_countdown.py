import unittest
from datetime import date

from scripts.season_countdown import season_start, countdown_label


class SeasonCountdownTests(unittest.TestCase):
    def test_season_boundaries(self):
        for season, month in [('WINTER', 1), ('Spring', 4), ('SUMMER', 7), ('FALL', 10)]:
            self.assertEqual(season_start(season, 2027), date(2027, month, 1))
        self.assertIsNone(season_start('UNKNOWN', 2027))
        self.assertIsNone(season_start('Winter', 0))

    def test_countdown_across_year(self):
        self.assertEqual(countdown_label(date(2027, 1, 1), date(2026, 10, 11)), 'Starts in 82 days')

    def test_singular_today_and_started(self):
        start = date(2027, 1, 1)
        self.assertEqual(countdown_label(start, date(2026, 12, 31)), 'Starts in 1 day')
        self.assertEqual(countdown_label(start, start), 'Starts today')
        self.assertEqual(countdown_label(start, date(2027, 1, 2)), 'Season underway')


if __name__ == '__main__':
    unittest.main()
