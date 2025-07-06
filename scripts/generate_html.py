#!/usr/bin/env python3
import json
from datetime import datetime, timedelta
import os

def load_data():
    """Load anime data and metadata"""
    try:
        with open('data/anime_data.json', 'r', encoding='utf-8') as f:
            anime_data = json.load(f)
        
        with open('data/other_anime_sorted.json', 'r', encoding='utf-8') as f:
            other_anime_sorted = json.load(f)
        
        with open('data/metadata.json', 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Load upcoming seasonal anime
        upcoming_anime = []
        upcoming_path = 'data/upcoming_seasonal_anime.json'
        if os.path.exists(upcoming_path):
            with open(upcoming_path, 'r', encoding='utf-8') as f:
                upcoming_anime = json.load(f)
        
        # Load manual streaming links
        manual_streaming_links = {}
        manual_streaming_path = 'data/manual_streaming_links.json'
        if os.path.exists(manual_streaming_path):
            with open(manual_streaming_path, 'r', encoding='utf-8') as f:
                manual_streaming_links = json.load(f)
        
        # Load recently finished anime
        recently_finished_anime = []
        recently_finished_path = 'data/recently_finished_anime.json'
        if os.path.exists(recently_finished_path):
            with open(recently_finished_path, 'r', encoding='utf-8') as f:
                recently_finished_anime = json.load(f)
        
        return anime_data, other_anime_sorted, metadata, upcoming_anime, manual_streaming_links, recently_finished_anime
    except FileNotFoundError as e:
        print(f"Data file not found: {e}")
        return [], [], {}, [], {}, []

def get_season_emoji(season):
    """Get emoji for a given season"""
    season_emojis = {
        'SPRING': '🌸',
        'SUMMER': '☀️', 
        'FALL': '🍂',
        'AUTUMN': '🍂',
        'WINTER': '❄️'
    }
    return season_emojis.get(season.upper(), '🎭')

def generate_html():
    """Generate static HTML file"""
    anime_data, other_anime_sorted, metadata, upcoming_anime, manual_streaming_links, recently_finished_anime = load_data()
    
    
    if not anime_data:
        print("No anime data found")
        return
    
    today_date = metadata.get('today_date', datetime.now().strftime('%Y-%m-%d'))
    tomorrow_date = metadata.get('tomorrow_date', (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))
    last_updated = metadata.get('last_updated', datetime.now().isoformat())
    
    # Load custom links if they exist
    custom_links = {}
    if os.path.exists('data/custom_links.json'):
        with open('data/custom_links.json', 'r', encoding='utf-8') as f:
            custom_links = json.load(f)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Anime Tracker</title>
        <link rel="stylesheet" href="css/style.css">
    </head>
    <body>
        <header>
            <h1>Current Anime Tracker</h1>
            <div class="anime-count">({len(anime_data)} anime)</div>
        </header>
        <nav class="nav-tabs">
            <button class="nav-tab active" data-tab="list">📋 List View</button>
            <button class="nav-tab" data-tab="calendar">📅 Calendar</button>
            <button class="nav-tab" onclick="window.location.href='rankings.html'">🏆 Rankings</button>
        </nav>
        <main>
            <!-- List View Section -->
            <div id="list-view" class="tab-content active">
                <div class="list-controls">
                    <div class="filter-controls">
                        <button class="list-tab active" data-list-tab="all">All Anime</button>
                        <button class="list-tab" data-list-tab="favorites">Favorites Only</button>
                    </div>
                    <div class="layout-controls">
                        <label for="layout-selector">Layout:</label>
                        <select id="layout-selector" class="layout-selector">
                            <option value="grid">Grid View</option>
                            <option value="compact">Compact List</option>
                            <option value="table">Table View</option>
                            <option value="poster">Poster Wall</option>
                        </select>
                    </div>
                </div>
                <div class="time-section">
                    <h2 class="section-title">
                        <span class="section-icon">🌟</span>
                        Today's Releases
                    <span class="date-label">{today_date}</span>
                    </h2>
                    <div class="anime-grid today-grid">
"""
    
    # Add today's releases
    for anime in anime_data:
        # Include anime if release_date is today OR if end_date is today (for final episodes)
        if anime.get('release_date') == today_date or anime.get('end_date') == today_date:
            custom_link = custom_links.get(anime['name'], anime['site_url'])
            link_domain = custom_link.split('//')[1].split('/')[0] if '//' in custom_link else 'anilist.co'
            
            html_content += f"""                        <div class="anime-card today-card" data-name="{anime['name']}" data-link="{custom_link}" data-anime-id="{anime['id']}" data-release="{anime.get('release_date', '')}" data-site-url="{anime['site_url']}" data-poster="{anime['poster_url']}">
                            <div class="card-image-wrapper">
                                <img class="anime-poster" src="{anime['poster_url']}" alt="{anime['name']} poster">
                                <div class="card-overlay">
                                    <button class="favorite-btn" data-anime-id="{anime['id']}">
                                        <span class="favorite-icon">♡</span>
                                    </button>
                                    <div class="popularity-rank-badge" data-tooltip="🔥 #{anime['popularity_rank']} most popular • {anime['popularity']:,} users tracking">
                                        #{anime['popularity_rank']}
                                    </div>
                                </div>
                                <div class="custom-link-badge" style="display: none;">
                                    <span class="custom-favicon"></span>
                                </div>
                            </div>
                            <div class="card-info">"""
            
            if anime.get('english_title'):
                html_content += f"""                                <div class="anime-english-title">{anime['english_title']}</div>"""
            
            html_content += f"""                                <h3 class="anime-title">{anime['name']}</h3>
                                <div class="episode-info">
                                    <span class="episode-badge">Episode {anime['episode']}</span>
                                    <a href="{custom_link}" target="_blank" class="main-link-btn">
                                        {link_domain}
                                    </a>
                                </div>
                                <div class="streaming-links">"""
            
            # Get manual streaming links if they exist
            manual_links = manual_streaming_links.get(anime['name'], [])
            all_streaming_links = anime.get('streaming_links', []) + manual_links
            
            # Remove duplicates based on site name
            seen_sites = set()
            unique_links = []
            for link in all_streaming_links:
                if link['site'] not in seen_sites:
                    seen_sites.add(link['site'])
                    unique_links.append(link)
            
            for link in unique_links:
                html_content += f"""                                    <a href="{link['url']}" target="_blank" title="{link['site']}" class="streaming-link">
                                        <img src="{link['icon']}" alt="{link['site']}">
                                    </a>"""
            
            html_content += """                                </div>
                            </div>
                        </div>"""
    
    html_content += f"""                    </div>
                </div>
                <div class="time-section">
                    <h2 class="section-title">
                        <span class="section-icon">📅</span>
                        Tomorrow's Releases
                    <span class="date-label">{tomorrow_date}</span>
                    </h2>
                    <div class="anime-grid tomorrow-grid">
"""
    
    # Add tomorrow's releases
    for anime in anime_data:
        # Include anime if release_date is tomorrow OR if end_date is tomorrow (for final episodes)
        if anime.get('release_date') == tomorrow_date or anime.get('end_date') == tomorrow_date:
            custom_link = custom_links.get(anime['name'], anime['site_url'])
            link_domain = custom_link.split('//')[1].split('/')[0] if '//' in custom_link else 'anilist.co'
            
            html_content += f"""                        <div class="anime-card tomorrow-card" data-name="{anime['name']}" data-link="{custom_link}" data-anime-id="{anime['id']}" data-release="{anime.get('release_date', '')}" data-site-url="{anime['site_url']}" data-poster="{anime['poster_url']}">
                            <div class="card-image-wrapper">
                                <img class="anime-poster" src="{anime['poster_url']}" alt="{anime['name']} poster">
                                <div class="card-overlay">
                                    <button class="favorite-btn" data-anime-id="{anime['id']}">
                                        <span class="favorite-icon">♡</span>
                                    </button>
                                    <div class="popularity-rank-badge" data-tooltip="🔥 #{anime['popularity_rank']} most popular • {anime['popularity']:,} users tracking">
                                        #{anime['popularity_rank']}
                                    </div>
                                </div>
                                <div class="custom-link-badge" style="display: none;">
                                    <span class="custom-favicon"></span>
                                </div>
                            </div>
                            <div class="card-info">"""
            
            if anime.get('english_title'):
                html_content += f"""                                <div class="anime-english-title">{anime['english_title']}</div>"""
            
            html_content += f"""                                <h3 class="anime-title">{anime['name']}</h3>
                                <div class="episode-info">
                                    <span class="episode-badge">Episode {anime['episode']}</span>
                                    <a href="{custom_link}" target="_blank" class="main-link-btn">
                                        {link_domain}
                                    </a>
                                </div>
                                <div class="streaming-links">"""
            
            # Get manual streaming links if they exist
            manual_links = manual_streaming_links.get(anime['name'], [])
            all_streaming_links = anime.get('streaming_links', []) + manual_links
            
            # Remove duplicates based on site name
            seen_sites = set()
            unique_links = []
            for link in all_streaming_links:
                if link['site'] not in seen_sites:
                    seen_sites.add(link['site'])
                    unique_links.append(link)
            
            for link in unique_links:
                html_content += f"""                                    <a href="{link['url']}" target="_blank" title="{link['site']}" class="streaming-link">
                                        <img src="{link['icon']}" alt="{link['site']}">
                                    </a>"""
            
            html_content += """                                </div>
                            </div>
                        </div>"""
    
    html_content += """                    </div>
                </div>"""
    
    # Add other seasonal anime section with current season emoji
    current_season = metadata.get('current_season', 'Spring').title()
    current_season_emoji = get_season_emoji(current_season)
    
    html_content += f"""                <div class="time-section">
                    <h2 class="section-title">
                        <span class="section-icon">{current_season_emoji}</span>
                        {current_season} 2025 Anime
                
                    </h2>
                    <div class="anime-grid other-grid">
"""
    
    # Add other anime (sorted)
    for anime in other_anime_sorted:
        custom_link = custom_links.get(anime['name'], anime['site_url'])
        link_domain = custom_link.split('//')[1].split('/')[0] if '//' in custom_link else 'anilist.co'
        
        html_content += f"""                        <div class="anime-card" data-name="{anime['name']}" data-link="{custom_link}" data-anime-id="{anime['id']}" data-release="{anime.get('release_date', '')}" data-site-url="{anime['site_url']}" data-poster="{anime['poster_url']}">
                            <div class="card-image-wrapper">
                                <img class="anime-poster" src="{anime['poster_url']}" alt="{anime['name']} poster">
                                <div class="card-overlay">
                                    <button class="favorite-btn" data-anime-id="{anime['id']}">
                                        <span class="favorite-icon">♡</span>
                                    </button>
                                    <div class="popularity-rank-badge" data-tooltip="🔥 #{anime['popularity_rank']} most popular • {anime['popularity']:,} users tracking">
                                        #{anime['popularity_rank']}
                                    </div>
                                </div>
                                <div class="custom-link-badge" style="display: none;">
                                    <span class="custom-favicon"></span>
                                </div>
                            </div>
                            <div class="card-info">"""
        
        if anime.get('english_title'):
            html_content += f"""                                <div class="anime-english-title">{anime['english_title']}</div>"""
        
        # Use next airing date if available, otherwise use release date
        next_airing = anime.get('next_airing_date')
        next_episode_num = anime.get('next_episode_number', anime['episode'])
        if next_airing:
            release_date_display = f"Next: {next_airing}"
            episode_display = f"Episode {next_episode_num}"
        else:
            release_date_display = anime.get('release_date', 'Ongoing')
            episode_display = f"Episode {anime['episode']}"
        html_content += f"""                                <h3 class="anime-title">{anime['name']}</h3>
                                <div class="episode-info">
                                    <span class="episode-badge">{episode_display}</span>
                                    <a href="{custom_link}" target="_blank" class="main-link-btn">
                                        {link_domain}
                                    </a>
                                    <span class="release-date">{release_date_display}</span>
                                </div>
                                <div class="streaming-links">"""
        
        for link in anime.get('streaming_links', []):
            html_content += f"""                                    <a href="{link['url']}" target="_blank" title="{link['site']}" class="streaming-link">
                                        <img src="{link['icon']}" alt="{link['site']}">
                                    </a>"""
        
        html_content += """                                </div>
                            </div>
                        </div>"""
    
    html_content += """                    </div>
                </div>"""
    
    # Add recently finished anime section if we have data
    if recently_finished_anime:
        html_content += """                <div class="time-section recently-finished-section">
                    <h2 class="section-title">
                        <span class="section-icon">✅</span>
                        Recently Finished (Last 2 Weeks)
                    </h2>
                    <div class="anime-grid recently-finished-grid">
"""
        
        # Add recently finished anime
        for anime in recently_finished_anime:
            custom_link = custom_links.get(anime['name'], anime['site_url'])
            link_domain = custom_link.split('//')[1].split('/')[0] if '//' in custom_link else 'anilist.co'
            
            # Display the total episodes and end date
            total_episodes = anime.get('episode', '?')
            end_date_display = f"Finished: {anime.get('end_date', 'Unknown')}"
            
            html_content += f"""                        <div class="anime-card recently-finished-card" data-name="{anime['name']}" data-link="{custom_link}" data-anime-id="{anime['id']}" data-release="{anime.get('end_date', '')}" data-site-url="{anime['site_url']}" data-poster="{anime['poster_url']}">
                            <div class="card-image-wrapper">
                                <img class="anime-poster" src="{anime['poster_url']}" alt="{anime['name']} poster">
                                <div class="card-overlay">
                                    <button class="favorite-btn" data-anime-id="{anime['id']}">
                                        <span class="favorite-icon">♡</span>
                                    </button>
                                    <div class="popularity-rank-badge" data-tooltip="🔥 #{anime['popularity_rank']} most popular • {anime['popularity']:,} users tracking">
                                        #{anime['popularity_rank']}
                                    </div>
                                </div>
                                <div class="custom-link-badge" style="display: none;">
                                    <span class="custom-favicon"></span>
                                </div>
                            </div>
                            <div class="card-info">"""
            
            if anime.get('english_title'):
                html_content += f"""                                <div class="anime-english-title">{anime['english_title']}</div>"""
            
            html_content += f"""                                <h3 class="anime-title">{anime['name']}</h3>
                                <div class="episode-info">
                                    <span class="episode-badge">Total: {total_episodes} Episodes</span>
                                    <a href="{custom_link}" target="_blank" class="main-link-btn">
                                        {link_domain}
                                    </a>
                                    <span class="release-date">{end_date_display}</span>
                                </div>
                                <div class="streaming-links">"""
            
            # Get manual streaming links if they exist
            manual_links = manual_streaming_links.get(anime['name'], [])
            all_streaming_links = anime.get('streaming_links', []) + manual_links
            
            # Remove duplicates based on site name
            seen_sites = set()
            unique_links = []
            for link in all_streaming_links:
                if link['site'] not in seen_sites:
                    seen_sites.add(link['site'])
                    unique_links.append(link)
            
            for link in unique_links:
                html_content += f"""                                    <a href="{link['url']}" target="_blank" title="{link['site']}" class="streaming-link">
                                        <img src="{link['icon']}" alt="{link['site']}">
                                    </a>"""
            
            html_content += """                                </div>
                            </div>
                        </div>"""
        
        html_content += """                    </div>
                </div>"""
    
    # Add upcoming seasonal anime section if we have data
    if upcoming_anime:
        next_season = metadata.get('next_season', 'Summer').title()
        next_season_year = metadata.get('next_season_year', 2025)
        season_emoji = get_season_emoji(next_season)
        
        html_content += f"""                <div class="time-section next-seasonal-section">
                    <h2 class="section-title">
                        <span class="section-icon">{season_emoji}</span>
                        Next Seasonal Anime ({next_season} {next_season_year})
                    </h2>
                    <div class="anime-grid upcoming-grid">
"""
        
        # Add all upcoming anime with show more functionality
        for i, anime in enumerate(upcoming_anime):
            # Add visibility class for items beyond the first 20
            visibility_class = "" if i < 20 else " hidden-upcoming"
            
            html_content += f"""                        <div class="anime-card upcoming-card{visibility_class}" data-name="{anime['name']}" data-link="{anime['site_url']}" data-anime-id="{anime['id']}" data-release="{anime.get('release_date', 'TBD')}" data-site-url="{anime['site_url']}" data-poster="{anime['poster_url']}">
                            <div class="card-image-wrapper">
                                <img class="anime-poster" src="{anime['poster_url']}" alt="{anime['name']} poster">
                                <div class="card-overlay">
                                    <button class="favorite-btn" data-anime-id="{anime['id']}">
                                        <span class="favorite-icon">♡</span>
                                    </button>
                                    <div class="popularity-rank-badge" data-tooltip="🔥 #{anime['popularity_rank']} most popular upcoming • {anime['popularity']:,} users tracking">
                                        #{anime['popularity_rank']}
                                    </div>
                                </div>
                            </div>
                            <div class="card-info">"""
            
            if anime.get('english_title'):
                html_content += f"""                                <div class="anime-english-title">{anime['english_title']}</div>"""
            
            html_content += f"""                                <h3 class="anime-title">{anime['name']}</h3>
                                <div class="episode-info">
                                    <span class="episode-badge">Episode 1</span>
                                    <a href="{anime['site_url']}" target="_blank" class="main-link-btn">
                                        anilist.co
                                    </a>
                                    <span class="release-date">{anime.get('release_date', 'TBD')}</span>
                                </div>
                                <div class="anime-details">
                                    <div class="studio-info">{anime.get('studios', 'TBD')}</div>
                                </div>
                            </div>
                        </div>"""
        
        # Add show more button if there are more than 20 anime
        if len(upcoming_anime) > 20:
            html_content += f"""                    </div>
                    <div class="show-more-container">
                        <button class="show-more-btn" id="show-more-upcoming" data-target="upcoming">
                            <span class="show-more-text">Show More ({len(upcoming_anime) - 20} more)</span>
                            <span class="show-less-text" style="display: none;">Show Less</span>
                            <span class="show-more-icon">▼</span>
                        </button>
                    </div>
                </div>"""
        else:
            html_content += """                    </div>
                </div>"""
    
    html_content += """            </div>
            <!-- Calendar View Section -->
            <div id="calendar-view" class="tab-content">
                <div class="calendar-controls">
                    <button class="calendar-tab active" data-calendar-tab="all">All Anime</button>
                    <button class="calendar-tab" data-calendar-tab="favorites">Favorites Only</button>
                </div>
                <div class="calendar-container">
                    <div class="calendar-grid" id="calendar-all">
                    <!-- Calendar will be populated by JavaScript -->
                    </div>
                    <div class="calendar-grid" id="calendar-favorites" style="display: none;">
                    <!-- Favorites calendar will be populated by JavaScript -->
                    </div>
                </div>
            </div>
        </main>
        <!-- Expanded Anime Modal -->
        <div id="anime-modal" class="modal">
            <div class="modal-content">
                <button class="modal-close">&times;</button>
                <div class="modal-body">
                <!-- Modal content will be populated by JavaScript -->
                </div>
            </div>
        </div>
        <!-- Context Menu -->
        <div id="context-menu" class="context-menu">
            <div class="context-item" id="edit-link">
                <span class="context-icon">🔗</span>
                Edit Link            
            </div>
            <div class="context-separator"></div>
            <div class="context-item" id="copy-main-title">
                <span class="context-icon">📄</span>
                Copy: Main Title
            </div>
            <div class="context-item" id="copy-english-title">
                <span class="context-icon">📋</span>
                Copy: English Title
            </div>
        </div>
        <!-- Footer with last updated info -->
        <footer style="text-align: center; padding: 2rem; color: var(--text-secondary); font-size: 0.875rem;">
            Last updated: """ + last_updated.split('T')[0] + """ at """ + last_updated.split('T')[1][:8] + """ UTC
        </footer>
        <!-- Pass anime data to JavaScript -->
        <script>
            window.animeData = """ + json.dumps(anime_data) + """;
            window.upcomingAnime = """ + json.dumps(upcoming_anime) + """;
            window.customLinks = """ + json.dumps(custom_links) + """;
            window.todayDate = \"""" + today_date + """\";
            window.tomorrowDate = \"""" + tomorrow_date + """\";
        </script>
        <script src="js/script.js"></script>
    </body>
</html>"""
    
    # Write the HTML file
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Generated index.html successfully")

def main():
    """Main function"""
    generate_html()

if __name__ == '__main__':
    main()