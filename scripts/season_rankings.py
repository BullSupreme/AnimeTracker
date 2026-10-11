"""Stable popularity tiers within each AniList season and year."""


def build_season_rankings(catalog):
    seasons = {}
    for anime in catalog:
        season = anime.get('season')
        year = anime.get('season_year')
        if season and year:
            seasons.setdefault((season, year), {})[anime['id']] = anime
    rankings = {}
    for (season, year), entries in seasons.items():
        ordered = sorted(entries.values(), key=lambda a: (-(a.get('popularity') or 0), a['id']))
        for rank, anime in enumerate(ordered, 1):
            tier = 'LR' if rank == 1 else 'UR' if rank <= 3 else 'SSR' if rank <= 6 else 'SR' if rank <= 10 else 'R' if rank <= 15 else None
            rankings[anime['id']] = {'rank': rank, 'tier': tier, 'season': season, 'year': year}
    return rankings


def rarity_attrs(ranking):
    if not ranking or not ranking['tier']:
        return ''
    label = f"{ranking['tier']} #{ranking['rank']}"
    title = f"{ranking['season'].title()} {ranking['year']} popularity rank #{ranking['rank']}"
    return (f' data-rarity="{ranking["tier"]}" data-season-rank="{ranking["rank"]}"'
            f' data-rarity-label="{label}" data-rarity-title="{title}"')
