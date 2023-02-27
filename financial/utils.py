import datetime


def utcnow() -> datetime.datetime:
    """Returns current date and time in UTC with tz set."""
    return datetime.datetime.now(datetime.timezone.utc)
