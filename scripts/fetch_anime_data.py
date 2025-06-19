#!/usr/bin/env python3
import json
import requests
from datetime import datetime, timedelta
import os

# Configuration
ANILIST_API_URL = "https://graphql.anilist.co"

def get_current_season():
    """Get current season based on current date"""
    current_month = datetime.now().month
    if current_month in [1, 2, 3]:
        return "WINTER"
    elif current_month in [4, 5, 6]:
        return "SPRING"
    elif current_month in [7, 8, 9]:
        return "SUMMER"
    else:  # 10, 11, 12
        return "FALL"

def get_next_season():
    """Get next season and year"""
    current_season = get_current_season()
    current_year = datetime.now().year
    
    season_map = {
        "WINTER": ("SPRING", current_year),
        "SPRING": ("SUMMER", current_year),
        "SUMMER": ("FALL", current_year),
        "FALL": ("WINTER", current_year + 1)
    }
    
    return season_map[current_season]

def is_within_season_threshold():
    """Check if we're within 3 weeks of next season"""
    current_month = datetime.now().month
    current_day = datetime.now().day
    
    # Season start dates (approximate)
    season_starts = {
        1: (1, 1),   # Winter starts Jan 1
        4: (4, 1),   # Spring starts Apr 1  
        7: (7, 1),   # Summer starts Jul 1
        10: (10, 1)  # Fall starts Oct 1
    }
    
    # Find next season start
    next_season_month = None
    for month in [1, 4, 7, 10]:
        if month > current_month:
            next_season_month = month
            break
    
    if next_season_month is None:
        next_season_month = 1  # Next year's winter
        next_year = datetime.now().year + 1
        next_season_start = datetime(next_year, 1, 1)
    else:
        next_season_start = datetime(datetime.now().year, next_season_month, 1)
    
    # Check if within 3 weeks (21 days)
    days_until_next_season = (next_season_start - datetime.now()).days
    return days_until_next_season <= 21

def fetch_current_anime():
    """Fetch currently airing anime from AniList API"""
    # First query for RELEASING anime
    query_releasing = '''
    query ($page: Int, $perPage: Int) {
        Page(page: $page, perPage: $perPage) {
            pageInfo {
                hasNextPage
                currentPage
            }
            media(status: RELEASING, type: ANIME, format_in: [TV, ONA, TV_SHORT], sort: [POPULARITY_DESC]) {
                id
                idMal
                title {
                    romaji
                    english
                }
                averageScore
                episodes
                nextAiringEpisode {
                    episode
                    airingAt
                }
                coverImage {
                    extraLarge
                    large
                    medium
                }
                siteUrl
                startDate {
                    year
                    month
                    day
                }
                endDate {
                    year
                    month
                    day
                }
                externalLinks {
                    site
                    url
                    icon
                }
                genres
                isAdult
                duration
                format
                popularity
                status
            }
        }
    }
    '''
    
    # Second query for recently FINISHED anime (within last 7 days)
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    query_finished = '''
    query ($page: Int, $perPage: Int, $startDate: FuzzyDateInt, $endDate: FuzzyDateInt) {
        Page(page: $page, perPage: $perPage) {
            pageInfo {
                hasNextPage
                currentPage
            }
            media(status: FINISHED, type: ANIME, format_in: [TV, ONA, TV_SHORT], sort: [POPULARITY_DESC], endDate_greater: $startDate, endDate_lesser: $endDate) {
                id
                idMal
                title {
                    romaji
                    english
                }
                averageScore
                episodes
                nextAiringEpisode {
                    episode
                    airingAt
                }
                coverImage {
                    extraLarge
                    large
                    medium
                }
                siteUrl
                startDate {
                    year
                    month
                    day
                }
                endDate {
                    year
                    month
                    day
                }
                externalLinks {
                    site
                    url
                    icon
                }
                genres
                isAdult
                duration
                format
                popularity
                status
            }
        }
    }
    '''
    
    all_anime = []
    
    try:
        # First, fetch all RELEASING anime
        print("Fetching currently airing anime...")
        page = 1
        per_page = 50
        
        while True:
            variables = {
                'page': page,
                'perPage': per_page
            }
            
            response = requests.post(
                ANILIST_API_URL,
                json={'query': query_releasing, 'variables': variables},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if not data or 'data' not in data:
                break
                
            page_data = data['data']['Page']
            all_anime.extend(page_data['media'])
            
            # Check if there are more pages
            if not page_data['pageInfo']['hasNextPage']:
                break
                
            page += 1
            print(f"Fetched page {page-1}, total anime so far: {len(all_anime)}")
        
        # Then, fetch recently FINISHED anime
        print("Fetching recently finished anime...")
        page = 1
        
        # Convert dates to FuzzyDateInt format (YYYYMMDD)
        # Include next 3 days to catch anime ending soon
        three_days_ahead = today + timedelta(days=3)
        start_fuzzy = int(f"{week_ago.year}{week_ago.month:02d}{week_ago.day:02d}")
        end_fuzzy = int(f"{three_days_ahead.year}{three_days_ahead.month:02d}{three_days_ahead.day:02d}")
        
        while True:
            variables = {
                'page': page,
                'perPage': per_page,
                'startDate': start_fuzzy,
                'endDate': end_fuzzy
            }
            
            response = requests.post(
                ANILIST_API_URL,
                json={'query': query_finished, 'variables': variables},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if not data or 'data' not in data:
                break
                
            page_data = data['data']['Page']
            finished_anime = page_data['media']
            
            # Add finished anime to our list
            all_anime.extend(finished_anime)
            
            # Check if there are more pages
            if not page_data['pageInfo']['hasNextPage']:
                break
                
            page += 1
            print(f"Fetched page {page-1} of finished anime, added {len(finished_anime)} anime")
        
        print(f"Total anime fetched: {len(all_anime)}")
        
        # Return in the same format as before
        return {'data': {'Page': {'media': all_anime}}}
        
    except requests.RequestException as e:
        print(f"Error fetching anime data: {e}")
        return None

def fetch_upcoming_seasonal_anime():
    """Fetch upcoming seasonal anime from AniList API"""
    next_season, next_year = get_next_season()
    
    query = '''
    query ($page: Int, $perPage: Int, $season: MediaSeason, $year: Int) {
        Page(page: $page, perPage: $perPage) {
            pageInfo {
                hasNextPage
                currentPage
            }
            media(status: NOT_YET_RELEASED, type: ANIME, format_in: [TV, ONA, TV_SHORT], season: $season, seasonYear: $year, sort: [POPULARITY_DESC]) {
                id
                idMal
                title {
                    romaji
                    english
                }
                averageScore
                episodes
                coverImage {
                    extraLarge
                    large
                    medium
                }
                siteUrl
                startDate {
                    year
                    month
                    day
                }
                season
                seasonYear
                genres
                isAdult
                duration
                format
                popularity
                favourites
                studios {
                    nodes {
                        name
                    }
                }
            }
        }
    }
    '''
    
    all_anime = []
    page = 1
    per_page = 50
    
    try:
        while True:
            variables = {
                'page': page,
                'perPage': per_page,
                'season': next_season,
                'year': next_year
            }
            
            response = requests.post(
                ANILIST_API_URL,
                json={'query': query, 'variables': variables},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if not data or 'data' not in data:
                break
                
            page_data = data['data']['Page']
            all_anime.extend(page_data['media'])
            
            # Check if there are more pages
            if not page_data['pageInfo']['hasNextPage']:
                break
                
            page += 1
            print(f"Fetched upcoming page {page-1}, total anime so far: {len(all_anime)}")
        
        # Return in the same format as before
        return {'data': {'Page': {'media': all_anime}}}
        
    except requests.RequestException as e:
        print(f"Error fetching upcoming anime data: {e}")
        return None

def process_anime_data(api_data):
    """Process API data into our format"""
    if not api_data or 'data' not in api_data:
        return []
    
    processed_anime = []
    
    # Filter cutoff - only include anime from recent seasons
    cutoff_date = datetime.now() - timedelta(days=365)  # 1 year cutoff
    
    # Kids anime blacklist - titles that are typically for children
    kids_anime_keywords = [
        'Maebashi Witches',
        'Shirobuta Kizoku',
        'Mashin Souzouden Wataru',
        'Crayon Shin-chan',
        'Doraemon',
        'Pokemon',
        'Pocket Monsters',
        'Beyblade',
        'Yu-Gi-Oh',
        'Digimon',
        'PreCure',
        'Pretty Cure',
        'Aikatsu',
        'PriPara',
        'Yokai Watch',
        'Hamtaro',
        'Anpanman'
    ]
    
    # Exception list for long-running anime we want to keep
    long_running_exceptions = [
        'ONE PIECE',
        'Naruto',
        'Detective Conan',
        'Boruto'
    ]
    
    for anime in api_data['data']['Page']['media']:
        # Skip anime that started too long ago (unless it's in our exception list)
        start_year = anime.get('startDate', {}).get('year')
        anime_title = anime['title']['romaji']
        anime_title_english = anime['title'].get('english') or ''
        
        
        # Extract end date for various logic checks
        end_date = None
        if anime.get('endDate') and anime['endDate'].get('year'):
            month = anime['endDate'].get('month') or 1
            day = anime['endDate'].get('day') or 1
            end_date = f"{anime['endDate']['year']}-{month:02d}-{day:02d}"
        
        # Check if this is an exception anime
        is_exception = False
        for exception in long_running_exceptions:
            if (exception.lower() in anime_title.lower() or 
                exception.lower() in anime_title_english.lower()):
                is_exception = True
                break
        
        if start_year and start_year < cutoff_date.year and not is_exception:
            continue  # Skip this anime entirely
            
        # Skip kids anime
        
        # Check if title contains any kids anime keywords
        is_kids_anime = False
        for keyword in kids_anime_keywords:
            if (keyword.lower() in anime_title.lower() or 
                (anime_title_english and keyword.lower() in anime_title_english.lower())):
                is_kids_anime = True
                break
        
        if is_kids_anime:
            continue  # Skip kids anime
            
        # Skip low popularity anime (less than 5000 popularity)
        popularity = anime.get('popularity', 0)
        if popularity < 5000:
            continue  # Skip unpopular anime
            
        # Skip short anime (less than 10 minutes per episode)
        episode_duration = anime.get('duration')
        anime_format = anime.get('format')
        
        if episode_duration and episode_duration < 10:
            continue  # Skip short format anime
        elif anime_format == 'TV_SHORT' and (not episode_duration or episode_duration < 10):
            continue  # Skip TV Short with unknown/short duration
            
        # Check if anime has a next airing episode or has aired recently
        has_next_episode = anime.get('nextAiringEpisode') is not None
        
        
        # If no next episode, check if it might be a final episode or finished series
        if not has_next_episode:
            # Check if this could be a final episode airing today/recently
            could_be_finale_today = False
            
            if start_year:
                start_month = anime.get('startDate', {}).get('month', 1)
                start_day = anime.get('startDate', {}).get('day', 1)
                try:
                    start_date_obj = datetime(start_year, start_month, start_day)
                    today_date = datetime.now().date()
                    start_date_only = start_date_obj.date()
                    
                    # Calculate days since start
                    days_since_start = (today_date - start_date_only).days
                    weeks_since_start = days_since_start // 7
                    days_remainder = days_since_start % 7
                    
                    # If today is the same weekday as start date and it's been 7+ days
                    if days_remainder == 0 and days_since_start >= 7:
                        could_be_finale_today = True
                    
                    # Also check if it's within the last week (might have aired yesterday/recently)
                    if 0 <= days_since_start <= 7:
                        could_be_finale_today = True
                        
                except (ValueError, TypeError):
                    pass
            
            # For anime without next episodes, check if they're still relevant
            if not could_be_finale_today:
                # Check if anime is ending soon (within 7 days) - if so, keep it
                ending_soon = False
                if end_date:
                    try:
                        today_date = datetime.now().date()
                        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                        days_until_end = (end_date_obj - today_date).days
                        # If ending within a week, consider it relevant
                        if -3 <= days_until_end <= 7:  # Include anime that ended up to 3 days ago
                            ending_soon = True
                    except (ValueError, TypeError):
                        pass
                
                # Check if anime finished recently (within last 7 days)
                recently_finished = False
                recently_finished_2weeks = False
                if end_date:
                    try:
                        today_date = datetime.now().date()
                        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                        days_since_end = (today_date - end_date_obj).days
                        if 0 <= days_since_end <= 7:  # Finished within last week
                            recently_finished = True
                        elif 0 <= days_since_end <= 14:  # Finished within last 2 weeks
                            recently_finished_2weeks = True
                    except (ValueError, TypeError):
                        pass
                
                # If anime is neither ending soon nor recently finished, skip it
                if not ending_soon and not recently_finished and not recently_finished_2weeks:
                    continue

        # Get episode info - use nextAiringEpisode if available, otherwise estimate
        episode_number = 1
        release_date = None
        next_airing_date = None
        # Initialize next airing preservation variables
        original_next_episode = None
        original_next_date = None
        
        if anime.get('nextAiringEpisode'):
            # Has confirmed next episode
            next_episode = anime['nextAiringEpisode']
            airing_timestamp = next_episode['airingAt']
            next_episode_number = next_episode['episode']
            
            # Convert timestamp to date string
            airing_date = datetime.fromtimestamp(airing_timestamp)
            next_airing_date = airing_date.strftime('%Y-%m-%d')
            
            # Store the original next airing info separately (never modified)
            original_next_episode = next_episode_number
            original_next_date = next_airing_date
            
            episode_number = next_episode_number
            release_date = next_airing_date
            
            # Additional check for long-running series even with nextAiringEpisode
            start_year = anime.get('startDate', {}).get('year')
            start_month = anime.get('startDate', {}).get('month', 1)
            
            # Check if anime started more than 3 months ago OR has high episode count
            started_long_ago = False
            if start_year:
                try:
                    start_date_obj = datetime(start_year, start_month, 1)
                    three_months_ago = datetime.now() - timedelta(days=90)  # 3 months for anime with next episode
                    started_long_ago = start_date_obj < three_months_ago
                except (ValueError, TypeError):
                    started_long_ago = False
            
            # Also consider high episode counts as indication of long-running series
            is_long_running = episode_number > 50
            
            # Check if this is an exception anime (same logic as above)
            is_exception_anime = False
            for exception in long_running_exceptions:
                if (exception.lower() in anime_title.lower() or 
                    exception.lower() in anime_title_english.lower()):
                    is_exception_anime = True
                    break
            
            if (started_long_ago or is_long_running) and not is_exception_anime:
                # Override release date for long-running series to exclude from today/tomorrow
                release_date = None
                # But preserve next_airing_date for display purposes
                # next_airing_date stays unchanged
            else:
                # For recent anime with next episode, check if we should show a different episode
                today_date = datetime.now().date()
                days_until_next = (airing_date.date() - today_date).days
                
                if 0 < days_until_next <= 7:
                    # Next episode is less than 7 days away
                    today_weekday = datetime.now().weekday()  # 0=Monday, 6=Sunday
                    next_episode_weekday = airing_date.weekday()
                    
                    if today_weekday == next_episode_weekday:
                        # Next episode airs on the same weekday as today
                        episode_number = episode_number - 1
                        release_date = today_date.strftime('%Y-%m-%d')
                        # Don't modify original_next_date and original_next_episode
                    else:
                        # Different weekday, calculate when the previous episode aired
                        if start_year and start_month:
                            try:
                                start_day = anime.get('startDate', {}).get('day') or 1
                                start_date_obj = datetime(start_year, start_month, start_day)
                                
                                # Calculate which day was the previous episode
                                previous_ep_date = airing_date.date() - timedelta(days=7)
                                
                                # If previous episode was yesterday or earlier this week, show it
                                days_since_prev = (today_date - previous_ep_date).days
                                if 0 < days_since_prev <= 2:  # Yesterday or day before
                                    episode_number = episode_number - 1
                                    release_date = previous_ep_date.strftime('%Y-%m-%d')
                            except (ValueError, TypeError):
                                pass
                elif start_year and start_month:
                    # Next episode is far away, check if today should have an episode
                    try:
                        start_day = anime.get('startDate', {}).get('day') or 1
                        start_date_obj = datetime(start_year, start_month, start_day)
                        start_date_only = start_date_obj.date()
                        
                        # Calculate days since start
                        days_since_start = (today_date - start_date_only).days
                        weeks_since_start = days_since_start // 7
                        days_remainder = days_since_start % 7
                        
                        # If today is the same weekday as start date, calculate expected episode
                        if days_remainder == 0 and days_since_start >= 7:
                            expected_episode = weeks_since_start + 1
                            # Only override if this would be earlier than the next scheduled episode
                            if expected_episode < episode_number:
                                episode_number = expected_episode
                                release_date = today_date.strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        pass
        else:
            # No next episode data - check if this anime just finished
            episode_count = anime.get('episodes', 1) or 1
            today_date = datetime.now().date()
            
            # Check if anime ended recently (tomorrow or day after) - means final episode was today
            recently_finished = False
            if end_date:
                try:
                    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                    days_until_end = (end_date_obj - today_date).days
                    
                    
                    # If end date is tomorrow (1 day) or day after (2 days), final episode was likely today
                    if 1 <= days_until_end <= 2:
                        episode_number = episode_count  # Final episode
                        release_date = today_date.strftime('%Y-%m-%d')  # Today
                        recently_finished = True
                except (ValueError, TypeError):
                    pass
            
            # If not recently finished, use normal logic for older anime
            if not recently_finished:
                start_year = anime.get('startDate', {}).get('year')
                start_month = anime.get('startDate', {}).get('month', 1)
                
                started_long_ago = False
                is_long_running = episode_count > 50
                
                if started_long_ago or is_long_running:
                    episode_number = episode_count
                    release_date = None
                else:
                    episode_number = episode_count
                    
                    # For recent ongoing anime, check if today would be an episode day
                    if start_year and start_month:
                        try:
                            start_day = anime.get('startDate', {}).get('day') or 1
                            start_date_obj = datetime(start_year, start_month, start_day)
                            today_date = datetime.now().date()
                            start_date_only = start_date_obj.date()
                            
                            # Calculate days since start
                            days_since_start = (today_date - start_date_only).days
                            weeks_since_start = days_since_start // 7
                            days_remainder = days_since_start % 7
                            
                            if (days_remainder == 0 and days_since_start >= 7):
                                # Calculate expected episode number for today
                                expected_episode = weeks_since_start + 1
                                if expected_episode <= episode_count:
                                    episode_number = expected_episode
                                    release_date = today_date.strftime('%Y-%m-%d')
                                else:
                                    release_date = None
                            else:
                                release_date = None
                        except (ValueError, TypeError):
                            release_date = None
                    else:
                        release_date = None
        
        # Get start date
        start_date = None
        if anime.get('startDate') and anime['startDate'].get('year'):
            month = anime['startDate'].get('month') or 1
            day = anime['startDate'].get('day') or 1
            start_date = f"{anime['startDate']['year']}-{month:02d}-{day:02d}"
        
        # Get end date (already extracted above for recently finished check)
        
        # Process streaming links - filter out social media and non-streaming sites
        streaming_links = []
        streaming_sites = {
            'Crunchyroll', 'Funimation', 'Netflix', 'Hulu', 'Amazon Prime Video', 
            'Disney Plus', 'HBO Max', 'VRV', 'Hidive', 'HIDIVE', 'AnimeLab', 'Wakanim',
            'Bilibili', 'iQiyi', 'Tencent Video', 'YouTube', 'Niconico',
            'AbemaTV', 'dAnime Store', 'U-NEXT', 'Muse Asia', 'Oceanveil', 'Crave',
            'Apple TV+', 'Apple TV Plus', 'Peacock'
        }
        
        # Domain mapping for consistent favicon extraction
        site_domains = {
            'Crunchyroll': 'crunchyroll.com',
            'Netflix': 'netflix.com',
            'Hulu': 'hulu.com',
            'Amazon Prime Video': 'primevideo.com',
            'Disney Plus': 'disneyplus.com',
            'HBO Max': 'hbomax.com',
            'YouTube': 'youtube.com',
            'Funimation': 'funimation.com',
            'VRV': 'vrv.co',
            'Hidive': 'www.hidive.com',
            'HIDIVE': 'www.hidive.com',
            'Bilibili': 'bilibili.com',
            'AnimeLab': 'animelab.com',
            'Wakanim': 'wakanim.tv',
            'Oceanveil': 'oceanveil.org',
            'Crave': 'crave.ca',
            'Apple TV+': 'tv.apple.com',
            'Apple TV Plus': 'tv.apple.com',
            'Peacock': 'peacocktv.com'
        }
        
        if anime.get('externalLinks'):
            for link in anime['externalLinks']:
                site_name = link.get('site', '')
                if site_name in streaming_sites and link.get('url'):
                    # Use Google's favicon service with proper domain
                    domain = site_domains.get(site_name)
                    
                    if not domain:
                        # Extract domain from URL as fallback
                        try:
                            from urllib.parse import urlparse
                            domain = urlparse(link['url']).netloc
                            # Remove www. prefix if present
                            if domain.startswith('www.'):
                                domain = domain[4:]
                        except:
                            domain = link['url']
                    
                    icon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=32"
                    
                    streaming_links.append({
                        'site': site_name,
                        'url': link['url'],
                        'icon': icon_url
                    })
        
        # Check if anime is ending today or tomorrow and set release_date accordingly
        today_str = datetime.now().strftime('%Y-%m-%d')
        tomorrow_str = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        if end_date and (end_date == today_str or end_date == tomorrow_str):
            # If anime ends today or tomorrow, set release_date to end_date for its final episode
            if not release_date or release_date != end_date:
                release_date = end_date
                # Set episode to total episodes for final episode
                if anime.get('episodes'):
                    episode_number = anime['episodes']
        
        # Always prioritize original next airing data when available
        final_next_airing_date = original_next_date
        final_next_episode = original_next_episode
        
        # Use fallbacks only if original data doesn't exist
        if not final_next_airing_date:
            final_next_airing_date = next_airing_date
        if not final_next_episode:
            final_next_episode = episode_number
        
        # Check if recently finished (within 2 weeks)
        is_recently_finished = False
        if end_date and not has_next_episode:
            try:
                today_date = datetime.now().date()
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
                days_since_end = (today_date - end_date_obj).days
                if 0 <= days_since_end <= 14:  # Finished within last 2 weeks
                    is_recently_finished = True
            except (ValueError, TypeError):
                pass
        
        processed_anime.append({
            'id': anime['id'],
            'mal_id': anime.get('idMal'),
            'name': anime['title']['romaji'],
            'english_title': anime['title'].get('english'),
            'episode': episode_number,
            'release_date': release_date,
            'next_airing_date': final_next_airing_date,
            'next_episode_number': final_next_episode,
            'poster_url': anime['coverImage'].get('extraLarge') or anime['coverImage'].get('large') or anime['coverImage']['medium'],
            'site_url': anime['siteUrl'],
            'start_date': start_date,
            'end_date': end_date,
            'streaming_links': streaming_links,
            'popularity': anime.get('popularity', 0),
            'anilist_score': anime.get('averageScore'),
            'recently_finished': is_recently_finished
        })
    
    # Sort by popularity (highest first) to calculate rankings
    processed_anime.sort(key=lambda x: x['popularity'], reverse=True)
    
    # Add popularity ranking to each anime
    for rank, anime in enumerate(processed_anime, 1):
        anime['popularity_rank'] = rank
    
    return processed_anime

def process_upcoming_anime_data(api_data):
    """Process upcoming seasonal anime API data"""
    if not api_data or 'data' not in api_data:
        return []
    
    processed_anime = []
    
    # Kids anime blacklist - same as main function
    kids_anime_keywords = [
        'Maebashi Witches', 'Shirobuta Kizoku', 'Mashin Souzouden Wataru',
        'Crayon Shin-chan', 'Doraemon', 'Pokemon', 'Pocket Monsters',
        'Beyblade', 'Yu-Gi-Oh', 'Digimon', 'PreCure', 'Pretty Cure',
        'Aikatsu', 'PriPara', 'Yokai Watch', 'Hamtaro', 'Anpanman'
    ]
    
    for anime in api_data['data']['Page']['media']:
        anime_title = anime['title']['romaji']
        anime_title_english = anime['title'].get('english') or ''
        
        # Skip kids anime
        is_kids_anime = False
        for keyword in kids_anime_keywords:
            if (keyword.lower() in anime_title.lower() or 
                (anime_title_english and keyword.lower() in anime_title_english.lower())):
                is_kids_anime = True
                break
        
        if is_kids_anime:
            continue
            
        # Skip low popularity anime (less than 1000 for upcoming anime - lower threshold)
        popularity = anime.get('popularity', 0)
        if popularity < 1000:
            continue
            
        # Skip short anime (less than 10 minutes per episode)
        episode_duration = anime.get('duration')
        anime_format = anime.get('format')
        
        if episode_duration and episode_duration < 10:
            continue
        elif anime_format == 'TV_SHORT' and (not episode_duration or episode_duration < 10):
            continue
        
        # Get start date
        start_date = None
        start_date_display = "TBD"
        if anime.get('startDate') and anime['startDate'].get('year'):
            month = anime['startDate'].get('month') or 1
            day = anime['startDate'].get('day') or 1
            start_date = f"{anime['startDate']['year']}-{month:02d}-{day:02d}"
            start_date_display = start_date
        
        # Get studio info
        studios = []
        if anime.get('studios') and anime['studios'].get('nodes'):
            studios = [studio['name'] for studio in anime['studios']['nodes']]
        studio_display = ', '.join(studios[:2]) if studios else 'TBD'  # Show up to 2 studios
        
        processed_anime.append({
            'id': anime['id'],
            'mal_id': anime.get('idMal'),
            'name': anime['title']['romaji'],
            'english_title': anime['title'].get('english'),
            'episode': 1,  # First episode for upcoming anime
            'release_date': start_date_display,
            'poster_url': anime['coverImage'].get('extraLarge') or anime['coverImage'].get('large') or anime['coverImage']['medium'],
            'site_url': anime['siteUrl'],
            'start_date': start_date,
            'season': anime.get('season', '').title(),
            'season_year': anime.get('seasonYear'),
            'studios': studio_display,
            'genres': anime.get('genres', []),
            'popularity': anime.get('popularity', 0),
            'favourites': anime.get('favourites', 0),
            'anilist_score': anime.get('averageScore'),
            'streaming_links': []  # Will be populated when anime starts airing
        })
    
    # Sort by popularity (highest first)
    processed_anime.sort(key=lambda x: x['popularity'], reverse=True)
    
    # Add popularity ranking
    for rank, anime in enumerate(processed_anime, 1):
        anime['popularity_rank'] = rank
    
    return processed_anime

def sort_other_anime(anime_list, today_date, tomorrow_date):
    """Sort other anime based on air dates"""
    other_anime = []
    recently_finished_anime = []
    today = datetime.strptime(today_date, '%Y-%m-%d').date()
    
    for anime in anime_list:
        # Skip anime that are in today or tomorrow sections
        if anime.get('release_date') == today_date or anime.get('release_date') == tomorrow_date:
            continue
        
        # Check if this is a recently finished anime
        if anime.get('recently_finished', False):
            recently_finished_anime.append(anime)
        else:
            # Add anime to other section
            other_anime.append(anime)
    
    # Sort other anime by priority
    def get_sort_priority(anime):
        release_date = anime.get('release_date')
        if not release_date:
            return (3, 0)  # Ongoing anime - medium priority, sorted by popularity rank
        
        try:
            air_date = datetime.strptime(release_date, '%Y-%m-%d').date()
            days_diff = (air_date - today).days
            
            if days_diff == 2:  # Airs in 2 days (day after tomorrow)
                return (0, anime.get('popularity_rank', 999))  # Highest priority
            elif days_diff == 3:  # Airs in 3 days
                return (1, anime.get('popularity_rank', 999))  # Second highest priority
            elif 4 <= days_diff <= 6:  # Airs in 4-6 days
                return (2, anime.get('popularity_rank', 999))  # Third priority
            elif days_diff >= 7:  # Airs in 7+ days (first episodes)
                return (4, anime.get('popularity_rank', 999))  # Lower priority
            elif days_diff == -1:  # Aired yesterday
                return (4, anime.get('popularity_rank', 999))  # Lower priority
            else:  # Other cases
                return (3, anime.get('popularity_rank', 999))  # Medium priority
        except (ValueError, TypeError):
            return (3, anime.get('popularity_rank', 999))  # Medium priority for invalid dates
    
    other_anime.sort(key=get_sort_priority)
    
    # Sort recently finished anime by end date (most recent first)
    recently_finished_anime.sort(key=lambda x: x.get('end_date', ''), reverse=True)
    
    return other_anime, recently_finished_anime

def main():
    """Main function to fetch and process anime data"""
    print("Fetching anime data from AniList API...")
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Fetch data from API
    api_data = fetch_current_anime()
    if not api_data:
        print("Failed to fetch data from API")
        return
    
    # Process the data
    processed_data = process_anime_data(api_data)
    print(f"Processed {len(processed_data)} anime")
    
    # Get today's and tomorrow's dates
    today = datetime.now().strftime('%Y-%m-%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Sort other anime with custom logic
    other_anime_sorted, recently_finished_sorted = sort_other_anime(processed_data, today, tomorrow)
    
    # Save processed data
    with open('data/anime_data.json', 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    
    # Save other anime sorted data
    with open('data/other_anime_sorted.json', 'w', encoding='utf-8') as f:
        json.dump(other_anime_sorted, f, ensure_ascii=False, indent=2)
    
    # Save recently finished anime data
    with open('data/recently_finished_anime.json', 'w', encoding='utf-8') as f:
        json.dump(recently_finished_sorted, f, ensure_ascii=False, indent=2)
    
    # Fetch upcoming seasonal anime
    next_season, next_year = get_next_season()
    print(f"Fetching upcoming {next_season.lower()} {next_year} anime...")
    
    upcoming_api_data = fetch_upcoming_seasonal_anime()
    upcoming_anime = []
    if upcoming_api_data:
        upcoming_anime = process_upcoming_anime_data(upcoming_api_data)
        print(f"Processed {len(upcoming_anime)} upcoming anime")
        
        # Save upcoming anime data
        with open('data/upcoming_seasonal_anime.json', 'w', encoding='utf-8') as f:
            json.dump(upcoming_anime, f, ensure_ascii=False, indent=2)
    else:
        print("Failed to fetch upcoming seasonal anime data")
    
    # Save metadata
    metadata = {
        'last_updated': datetime.now().isoformat(),
        'total_anime': len(processed_data),
        'total_upcoming_anime': len(upcoming_anime),
        'current_season': get_current_season(),
        'next_season': next_season,
        'next_season_year': next_year,
        'today_date': today,
        'tomorrow_date': tomorrow
    }
    
    with open('data/metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"Data saved to data/ directory")
    print(f"Last updated: {metadata['last_updated']}")
    print(f"Next season: {next_season.title()} {next_year}")

if __name__ == '__main__':
    main()