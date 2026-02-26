#!/usr/bin/env python3
"""
Generate all-anime.html from data/all_anime_catalog.json.

This creates a fully self-contained static page with embedded JSON data
for client-side filtering, sorting, and search — no server needed.
"""
import json
import os
from datetime import datetime
from urllib.parse import quote

CATALOG_FILE = "data/all_anime_catalog.json"
OUTPUT_FILE = "all-anime.html"


def get_current_season():
    """Get current season and year."""
    month = datetime.now().month
    year = datetime.now().year
    if month in [1, 2, 3]:
        return "WINTER", year
    elif month in [4, 5, 6]:
        return "SPRING", year
    elif month in [7, 8, 9]:
        return "SUMMER", year
    else:
        return "FALL", year


def season_sort_key(entry):
    """Sort key for season dropdown: newest first."""
    season_order = {"WINTER": 0, "SPRING": 1, "SUMMER": 2, "FALL": 3}
    year = entry.get("season_year") or 0
    season = entry.get("season") or "WINTER"
    return (-year, -season_order.get(season, 0))


def build_season_options(catalog):
    """Build sorted list of unique season+year combos for the filter dropdown."""
    seen = set()
    seasons = []
    for anime in catalog:
        s = anime.get("season")
        y = anime.get("season_year")
        if s and y:
            key = f"{s}_{y}"
            if key not in seen:
                seen.add(key)
                seasons.append({"season": s, "year": y})

    seasons.sort(key=lambda e: (-e["year"], -["WINTER", "SPRING", "SUMMER", "FALL"].index(e["season"]) if e["season"] in ["WINTER", "SPRING", "SUMMER", "FALL"] else 0))
    return seasons


def season_emoji(season):
    emojis = {"SPRING": "🌸", "SUMMER": "☀️", "FALL": "🍂", "WINTER": "❄️"}
    return emojis.get(season, "🎭")


def generate_html(catalog):
    current_season, current_year = get_current_season()
    season_options = build_season_options(catalog)
    last_updated = datetime.now().strftime("%Y-%m-%d")

    # Build season options HTML
    season_opts_html = '<option value="">All Seasons</option>\n'
    for s in season_options:
        emoji = season_emoji(s["season"])
        label = f'{emoji} {s["season"].capitalize()} {s["year"]}'
        value = f'{s["season"]}_{s["year"]}'
        selected = 'selected' if s["season"] == current_season and s["year"] == current_year else ''
        season_opts_html += f'                        <option value="{value}" {selected}>{label}</option>\n'

    # Embed catalog as JSON (sorted by popularity descending)
    catalog_sorted = sorted(catalog, key=lambda x: x.get("popularity", 0), reverse=True)
    catalog_json = json.dumps(catalog_sorted, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>All Anime - Anime Tracker</title>
    <link rel="stylesheet" href="css/style.css">
    <style>
        /* All Anime Page Specific Styles */
        .all-anime-header {{
            display: flex;
            align-items: center;
            gap: 1.5rem;
            padding: 1rem 1.5rem;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            flex-wrap: wrap;
        }}

        .all-anime-header h1 {{
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .back-btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.4rem 1rem;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.9rem;
            transition: all var(--transition-fast);
            white-space: nowrap;
        }}

        .back-btn:hover {{
            border-color: var(--accent-primary);
            color: var(--accent-primary);
        }}

        .catalog-stats {{
            margin-left: auto;
            color: var(--text-dim);
            font-size: 0.85rem;
        }}

        .all-anime-controls {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            align-items: center;
            padding: 1rem 1.5rem;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .search-wrapper {{
            position: relative;
            flex: 1;
            min-width: 200px;
            max-width: 400px;
        }}

        .search-icon {{
            position: absolute;
            left: 0.75rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-dim);
            pointer-events: none;
        }}

        .search-input {{
            width: 100%;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            border-radius: 8px;
            padding: 0.5rem 1rem 0.5rem 2.2rem;
            font-size: 0.9rem;
            transition: border-color var(--transition-fast);
        }}

        .search-input:focus {{
            outline: none;
            border-color: var(--accent-primary);
        }}

        .search-input::placeholder {{
            color: var(--text-dim);
        }}

        .control-select {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            border-radius: 8px;
            padding: 0.5rem 0.75rem;
            font-size: 0.85rem;
            cursor: pointer;
            transition: border-color var(--transition-fast);
        }}

        .control-select:focus {{
            outline: none;
            border-color: var(--accent-primary);
        }}

        .control-select option {{
            background: var(--bg-card);
        }}

        .poster-toggle-wrapper {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--text-secondary);
            font-size: 0.85rem;
            white-space: nowrap;
        }}

        .toggle-switch {{
            position: relative;
            width: 44px;
            height: 24px;
            cursor: pointer;
        }}

        .toggle-switch input {{
            opacity: 0;
            width: 0;
            height: 0;
        }}

        .toggle-slider {{
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: var(--border-color);
            border-radius: 24px;
            transition: var(--transition-fast);
        }}

        .toggle-slider::before {{
            content: '';
            position: absolute;
            width: 18px;
            height: 18px;
            left: 3px;
            top: 3px;
            background: white;
            border-radius: 50%;
            transition: var(--transition-fast);
        }}

        .toggle-switch input:checked + .toggle-slider {{
            background: var(--accent-primary);
        }}

        .toggle-switch input:checked + .toggle-slider::before {{
            transform: translateX(20px);
        }}

        .results-count {{
            color: var(--text-dim);
            font-size: 0.8rem;
            white-space: nowrap;
        }}

        /* All Anime Grid */
        .all-anime-main {{
            padding: 1.5rem;
            max-width: 1800px;
            margin: 0 auto;
        }}

        .all-anime-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
            gap: 1rem;
            animation: fadeIn 0.3s ease;
        }}

        .all-anime-grid.poster-mode {{
            grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
            gap: 0.5rem;
        }}

        .all-anime-grid.poster-mode .card-info {{
            display: none;
        }}

        .all-anime-grid.poster-mode .anime-card {{
            border-radius: 8px;
        }}

        /* Card extras */
        .score-genre-row {{
            display: flex;
            gap: 0.4rem;
            flex-wrap: wrap;
            align-items: center;
        }}

        .score-badge {{
            background: rgba(251, 191, 36, 0.15);
            color: var(--accent-gold);
            border: 1px solid rgba(251, 191, 36, 0.3);
            padding: 0.15rem 0.5rem;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 600;
            white-space: nowrap;
        }}

        .season-badge {{
            background: rgba(139, 92, 246, 0.15);
            color: #a78bfa;
            border: 1px solid rgba(139, 92, 246, 0.3);
            padding: 0.15rem 0.5rem;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 500;
            white-space: nowrap;
        }}

        .genre-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.25rem;
            margin-top: 0.25rem;
        }}

        .genre-tag {{
            background: rgba(59, 130, 246, 0.12);
            color: var(--accent-primary);
            border: 1px solid rgba(59, 130, 246, 0.25);
            padding: 0.1rem 0.45rem;
            border-radius: 20px;
            font-size: 0.68rem;
        }}

        .no-results {{
            grid-column: 1 / -1;
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-secondary);
        }}

        .no-results-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}

        .loading-overlay {{
            grid-column: 1 / -1;
            text-align: center;
            padding: 4rem;
            color: var(--text-secondary);
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(8px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Responsive */
        @media (max-width: 600px) {{
            .all-anime-controls {{ padding: 0.75rem; }}
            .all-anime-main {{ padding: 0.75rem; }}
            .all-anime-grid {{ grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); }}
        }}

        /* Make nine-anime-btn match existing style */
        .nine-anime-btn {{
            background: #10b981;
            color: white;
            border: none;
            border-radius: 20px;
            padding: 0.2rem 0.6rem;
            font-size: 0.75rem;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            white-space: nowrap;
        }}

        .nine-anime-btn:hover {{
            background: #059669;
        }}
    </style>
</head>
<body>
    <div class="all-anime-header">
        <a href="index.html" class="back-btn">← Tracker</a>
        <h1>🎬 All Anime</h1>
        <div class="catalog-stats" id="catalog-stats">Loading catalog...</div>
    </div>

    <div class="all-anime-controls">
        <div class="search-wrapper">
            <span class="search-icon">🔍</span>
            <input type="text" id="search-input" class="search-input" placeholder="Search anime...">
        </div>

        <select id="sort-select" class="control-select" title="Sort by">
            <option value="season_popular">⭐ Popular This Season</option>
            <option value="popular_all">🔥 Most Popular All Time</option>
            <option value="score">⭐ Highest Score</option>
            <option value="newest">🆕 Newest First</option>
            <option value="oldest">📅 Oldest First</option>
        </select>

        <select id="season-select" class="control-select" title="Filter by season">
{season_opts_html}        </select>

        <div class="poster-toggle-wrapper">
            <span>Cards</span>
            <label class="toggle-switch" title="Toggle poster-only view">
                <input type="checkbox" id="poster-toggle">
                <span class="toggle-slider"></span>
            </label>
            <span>Posters</span>
        </div>

        <span class="results-count" id="results-count"></span>
    </div>

    <main class="all-anime-main">
        <div class="all-anime-grid" id="anime-grid">
            <div class="loading-overlay">Loading anime catalog...</div>
        </div>
    </main>

    <!-- Context Menu (reuse existing pattern) -->
    <div class="context-menu" id="context-menu">
        <div class="context-item" id="ctx-anilist">
            <span class="context-icon">📋</span> Open on AniList
        </div>
        <div class="context-item" id="ctx-9anime">
            <span class="context-icon">▶️</span> Search on 9anime
        </div>
        <div class="context-separator"></div>
        <div class="context-item" id="ctx-favorite">
            <span class="context-icon">♡</span> Toggle Favorite
        </div>
    </div>

    <script>
    // ============================================================
    // EMBEDDED CATALOG DATA
    // ============================================================
    const ALL_ANIME_DATA = {catalog_json};

    // ============================================================
    // STATE
    // ============================================================
    const CURRENT_SEASON = "{current_season}";
    const CURRENT_YEAR = {current_year};
    const CATALOG_TOTAL = ALL_ANIME_DATA.length;

    let favorites = [];
    try {{
        const raw = document.cookie.split('; ').find(r => r.startsWith('favorites='));
        if (raw) favorites = JSON.parse(decodeURIComponent(raw.split('=')[1]));
    }} catch(e) {{ favorites = []; }}

    let contextTarget = null;

    // ============================================================
    // COOKIE HELPERS
    // ============================================================
    function getCookie(name) {{
        const match = document.cookie.split('; ').find(r => r.startsWith(name + '='));
        return match ? decodeURIComponent(match.split('=')[1]) : null;
    }}

    function setCookie(name, value, days) {{
        const d = new Date();
        d.setTime(d.getTime() + days * 24 * 60 * 60 * 1000);
        document.cookie = name + '=' + encodeURIComponent(value) + '; expires=' + d.toUTCString() + '; path=/';
    }}

    // ============================================================
    // FAVORITES
    // ============================================================
    function saveFavorites() {{
        setCookie('favorites', JSON.stringify(favorites), 30);
    }}

    function isFavorite(id) {{
        return favorites.includes(String(id));
    }}

    function toggleFavorite(id) {{
        const sid = String(id);
        if (favorites.includes(sid)) {{
            favorites = favorites.filter(f => f !== sid);
        }} else {{
            favorites.push(sid);
        }}
        saveFavorites();
        // Update all cards with this id
        document.querySelectorAll(`[data-anime-id="${{sid}}"] .favorite-icon`).forEach(icon => {{
            icon.textContent = isFavorite(sid) ? '♥' : '♡';
            icon.closest('.favorite-btn').classList.toggle('active', isFavorite(sid));
        }});
    }}

    // ============================================================
    // FILTERING & SORTING
    // ============================================================
    function getFilteredData() {{
        const query = document.getElementById('search-input').value.toLowerCase().trim();
        const sortVal = document.getElementById('sort-select').value;
        const seasonVal = document.getElementById('season-select').value;

        let data = ALL_ANIME_DATA.slice();

        // Season filter
        if (seasonVal) {{
            const [filterSeason, filterYear] = seasonVal.split('_');
            data = data.filter(a => a.season === filterSeason && String(a.season_year) === filterYear);
        }} else if (sortVal === 'season_popular') {{
            // Default: current season only
            data = data.filter(a => a.season === CURRENT_SEASON && a.season_year === CURRENT_YEAR);
        }}

        // Search filter
        if (query) {{
            data = data.filter(a => {{
                const name = (a.name || '').toLowerCase();
                const eng = (a.english_title || '').toLowerCase();
                return name.includes(query) || eng.includes(query);
            }});
        }}

        // Sort
        switch (sortVal) {{
            case 'season_popular':
            case 'popular_all':
                data.sort((a, b) => (b.popularity || 0) - (a.popularity || 0));
                break;
            case 'score':
                data.sort((a, b) => (b.anilist_score || 0) - (a.anilist_score || 0));
                break;
            case 'newest':
                data.sort((a, b) => (b.start_date || '').localeCompare(a.start_date || ''));
                break;
            case 'oldest':
                data.sort((a, b) => (a.start_date || '').localeCompare(b.start_date || ''));
                break;
        }}

        return data;
    }}

    // ============================================================
    // RENDER
    // ============================================================
    function buildCard(anime, rank) {{
        const id = anime.id;
        const name = anime.name || '';
        const eng = anime.english_title || '';
        const poster = anime.poster_url || '';
        const siteUrl = anime.site_url || `https://anilist.co/anime/${{id}}`;
        const score = anime.anilist_score;
        const season = anime.season;
        const seasonYear = anime.season_year;
        const genres = anime.genres || [];
        const episodes = anime.episodes;
        const popularity = anime.popularity || 0;
        const searchTitle = encodeURIComponent(eng || name);
        const nineAnimeUrl = `https://9animetv.to/search?keyword=${{searchTitle}}`;
        const isFav = isFavorite(id);

        const scoreBadge = score ? `<span class="score-badge">⭐ ${{score}}/100</span>` : '';
        const seasonLabel = season && seasonYear
            ? `<span class="season-badge">${{season.charAt(0) + season.slice(1).toLowerCase()}} ${{seasonYear}}</span>`
            : '';
        const episodeLabel = episodes ? `${{episodes}} ep` : 'Ongoing';
        const engTitle = eng ? `<div class="anime-english-title">${{escapeHtml(eng)}}</div>` : '';
        const popularityTooltip = `🔥 #${{rank}} most popular • ${{popularity.toLocaleString()}} users tracking`;

        const genreTagsHtml = genres.slice(0, 3).map(g =>
            `<span class="genre-tag">${{escapeHtml(g)}}</span>`
        ).join('');

        return `<div class="anime-card all-anime-card"
                     data-id="${{id}}"
                     data-anime-id="${{id}}"
                     data-popularity="${{popularity}}"
                     data-score="${{score || 0}}"
                     data-season="${{season || ''}}"
                     data-season-year="${{seasonYear || ''}}"
                     data-name="${{escapeAttr(name)}}"
                     data-english="${{escapeAttr(eng)}}"
                     data-link="${{escapeAttr(siteUrl)}}"
                     data-site-url="${{escapeAttr(siteUrl)}}"
                     data-poster="${{escapeAttr(poster)}}">
            <div class="card-image-wrapper">
                <img class="anime-poster" src="${{escapeAttr(poster)}}" loading="lazy" alt="${{escapeAttr(name)}} poster"
                     onerror="this.src='data:image/svg+xml,<svg xmlns=\\'http://www.w3.org/2000/svg\\'><rect width=\\'100%\\' height=\\'100%\\' fill=\\'%231e2433\\'/></svg>'">
                <div class="card-overlay">
                    <button class="favorite-btn${{isFav ? ' active' : ''}}" data-anime-id="${{id}}" onclick="event.stopPropagation(); toggleFavorite(${{id}})">
                        <span class="favorite-icon">${{isFav ? '♥' : '♡'}}</span>
                    </button>
                    <div class="popularity-rank-badge" data-tooltip="${{escapeAttr(popularityTooltip)}}">#${{rank}}</div>
                </div>
            </div>
            <div class="card-info">
                ${{engTitle}}
                <h3 class="anime-title">${{escapeHtml(name)}}</h3>
                <div class="episode-info">
                    <span class="episode-badge">${{episodeLabel}}</span>
                    <a href="${{escapeAttr(siteUrl)}}" target="_blank" class="main-link-btn" onclick="event.stopPropagation()">anilist.co</a>
                    <a href="${{escapeAttr(nineAnimeUrl)}}" target="_blank" class="nine-anime-btn" onclick="event.stopPropagation()">9anime</a>
                </div>
                <div class="score-genre-row">
                    ${{scoreBadge}}
                    ${{seasonLabel}}
                </div>
                ${{genreTagsHtml ? `<div class="genre-tags">${{genreTagsHtml}}</div>` : ''}}
            </div>
        </div>`;
    }}

    function renderAnime() {{
        const grid = document.getElementById('anime-grid');
        const data = getFilteredData();

        document.getElementById('results-count').textContent =
            data.length === CATALOG_TOTAL ? `${{CATALOG_TOTAL.toLocaleString()}} anime` : `${{data.length.toLocaleString()}} / ${{CATALOG_TOTAL.toLocaleString()}}`;

        if (data.length === 0) {{
            grid.innerHTML = `<div class="no-results">
                <div class="no-results-icon">🔍</div>
                <div>No anime found matching your filters.</div>
            </div>`;
            return;
        }}

        // Build all cards (virtualise for large sets)
        const MAX_RENDER = 500;
        const rendered = data.slice(0, MAX_RENDER);
        const html = rendered.map((anime, i) => buildCard(anime, i + 1)).join('');

        const moreHtml = data.length > MAX_RENDER
            ? `<div class="no-results" style="grid-column:1/-1">
                <div>Showing ${{MAX_RENDER}} of ${{data.length}} results. Use search or filters to narrow down.</div>
               </div>`
            : '';

        grid.innerHTML = html + moreHtml;
        attachTooltips();
        updateFavoriteStates();
    }}

    // ============================================================
    // TOOLTIP (reuse existing pattern)
    // ============================================================
    function attachTooltips() {{
        // Uses CSS tooltip via data-tooltip attribute — handled by existing style.css
    }}

    function updateFavoriteStates() {{
        document.querySelectorAll('.favorite-btn').forEach(btn => {{
            const id = btn.getAttribute('data-anime-id');
            const active = isFavorite(id);
            btn.classList.toggle('active', active);
            const icon = btn.querySelector('.favorite-icon');
            if (icon) icon.textContent = active ? '♥' : '♡';
        }});
    }}

    // ============================================================
    // CONTEXT MENU
    // ============================================================
    function showContextMenu(x, y, card) {{
        contextTarget = card;
        const menu = document.getElementById('context-menu');
        menu.style.display = 'block';
        menu.style.left = Math.min(x, window.innerWidth - 200) + 'px';
        menu.style.top = Math.min(y, window.innerHeight - 120) + 'px';
    }}

    document.addEventListener('contextmenu', e => {{
        const card = e.target.closest('.all-anime-card');
        if (card) {{
            e.preventDefault();
            showContextMenu(e.clientX, e.clientY, card);
        }}
    }});

    document.getElementById('ctx-anilist').addEventListener('click', () => {{
        if (contextTarget) window.open(contextTarget.dataset.siteUrl, '_blank');
        document.getElementById('context-menu').style.display = 'none';
    }});

    document.getElementById('ctx-9anime').addEventListener('click', () => {{
        if (contextTarget) {{
            const eng = contextTarget.dataset.english || contextTarget.dataset.name;
            window.open(`https://9animetv.to/search?keyword=${{encodeURIComponent(eng)}}`, '_blank');
        }}
        document.getElementById('context-menu').style.display = 'none';
    }});

    document.getElementById('ctx-favorite').addEventListener('click', () => {{
        if (contextTarget) toggleFavorite(contextTarget.dataset.id);
        document.getElementById('context-menu').style.display = 'none';
    }});

    document.addEventListener('click', () => {{
        document.getElementById('context-menu').style.display = 'none';
    }});

    // ============================================================
    // UTIL
    // ============================================================
    function escapeHtml(str) {{
        if (!str) return '';
        return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }}

    function escapeAttr(str) {{
        if (!str) return '';
        return str.replace(/"/g, '&quot;');
    }}

    // ============================================================
    // EVENT LISTENERS
    // ============================================================
    let searchTimer;
    document.getElementById('search-input').addEventListener('input', () => {{
        clearTimeout(searchTimer);
        searchTimer = setTimeout(renderAnime, 200);
    }});

    document.getElementById('sort-select').addEventListener('change', renderAnime);
    document.getElementById('season-select').addEventListener('change', () => {{
        // When user picks a season manually, disable the "current season default" filter in sort
        const sortEl = document.getElementById('sort-select');
        if (sortEl.value === 'season_popular' && document.getElementById('season-select').value) {{
            // Season is now explicitly filtered, keep sort as popular
        }}
        renderAnime();
    }});

    document.getElementById('poster-toggle').addEventListener('change', e => {{
        document.getElementById('anime-grid').classList.toggle('poster-mode', e.target.checked);
    }});

    // ============================================================
    // INIT
    // ============================================================
    document.getElementById('catalog-stats').textContent =
        `${{CATALOG_TOTAL.toLocaleString()}} anime in catalog · Updated {last_updated}`;

    renderAnime();
    </script>
</body>
</html>
"""
    return html


def main():
    if not os.path.exists(CATALOG_FILE):
        print(f"ERROR: {CATALOG_FILE} not found.")
        print("Run 'python scripts/fetch_all_anime.py --full' to build the initial catalog.")
        # Create a placeholder so the page can still be generated
        print("Creating empty placeholder catalog...")
        os.makedirs('data', exist_ok=True)
        with open(CATALOG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)

    with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    print(f"Loaded {len(catalog)} anime from catalog")

    html = generate_html(catalog)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Generated {OUTPUT_FILE} ({os.path.getsize(OUTPUT_FILE) // 1024} KB)")


if __name__ == '__main__':
    main()
