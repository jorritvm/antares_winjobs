from datetime import datetime, date, time

def iso_format_date(dt: date, date_separator: str = "-") -> str:
    """Return date stamp as YYYYMMDD."""
    return dt.strftime(f"%Y{date_separator}%m{date_separator}%d")

def iso_format_time(tm: time, time_separator: str = ":") -> str:
    """Return time as HHMMSS."""
    return tm.strftime(f"%H{time_separator}%M{time_separator}%S")

def iso_format_datetime(dt: datetime,
                        date_separator: str = "-",
                        datetime_separator: str = "T",
                        time_separator: str = ":") -> str:
    """Return datetime as YYYYMMDDTHHMMSS."""
    date_part = iso_format_date(dt.date(), date_separator)
    time_part = iso_format_time(dt.time(), time_separator)
    return f"{date_part}{datetime_separator}{time_part}"


def get_date_stamp(date_separator: str = "-") -> str:
    """Return date stamp for current day."""
    return iso_format_date(datetime.now().date(), date_separator)

def get_time_stamp(time_separator: str = ":") -> str:
    """Return time stamp for current time."""
    return iso_format_time(datetime.now().time(), time_separator)

def get_datetime_stamp(date_separator: str = "-",
                       datetime_separator: str = "T",
                       time_separator: str = ":") -> str:
    """Return date time stamp for current time."""
    return iso_format_datetime(datetime.now(), date_separator, datetime_separator, time_separator)
