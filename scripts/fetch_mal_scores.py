#!/usr/bin/env python3
import json
import requests
import time
import os
from datetime import datetime

# MAL Jikan API (unofficial but reliable)
JIKAN_API_URL = "https://api.jikan.moe/v4"

def fetch_mal_score(mal_id, retry_count=3):
    """Fetch MAL score for a specific anime by MAL ID"""
    if not mal_id:
        return None
    
    for attempt in range(retry_count):
        try:
            response = requests.get(
                f"{JIKAN_API_URL}/anime/{mal_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                anime_data = data.get('data', {})
                return {
                    'mal_score': anime_data.get('score'),
                    'mal_scored_by': anime_data.get('scored_by'),
                    'mal_rank': anime_data.get('rank'),
                    'mal_popularity': anime_data.get('popularity'),
                    'mal_members': anime_data.get('members')
                }
            elif response.status_code == 429:  # Rate limited
                print(f"Rate limited, waiting before retry...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Error fetching MAL data for ID {mal_id}: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"Request error for MAL ID {mal_id}: {e}")
            if attempt < retry_count - 1:
                time.sleep(1)
    
    return None

def update_anime_with_mal_scores(anime_data_file):
    """Update existing anime data with MAL scores"""
    # Load existing anime data
    with open(anime_data_file, 'r', encoding='utf-8') as f:
        anime_data = json.load(f)
    
    updated_count = 0
    skipped_count = 0
    
    print(f"Updating {len(anime_data)} anime with MAL scores...")
    
    for i, anime in enumerate(anime_data):
        mal_id = anime.get('mal_id')
        
        # Skip if no MAL ID or already has MAL score
        if not mal_id or anime.get('mal_score') is not None:
            skipped_count += 1
            continue
        
        print(f"Fetching MAL data for {anime['name']} (MAL ID: {mal_id}) [{i+1}/{len(anime_data)}]")
        
        mal_data = fetch_mal_score(mal_id)
        if mal_data:
            anime.update(mal_data)
            updated_count += 1
        
        # Rate limit: Jikan API allows 3 requests per second
        time.sleep(0.35)  # ~2.8 requests per second to be safe
    
    print(f"\nUpdated {updated_count} anime with MAL scores")
    print(f"Skipped {skipped_count} anime (no MAL ID or already has score)")
    
    # Save updated data
    with open(anime_data_file, 'w', encoding='utf-8') as f:
        json.dump(anime_data, f, ensure_ascii=False, indent=2)
    
    return anime_data

def update_all_anime_files():
    """Update all anime data files with MAL scores"""
    data_files = [
        'data/anime_data.json',
        'data/other_anime_sorted.json',
        'data/upcoming_seasonal_anime.json'
    ]
    
    for file_path in data_files:
        if os.path.exists(file_path):
            print(f"\nUpdating {file_path}...")
            update_anime_with_mal_scores(file_path)
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    update_all_anime_files()