import re
from datetime import datetime, date, time
import utils.time_utils as time_utils

def test_iso_format_date_default():
    d = date(2024, 6, 1)
    assert time_utils.iso_format_date(d) == "2024-06-01"

def test_iso_format_date_custom_sep():
    d = date(2024, 6, 1)
    assert time_utils.iso_format_date(d, date_separator="") == "20240601"

def test_iso_format_time_default():
    t = time(13, 5, 9)
    assert time_utils.iso_format_time(t) == "13:05:09"

def test_iso_format_time_custom_sep():
    t = time(13, 5, 9)
    assert time_utils.iso_format_time(t, time_separator="") == "130509"

def test_iso_format_datetime_default():
    dt = datetime(2024, 6, 1, 13, 5, 9)
    assert time_utils.iso_format_datetime(dt) == "2024-06-01T13:05:09"

def test_iso_format_datetime_custom_seps():
    dt = datetime(2024, 6, 1, 13, 5, 9)
    assert time_utils.iso_format_datetime(dt, date_separator="", datetime_separator="_", time_separator="") == "20240601_130509"

def test_get_date_stamp_matches_today():
    today = date.today()
    assert time_utils.get_date_stamp() == today.strftime("%Y-%m-%d")

def test_get_time_stamp_format():
    # Match HH:MM:SS
    stamp = time_utils.get_time_stamp()
    assert re.match(r"\d{2}:\d{2}:\d{2}", stamp)

def test_get_datetime_stamp_format():
    # Match YYYY-MM-DDTHH:MM:SS
    stamp = time_utils.get_datetime_stamp()
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", stamp)