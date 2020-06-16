"Tests for the time module."

import datetime

import pytest # type: ignore

from mvcs.error import Error
from mvcs.time import datetime_from_str, timedelta_from_str, timedelta_to_path_str

@pytest.mark.parametrize("dt_str,expected", [
    # Either "T" or space should work as the date/time separator
    ("1970-01-01 00:00:00", datetime.datetime(1970, 1, 1)),
    ("1970-01-01T00:00:00", datetime.datetime(1970, 1, 1)),
    ("1999-12-31 23:59:59", datetime.datetime(1999, 12, 31, hour=23, minute=59, second=59)),
    ("1999-12-31T23:59:59", datetime.datetime(1999, 12, 31, hour=23, minute=59, second=59)),
    # MINYEAR (1) should work if it's in %Y format
    ("0001-01-01T00:00:00", datetime.datetime(1, 1, 1)),
    # Zero-padding is optional
    ("1970-1-01T00:00:00", datetime.datetime(1970, 1, 1)),
    ("1970-01-1T00:00:00", datetime.datetime(1970, 1, 1)),
    ("1970-01-01T0:00:00", datetime.datetime(1970, 1, 1)),
    ("1970-01-01T00:0:00", datetime.datetime(1970, 1, 1)),
    ("1970-01-01T00:00:0", datetime.datetime(1970, 1, 1)),
])
def test_datetime_from_str(dt_str, expected):
    "datetime strings are parsed as expected."
    dt_parsed = datetime_from_str(dt_str)
    assert dt_parsed == expected

@pytest.mark.parametrize("dt_str", [
    # Cannot be empty
    "",
    # Leading/trailing space is invalid
    " 1970-01-01T00:00:00",
    "1970-01-01T00:00:00 ",
    # Out of range values are invalid
    "0000-01-01T00:00:00",
    "1970-00-01T00:00:00",
    "1970-13-01T00:00:00",
    "1970-13-01T00:00:00",
    "1970-02-00T00:00:00",
    "1970-02-29T00:00:00",
    "1970-01-01T24:00:00",
    "1970-01-01T00:60:00",
    "1970-01-01T00:00:60",
    # Year requires %Y format (CCYY)
    "999-01-01T00:00:00",
])
def test_datetime_from_str_invalid(dt_str):
    "Parsing an invalid datetime string raise an error."
    with pytest.raises(Error):
        datetime_from_str(dt_str)

@pytest.mark.parametrize("td_str,expected", [
    ("00:00:00", datetime.timedelta()),
    ("00:01:00", datetime.timedelta(minutes=1)),
    ("01:00:00", datetime.timedelta(hours=1)),
    ("23:59:59", datetime.timedelta(hours=23, minutes=59, seconds=59)),
    # Hours are optional
    ("00:00", datetime.timedelta()),
    ("01:00", datetime.timedelta(minutes=1)),
    ("59:59", datetime.timedelta(minutes=59, seconds=59)),
    # Minutes are optional
    ("00", datetime.timedelta()),
    ("59", datetime.timedelta(seconds=59)),
    # Zero-padding is optional
    ("0", datetime.timedelta()),
    ("0:0", datetime.timedelta()),
    ("0:0:0", datetime.timedelta()),
    ("1", datetime.timedelta(seconds=1)),
    ("1:1", datetime.timedelta(minutes=1, seconds=1)),
    ("1:1:1", datetime.timedelta(hours=1, minutes=1, seconds=1)),
    # Values are not limited to %H:%M:%S format
    ("99", datetime.timedelta(minutes=1, seconds=39)),
    ("999:99:99", datetime.timedelta(days=41, hours=16, minutes=40, seconds=39)),
    # Overall value can be negative to be that far in the past
    ("-01", -1 * datetime.timedelta(seconds=1)),
    ("-01:01", -1 * datetime.timedelta(minutes=1, seconds=1)),
    ("-01:01:01", -1 * datetime.timedelta(hours=1, minutes=1, seconds=1)),
])
def test_timedelta_from_str(td_str, expected):
    "timedelta strings are parsed as expected."
    td_parsed = timedelta_from_str(td_str)
    assert td_parsed == expected

@pytest.mark.parametrize("td_str", [
    # Values cannot be empty
    "",
    ":00",
    ":00:00",
    # Fractional values aren't supported
    "0.5",
    "0.5:00",
    "0.5:00:00",
    # Negative values (except at the beginning) aren't supported
    "0:-1",
    "0:-1:0",
    # Format is limited to hours (days/years don't work)
    "0:0:0:0",
])
def test_timedelta_from_str_invalid(td_str):
    "Parsing an invalid timedelta string raise an error."
    with pytest.raises(Error):
        timedelta_from_str(td_str)

@pytest.mark.parametrize("delta_t,expected", [
    (datetime.timedelta(), "0h00m00s"),
    (datetime.timedelta(seconds=1), "0h00m01s"),
    (datetime.timedelta(seconds=59), "0h00m59s"),
    (datetime.timedelta(minutes=1), "0h01m00s"),
    (datetime.timedelta(hours=1), "1h00m00s"),
    (datetime.timedelta(hours=99, minutes=59, seconds=59), "99h59m59s"),
    # Unconventional/overflowing values are displayed correctly
    (datetime.timedelta(minutes=2, seconds=123), "0h04m03s"),
    # Displayed time never goes negative
    (-1 * datetime.timedelta(days=1), "0h00m00s"),
])
def test_timedelta_to_path_str(delta_t, expected):
    "Filename segments from timedelta objects are constructed as expected."
    path = timedelta_to_path_str(delta_t)
    assert path == expected
