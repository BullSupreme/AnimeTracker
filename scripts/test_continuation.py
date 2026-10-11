import unittest
from datetime import date

from scripts.continuation import continuation_metadata, get_continuation_badges, continuation_html


class ContinuationTests(unittest.TestCase):
    def labels(self, **anime):
        return [b['label'] for b in get_continuation_badges(anime, date(2026, 1, 15))]

    def test_part_and_season_share_one_sequel_badge(self):
        self.assertEqual(self.labels(name='Example 2nd Season Part 2', english_title='Example Part 2',
                                     prequels=[{'title': {'romaji': 'Example'}}]), ['Sequel'])
        self.assertEqual(self.labels(name='Example Part 2'), ['Sequel'])

    def test_cour_orders(self):
        self.assertEqual(self.labels(name='Example 2nd Cour'), ['Sequel'])
        self.assertEqual(self.labels(name='Example Cour 3'), ['Sequel'])
        self.assertEqual(self.labels(name='Example Second Cour'), ['Sequel'])
        self.assertEqual(self.labels(name='Example Second Season'), ['Sequel'])
        self.assertEqual(self.labels(name='Example 1st Cour'), [])

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

    def test_single_prequel_links_to_anilist(self):
        html = continuation_html({'prequels': [{'id': 123, 'title': {'english': 'Previous'}}]})
        self.assertIn('href="https://anilist.co/anime/123/"', html)
        self.assertIn('aria-label="Open preceding anime: Previous"', html)
        self.assertNotIn('<details', html)

    def test_multiple_prequels_offer_choice_and_deduplicate(self):
        html = continuation_html({'prequels': [{'id': 1}, {'id': 2}, {'id': 1}]})
        self.assertIn('<details', html)
        self.assertEqual(html.count('href='), 2)

    def test_title_only_sequel_does_not_invent_previous_link(self):
        html = continuation_html({'name': 'Example Season 2'})
        self.assertIn('Sequel', html)
        self.assertNotIn('href=', html)


if __name__ == '__main__':
    unittest.main()
