from datetime import datetime


def empty_to_none(value):
    value = value.strip() if isinstance(value, str) else value
    return value or None


def parse_date(value):
    value = empty_to_none(value)
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_time(value):
    if not value:
        return None

    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            pass

    return None


def upper(value):
    return empty_to_none(value.upper()) if value else None


def lower(value):
    return empty_to_none(value.lower()) if value else None


def proper(value):
    return empty_to_none(value.title()) if value else None
