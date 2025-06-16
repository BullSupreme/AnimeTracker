# Anime Tracker

![Version](https://img.shields.io/badge/version-3.1-blue)
![Release](https://img.shields.io/badge/release-stable-green)
[![GitHub Pages](https://img.shields.io/badge/live-site-brightgreen)](https://bullsupreme.github.io/AnimeTracker/)

A beautiful, responsive anime tracking website that displays currently airing anime with automatic updates via GitHub Actions.

🔗 **[View Live Site](https://bullsupreme.github.io/AnimeTracker/)**

## 🚀 Features

**Automatic updates**: Runs twice daily (8 AM & 8 PM UTC)

## 📁 Files Included

- `index.html` - Main page (auto-generated)
- `css/style.css` - All styles with rank colors
- `js/script.js` - JavaScript functionality
- `data/` - JSON data files
- `scripts/` - Python automation scripts
- `.github/workflows/` - Auto-update workflow

## ✨ Features

- 🌟 Today's & Tomorrow's anime releases
- 📺 Next airing episodes with future dates
- 🎨 Colored User Tracking rank badges (Gold/Silver/Bronze)
- ⭐ Favorites system (browser cookies)
- 📱 Fully responsive design
- 🔄 Automatic data updates twice daily
- 💫 Hover UI elements (favorites, ranks)
- 🚀 Fast custom tooltips

## 🔗 GitHub Actions

The workflow automatically:
- Fetches fresh anime data from AniList API
- Generates updated static HTML
- Commits and deploys changes

Perfect for GitHub Pages hosting! 🎉

## 📚 Version History

### Version 3.1 (Current)
- Bug fixes and performance improvements
- Enhanced next episode tracking logic.

### Version 3.0
- Enhanced UI with hover-only elements (favorites, rank badges)
- Calendar feature for organized viewing
- Dedicated Favorites tab with improved layout
- Next season anime preview section
- GitHub Pages deployment with GitHub Actions for automatic updates

### Version 2.0
- Complete refactor to Python backend with HTML/JavaScript/CSS frontend
- Basic favorite functionality with browser storage
- Full current season anime library using AniList API
- PyInstaller executable for easy distribution to friends
- Responsive web-based interface
- Distrubuted to Friends only using Pyinstaller .exe conversion.

### Version 1.0
- Small Python application using CustomTkinter module for UI
- Basic weekly anime display with streaming links
- MyAnimeList API integration
- Desktop application for personal use