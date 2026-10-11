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
    if prequels or (season and int(next(g for g in season.groups() if g)) > 1):
        names = [(p.get('title') or {}).get('english') or (p.get('title') or {}).get('romaji')
                 for p in prequels]
        detail = 'Follows: ' + ', '.join(n for n in names if n) if any(names) else 'Explicit sequel season in the title'
        badges.append(dict(key='sequel', label='Sequel', detail=detail))
    if part and int(part.group(1)) > 1:
        badges.append(dict(key='part', label=f'Part {part.group(1)}', detail='Part number stated in the AniList title'))
    if cour:
        number = int(next(g for g in cour.groups() if g))
        if number > 1:
            suffix = 'th' if 10 <= number % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(number % 10, 'th')
            badges.append(dict(key='cour', label=f'{number}{suffix} Cour', detail='Cour number stated in the AniList title'))
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
        f'<span class="continuation-badge continuation-{badge["key"]}" tabindex="0"'
        f' title="{escape(badge["detail"], quote=True)}">{escape(badge["label"])}</span>'
        for badge in badges) + '</div>'
