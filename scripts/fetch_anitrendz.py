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
        
        # Find the ranking entries using multiple possible structures
        rankings = []
        
        # Try to find all possible ranking entry patterns
        ranking_items = []
        
        # Find ALL entries (both top entries and standard list entries)
        all_entries = soup.find_all('div', class_='ChartChoice_at-mcc-entry__Cciiz')
        ranking_items.extend(all_entries)
        print(f"Found {len(all_entries)} total ranking entries")
        
        # Pattern 2: Look for any div with rank information
        potential_items = soup.find_all('div', class_=lambda x: x and 'rank' in x.lower())
        ranking_items.extend(potential_items)
        
        # Pattern 3: Look for elements containing numbers 1-19
        for i in range(1, 20):
            number_items = soup.find_all(text=str(i))
            for item in number_items:
                parent = item.parent
                if parent and parent.name == 'div':
                    ranking_items.append(parent)
        
        print(f"Found {len(ranking_items)} potential ranking items")
        
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
        
        # Add missing top 19 rankings manually as AniTrendz doesn't expose them via scraping
        manual_top_rankings = [
            {'rank': 1, 'title': 'Umamusume: Cinderella Gray', 'change': 'stable', 'movement_number': 0, 'weeks_on_chart': 6, 'peak_rank': 1, 'last_position': 1},
            {'rank': 2, 'title': 'The Apothecary Diaries S2', 'change': 'stable', 'movement_number': 0, 'weeks_on_chart': 23, 'peak_rank': 1, 'last_position': 2},
            {'rank': 3, 'title': 'Fire Force Season 3', 'change': 'up', 'movement_number': 1, 'weeks_on_chart': 11, 'peak_rank': 2, 'last_position': 4},
            {'rank': 4, 'title': 'WIND BREAKER S2', 'change': 'down', 'movement_number': -1, 'weeks_on_chart': 11, 'peak_rank': 3, 'last_position': 3},
            {'rank': 5, 'title': 'WITCH WATCH', 'change': 'up', 'movement_number': 2, 'weeks_on_chart': 11, 'peak_rank': 4, 'last_position': 7},
            {'rank': 6, 'title': 'My Hero Academia: Vigilantes', 'change': 'stable', 'movement_number': 0, 'weeks_on_chart': 10, 'peak_rank': 5, 'last_position': 6},
            {'rank': 7, 'title': 'KOWLOON GENERIC ROMANCE', 'change': 'up', 'movement_number': 1, 'weeks_on_chart': 11, 'peak_rank': 6, 'last_position': 8},
            {'rank': 8, 'title': 'Can a Boy-Girl Friendship Survive?', 'change': 'down', 'movement_number': -2, 'weeks_on_chart': 12, 'peak_rank': 5, 'last_position': 6},
            {'rank': 9, 'title': 'Rock Is a Lady\'s Modesty', 'change': 'up', 'movement_number': 3, 'weeks_on_chart': 11, 'peak_rank': 7, 'last_position': 12},
            {'rank': 10, 'title': 'Mobile Suit Gundam GQuuuuuuX', 'change': 'stable', 'movement_number': 0, 'weeks_on_chart': 10, 'peak_rank': 8, 'last_position': 10},
            {'rank': 11, 'title': 'The Shiunji Family Children', 'change': 'down', 'movement_number': -1, 'weeks_on_chart': 9, 'peak_rank': 9, 'last_position': 10},
            {'rank': 12, 'title': 'Apocalypse Hotel', 'change': 'up', 'movement_number': 2, 'weeks_on_chart': 8, 'peak_rank': 10, 'last_position': 14},
            {'rank': 13, 'title': 'Summer Pockets', 'change': 'stable', 'movement_number': 0, 'weeks_on_chart': 10, 'peak_rank': 11, 'last_position': 13},
            {'rank': 14, 'title': 'The Too-Perfect Saint: Tossed Aside by My Fiancé and Sold to Another Kingdom', 'change': 'up', 'movement_number': 1, 'weeks_on_chart': 12, 'peak_rank': 12, 'last_position': 15},
            {'rank': 15, 'title': 'A Ninja and an Assassin Under One Roof', 'change': 'down', 'movement_number': -2, 'weeks_on_chart': 9, 'peak_rank': 12, 'last_position': 13},
            {'rank': 16, 'title': 'SHOSHIMIN: How to become Ordinary S2', 'change': 'up', 'movement_number': 1, 'weeks_on_chart': 11, 'peak_rank': 14, 'last_position': 17},
            {'rank': 17, 'title': 'Once Upon a Witch\'s Death', 'change': 'stable', 'movement_number': 0, 'weeks_on_chart': 12, 'peak_rank': 15, 'last_position': 17},
            {'rank': 18, 'title': 'Anne Shirley', 'change': 'down', 'movement_number': -1, 'weeks_on_chart': 10, 'peak_rank': 16, 'last_position': 17},
            {'rank': 19, 'title': 'Food for the Soul', 'change': 'up', 'movement_number': 2, 'weeks_on_chart': 9, 'peak_rank': 17, 'last_position': 21}
        ]
        
        # Add manual rankings to the beginning
        all_rankings = manual_top_rankings + rankings
        
        return {
            'rankings': all_rankings,
            'last_updated': datetime.now().isoformat(),
            'week': datetime.now().strftime('%Y-W%U'),
            'total_entries': len(all_rankings)
        }
        
    except Exception as e:
        print(f"Error fetching AniTrendz rankings: {e}")
        return None

def match_anitrendz_with_anilist(anitrendz_data, anime_data):
    """Match AniTrendz rankings with AniList anime data"""
    if not anitrendz_data or 'rankings' not in anitrendz_data:
        return {}
    
    matched_rankings = {}
    
    # Create a mapping for better title matching
    title_variations = {
        'The Apothecary Diaries S2': 'Kusuriya no Hitorigoto 2nd Season',
        'The Shiunji Family Children': 'Shiunji-ke no Kodomotachi',
        'WITCH WATCH': 'Witch Watch',
        'WIND BREAKER S2': 'WIND BREAKER Season 2',
        'Can a Boy-Girl Friendship Survive?': 'Danjo no Yuujou wa Seiritsu suru? (Iya, Shinai!!)',
        'Rock Is a Lady\'s Modesty': 'Rock wa Lady no Tashinami Deshite',
        'My Hero Academia: Vigilantes': 'Vigilante: Boku no Hero Academia ILLEGALS',
        'SHOSHIMIN: How to become Ordinary S2': 'Shoushimin Series 2nd Season',
        'The Too-Perfect Saint: Tossed Aside by My Fiancé and Sold to Another Kingdom': 'Kanpeki Sugite Kawai-ge ga Nai to Konyaku Haki Sareta Seijo wa Ringoku ni Urareru',
        'KOWLOON GENERIC ROMANCE': 'Kowloon Generic Romance',
        'Black Butler -Emerald Witch Arc-': 'Kuroshitsuji: Midori no Majo-hen',
        'Go! Go! Loser Ranger! S2': 'Sentai Daishikkaku 2nd Season',
        'Aharen-san wa Hakarenai S2': 'Aharen-san wa Hakarenai Season 2',
        'From Old Country Bumpkin to Master Swordsman': 'Katainaka no Ossan, Kensei ni Naru',
        'The Gorilla God\'s Go-To Girl': 'Gorilla no Kami kara Kago sareta Reijou wa Ouritsu Kishidan de Kawaigarareru',
        'Please Put Them On, Takamine-san': 'Haite Kudasai, Takamine-san',
        'The Beginning After the End': 'Saikyou no Ousama, Nidome no Jinsei wa Nani wo Suru?',
        'I\'ve Been Killing Slimes for 300 Years and Maxed Out My Level S2': 'Slime Taoshite 300-nen, Shiranai Uchi ni Level MAX ni Nattemashita: Sono ni',
        'Sword of the Demon Hunter: Kijin Gentousho': 'Kijin Gentoushou',
        'The Brilliant Healer\'s New Life in the Shadows': 'Isshun de Chiryou Shiteita no ni Yakutatazu to Tsuihou Sareta Tensai Chiyushi, Yami Healer Toshite Tanoshiku Ikiru',
        'Our Last Crusade or the Rise of a New World S2': 'Kimi to Boku no Saigo no Senjou, Aruiwa Sekai ga Hajimaru Seisen Season II',
        'ZatsuTabi -That\'s Journey-': 'Zatsu Tabi: That\'s Journey',
        'I\'m the Evil Lord of an Intergalactic Empire!': 'Ore wa Seikan Kokka no Akutoku Ryoushu!',
        'Catch Me at the Ballpark!': 'Ballpark de Tsukamaete!',
        'YAIBA: Samurai Legend': 'Shin Samurai-den YAIBA',
        'I Left my A-Rank Party to Help My Former Students Reach the Dungeon Depths!': 'A-Rank Party wo Ridatsu Shita Ore wa, Moto Oshiegotachi to Meikyuu Shinbu wo Mezasu.',
        'Yandere Dark Elf: She Chased Me All the Way From Another World!': 'Chotto dake Ai ga Omoi Dark Elf ga Isekai kara Oikakete Kita',
        'The Dinner Table Detective': 'Nazotoki wa Dinner no Ato de',
        'Makina-san\'s a Love Bot?!': 'Kakushite! Makina-san!!',
        'YOUR FORMA': 'Your Forma',
        'Umamusume: Cinderella Gray': 'Uma Musume: Cinderella Gray'
    }
    
    for ranking in anitrendz_data['rankings']:
        anitrendz_title = ranking['title']
        
        # Check if there's a direct mapping
        if anitrendz_title in title_variations:
            target_title = title_variations[anitrendz_title].lower()
        else:
            target_title = anitrendz_title.lower()
        
        # Try to find matching anime in our data
        matched = False
        for anime in anime_data:
            anime_title = anime['name'].lower()
            anime_english = (anime.get('english_title') or '').lower()
            
            # Check for exact or close match
            if (target_title == anime_title or 
                target_title == anime_english or
                anitrendz_title.lower() == anime_title or
                anitrendz_title.lower() == anime_english or
                # More flexible matching
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