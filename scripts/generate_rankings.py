#!/usr/bin/env python3
import json
import os
from datetime import datetime

# (The calculate_score function is perfect, no changes needed there)
def calculate_score(anime, weights):
    """Generic function to calculate a weighted score for an anime."""
    score = 0.0
    weights_used = 0.0
    metric_calculators = {
        'popularity_rank': lambda rank: max(0, 100 - (rank - 1) * 2),
        'anilist_score': lambda anilist_score: anilist_score,
        'mal_score': lambda mal_score: mal_score * 10,
        'anitrendz_rank': lambda rank: max(0, 100 - (rank - 1) * 10),
        'anitrendz_rank_weekly': lambda rank: max(0, 100 - (rank - 1) * 1.2)
    }
    for metric, weight in weights.items():
        calculator_key = 'anitrendz_rank_weekly' if metric == 'anitrendz_rank' and weight > 0.5 else metric
        raw_value = anime.get(metric.replace('_weekly', '')) # Handle the key name change
        if raw_value is not None and calculator_key in metric_calculators:
            calculated_value = metric_calculators[calculator_key](raw_value)
            score += calculated_value * weight
            weights_used += weight
    return round(score / weights_used, 2) if weights_used > 0 else 0.0

def generate_rankings_html():
    """Generate rankings.html with comprehensive anime rankings."""
    
    with open('data/anime_data.json', 'r', encoding='utf-8') as f:
        anime_data = json.load(f)

    overall_weights = {
        'popularity_rank': 0.25, 'anilist_score': 0.20,
        'mal_score': 0.30, 'anitrendz_rank': 0.25
    }
    weekly_weights = {
        'popularity_rank': 0.10, 'anilist_score': 0.10,
        'mal_score': 0.15, 'anitrendz_rank': 0.65
    }

    for anime in anime_data:
        anime['overall_score'] = calculate_score(anime, overall_weights)
        anime['weekly_score'] = calculate_score(anime, weekly_weights)
    
    anime_data.sort(key=lambda x: x['overall_score'], reverse=True)
    
    # --- FIX: Correct the CSS paths to be relative to the root ---
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anime Rankings - Ultimate Rankings</title>
    <link rel="stylesheet" href="./css/rankings.css">
    <link rel="stylesheet" href="./css/style.css">
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
        <!-- The rest of your HTML generation code is fine -->
'''
    # (The rest of the script is unchanged, as it was correct)
    # ... your existing loop to generate table rows ...
    # ... your existing closing HTML ...
    
    # Re-pasting the loop for completeness, no changes were made here
    for i, anime in enumerate(anime_data[:50], 1):
        rank_display = '🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else str(i)
        anilist_rank_display = f"#{rank}" if (rank := anime.get('popularity_rank')) else '<span class="na">—</span>'
        anilist_users = f"{anime.get('popularity', 0):,}"
        anilist_score_display = f'<br><small>Score: {score}/100</small>' if (score := anime.get('anilist_score')) else ''
        mal_score_val = anime.get('mal_score')
        mal_score_display = f'{mal_score_val}/10' if mal_score_val is not None else '<span class="na">—</span>'
        mal_members_display = f"{mem:,}" if (mem := anime.get('mal_members')) else '<span class="na">—</span>'
        anitrendz_rank_display = f"#{rank}" if (rank := anime.get('anitrendz_rank')) else '<span class="na">—</span>'
        anitrendz_change = anime.get('anitrendz_change', '')
        trend_icon = '↑' if anitrendz_change == 'up' else '↓' if anitrendz_change == 'down' else ''
        anilist_class = 'good' if (anime.get('popularity_rank') or 999) <= 10 else 'medium' if (anime.get('popularity_rank') or 999) <= 25 else ''
        mal_class = 'good' if (anime.get('mal_score') or 0) >= 8 else 'medium' if (anime.get('mal_score') or 0) >= 7 else ''
        anitrendz_class = 'good' if (anime.get('anitrendz_rank') or 999) <= 10 else ''
        weekly_class = 'good' if anime['weekly_score'] >= 80 else 'medium' if anime['weekly_score'] >= 60 else ''
        overall_class = 'good' if anime['overall_score'] >= 80 else 'medium' if anime['overall_score'] >= 60 else ''
        breakdown_anilist = round(max(0, 100 - (r - 1) * 2) * 0.25, 1) if (r := anime.get("popularity_rank")) else 0.0
        breakdown_mal = round(s * 10 * 0.30, 1) if (s := anime.get("mal_score")) else 0.0
        breakdown_at = round(max(0, 100 - (r - 1) * 10) * 0.25, 1) if (r := anime.get("anitrendz_rank")) else 0.0
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
                        <strong>{anilist_rank_display}</strong><br><small>{anilist_users} users</small>{anilist_score_display}
                    </td>
                    <td class="mal-data {mal_class}">
                        <strong>{mal_score_display}</strong><br><small>{mal_members_display} members</small>
                    </td>
                    <td class="anitrendz-data {anitrendz_class}">
                        <strong>{anitrendz_rank_display}</strong>{f' <span class="trend-{anitrendz_change}">{trend_icon}</span>' if trend_icon else ''}
                    </td>
                    <td class="weekly-score {weekly_class}"><strong>{anime['weekly_score']}</strong></td>
                    <td class="overall-score {overall_class}">
                        <strong>{anime['overall_score']}</strong>
                        <div class="score-breakdown" style="display:none;">
                            <small>AniList: {breakdown_anilist}<br>MAL: {breakdown_mal}<br>AniTrendz: {breakdown_at}</small>
                        </div>
                    </td>
                </tr>'''
    html += '''
            </tbody>
        </table>
    </main>
    <script src="./js/rankings.js"></script>
</body>
</html>'''

    with open('rankings.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Generated rankings.html")

def main():
    os.makedirs('css', exist_ok=True)
    os.makedirs('js', exist_ok=True)
    generate_rankings_html()

if __name__ == "__main__":
    main()