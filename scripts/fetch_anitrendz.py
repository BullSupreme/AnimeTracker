#!/usr/bin/env python3
import json
import re
from datetime import datetime
from requests_html import HTMLSession
from bs4 import BeautifulSoup

def fetch_anitrendz_rankings():
    """Fetch current weekly anime rankings from AniTrendz"""
    url = "https://www.anitrendz.com/charts/top-anime"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        session = HTMLSession()
        response = session.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Render JavaScript to load dynamic content
        response.html.render(timeout=30, sleep=2)
        
        soup = BeautifulSoup(response.html.html, 'html.parser')
        
        # Find the ranking entries using multiple possible structures
        rankings = []
        
        # Find ALL entries (both top entries and standard list entries)
        all_entries = soup.find_all('div', class_='ChartChoice_at-mcc-entry__Cciiz')
        print(f"Found {len(all_entries)} total ranking entries")
        
        # Pattern 2: Look for any div with rank information
        potential_items = soup.find_all('div', class_=lambda x: x and 'rank' in x.lower())
        all_entries.extend([item for item in potential_items if item not in all_entries])
        
        # Pattern 3: Look for elements containing numbers 1-50 (expanded range)
        for i in range(1, 51):
            number_items = soup.find_all(text=str(i))
            for item in number_items:
                parent = item.parent
                if parent and parent.name == 'div' and parent not in all_entries:
                    all_entries.append(parent)
        
        print(f"Found {len(all_entries)} potential ranking items after deduping")
        
        for item in all_entries:
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
                        match = re.search(r'([+-]?\d+)|(\d+W)', number_text)
                        if match:
                            val = match.group(1) or match.group(2)
                            if 'W' in val:
                                movement_number = int(val.replace('W', ''))
                            else:
                                movement_number = int(val)
                
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
        
        # Sort by rank to ensure order (in case parsing order varies)
        rankings.sort(key=lambda x: x['rank'])
        
        return {
            'rankings': rankings,
            'last_updated': datetime.now().isoformat(),
            'week': datetime.now().strftime('%Y-W%U'),
            'total_entries': len(rankings)
        }
        
    except Exception as e:
        print(f"Error fetching AniTrendz rankings: {e}")
        return None

def match_anitrendz_with_anilist(anitrendz_data, anime_data):
    """Match AniTrendz rankings with AniList anime data"""
    if not anitrendz_data or 'rankings' not in anitrendz_data:
        return {}
    
    matched_rankings = {}
    
    # Dynamically generate title variations from anime_data.json
    title_variations = {}
    for anime in anime_data:
        name = anime.get('name', '').lower()
        english = anime.get('english_title', '').lower()
        if name and english and name != english:
            title_variations[english] = name  # Map English to romaji/AniList primary
        # Add more variations if needed, e.g., removing "S2" for seasons
        no_season = re.sub(r'\s(s\d+|season \d+)', '', english)
        if no_season != english:
            title_variations[no_season] = name
    
    # Still include some manual overrides if dynamic misses edge cases
    title_variations.update({
        # Add persistent ones here if tests show mismatches, e.g.:
        #'the rising of the shield hero s4': 'tate no yuusha no nariagari season 4',
    })
    
    for ranking in anitrendz_data['rankings']:
        anitrendz_title = ranking['title'].lower()
        
        # Check if there's a mapping
        if anitrendz_title in title_variations:
            target_title = title_variations[anitrendz_title]
        else:
            target_title = anitrendz_title
        
        # Try to find matching anime in our data
        matched = False
        for anime in anime_data:
            anime_title = anime['name'].lower()
            anime_english = (anime.get('english_title') or '').lower()
            
            # Check for exact or close match
            if (target_title == anime_title or 
                target_title == anime_english or
                anitrendz_title == anime_title or
                anitrendz_title == anime_english or
                target_title in anime_title or
                target_title in anime_english or
                anime_title in target_title or
                anime_english in target_title):
                
                matched_rankings[anime['id']] = {
                    'anitrendz_rank': ranking['rank'],
                    'anitrendz_change': ranking['change'],
                    'anitrendz_movement': ranking['movement_number'],
                    'anitrendz_weeks': ranking['weeks_on_chart'],
                    'anitrendz_peak': ranking['peak_rank']
                }
                matched = True
                break
        
        if not matched:
            print(f"No match found for Anitrendz title: {ranking['title']}")
    
    return matched_rankings

def save_anitrendz_data():
    """Fetch and save AniTrendz rankings"""
    print("Fetching AniTrendz weekly rankings...")
    
    rankings = fetch_anitrendz_rankings()
    if rankings:
        # Save raw AniTrendz data
        with open('data/anitrendz_rankings.json', 'w', encoding='utf-8') as f:
            json.dump(rankings, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(rankings['rankings'])} AniTrendz rankings")
        
        # Load anime data to match rankings
        try:
            with open('data/anime_data.json', 'r', encoding='utf-8') as f:
                anime_data = json.load(f)
            
            # Match rankings with anime
            matched = match_anitrendz_with_anilist(rankings, anime_data)
            
            # Update anime data with AniTrendz rankings
            for anime in anime_data:
                if anime['id'] in matched:
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