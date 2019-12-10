from datetime import datetime


def format_date(date: datetime, fmt: str = '%Y-%m-%d') -> str:
    return date.strftime(fmt)


def date_from_string(date: str, fmt: str = '%Y-%m-%d') -> datetime.date:
    return datetime.strptime(date, fmt).date()
