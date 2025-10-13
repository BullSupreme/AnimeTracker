# Claude Code Memory - Anime Tracker Project

## Project Overview
This is an anime tracking web application that displays currently airing anime with release schedules. The project fetches data from the AniList API and generates a static HTML site served by a Python server.

## Project Structure
```
AnimeTracker/
├── data/                           # JSON data files
│   ├── anime_data.json            # Main anime data from API
│   ├── other_anime_sorted.json    # Processed "Other" section data
│   ├── metadata.json              # Last updated info and dates
│   ├── custom_links.json          # User-customized streaming links
│   ├── manual_streaming_links.json
│   └── 9anime_links.json          # 9anime watch URLs (manually populated)
├── scripts/
│   ├── fetch_anime_data.py        # Fetches data from AniList API
│   └── generate_html.py           # Generates static HTML from JSON
├── css/style.css                  # Main stylesheet
├── js/script.js                   # Frontend JavaScript
├── index.html                     # Generated static HTML
├── game/                          # Anime gacha game component
│   ├── index.html                # Game HTML file
│   ├── script.js                 # Game JavaScript
│   └── style.css                 # Game styles
└── server.py                      # Development server
```

## Key Components

### Data Flow
1. `fetch_anime_data.py` → Fetches from AniList GraphQL API → `data/*.json`
2. `generate_html.py` → Reads JSON data → Generates `index.html`
3. `server.py` → Serves static files and provides `/refresh` and `/generate` endpoints

### HTML Generation Logic (generate_html.py:240-248)
```python
# Use next airing date if available, otherwise use release date
next_airing = anime.get('next_airing_date')
next_episode_num = anime.get('next_episode_number', anime['episode'])
if next_airing:
    release_date_display = f"Next: {next_airing}"
    episode_display = f"Next Episode {next_episode_num}"
else:
    release_date_display = anime.get('release_date', 'Ongoing')
    episode_display = f"Episode {anime['episode']}"
```

### Data Processing (fetch_anime_data.py:414-423)
```python
# Always prioritize original next airing data when available
final_next_airing_date = original_next_date
final_next_episode = original_next_episode

# Use fallbacks only if original data doesn't exist
if not final_next_airing_date:
    final_next_airing_date = next_airing_date
if not final_next_episode:
    final_next_episode = episode_number
```

## Recent Major Changes

### 9anime Button Integration (2025-10-12)
**Purpose**: Add direct 9anime links next to AniList buttons for each anime card
**Implementation**:
- Created `data/9anime_links.json` to store 9anime URLs
- Added green "9anime" button next to "anilist.co" button in all anime sections
- Button only appears when URL exists in 9anime_links.json
- CSS styling: `.nine-anime-btn` with green (#10b981) background

**Manual Process** (automated scraping doesn't work reliably):
1. Google "9anime [English Title]"
2. Copy first URL to `9anime_links.json`
3. Run `python scripts/generate_html.py`
4. See [HOW_TO_ADD_9ANIME_LINKS.md](HOW_TO_ADD_9ANIME_LINKS.md)

**Key Files**:
- `data/9anime_links.json` - Manually maintained URL database
- `css/style.css:1204-1225` - Button styling
- `generate_html.py` - Loads and inserts buttons in all sections
- `scripts/fetch_9anime_links.py` - Attempted automation (doesn't work reliably)

## Recent Major Changes

### Next Airing Episode Feature
**Problem**: "Other Animes" section showed past episode dates instead of upcoming episodes
**Solution**: Modified data processing to preserve and display `nextAiringEpisode` data from AniList API

**Key Changes:**
1. **fetch_anime_data.py**: Preserve `next_airing_date` and `next_episode_number` fields
2. **generate_html.py**: Display "Next Episode X" and "Next: YYYY-MM-DD" format when available
3. **Data synchronization**: Ensure both main and AnimeTracker-Clean directories have same data

**Result**: 32+ anime now show "Next Episode 12" and "Next: 2025-06-20" instead of "Episode 11" and "2025-06-13"

### Recently Finished Anime Feature
**Problem**: Seasonal anime watchers can't watch anime as they air and need recently finished shows to stay visible
**Solution**: Added a new "Recently Finished" section that shows anime completed within the last 2 weeks

**Key Changes:**
1. **fetch_anime_data.py**: 
   - Track anime that finished within last 14 days with `recently_finished` flag
   - Create separate `data/recently_finished_anime.json` file
   - Modified `sort_other_anime()` to separate recently finished from ongoing anime
2. **generate_html.py**: 
   - Load recently finished anime data
   - Add new section between "Other Animes" and "Next Seasonal Anime"
   - Display total episodes and finish date
3. **css/style.css**: 
   - Added `.recently-finished-section` styling with green theme
   - Similar visual style to upcoming anime section

**Result**: Anime that finished airing within the last 2 weeks now appear in a dedicated section with finish date and total episode count

### Genre Data Integration
**Problem**: Anime genre data was not being included in the processed JSON output for use in other applications
**Solution**: Modified data processing to include genre information from AniList API

**Key Changes:**
1. **fetch_anime_data.py**: Added `genres` field to the processed anime data output (line 719)
2. **Data Structure**: Each anime now includes a `genres` array with genre strings from AniList
3. **API Integration**: Existing GraphQL queries already fetched genres - just needed to include in output

**Result**: All anime entries now include genre data like `["Action", "Adventure", "Comedy"]` for use in external applications like the gacha game

### Anime Gacha Game Integration
**Purpose**: Interactive gacha game that uses anime data from the tracker for character collection
**Location**: `/game/` directory with modular architecture (refactored 2025-08-16)
**Documentation**: See `game/CLAUDE.md` for detailed game-specific documentation

**Key Features:**
1. **Data Integration**: Uses anime data from `data/*.json` files for character pool
2. **Genre System**: Leverages genre data added to anime entries for rarity/type classification
3. **Modular Architecture**: Separate managers for summoning, battles, collections, career mode
4. **7-Tier Rarity System**: LR, TUR, UR, SSR, SR, R, N based on anime popularity
5. **Battle System**: Genre-based battles with idle mechanics and stat-based resolution
6. **Career Mode**: Anime progression simulation with Hall of Fame for generated cards

**Recent Refactoring (2025-08-16):**
- Split monolithic 6000+ line script into focused modules (~200-500 lines each)
- Separated CSS into system-specific files for better maintainability
- Preserved all functionality while improving developer experience

### UI Improvements
- **Hover Effects**: Fixed favorite icon and rank badge to only show on hover (not always visible)
- **Visual Fixes**: Removed blinking line at bottom of posters by eliminating scale transform
- **Custom Tooltips**: Replaced browser title attributes with faster CSS/JS tooltips for popularity ranks

## Development Workflows

### Data Refresh
1. Run `python3 scripts/fetch_anime_data.py` (may timeout due to API limits)
2. Run `python3 scripts/generate_html.py` to update HTML
3. Alternative: Visit `http://localhost:8000/refresh` (fetches + generates)

### Server Commands
- `python3 server.py` - Start development server on port 8000
- Server endpoints:
  - `/` - Main anime tracker
  - `/refresh` - Fetch fresh data from API
  - `/generate` - Regenerate HTML from existing data
  - `/game/` - Anime gacha game (located in \game\ directory)

### Directory Synchronization
- **Main directory**: `/mnt/c/Users/Louis/PythonProjects/AnimeTracker/` (development/working directory)
- **Clean directory**: `/mnt/c/Users/Louis/PythonProjects/AnimeTracker/AnimeTracker-Clean/` (GitHub repository)
- When updating data, ensure both directories have same JSON files
- Run HTML generation in both directories for consistency
- **Important**: The Clean directory is the GitHub repo - keep it updated with all changes

## Common Issues

### Browser Caching
- Users may see old content due to browser cache
- Solution: Hard refresh (Ctrl+F5) or clear cache
- HTML files are static, so changes require regeneration + refresh

### API Timeouts
- AniList API frequently times out during data fetching
- Workaround: Copy data files between directories when API fails
- Next airing data is preserved in existing JSON files

### Data Synchronization
- Server runs from main directory, not AnimeTracker-Clean
- Always update main directory data when making changes
- Copy updated files: `cp AnimeTracker-Clean/data/*.json data/`
- **Remember**: Clean directory = GitHub repo, so sync changes there for version control

## Key File Paths
- Main data: `/mnt/c/Users/Louis/PythonProjects/AnimeTracker/data/other_anime_sorted.json`
- Clean data: `/mnt/c/Users/Louis/PythonProjects/AnimeTracker/AnimeTracker-Clean/data/other_anime_sorted.json`
- HTML generation: Line 240-248 in `scripts/generate_html.py`
- Server serving: Serves from main directory (not Clean)

## Testing Commands
- `rg -c "Next Episode" index.html` - Count next episode entries
- `rg -A 5 "anime_name" data/other_anime_sorted.json` - Check anime data
- `rg -A 3 "Next Episode" index.html` - Verify HTML generation

## Notes for Future Development
- Always test in both directories when making changes
- API data contains `nextAiringEpisode` with `episode` and `airingAt` timestamp
- HTML generation logic prioritizes next airing data over calculated dates
- Static site means changes require regeneration, not just data updates
- Game component uses anime data for character pool and gacha mechanics
- Genre data integration enables better game classification and rarity systems

## Current Status
- **Main Tracker**: Fully functional with next airing episodes and recently finished anime
- **Game Component**: Located in `/game/` directory, ready for bug fixes and refinements
- **Data Integration**: Genre data successfully integrated for external application use
- **Ready for**: Bug fixing phase for game component