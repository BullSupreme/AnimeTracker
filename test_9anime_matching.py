#!/usr/bin/env python3
"""
Test script to verify 9anime link matching
"""
import json
import sys
sys.path.insert(0, 'scripts')
from generate_html import find_9anime_link

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
