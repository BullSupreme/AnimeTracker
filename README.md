# Anime Tracker v3.0 - GitHub Pages Edition

A beautiful, responsive anime tracking website that displays currently airing anime with automatic updates via GitHub Actions.

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
- 🎨 Colored rank badges (Gold/Silver/Bronze)
- ⭐ Favorites system (browser cookies)
- 📱 Fully responsive design
- 🔄 Automatic data updates twice daily
- 💫 Hover-only UI elements (favorites, ranks)
- 🚀 Fast custom tooltips

## 🛠 Manual Updates

```bash
python3 scripts/fetch_anime_data.py
python3 scripts/generate_html.py
```

## 🔗 GitHub Actions

The workflow automatically:
- Fetches fresh anime data from AniList API
- Generates updated static HTML
- Commits and deploys changes

Perfect for GitHub Pages hosting! 🎉