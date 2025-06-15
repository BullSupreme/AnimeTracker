#!/usr/bin/env python3
import json
import requests
from datetime import datetime, timedelta
import os

# Configuration
ANILIST_API_URL = "https://graphql.anilist.co"

def fetch_current_anime():
    """Fetch currently airing anime from AniList API"""
    query = '''
    query ($page: Int, $perPage: Int) {
        Page(page: $page, perPage: $perPage) {
            pageInfo {
                hasNextPage
                currentPage
            }
            media(status: RELEASING, type: ANIME, format_in: [TV, ONA, TV_SHORT], sort: [POPULARITY_DESC]) {
                id
                title {
                    romaji
                    english
                }
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
                'perPage': per_page
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
            print(f"Fetched page {page-1}, total anime so far: {len(all_anime)}")
        
        # Return in the same format as before
        return {'data': {'Page': {'media': all_anime}}}
        
    except requests.RequestException as e:
        print(f"Error fetching anime data: {e}")
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
    
    for anime in api_data['data']['Page']['media']:
        # Skip anime that started too long ago
        start_year = anime.get('startDate', {}).get('year')
        if start_year and start_year < cutoff_date.year:
            continue  # Skip this anime entirely
            
        # Skip kids anime
        anime_title = anime['title']['romaji']
        anime_title_english = anime['title'].get('english') or ''
        
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
            
            # If it's not a potential finale, skip old anime without next episodes
            if not could_be_finale_today:
                if start_year:
                    start_month = anime.get('startDate', {}).get('month', 1)
                    start_day = anime.get('startDate', {}).get('day', 1)
                    try:
                        start_date_obj = datetime(start_year, start_month, start_day)
                        four_weeks_ago = datetime.now() - timedelta(days=28)
                        if start_date_obj < four_weeks_ago:
                            continue  # Skip anime with no upcoming episodes that started > 4 weeks ago
                    except (ValueError, TypeError):
                        pass

        # Get episode info - use nextAiringEpisode if available, otherwise estimate
        episode_number = 1
        release_date = None
        
        if anime.get('nextAiringEpisode'):
            # Has confirmed next episode
            next_episode = anime['nextAiringEpisode']
            airing_timestamp = next_episode['airingAt']
            episode_number = next_episode['episode']
            
            # Convert timestamp to date string
            airing_date = datetime.fromtimestamp(airing_timestamp)
            release_date = airing_date.strftime('%Y-%m-%d')
            
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
            
            if started_long_ago or is_long_running:
                # Override release date for long-running series to exclude from today/tomorrow
                release_date = None
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
            # No next episode data - check if anime is old or long-running
            start_year = anime.get('startDate', {}).get('year')
            start_month = anime.get('startDate', {}).get('month', 1)
            
            started_long_ago = False
            episode_count = anime.get('episodes', 1) or 1
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
        
        # Process streaming links - filter out social media and non-streaming sites
        streaming_links = []
        streaming_sites = {
            'Crunchyroll', 'Funimation', 'Netflix', 'Hulu', 'Amazon Prime Video', 
            'Disney Plus', 'HBO Max', 'VRV', 'Hidive', 'AnimeLab', 'Wakanim',
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
            'Hidive': 'hidive.com',
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
        
        processed_anime.append({
            'id': anime['id'],
            'name': anime['title']['romaji'],
            'english_title': anime['title'].get('english'),
            'episode': episode_number,
            'release_date': release_date,
            'poster_url': anime['coverImage'].get('extraLarge') or anime['coverImage'].get('large') or anime['coverImage']['medium'],
            'site_url': anime['siteUrl'],
            'start_date': start_date,
            'streaming_links': streaming_links,
            'popularity': anime.get('popularity', 0)
        })
    
    # Sort by popularity (highest first) to calculate rankings
    processed_anime.sort(key=lambda x: x['popularity'], reverse=True)
    
    # Add popularity ranking to each anime
    for rank, anime in enumerate(processed_anime, 1):
        anime['popularity_rank'] = rank
    
    return processed_anime

def sort_other_anime(anime_list, today_date, tomorrow_date):
    """Sort other anime based on air dates"""
    other_anime = []
    today = datetime.strptime(today_date, '%Y-%m-%d').date()
    
    for anime in anime_list:
        # Skip anime that are in today or tomorrow sections
        if anime.get('release_date') == today_date or anime.get('release_date') == tomorrow_date:
            continue
            
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
    return other_anime

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
    other_anime_sorted = sort_other_anime(processed_data, today, tomorrow)
    
    # Save processed data
    with open('data/anime_data.json', 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    
    # Save other anime sorted data
    with open('data/other_anime_sorted.json', 'w', encoding='utf-8') as f:
        json.dump(other_anime_sorted, f, ensure_ascii=False, indent=2)
    
    # Save metadata
    metadata = {
        'last_updated': datetime.now().isoformat(),
        'total_anime': len(processed_data),
        'today_date': today,
        'tomorrow_date': tomorrow
    }
    
    with open('data/metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"Data saved to data/ directory")
    print(f"Last updated: {metadata['last_updated']}")

if __name__ == '__main__':
    main()