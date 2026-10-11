import unittest
from datetime import date

from scripts.continuation import continuation_metadata, get_continuation_badges, continuation_html


class ContinuationTests(unittest.TestCase):
    def labels(self, **anime):
        return [b['label'] for b in get_continuation_badges(anime, date(2026, 1, 15))]

    def test_sequel_and_part_coexist_without_duplicates(self):
        self.assertEqual(self.labels(name='Example 2nd Season Part 2', english_title='Example Part 2',
                                     prequels=[{'title': {'romaji': 'Example'}}]), ['Sequel', 'Part 2'])

    def test_cour_orders(self):
        self.assertEqual(self.labels(name='Example 2nd Cour'), ['2nd Cour'])
        self.assertEqual(self.labels(name='Example Cour 3'), ['3rd Cour'])
        self.assertEqual(self.labels(name='Example Second Cour'), ['2nd Cour'])
        self.assertEqual(self.labels(name='Example Second Season'), ['Sequel'])

    def test_not_every_number_or_relation_means_sequel(self):
        self.assertEqual(self.labels(name='86', english_title='Example Part 1'), [])
        normalized = continuation_metadata({'relations': {'edges': [
            {'relationType': 'PREQUEL', 'node': {'type': 'MANGA'}},
            {'relationType': 'SIDE_STORY', 'node': {'type': 'ANIME'}}, None]}})
        self.assertEqual(normalized['prequels'], [])

    def test_carryover_year_boundary(self):
        self.assertEqual(self.labels(status='RELEASING', season='FALL', season_year=2025), ['From Last Season'])
        self.assertEqual(self.labels(status='RELEASING', season='SPRING', season_year=2025), ['Continuing'])
        self.assertEqual(self.labels(status='FINISHED', season='FALL', season_year=2025), [])
        self.assertEqual(self.labels(status='RELEASING', season='WINTER', season_year=2026), [])
        self.assertEqual(self.labels(status='NOT_YET_RELEASED', season='FALL', season_year=2025), [])

    def test_normalized_metadata_survives_calendar_snapshot(self):
        anime = {'prequels': [{'id': 1}], 'status': 'RELEASING', 'season': 'Spring', 'season_year': 2026}
        self.assertEqual(continuation_metadata(anime), anime)

    def test_later_released_prequel_does_not_label_original_as_sequel(self):
        self.assertEqual(self.labels(name='Original', season='FALL', season_year=1999,
                                     prequels=[{'season': 'WINTER', 'seasonYear': 2024}]), [])

    def test_html_escapes_related_titles(self):
        self.assertIn('&lt;Example&gt;', continuation_html({'prequels': [{'title': {'romaji': '<Example>'}}]}))


if __name__ == '__main__':
    unittest.main()
