"""Small continuation badges using anime prequels and explicit title wording."""
import re
from datetime import date
from html import escape

SEASONS = ('WINTER', 'SPRING', 'SUMMER', 'FALL')
RELATION_FIELDS = '''relations { edges { relationType node {
    id type title { romaji english } season seasonYear
} } }'''


def continuation_metadata(raw):
    relations = raw.get('relations') or {}
    prequels = [edge['node'] for edge in relations.get('edges', []) or []
                if edge and edge.get('relationType') == 'PREQUEL'
                and (edge.get('node') or {}).get('type') == 'ANIME']
    return {
        'prequels': prequels if 'relations' in raw else raw.get('prequels', []),
        'season': raw.get('season'),
        'season_year': raw.get('seasonYear', raw.get('season_year')),
        'status': raw.get('status'),
    }


def season_index(season, year):
    season = str(season or '').upper()
    if season in SEASONS and isinstance(year, int):
        return year * 4 + SEASONS.index(season)
    return None


def get_continuation_badges(anime, today=None):
    today = today or date.today()
    titles = ' | '.join(str(anime.get(key) or '') for key in ('name', 'english_title'))
    for word, number in {'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5, 'sixth': 6}.items():
        titles = re.sub(r'\b' + word + r'(?=\s+(?:season|cour|part)\b)', str(number) + 'th', titles, flags=re.I)
    # Numbers must be attached to explicit continuation words, never bare title digits.
    part = re.search(r'\bpart\s*(\d+)\b', titles, re.I)
    cour = re.search(r'\b(\d+)(?:st|nd|rd|th)?\s*cour\b|\bcour\s*(\d+)\b', titles, re.I)
    season = re.search(r'\b(\d+)(?:st|nd|rd|th)?\s*season\b|\bseason\s*(\d+)\b', titles, re.I)
    started = season_index(anime.get('season'), anime.get('season_year'))
    # A later-released origin special does not make the original series a sequel.
    prequels = [p for p in anime.get('prequels') or []
                if started is None or season_index(p.get('season'), p.get('seasonYear')) is None
                or season_index(p.get('season'), p.get('seasonYear')) <= started]
    badges = []
    explicit_continuation = any(match and int(next(g for g in match.groups() if g)) > 1
                                for match in (season, part, cour))
    if prequels or explicit_continuation:
        names = [(p.get('title') or {}).get('english') or (p.get('title') or {}).get('romaji')
                 for p in prequels]
        detail = 'Follows: ' + ', '.join(n for n in names if n) if any(names) else 'Explicit continuation in the title'
        previous = {}
        for prequel in prequels:
            media_id = prequel.get('id')
            if isinstance(media_id, int) and media_id > 0:
                title = prequel.get('title') or {}
                previous[media_id] = dict(url=f'https://anilist.co/anime/{media_id}/',
                                         title=title.get('english') or title.get('romaji') or f'Anime {media_id}')
        badges.append(dict(key='sequel', label='Sequel', detail=detail, previous=list(previous.values())))
    current = today.year * 4 + (today.month - 1) // 3
    if anime.get('status') == 'RELEASING' and started is not None and started < current:
        label = 'From Last Season' if started == current - 1 else 'Continuing'
        detail = f'Still airing; began in {str(anime["season"]).title()} {anime["season_year"]}'
        badges.append(dict(key='continuing', label=label, detail=detail))
    return badges


def continuation_html(anime):
    badges = anime.get('continuation_badges')
    if badges is None:
        badges = get_continuation_badges(anime)
    if not badges:
        return ''
    return '<div class="continuation-badges" aria-label="Series continuation">' + ''.join(
        render_badge(badge) for badge in badges) + '</div>'


def render_badge(badge):
    attrs = (f'class="continuation-badge continuation-{badge["key"]}"'
             f' title="{escape(badge["detail"], quote=True)}"')
    label = escape(badge['label'])
    previous = badge.get('previous') or []
    if len(previous) == 1:
        return (f'<a {attrs} href="{escape(previous[0]["url"], quote=True)}"'
                f' target="_blank" rel="noopener noreferrer"'
                f' aria-label="Open preceding anime: {escape(previous[0]["title"], quote=True)}">{label}</a>')
    if len(previous) > 1:
        links = ''.join(f'<a href="{escape(p["url"], quote=True)}" target="_blank"'
                        f' rel="noopener noreferrer">{escape(p["title"])}</a>' for p in previous)
        return (f'<details class="previous-anime-picker"><summary {attrs}>{label}</summary>'
                f'<div class="previous-anime-links">{links}</div></details>')
    return f'<span {attrs} tabindex="0">{label}</span>'
