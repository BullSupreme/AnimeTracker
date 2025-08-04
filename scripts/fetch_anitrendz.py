#!/usr/bin/env python3
import json
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def fetch_anitrendz_rankings():
    """Fetch current weekly anime rankings from AniTrendz"""
    url = "https://www.anitrendz.com/charts/top-anime"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find ranking entries using the primary structure only (to avoid duplicates)
        ranking_items = soup.find_all('div', class_='ChartChoice_at-mcc-entry__Cciiz')
        print(f"Found {len(ranking_items)} ranking entries")
        
        rankings = []
        
        for item in ranking_items:
            try:
                # Get rank from the new structure
                rank_elem = item.find('div', class_='ChartChoice_main-rank___oDHZ')
                if rank_elem:
                    rank_div = rank_elem.find('div')
                    if rank_div:
                        rank = int(rank_div.text.strip())
                    else:
                        continue
                else:
                    continue
                
                # Get anime title from the new structure
                title_elem = item.find('div', class_='ChartChoice_entry-title__dp5Tw')
                if title_elem:
                    title = title_elem.text.strip()
                else:
                    continue
                
                # Get change indicator from movement section
                change = 'stable'
                movement_elem = item.find('div', class_='ChartChoice_at-mcc-e-movement__5jaUV')
                if movement_elem:
                    # Check for arrow images
                    arrow_img = movement_elem.find('img')
                    if arrow_img and arrow_img.get('alt'):
                        alt = arrow_img.get('alt')
                        if 'up-arrow' in alt:
                            change = 'up'
                        elif 'down-arrow' in alt:
                            change = 'down'
                        elif 'right-arrow' in alt:
                            change = 'stable'
                
                # Get movement number if available
                movement_number = 0
                if movement_elem:
                    number_elem = movement_elem.find('div', class_='ChartChoice_arrow-number__rEGbh')
                    if number_elem:
                        number_text = number_elem.text.strip()
                        # Extract number from strings like "+2", "-1", "3W", "RE"
                        if number_text.isdigit():
                            movement_number = int(number_text)
                        elif number_text.startswith(('+', '-')):
                            try:
                                movement_number = int(number_text)
                            except ValueError:
                                movement_number = 0
                
                # Get stats (weeks on chart, peak, etc.)
                weeks_on_chart = 0
                peak_rank = 0
                last_position = 0
                
                stats_divs = item.find_all('div', class_='ChartChoice_stats-entry__Lgw6A')
                for stats_div in stats_divs:
                    span = stats_div.find('span')
                    img = stats_div.find('img')
                    if span and img:
                        alt = img.get('alt', '')
                        value = span.text.strip()
                        try:
                            if 'peak' in alt.lower():
                                peak_rank = int(value)
                            elif 'weeks' in alt.lower():
                                weeks_on_chart = int(value)
                            elif 'lastposition' in alt.lower():
                                last_position = int(value)
                        except ValueError:
                            continue
                
                rankings.append({
                    'rank': rank,
                    'title': title,
                    'change': change,
                    'movement_number': movement_number,
                    'weeks_on_chart': weeks_on_chart,
                    'peak_rank': peak_rank,
                    'last_position': last_position
                })
                
            except Exception as e:
                print(f"Error parsing ranking item: {e}")
                continue
        
        # Sort rankings by rank to deduplicate or order them (optional, but helpful)
        rankings = sorted(set(tuple(sorted(d.items())) for d in rankings))  # Dedup by converting to sorted tuples
        rankings = [dict(t) for t in rankings]
        
        return {
            'rankings': rankings,
            'last_updated': datetime.now().isoformat(),
            'week': datetime.now().strftime('%Y-W%U'),
            'total_entries': len(rankings)
        }
        
    except Exception as e:
        print(f"Error fetching AniTrendz rankings: {e}")
        return None

def get_title_variations(title):
    if not title:
        return set()
    lower = title.lower()
    base = lower
    season_num = None
    part_num = None

    # Season
    season_match = re.search(r'(s|season|(\d+)(nd|rd|th)\s+season\s*)(\d+)', base, re.IGNORECASE)
    if season_match:
        season_num = int(season_match.group(4) or season_match.group(2))
        base = re.sub(r'(s|season|\d+(nd|rd|th)\s+season\s*)\d+', '', base, flags=re.IGNORECASE).strip()

    # Part
    part_match = re.search(r'part\s*(ii|iii|iv|v|2|3|4|5)', base, re.IGNORECASE)
    if part_match:
        p = part_match.group(1).lower()
        if p == 'ii': part_num = 2
        elif p == 'iii': part_num = 3
        elif p == 'iv': part_num = 4
        elif p == 'v': part_num = 5
        else: part_num = int(p)
        base = re.sub(r'part\s*(ii|iii|iv|v|2|3|4|5)', '', base, flags=re.IGNORECASE).strip()

    variations = set([base.strip()])

    # Season variations
    season_vars = ['']
    if season_num:
        season_vars += [f' s{season_num}', f' season {season_num}']
        if season_num == 1:
            season_vars += [' 1st season']
        elif season_num == 2:
            season_vars += [' 2nd season']
        elif season_num == 3:
            season_vars += [' 3rd season']
        else:
            season_vars += [f' {season_num}th season']

    # Part variations
    part_vars = ['']
    if part_num:
        part_vars += [f' part {part_num}']
        if part_num == 2:
            part_vars += [' part ii']
        elif part_num == 3:
            part_vars += [' part iii']
        elif part_num == 4:
            part_vars += [' part iv']
        elif part_num == 5:
            part_vars += [' part v']

    # Combine
    for s in season_vars:
        for p in part_vars:
            var = (base + s + p).strip()
            if var:
                variations.add(var)

    return variations

def match_anitrendz_with_anilist(anitrendz_data, anime_data):
    """Match AniTrendz rankings with AniList anime data"""
    if not anitrendz_data or 'rankings' not in anitrendz_data:
        return {}
    
    matched_rankings = {}
    
    # Dynamically generate title variations from anime_data.json
    title_variations = {}
    for anime in anime_data:
        name = (anime.get('name') or '').lower()
        english = (anime.get('english_title') or '').lower()
        if name and english and name != english:
            title_variations[english] = name  # Map English to romaji/AniList primary
    
    for ranking in anitrendz_data['rankings']:
        anitrendz_title = ranking.get('title')
        if not anitrendz_title:  # Skip if no title
            continue
        
        anitrendz_variations = get_title_variations(anitrendz_title)
        
        # Check if there's a direct mapping
        anitrendz_lower = anitrendz_title.lower()
        if anitrendz_lower in title_variations:
            target_title = title_variations[anitrendz_lower].lower()
            anitrendz_variations.update(get_title_variations(target_title))
        else:
            target_title = anitrendz_lower
        
        # Try to find matching anime in our data
        matched = False
        for anime in anime_data:
            anime_title = (anime.get('name') or '').lower()
            anime_english = (anime.get('english_title') or '').lower()
            
            anime_variations = get_title_variations(anime_title)
            anime_variations.update(get_title_variations(anime_english))
            
            # Check for exact or close match
            for var in anitrendz_variations:
                if (var in anime_variations or
                    var == anime_title or
                    var == anime_english or
                    anitrendz_lower == anime_title or
                    anitrendz_lower == anime_english or
                    # More flexible matching
                    var in anime_title or
                    var in anime_english or
                    anime_title in var or
                    anime_english in var):
                    
                    matched_rankings[anime['id']] = {
                        'anitrendz_rank': ranking['rank'],
                        'anitrendz_change': ranking['change'],
                        'anitrendz_movement': ranking['movement_number'],
                        'anitrendz_weeks': ranking['weeks_on_chart'],
                        'anitrendz_peak': ranking['peak_rank']
                    }
                    matched = True
                    break
            if matched:
                break
        
        if not matched:
            pass  # Skip problematic Unicode titles for now
    
    return matched_rankings

def save_anitrendz_data():
    """Fetch and save AniTrendz rankings"""
    print("Fetching AniTrendz weekly rankings...")
    
    rankings = fetch_anitrendz_rankings()
    if rankings:
        # Save raw AniTrendz data
        with open('data/anitrendz_rankings.json', 'w', encoding='utf-8') as f:
            json.dump(rankings, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {rankings['total_entries']} AniTrendz rankings")
        
        # Load anime data to match rankings
        try:
            with open('data/anime_data.json', 'r', encoding='utf-8') as f:
                anime_data = json.load(f)
            
            # Match rankings with anime
            matched = match_anitrendz_with_anilist(rankings, anime_data)
            
            # Update anime data with AniTrendz rankings
            for anime in anime_data:
                if anime.get('id') in matched:  # Safe check
                    anime.update(matched[anime['id']])
            
            # Save updated anime data
            with open('data/anime_data.json', 'w', encoding='utf-8') as f:
                json.dump(anime_data, f, ensure_ascii=False, indent=2)
            
            print(f"Matched {len(matched)} anime with AniTrendz rankings")
            
        except Exception as e:
            print(f"Error matching AniTrendz data: {e}")
    else:
        print("Failed to fetch AniTrendz rankings")

if __name__ == "__main__":
    save_anitrendz_data()