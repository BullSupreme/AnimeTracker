#!/usr/bin/env python3
import json
import os
from datetime import datetime

def calculate_overall_score(anime):
    """Calculate overall ranking score based on multiple metrics"""
    score = 0.0
    weights_used = 0.0
    
    # AniList popularity rank (normalized to 0-100)
    if anime.get('popularity_rank'):
        anilist_rank_score = max(0, 100 - (anime['popularity_rank'] - 1) * 2)
        score += anilist_rank_score * 0.25
        weights_used += 0.25
    
    # AniList score (already 0-100)
    if anime.get('anilist_score'):
        score += anime['anilist_score'] * 0.20
        weights_used += 0.20
    
    # MAL score (0-10, convert to 0-100)
    if anime.get('mal_score'):
        mal_score_normalized = anime['mal_score'] * 10
        score += mal_score_normalized * 0.30
        weights_used += 0.30
    
    # AniTrendz rank (normalized to 0-100)
    if anime.get('anitrendz_rank'):
        anitrendz_score = max(0, 100 - (anime['anitrendz_rank'] - 1) * 10)
        score += anitrendz_score * 0.25
        weights_used += 0.25
    
    # Normalize score based on available data
    if weights_used > 0:
        normalized_score = score / weights_used
    else:
        normalized_score = 0
    
    return round(normalized_score, 2)

def calculate_weekly_score(anime):
    """Calculate weekly score with higher AniTrendz weighting"""
    score = 0.0
    weights_used = 0.0
    
    # AniList popularity rank (normalized to 0-100) - reduced weight
    if anime.get('popularity_rank'):
        anilist_rank_score = max(0, 100 - (anime['popularity_rank'] - 1) * 2)
        score += anilist_rank_score * 0.10
        weights_used += 0.10
    
    # AniList score (already 0-100) - reduced weight
    if anime.get('anilist_score'):
        score += anime['anilist_score'] * 0.10
        weights_used += 0.10
    
    # MAL score (0-10, convert to 0-100) - reduced weight
    if anime.get('mal_score'):
        mal_score_normalized = anime['mal_score'] * 10
        score += mal_score_normalized * 0.15
        weights_used += 0.15
    
    # AniTrendz rank (normalized to 0-100) - MUCH HIGHER WEIGHT for weekly trends
    if anime.get('anitrendz_rank'):
        anitrendz_score = max(0, 100 - (anime['anitrendz_rank'] - 1) * 1.2)
        score += anitrendz_score * 0.65
        weights_used += 0.65
    
    # Normalize score based on available data
    if weights_used > 0:
        normalized_score = score / weights_used
    else:
        normalized_score = 0
    
    return round(normalized_score, 2)

def generate_rankings_html():
    """Generate rankings.html with comprehensive anime rankings"""
    
    # Load anime data
    try:
        with open('data/anime_data.json', 'r', encoding='utf-8') as f:
            anime_data = json.load(f)
    except FileNotFoundError:
        print("Error: 'data/anime_data.json' file not found. Please ensure the file exists in the 'data' directory.")
        return
    except json.JSONDecodeError:
        print("Error: 'data/anime_data.json' contains invalid JSON. Please check the file format.")
        return
    except Exception as e:
        print(f"Error loading anime_data.json: {str(e)}")
        return
    
    # Calculate both overall and weekly scores
    for anime in anime_data:
        anime['overall_score'] = calculate_overall_score(anime)
        anime['weekly_score'] = calculate_weekly_score(anime)
    
    # Sort by overall score
    anime_data.sort(key=lambda x: x['overall_score'], reverse=True)
    
    # Generate HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title净="css/rankings.css">
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <h1>🏆 Anime Rankings</h1>
        <button id="update-btn" class="update-btn">🔄 Update</button>
    </header>
    <nav class="nav-tabs">
        <button class="nav-tab" onclick="window.location.href='index.html'">📋 List View</button>
        <button class="nav-tab" onclick="window.location.href='index.html#calendar';">📅 Calendar</button>
        <button class="nav-tab active">🏆 Rankings</button>
    </nav>

    <main>
        <div class="info-section">
            <p>Comprehensive rankings combining data from multiple sources:</p>
            <ul>
                <li>
                    <a href="https://anilist.co" target="_blank" class="source-link">
                        <img src="https://anilist.co/favicon.ico" alt="AniList" class="source-favicon">
                        <div> <strong>AniList</strong> <small>User tracking & community score</small> </div>
                    </a>
                </li>
                <li>
                    <a href="https://myanimelist.net" target="_blank" class="source-link">
                        <img src="https://myanimelist.net/favicon.ico" alt="MyAnimeList" class="source-favicon">
                        <div> <strong>MyAnimeList</strong> <small>Critical ratings & member count</small> </div>
                    </a>
                </li>
                <li>
                    <a href="https://anitrendz.com" target="_blank" class class="source-link">
                        <img src="https://www.google.com/s2/favicons?domain=anitrendz.com&sz=16" alt="AniTrendz" class="source-favicon">
                        <div> <strong>AniTrendz</strong> <small>Weekly popularity polls</small> </div>
                    </a>
                </li>
            </ul>
        </div>

        <div class="controls">
            <label>
                Sort by: 
                <select id="sort-select">
                    <option value="overall">Overall Score</option>
                    <option value="weekly">Weekly Score</option>
                    <option value="anilist">AniList Rank</option>
                    <option value="mal">MAL Score</option>
                    <option value="anitrendz">AniTrendz Rank</option>
                </select>
            </label>
            <button id="toggle-onepiece" class="filter-btn" data-hidden="false">
                🏴‍☠️ Hide One Piece
            </button>
        </div>

        <table id="rankings-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Anime</th>
                    <th class="sortable" data-sort="anilist">AniList<br><small>Rank / Users</small></th>
                    <th class="sortable" data-sort="mal">MAL<br><small>Score / Members</small></th>
                    <th class="sortable" data-sort="anitrendz">AniTrendz<br><small>Rank / Trend</small></th>
                    <th class="sortable" data-sort="weekly">Weekly<br><small>Score</small></th>
                    <th class="sortable" data-sort="overall">Overall<br><small>Score</small></th>
                </tr>
            </thead>
            <tbody>
'''
    
    # Add anime rows
    for i, anime in enumerate(anime_data[:50], 1):  # Show top 50 by default
        # Determine medal emoji for top 3
        rank_display = ''
        if i == 1:
            rank_display = '🥇'
        elif i == 2:
            rank_display = '🥈'
        elif i == 3:
            rank_display = '🥉'
        else:
            rank_display = str(i)
        
        # Format AniList data
        anilist_rank_value = anime.get('popularity_rank')
        if anilist_rank_value:
            anilist_rank = f"#{anilist_rank_value}"
        else:
            anilist_rank = '<span style="color: #ff5722; font-weight: bold;">—</span>'
        anilist_users = f"{anime.get('popularity', 0):,}"
        anilist_score = anime.get('anilist_score', 0)
        if anilist_score is None:
            anilist_score = 0
        
        # Format MAL data
        mal_score = anime.get('mal_score', 0)
        if mal_score is None:
            mal_score = 0
        mal_score_display = mal_score if mal_score != 0 else '<span style="color: #ff5722; font-weight: bold;">—</span>'
        mal_members = anime.get('mal_members', 0)
        if mal_members:
            mal_members = f"{mal_members:,}"
        else:
            mal_members = '<span style="color: #ff5722; font-weight: bold;">—</span>'
        
        # Format AniTrendz data
        anitrendz_rank_value = anime.get('anitrendz_rank')
        if anitrendz_rank_value:
            anitrendz_rank = f"#{anitrendz_rank_value}"
        else:
            anitrendz_rank = '<span style="color: #ff5722; font-weight: bold;">—</span>'
        anitrendz_change = anime.get('anitrendz_change', '')
        trend_icon = ''
        if anitrendz_change == 'up':
            trend_icon = '↑'
        elif anitrendz_change == 'down':
            trend_icon = '↓'
        
        # Determine cell colors based on rankings
        anilist_class = 'good' if anime.get('popularity_rank', 999) <= 10 else 'medium' if anime.get('popularity_rank', 999) <= 25 else ''
        mal_class = 'good' if mal_score >= 8 else 'medium' if mal_score >= 7 else ''
        anitrendz_class = 'good' if anime.get('anitrendz_rank', 999) <= 10 else ''
        weekly_class = 'good' if anime['weekly_score'] >= 80 else 'medium' if anime['weekly_score'] >= 60 else ''
        overall_class = 'good' if anime['overall_score'] >= 80 else 'medium' if anime['overall_score'] >= 60 else ''
        
        html += f'''
                <tr data-anime-id="{anime['id']}">
                    <td class="rank">{rank_display}</td>
                    <td class="anime-title">
                        <img src="{anime['poster_url']}" alt="{anime['name']}" class="mini-poster">
                        <div>
                            <a href="{anime['site_url']}" target="_blank">{anime['name']}</a>
                            {f'<small>{anime["english_title"]}</small>' if anime.get('english_title') else ''}
                        </div>
                    </td>
                    <td class="anilist-data {anilist_class}">
                        <strong>{anilist_rank}</strong><br>
                        <small>{anilist_users} users</small>
                        {f'<br><small>Score: {anilist_score}/100</small>' if anilist_score else ''}
                    </td>
                    <td class="mal-data {mal_class}">
                        <strong>{mal_score_display}/10</strong><br>
                        <small>{mal_members} members</small>
                    </td>
                    <td class="anitrendz-data {anitrendz_class}">
                        <strong>{anitrendz_rank}</strong>
                        {f' <span class="trend-{anitrendz_change}">{trend_icon}</span>' if trend_icon else ''}
                    </td>
                    <td class="weekly-score {weekly_class}">
                        <strong>{anime['weekly_score']}</strong>
                    </td>
                    <td class="overall-score {overall_class}">
                        <strong>{anime['overall_score']}</strong>
                        <div class="score-breakdown" style="display:none;">
                            <small>
                                AniList: {round(max(0, 100 - (anime.get('popularity_rank', 50) - 1) * 2) * 0.25, 1)}<br>
                                MAL: {round(mal_score * 10 * 0.30, 1) if mal_score != 0 else 0}<br>
                                AniTrendz: {round(max(0, 100 - (anime.get('anitrendz_rank', 10) - 1) * 10) * 0.25, 1) if anime.get('anitrendz_rank') else 0}
                            </small>
                        </div>
                    </td>
                </tr>
'''
    
    # Close HTML tags
    html += '''
            </tbody>
        </table>
        
        <div class="last-updated">
            Last updated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M UTC') + '''
        </div>
    </main>

    <!-- Update Modal -->
    <div id="update-modal" class="modal" style="display: none;">
        <div class="modal-content">
            <div class="loading-spinner"></div>
            <h3 id="modal-title">Updating Rankings...</h3>
            <div id="modal-status">
                <p>🔄 Starting update process...</p>
            </div>
            <button id="modal-close" class="modal-close" style="display: none;">✕ Close</button>
        </div>
    </div>

    <script src="js/rankings.js"></script>
</body>
</html>'''
    
    # Save HTML file
    try:
        with open('rankings.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Generated rankings.html")
    except Exception as e:
        print(f"Error writing rankings.html: {str(e)}")

def main():
    # Create directories if needed
    os.makedirs('css', exist_ok=True)
    os.makedirs('js', exist_ok=True)
    
    # Generate rankings page
    generate_rankings_html()

if __name__ == "__main__":
    main()