#!/usr/bin/env python3
"""
Test script to verify 9anime link matching
"""
import json
import sys
sys.path.insert(0, 'scripts')
from generate_html import create_9anime_search_url, find_9anime_link, sanitize_9anime_search_title


search_cleanup_cases = {
    "The Angel Next Door Spoils Me Rotten2": "The Angel Next Door Spoils Me Rotten",
    "The Angel Next Door Spoils Me Rotten Season2": "The Angel Next Door Spoils Me Rotten",
    "The Angel Next Door Spoils Me Rotten S2": "The Angel Next Door Spoils Me Rotten",
    "The Angel Next Door Spoils Me Rotten Season 2": "The Angel Next Door Spoils Me Rotten Season 2",
    "Go For It, Nakamura-kun!!": "Go For It, Nakamura",
    "Go For It, Nakamura - kun!!": "Go For It, Nakamura",
    "Go For It, Nakamura kun": "Go For It, Nakamura kun",
    "The strongest job is an appraiser (provisional)!": "The strongest job is an appraiser (provisional)",
}

for raw_title, expected_title in search_cleanup_cases.items():
    actual_title = sanitize_9anime_search_title(raw_title)
    assert actual_title == expected_title, f"{raw_title!r}: expected {expected_title!r}, got {actual_title!r}"

assert create_9anime_search_url("The Angel Next Door Spoils Me Rotten2").endswith(
    "?s=The+Angel+Next+Door+Spoils+Me+Rotten"
)
assert create_9anime_search_url("Go For It, Nakamura-kun!!").endswith(
    "?s=Go+For+It%2C+Nakamura"
)

# Load data
with open('data/anime_data.json', 'r', encoding='utf-8') as f:
    anime_data = json.load(f)

with open('data/9anime_links.json', 'r', encoding='utf-8') as f:
    nine_anime_links = json.load(f)

# Test matching for popular anime
test_cases = [
    "Boku no Hero Academia FINAL SEASON",
    "SPY×FAMILY Season 3",
    "Fumetsu no Anata e Season 3",
    "ONE PIECE",
    "Ranma 1/2 (2024) 2nd Season"
]

print("Testing 9anime link fuzzy matching:")
print("=" * 80)

for anime_name in test_cases:
    # Find anime in data
    anime = next((a for a in anime_data if a['name'] == anime_name), None)

    if anime:
        english_title = anime.get('english_title')
        nine_anime_url = find_9anime_link(anime_name, english_title, nine_anime_links)

        print(f"\nAnime: {anime_name}")
        if english_title:
            print(f"  English: {english_title}")
        print(f"  9anime URL: {nine_anime_url if nine_anime_url else 'NOT FOUND'}")

        # Extract ID from URL for verification
        if nine_anime_url:
            id_part = nine_anime_url.split('-')[-1]
            print(f"  ID: {id_part}")
    else:
        print(f"\nAnime: {anime_name} - NOT IN ANIME DATA")

print("\n" + "=" * 80)
print("Test complete!")
