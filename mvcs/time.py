"Time handling module."

import datetime

from mvcs.error import Error

def datetime_from_str(dt_s: str) -> datetime.datetime:
    "Parse a `str` as a `datetime.datetime` object."

    for sep in ("T", " "):
        try:
            return datetime.datetime.strptime(dt_s, f"%Y-%m-%d{sep}%H:%M:%S")
        except ValueError:
            pass
    raise Error(f"error parsing datetime: {dt_s}")

def timedelta_from_str(td_s: str) -> datetime.timedelta:
    "Parse a `str` as a `datetime.timedelta` object."

    if td_s.startswith("-"):
        s_positive = td_s.lstrip("-")
        sign_factor = -1
    else:
        s_positive = td_s
        sign_factor = 1

    for fmt in ("%H:%M:%S", "%M:%S", "%S"):
        try:
            dt_parsed = datetime.datetime.strptime(s_positive, fmt)
            return sign_factor * datetime.timedelta(
                hours=dt_parsed.hour,
                minutes=dt_parsed.minute,
                seconds=dt_parsed.second,
            )
        except ValueError:
            pass
    raise Error(f"error parsing timedelta: {td_s}")

def timedelta_to_path_str(delta_t: datetime.timedelta) -> str:
    "Get a filename-safe version of a `datetime.timedelta` object."

    seconds = max(0, delta_t.total_seconds())
    hours = int(seconds / 3600)
    seconds = seconds - hours * 3600
    minutes = int(seconds / 60)
    seconds = int(seconds - minutes * 60)
    return f"{hours}h{minutes:02}m{seconds:02}s"
