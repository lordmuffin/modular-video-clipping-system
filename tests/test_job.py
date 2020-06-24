"Tests for the job module."

from pathlib import Path
import datetime

import pytest # type: ignore

from mvcs.config import Config, Replace
from mvcs.error import Error
from mvcs.job import Clip, Job, Video

@pytest.mark.parametrize("data,expected", [
    # Times can be specified in any parsable format
    (
        {"time": "0 - 10", "title": "test"},
        Clip(
            end=datetime.timedelta(seconds=10),
            start=datetime.timedelta(),
            title="test",
        ),
    ),
    (
        {"time": "100 - 2:00", "title": "test"},
        Clip(
            end=datetime.timedelta(minutes=2),
            start=datetime.timedelta(seconds=100),
            title="test",
        ),
    ),
    # Leading/trailing/internal spaces in the time are optional
    (
        {"time": "0-10", "title": "test"},
        Clip(
            end=datetime.timedelta(seconds=10),
            start=datetime.timedelta(),
            title="test",
        ),
    ),
    (
        {"time": "  0    -   10 ", "title": "test"},
        Clip(
            end=datetime.timedelta(seconds=10),
            start=datetime.timedelta(),
            title="test",
        ),
    ),
    # Whitespace is preserved in the title
    (
        {"time": "0 - 10", "title": "  a  b   "},
        Clip(
            end=datetime.timedelta(seconds=10),
            start=datetime.timedelta(),
            title="  a  b   ",
        ),
    ),
])
def test_clip_from_dict(data, expected):
    "Clips are deserialized from dicts correctly."
    clip = Clip.from_dict(data)
    assert clip == expected

@pytest.mark.parametrize("data", [
    # Clip length must be positive and non-zero
    {"time": "60 - 1:00", "title": "test"},
    {"time": "1 - 0", "title": "test"},
    # Start time cannot be negative
    {"time": "-1 - 0", "title": "test"},
    # Time requires start and end
    {"time": "10", "title": "test"},
    {"time": "- 10", "title": "test"},
    {"time": "10 -", "title": "test"},
    # Time cannot be None/empty or unspecified
    {"time": None, "title": "test"},
    {"time": "", "title": "test"},
    {"title": "test"},
    # Title cannot be empty or unspecified
    {"time": "1 - 10", "title": ""},
    {"time": "1 - 10"},
])
def test_clip_from_dict_invalid(data):
    "Deserializing an invalid clip dict results in an error."
    with pytest.raises(Error):
        Clip.from_dict(data)

# pylint: disable=too-many-arguments
@pytest.mark.parametrize("clip,config,date,epoch,title,expected", [
    # Clip start time is relative to video time with epoch 0
    (
        Clip.from_dict({"time": "1-2", "title": "title"}),
        Config.default(),
        datetime.datetime(1970, 1, 1),
        datetime.timedelta(),
        "test",
        "1970-01-01 00-00-00 - t+0h00m01s - test - title.mkv",
    ),
    # Clip start time and video time are adjusted with positive epoch
    (
        Clip.from_dict({"time": "1-2", "title": "title"}),
        Config.default(),
        datetime.datetime(1970, 1, 1),
        datetime.timedelta(seconds=1),
        "test",
        "1970-01-01 00-00-01 - t+0h00m00s - test - title.mkv",
    ),
    # Clip start time and video time are adjusted with negative epoch
    (
        Clip.from_dict({"time": "1-2", "title": "title"}),
        Config.default(),
        datetime.datetime(1970, 1, 1),
        -1 * datetime.timedelta(seconds=1),
        "test",
        "1969-12-31 23-59-59 - t+0h00m02s - test - title.mkv",
    ),
    # Clip start time saturates at 0 when it is before the epoch
    (
        Clip.from_dict({"time": "1-2", "title": "title"}),
        Config.default(),
        datetime.datetime(1970, 1, 1),
        datetime.timedelta(seconds=3),
        "test",
        "1970-01-01 00-00-03 - t+0h00m00s - test - title.mkv",
    ),
    # Problematic characters are munged and lowercased
    (
        Clip.from_dict({"time": "0-1", "title": "THIS? is/bad"}),
        Config.default(),
        datetime.datetime(1970, 1, 1),
        datetime.timedelta(),
        "NOT/VERY|GOOD<AT>\\ALL:*\"HERE?",
        "1970-01-01 00-00-00 - t+0h00m00s - not-very-good-at--all---here- - this- is-bad.mkv",
    ),
    # The output filename respects the config
    (
        Clip.from_dict({"time": "1-2", "title": "title"}),
        Config.default()._replace(
            filename_replace=Replace.from_dict({" ": "_"}),
            output_ext="mp4",
        ),
        datetime.datetime(1970, 1, 1),
        datetime.timedelta(),
        "test",
        "1970-01-01_00-00-00_-_t+0h00m01s_-_test_-_title.mp4",
    ),
])
def test_clip_path_str(clip, config, date, epoch, title, expected):
    "Getting the filename for a clip works as expected."
    path = clip.path_str(config, date, epoch, title)
    assert path == expected

@pytest.mark.parametrize("data,expected", [
    # Values are deserialized into expected types
    (
        {
            "clips": [
                {
                    "time": "0-1",
                    "title": "clip1",
                },
                {
                    "time": "1-2",
                    "title": "clip2",
                },
            ],
            "date": "1970-01-01T00:00:00",
            "epoch": "1:02:03",
            "title": "test",
        },
        Video(
            clips=[
                Clip(
                    end=datetime.timedelta(seconds=1),
                    start=datetime.timedelta(),
                    title="clip1",
                ),
                Clip(
                    end=datetime.timedelta(seconds=2),
                    start=datetime.timedelta(seconds=1),
                    title="clip2",
                ),
            ],
            date=datetime.datetime(1970, 1, 1),
            epoch=datetime.timedelta(hours=1, minutes=2, seconds=3),
            title="test",
        ),
    ),
    # Clips and epoch can be empty/undefined
    (
        {
            "clips": [],
            "date": "1970-01-01T00:00:00",
            "title": "test",
        },
        Video(date=datetime.datetime(1970, 1, 1), title="test"),
    ),
    (
        {
            "date": "1970-01-01T00:00:00",
            "title": "test",
        },
        Video(date=datetime.datetime(1970, 1, 1), title="test"),
    ),
])
def test_video_from_dict(data, expected):
    "Videos are deserialized from dicts correctly."
    video = Video.from_dict(data)
    assert video == expected

@pytest.mark.parametrize("data", [
    # Clips must be a list of dicts
    {
        "clips": "",
        "date": "1970-01-01T00:00:00",
        "title": "test",
    },
    {
        "clips": {},
        "date": "1970-01-01T00:00:00",
        "title": "test",
    },
    {
        "clips": [""],
        "date": "1970-01-01T00:00:00",
        "title": "test",
    },
    {
        "clips": [[]],
        "date": "1970-01-01T00:00:00",
        "title": "test",
    },
    # Date and title must be defined
    {"title": "test"},
    {"date": "1970-01-01T00:00:00"},
])
def test_video_from_dict_invalid(data):
    "Deserializing an invalid video dict results in an error."
    with pytest.raises(Error):
        Video.from_dict(data)

@pytest.mark.parametrize("config,path,expected", [
    # Default config works as expected
    (
        Config.default(),
        Path("/foo/bar/1970-01-01 00-00-00.mkv"),
        Video.from_dict({"date": "1970-01-01T00:00:00", "title": "video"}),
    ),
    # Filename handling config is respected
    (
        Config.default()._replace(
            filename_replace=Replace.from_dict({" ": "_"}),
            video_filename_format="%Y %m %d %H %M %S",
            video_ext="mp4",
        ),
        Path("/foo/bar/1970_01_01_02_03_04.mp4"),
        Video.from_dict({"date": "1970-01-01T02:03:04", "title": "video"}),
    ),
])
def test_video_from_path(config, path, expected):
    "Default videos are created from filesystem paths correctly."
    video = Video.from_path(config, path)
    assert video == expected

@pytest.mark.parametrize("config,path", [
    # Files that don't match the video filename format are rejected
    (Config.default(), Path("/foo/bar/baz.mkv")),
    # Files with the wrong extension are rejected
    (Config.default(), Path("/foo/bar/1970-01-01 00-00-00.mp4")),
])
def test_video_from_path_invalid(config, path):
    "Invalid paths raise an error."
    with pytest.raises(Error):
        Video.from_path(config, path)

@pytest.mark.parametrize("data,expected", [
    # Values are deserialized into expected types
    (
        {
            "output-dir": "/foo/bar",
            "video-dir": "baz/qux",
            "videos": [
                {"date": "1970-01-01T00:00:00", "title": "test1"},
                {"date": "1970-01-02T00:00:00", "title": "test2"},
            ],
        },
        Job(
            output_dir=Path("/foo/bar"),
            video_dir=Path("baz/qux"),
            videos=[
                Video(date=datetime.datetime(1970, 1, 1), title="test1"),
                Video(date=datetime.datetime(1970, 1, 2), title="test2"),
            ],
        ),
    ),
    # All fields are optional
    (
        {},
        Job(output_dir=Path("."), video_dir=Path(".")),
    ),
])
def test_job_from_dict(data, expected):
    "Jobs are deserialized from dicts correctly."
    job = Job.from_dict(Config.default(), data)
    assert job == expected

@pytest.mark.parametrize("data", [
    # videos must be a list of dicts
    {"videos": ""},
    {"videos": {}},
    {"videos": [""]},
    {"videos": [[]]},
])
def test_job_from_dict_invalid(data):
    "Deserializing an invalid job dict results in an error."
    with pytest.raises(Error):
        Job.from_dict(Config.default(), data)
