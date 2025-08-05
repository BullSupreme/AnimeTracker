#!/usr/bin/env python3
import json
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import difflib

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

    # Cour
    cour_match = re.search(r'cour\s*(\d+)', base, re.IGNORECASE)
    if cour_match:
        c = int(cour_match.group(1))
        base = re.sub(r'cour\s*\d+', '', base, flags=re.IGNORECASE).strip()
        if c == 2:
            base += ' part 2'

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

hardcoded_mappings = {
    "takopi's original sin": "takopii no genzai",
    "my dress-up darling s2": "sono bisque doll wa koi wo suru season 2",
    "the fragrant flower blooms with dignity": "kaoru hana wa rin to saku",
    "dan da dan s2": "dandadan 2nd season",
    "the summer hikaru died": "hikaru ga shinda natsu",
    "secrets of the silent witch": "silent witch: chinmoku no majo no kakushigoto",
    "toilet-bound hanako-kun s2 part ii": "jibaku shounen hanako-kun 2 part 2",
    "rascal does not dream of santa claus": "seishun buta yarou wa santa claus no yume wo minai",
    "gachiakuta": "gachiakuta",
    "there's no freaking way i'll be your lover! unless...": "watashi ga koibito ni nareru wake naijan, murimuri! (※muri ja nakatta!?)",
    "kaiju no. 8 s2": "kaijuu 8-gou 2nd season",
    "call of the night s2": "yofukashi no uta season 2",
    "witch watch": "witch watch",
    "rent-a-girlfriend s4": "kanojo, okarishimasu 4th season",
    "dr. stone science future part ii": "dr. stone: science future part 2",
    "sakamoto days part ii": "sakamoto days part 2",
    "grand blue dreaming s2": "grand blue season 2",
    "clevatess": "clevatess: majuu no ou to akago to kabane no yuusha",
    "ruri rocks": "ruri no houseki",
    "dealing with mikadono sisters is a breeze": "mikadono sanshimai wa angai, choroi.",
    "the rising of the shield hero s4": "tate no yuusha no nariagari season 4",
    "the water magician": "mizu zokusei no mahou tsukai",
    "a couple of cuckoos s2": "kakkou no iinazuke season 2",
    "anne shirley": "anne shirley",
    "see you tomorrow at the food court": "food court de, mata ashita.",
    "new panty & stocking with garterbelt": "new panty & stocking with garterbelt",
    "bad girl": "bad girl",
    "tougen anki": "tougen anki",
    "betrothed to my sister's ex": "zutaboro reijou wa ane no moto konyakusha ni dekiai sareru",
    "with you and the rain": "ame to kimi to",
    "summer pockets": "summer pockets",
    "i was reincarnated as the 7th prince so i can take my time perfecting my magical ability s2": "tensei shitara dai nana ouji dattanode, kimamani majutsu wo kiwamemasu 2nd season",
    "watari-kun's ****** is about to collapse": "watari-kun no xx ga houkai sunzen",
    "cultural exchange with a game centre girl": "gacen shoujo to ibunka kouryuu",
    "detectives these days are crazy!": "mattaku saikin no tantei to kitara",
    "april showers bring may flowers": "haru no yurei",
    "welcome to the outcast's restaurant!": "tsuihousha shokudou e youkoso!",
    "private tutor to the duke's daughter": "koujo denka no katei kyoushi",
    "nukitashi the animation": "nukitashi the animation",
    "apocalypse bringer mynoghra: world conquest starts with the civilization of ruin": "isekai mokushiroku mynoghra: hametsu no bunmei de hajimeru sekai seifuku",
    "let's go karaoke!": "karaoke iko!",
    "solo camping for two": "futari solo camp",
    "turkey! -time to strike-": "turkey!",
    "scooped up by an s-rank adventurer!": "yuusha party wo tsuihou sareta shiro madoushi, s rank boukensha ni hirowareru: kono shiro madoushi ga kikakugaisugiru",
    "sword of the demon hunter: kijin gentousho": "kijin gentoushou",
    "reborn as a vending machine, i now wander the dungeon s2": "jidou hanbaiki ni umarekawatta ore wa meikyuu wo samayou 2nd season",
    "arknights: rise from ember": "arknights: enshin shomei",
    "the shy hero and the assassin princesses": "kizetsu yuusha to ansatsu hime",
    "onmyo kaiten re:birth verse": "onmyo kaiten re:verse",
    "new saga": "tsuyokute new saga",
    "hotel inhumans": "hotel inhumans",
    "uglymug, epicfighter": "busamen gachi fighter",
    "hell teacher: jigoku sensei nube": "jigoku sensei nube (2025)",
    "9-nine- ruler's crown": "9-nine- shihaisha no oukan",
    "dekin no mogura: the earthbound mole": "dekin no mogura",
    "necronomico and the cosmic horror show": "necronomico no cosmic horror show",
    "fermat kitchen": "fermat no ryouri",
    "puniru is a kawaii slime s2": "puniru wa kawaii slime season 2",
    "yaiba: samurai legend": "shin samurai-den yaiba",
    "milky☆subway: the galactic limited express": "ginga tokkyuu milky☆subway",
    "mr. osomatsu s4": "osomatsu-san 4th season",
    "kamitsubaki city under construction": "kamitsubaki-shi kensetsuchuu.",
    "harmony of mille-feuille": "utagoe wa mille-feuille",
    "binan koukou chikyuu bouei-bu haikara!": "binan koukou chikyuu bouei-bu haikara!",
    "cardfight!! vanguard divinez deluxe finals": "cardfight!! vanguard divinez deluxe kesshou-hen",
    "princession orchestra": "princession orchestra",
    "me and the alien muumu": "uchuujin muumu",
    "secret aipri ring arc": "himitsu no aipri: ring-hen"
}

def match_anitrendz_with_anilist(anitrendz_data, anime_data):
    """Match AniTrendz rankings with AniList anime data"""
    if not anitrendz_data or 'rankings' not in anitrendz_data:
        return {}
    
    matched_rankings = {}
    
    # Create a list of all possible anime titles from anime_data for fuzzy matching
    anime_titles = []
    for anime in anime_data:
        anime_title = (anime.get('name') or '').lower()
        anime_english = (anime.get('english_title') or '').lower()
        anime_id = anime.get('id')
        anime_titles.append((anime_title, anime_id))
        if anime_english and anime_english != anime_title:
            anime_titles.append((anime_english, anime_id))
    
    for ranking in anitrendz_data['rankings']:
        anitrendz_title = ranking.get('title')
        if not anitrendz_title:  # Skip if no title
            continue
        
        anitrendz_lower = anitrendz_title.lower()
        if anitrendz_lower in hardcoded_mappings:
            mapped_title = hardcoded_mappings[anitrendz_lower]
            anitrendz_title = mapped_title
            anitrendz_lower = mapped_title.lower()
        
        anitrendz_variations = get_title_variations(anitrendz_title)
        
        matched = False
        for anime in anime_data:
            anime_title_lower = (anime.get('name') or '').lower()
            anime_english_lower = (anime.get('english_title') or '').lower()
            
            anime_variations = get_title_variations(anime.get('name') or '')
            anime_variations.update(get_title_variations(anime.get('english_title') or ''))
            
            for var in anitrendz_variations:
                if (var in anime_variations or
                    var == anime_title_lower or
                    var == anime_english_lower or
                    anitrendz_lower == anime_title_lower or
                    anitrendz_lower == anime_english_lower or
                    var in anime_title_lower or
                    var in anime_english_lower or
                    anime_title_lower in var or
                    anime_english_lower in var):
                    
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
            # Fallback to fuzzy matching
            closest = difflib.get_close_matches(anitrendz_lower, [t[0] for t in anime_titles], n=1, cutoff=0.8)
            if closest:
                closest_title = closest[0]
                for t, id in anime_titles:
                    if t == closest_title:
                        matched_rankings[id] = {
                            'anitrendz_rank': ranking['rank'],
                            'anitrendz_change': ranking['change'],
                            'anitrendz_movement': ranking['movement_number'],
                            'anitrendz_weeks': ranking['weeks_on_chart'],
                            'anitrendz_peak': ranking['peak_rank']
                        }
                        print(f"Fuzzy matched '{anitrendz_title}' to '{closest_title}'")
                        break
    
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