"""Content indicators based on explicit AniList metadata, not age-rating guesses."""
from html import escape

SEXUAL_THEME_TAGS = {
    'Anal Sex', 'Group Sex', 'Public Sex', 'Sex Toys', 'Erotic Piercings',
    'Hypersexuality', 'Psychosexual', 'Sexual Violence',
}


def content_metadata(raw):
    return {
        'genres': raw.get('genres') or [],
        'is_adult': raw.get('isAdult', raw.get('is_adult')),
        'tags': [dict(name=tag['name'], rank=tag.get('rank'))
                 for tag in raw.get('tags', []) or [] if isinstance(tag, dict)
                 and tag.get('name') in SEXUAL_THEME_TAGS | {'Nudity'}],
    }


def get_content_warnings(anime):
    tags = {tag['name'] for tag in anime.get('tags', []) or []
            if isinstance(tag, dict) and tag.get('name')}
    warnings = []
    if 'Ecchi' in (anime.get('genres') or []):
        warnings.append({'key': 'ecchi', 'label': 'Ecchi', 'detail': 'AniList genre: Ecchi (sexualized content / fanservice)'})
    if 'Nudity' in tags:
        warnings.append({'key': 'nudity', 'label': 'Nudity', 'detail': 'AniList content tag: Nudity'})
    sexual_tags = sorted(tags & SEXUAL_THEME_TAGS)
    if sexual_tags:
        warnings.append({'key': 'sexual', 'label': 'Sexual Themes', 'detail': 'AniList content tags: ' + ', '.join(sexual_tags)})
    if anime.get('is_adult') is True or anime.get('isAdult') is True:
        warnings.append({'key': 'adult', 'label': '18+ / Adult', 'detail': 'AniList marks this title as intended only for adult audiences'})
    return warnings


def content_warning_html(anime):
    warnings = get_content_warnings(anime)
    if not warnings:
        return ''
    badges = ''.join(
        f'<span class="content-warning content-warning-{warning["key"]}" tabindex="0"'
        f' title="{escape(warning["detail"], quote=True)}"'
        f' aria-label="{escape(warning["detail"], quote=True)}">{warning["label"]}</span>'
        for warning in warnings)
    return '<div class="content-warnings" aria-label="Content warnings">' + badges + '</div>'
