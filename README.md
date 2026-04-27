# Anime Tracker

![Version](https://img.shields.io/badge/version-3.3-blue)
![Release](https://img.shields.io/badge/release-stable-green)
[![GitHub Pages](https://img.shields.io/badge/live-site-brightgreen)](https://bullsupreme.github.io/AnimeTracker/)

A static anime tracking site generated from AniList data and deployed with GitHub Pages.

[View Live Site](https://bullsupreme.github.io/AnimeTracker/)

## Overview

This repository is built around scheduled data fetches plus static HTML generation.
The Python scripts pull anime data, process it into JSON, and generate the site pages used by GitHub Pages.

## Features

- Today and Tomorrow release lists for currently airing anime
- Calendar view with `All Anime` and `Favorites Only` modes
- Recently finished anime section
- Upcoming seasonal anime preview section
- Favorites saved in browser cookies
- All-anime catalog page with client-side search, sorting, and season filters
- AniList popularity badges and hover-driven card UI
- Per-title custom link overrides stored locally in the browser
- Static output with no server required for GitHub Pages hosting

## Generated Pages

- `index.html` - Main tracker page
- `all-anime.html` - Full anime catalog page

## Project Structure

- `css/style.css` - Site styling
- `js/script.js` - Main client-side behavior
- `data/` - Generated JSON data files used by the site
- `scripts/fetch_anime_data.py` - Fetches airing, recently finished, and upcoming seasonal data
- `scripts/generate_html.py` - Builds `index.html`
- `scripts/fetch_all_anime.py` - Maintains the full anime catalog
- `scripts/generate_all_anime_html.py` - Builds `all-anime.html`
- `.github/workflows/update-anime-data.yml` - Twice-daily data/site refresh
- `.github/workflows/update-all-anime-catalog.yml` - Monthly catalog refresh

## Automation

GitHub Actions handles two scheduled jobs:

- `update-anime-data.yml` runs twice daily at `08:00` and `20:00` UTC
- `update-all-anime-catalog.yml` runs monthly on the `1st` at `06:00` UTC

These workflows fetch fresh data, regenerate the static pages, and commit the updates back to the repository.

## Local Usage

Install dependencies:

```bash
pip install -r requirements.txt
```

Refresh the main site data and rebuild `index.html`:

```bash
python scripts/fetch_anime_data.py
python scripts/generate_html.py
```

Build or refresh the full catalog page:

```bash
python scripts/fetch_all_anime.py --full
python scripts/generate_all_anime_html.py
```

For regular local updates after the initial full catalog build, the incremental mode is enough:

```bash
python scripts/fetch_all_anime.py
python scripts/generate_all_anime_html.py
```

## Deployment Note

The clean version is intended for static hosting on GitHub Pages.
If you run it outside that setup, you are responsible for scheduling the fetch/generation scripts yourself.

## Version History

### Version 3.3 (Current)

- Removed Rankings page and external ranking data sources
- Simplified the codebase by removing ranking workflows and scripts
- Kept AniList popularity rank badges on anime cards
- Streamlined server endpoints and removed ranking-related code

### Version 3.2

- Enhanced AniTrendz scraping with JS rendering via `requests-html`
- Removed outdated hardcoded rankings in favor of current fetched data
- Improved title matching using dynamic variations from `anime_data.json`
- Fixed scheduled GitHub Actions push failures with `git pull --rebase`

### Version 3.0 - 3.1

- Enhanced UI with hover-only elements
- Added calendar browsing
- Added Favorites tab improvements
- Added next-season anime preview support
- Moved to GitHub Pages deployment with automated updates

### Version 2.0

- Refactored to a Python data pipeline with HTML, CSS, and JavaScript frontend
- Added basic favorites with browser storage
- Added a full current-season anime library using AniList API
- Built a PyInstaller executable for friend distribution

### Version 1.0

- Started as a small CustomTkinter desktop app
- Displayed weekly anime with streaming links
- Used MyAnimeList API integration
