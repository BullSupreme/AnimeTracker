#!/usr/bin/env python3
import json
import os
from datetime import datetime

# NEW: Reusable function to calculate any score based on a weights dictionary.
# This one function replaces the two original, repetitive functions.
def calculate_score(anime, weights):
    """Generic function to calculate a weighted score for an anime."""
    score = 0.0
    weights_used = 0.0

    # A mapping from metric names to their calculation logic.
    metric_calculators = {
        'anilist_rank': lambda rank: max(0, 100 - (rank - 1) * 2),
        'anilist_score': lambda anilist_score: anilist_score,
        'mal_score': lambda mal_score: mal_score * 10,
        'anitrendz_rank': lambda rank: max(0, 100 - (rank - 1) * 10),
        # A special calculator for the weekly anitrendz score with more generous points
        'anitrendz_rank_weekly': lambda rank: max(0, 100 - (rank - 1) * 1.2)
    }

    # Iterate through the provided weights and calculate the score
    for metric, weight in weights.items():
        # Determine which calculator to use ('anitrendz_rank_weekly' or default 'anitrendz_rank')
        calculator_key = 'anitrendz_rank_weekly' if metric == 'anitrendz_rank' and weight > 0.5 else metric
        
        # Get the raw value from the anime data, skipping if it's missing or None
        raw_value = anime.get(metric)
        if raw_value is not None and metric in metric_calculators:
            calculated_value = metric_calculators[calculator_key](raw_value)
            score += calculated_value * weight
            weights_used += weight

    # Normalize the final score
    return round(score / weights_used, 2) if weights_used > 0 else 0.0

def generate_rankings_html():
    """Generate rankings.html with comprehensive anime rankings."""
    
    with open('data/anime_data.json', 'r', encoding='utf-8') as f:
        anime_data = json.load(f)

    # REFACTORED: Define weights in clean dictionaries
    overall_weights = {
        'popularity_rank': 0.25,
        'anilist_score': 0.20,
        'mal_score': 0.30,
        'anitrendz_rank': 0.25
    }
    weekly_weights = {
        'popularity_rank': 0.10,
        'anilist_score': 0.10,
        'mal_score': 0.15,
        'anitrendz_rank': 0.65 # This will use the 'anitrendz_rank_weekly' calculator due to its high weight
    }

    # REFACTORED: Calculate scores with single-line calls to the new function
    for anime in anime_data:
        anime['overall_score'] = calculate_score(anime, overall_weights)
        anime['weekly_score'] = calculate_score(anime, weekly_weights)
    
    anime_data.sort(key=lambda x: x['overall_score'], reverse=True)
    
    # --- The HTML generation part remains largely the same, but we need to fix the error inside it ---
    
    # Start of HTML (collapsed for brevity, no changes here)
    html = f'''<!DOCTYPE html>...''' 

    for i, anime in enumerate(anime_data[:50], 1):
        rank_display = '🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else str(i)
        
        # --- Data Formatting with robust None checks ---
        anilist_rank_display = f"#{rank}" if (rank := anime.get('popularity_rank')) else '<span class="na">—</span>'
        anilist_users = f"{anime.get('popularity', 0):,}"
        anilist_score_display = f'<br><small>Score: {score}/100</small>' if (score := anime.get('anilist_score')) else ''

        mal_score_val = anime.get('mal_score')
        mal_score_display = f'{mal_score_val}/10' if mal_score_val is not None else '<span class="na">—</span>'
        mal_members_display = f"{mem:,}" if (mem := anime.get('mal_members')) else '<span class="na">—</span>'

        anitrendz_rank_display = f"#{rank}" if (rank := anime.get('anitrendz_rank')) else '<span class="na">—</span>'
        anitrendz_change = anime.get('anitrendz_change', '')
        trend_icon = '↑' if anitrendz_change == 'up' else '↓' if anitrendz_change == 'down' else ''

        # --- CSS Class Calculation (robust against None) ---
        anilist_class = 'good' if (anime.get('popularity_rank') or 999) <= 10 else 'medium' if (anime.get('popularity_rank') or 999) <= 25 else ''
        mal_class = 'good' if (anime.get('mal_score') or 0) >= 8 else 'medium' if (anime.get('mal_score') or 0) >= 7 else ''
        anitrendz_class = 'good' if (anime.get('anitrendz_rank') or 999) <= 10 else ''
        weekly_class = 'good' if anime['weekly_score'] >= 80 else 'medium' if anime['weekly_score'] >= 60 else ''
        overall_class = 'good' if anime['overall_score'] >= 80 else 'medium' if anime['overall_score'] >= 60 else ''
        
        # --- Breakdown Calculation (robust against None) ---
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
                        <strong>{anilist_rank_display}</strong><br>
                        <small>{anilist_users} users</small>
                        {anilist_score_display}
                    </td>
                    <td class="mal-data {mal_class}">
                        <strong>{mal_score_display}</strong><br>
                        <small>{mal_members_display} members</small>
                    </td>
                    <td class="anitrendz-data {anitrendz_class}">
                        <strong>{anitrendz_rank_display}</strong>
                        {f' <span class="trend-{anitrendz_change}">{trend_icon}</span>' if trend_icon else ''}
                    </td>
                    <td class="weekly-score {weekly_class}"><strong>{anime['weekly_score']}</strong></td>
                    <td class="overall-score {overall_class}">
                        <strong>{anime['overall_score']}</strong>
                        <div class="score-breakdown" style="display:none;">
                            <small>
                                AniList: {breakdown_anilist}<br>
                                MAL: {breakdown_mal}<br>
                                AniTrendz: {breakdown_at}
                            </small>
                        </div>
                    </td>
                </tr>
'''
    
    # End of HTML (collapsed for brevity, no changes here)
    html += '''...</tbody></table>...'''

    with open('rankings.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("Generated rankings.html")

def main():
    os.makedirs('css', exist_ok=True)
    os.makedirs('js', exist_ok=True)
    generate_rankings_html()

if __name__ == "__main__":
    main()