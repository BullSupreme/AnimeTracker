"""Calendar-season countdown, independent of individual anime premieres."""
from datetime import date

SEASON_MONTHS = {'WINTER': 1, 'SPRING': 4, 'SUMMER': 7, 'FALL': 10, 'AUTUMN': 10}


def season_start(season, year):
    month = SEASON_MONTHS.get(str(season).upper())
    if month is None or not isinstance(year, int):
        return None
    try:
        return date(year, month, 1)
    except ValueError:
        return None


def countdown_label(start, today=None):
    days = (start - (today or date.today())).days
    if days < 0:
        return 'Season underway'
    if days == 0:
        return 'Starts today'
    return f'Starts in {days} ' + ('day' if days == 1 else 'days')
