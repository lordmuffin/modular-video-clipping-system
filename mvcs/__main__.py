#!/usr/bin/env python3

# clip.py - create clips from OBS captures using ffmpeg and YAML
#
# USAGE
# -----
#
# Write a `clip.yaml` file describing where to find the OBS recordings, where to
# save the clips to, and provide a list of source videos and the clips that
# should be created. Run with `python3 clip.py`.
#
# EXAMPLE YAML
# ------------
#
# Here is a sample `clip.yaml`.
#
#     # Absolute path to the OBS recording directory (source videos)
#     video-dir: "c:/OBS Captures"
#
#     # Absolute path to the directory to save clips to (must already exist)
#     output-dir: "c:/OBS Clips"
#
#     # List of source videos (identified by timestamp-based naming convention)
#     videos:
#       - date: "2020-01-01T00:00:00"
#         # Virtual "start" time in the source video (for output filename)
#         epoch: "0"
#
#         # Base title for all clips (for output filename)
#         title: "video 1"
#
#         # List of clips to create
#         clips:
#           - time: "0 - 5:00"
#             title: "first five minutes of the video"
#           - time: "1:30:00 - 1:30:01"
#             title: "one second long"
#
#       - date: "2020-01-02T00:00:00"
#         epoch: "15"
#         title: "video 2"
#         clips:
#           - time: "0 - 15"
#             title: "before the epoch"
#           - time: "15 - 30"
#             title: "on the epoch"
#           - time: "30 - 45"
#             title: "after the epoch"
#
# This file references two source videos:
#
# 1. `c:/OBS Captures/2020-01-01 00-00-00.mkv`
# 2. `c:/OBS Captures/2020-01-02 01-00-00.mkv`
#
# From these, it will create five clips:
#
# 1. `c:/OBS Clips/2020-01-01 00-00-00 - t+0h00m00s - video 1 - first five minutes of the video.mkv`
# 2. `c:/OBS Clips/2020-01-01 00-00-00 - t+1h30m00s - video 1 - one second long.mkv`
# 3. `c:/OBS Clips/2020-01-02 00-00-15 - t+0h00m00s - video 2 - before the epoch.mkv`
# 4. `c:/OBS Clips/2020-01-02 00-00-15 - t+0h00m00s - video 2 - on the epoch.mkv`
# 5. `c:/OBS Clips/2020-01-02 00-00-15 - t+0h00m15s - video 2 - after the epoch.mkv`
#
# Note the timestamp used in the output filename reflects the epoch-adjusted
# virtual start time of the video, and the relative timestamp of each clip also
# accounts for the epoch (but will never be negative).

import datetime
import getopt
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Type, TypeVar

import yaml

class Error(Exception): pass

#==============================================================================
# Configuration
#==============================================================================

# Command-line configuration.
ConfigType = TypeVar("ConfigType", bound="Config")
class Config(NamedTuple):
    job_path: Path

    # Get configuration by parsing the program arguments.
    @classmethod
    def from_argv(cls: Type[ConfigType], argv: List[str]) -> ConfigType:
        config = {
            "job_path": Path("clip.yaml"),
        }

        try:
            opts, _args = getopt.getopt(argv[1:], "j:", longopts=[
                "job-path=",
            ])
        except getopt.GetoptError as ex:
            raise Error(ex)

        for opt, optarg in opts:
            if opt in ("-j", "--job-path"):
                config["job_path"] = Path(optarg)
            else:
                raise Error(f"unhandled option: {opt}")

        return cls(**config)

#==============================================================================
# Job execution
#==============================================================================

# Parse a `str` as a `datetime.datetime` object.
def datetime_from_str(s: str) -> datetime.datetime:
    for sep in ("T", " "):
        try:
            return datetime.datetime.strptime(s, f"%Y-%m-%d{sep}%H:%M:%S")
        except ValueError:
            pass
    raise Error(f"error parsing datetime: {s}")

# Parse a `str` as a `datetime.timedelta` object.
def timedelta_from_str(s: str) -> datetime.timedelta:
    if s.startswith("-"):
        s_positive = s.lstrip("-")
        sign_factor = -1
    else:
        s_positive = s
        sign_factor = 1

    for fmt in ("%H:%M:%S", "%M:%S", "%S"):
        try:
            dt = datetime.datetime.strptime(s_positive, fmt)
            return sign_factor * datetime.timedelta(
                hours=dt.hour,
                minutes=dt.minute,
                seconds=dt.second,
            )
        except ValueError:
            pass
    raise Error(f"error parsing timedelta: {s}")

# Get a filename-safe version of a `datetime.timedelta` object.
def timedelta_to_path_str(t: datetime.timedelta) -> str:
    seconds = max(0, t.total_seconds())
    hours = int(seconds / 3600)
    seconds = seconds - hours * 3600
    minutes = int(seconds / 60)
    seconds = int(seconds - minutes * 60)
    return f"{hours}h{minutes:02}m{seconds:02}s"

# Data about a single video clip that should be created.
ClipType = TypeVar("ClipType", bound="Clip")
class Clip(NamedTuple):
    # Source video timestamp for the end of the clip.
    end: datetime.timedelta
    # Source video timestamp for the start of the clip.
    start: datetime.timedelta
    # Clip title.
    title: str

    # Create a `Clip` from an untyped `dict` (YAML deserialization result).
    @classmethod
    def from_dict(cls: Type[ClipType], data: Dict[str, Any]) -> ClipType:
        (start, end) = (timedelta_from_str(t.strip()) for t in data["time"].split("-", maxsplit=1))
        clip = {
            "end": end,
            "start": start,
            "title": data["title"],
        }

        if clip["end"] <= clip["start"]:
            raise Error(f"bad clip start/end: {clip}")

        return cls(**clip)

    # Get the file name for a clip.
    def path_str(self, date: datetime.datetime, epoch: datetime.timedelta, title: str) -> str:
        date_str = (date + epoch).strftime("%Y-%m-%d %H:%M:%S")
        start_str = timedelta_to_path_str(self.start - epoch)
        path_str = f"{date_str} - T+{start_str} - {title} - {self.title}.mkv"
        return re.sub(r"[/\:]", "-", path_str.casefold())

    # Use ffmpeg to write the lossless video clip file.
    def write(self, src: Path, dst: Path):
        cmd = (
            "ffmpeg",
            "-ss", str(self.start.total_seconds()),
            "-i", str(src),
            "-c:a", "copy",
            "-c:v", "copy",
            "-map", "0:v",
            "-map", "0:a",
            "-t", str((self.end - self.start).total_seconds()),
            str(dst),
        )
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as ex:
            raise Error(ex)

# Data about an OBS capture video and clips to create from it.
VideoType = TypeVar("VideoType", bound="Video")
class Video(NamedTuple):
    # List of clips to create from the video.
    clips: List[Clip]
    # Video timestamp (recording start time)
    date: datetime.datetime
    # Virtual "start" time in the source video (for output filename)
    epoch: datetime.timedelta
    # Base title used for all clips from this video.
    title: str

    # Create a `Video` from an untyped `dict` (YAML deserialization result).
    @classmethod
    def from_dict(cls: Type[VideoType], data: Dict[str, Any]) -> VideoType:
        return cls(
            clips=[Clip.from_dict(clip) for clip in data.get("clips", [])],
            date=datetime_from_str(str(data["date"])),
            epoch=timedelta_from_str(str(data.get("epoch", 0))),
            title=data["title"],
        )

    # Create all requested clips from the video.
    def write_clips(self, src_dir: Path, dst_dir: Path):
        src = src_dir / self.date.strftime("%Y-%m-%d %H-%M-%S.mkv")
        if not src.is_file():
            raise Error(f"missing video file: {src}")

        for clip in self.clips:
            dst = dst_dir / clip.path_str(self.date, self.epoch, self.title)
            clip.write(src, dst)

# Data about the full set of videos and clips to produce from them.
JobType = TypeVar("JobType", bound="Job")
class Job(NamedTuple):
    # Directory where the clips should be written to.
    output_dir: Path
    # Directory where the source videos can be found.
    video_dir: Path
    # List of videos to create clips from.
    videos: List[Video]

    # Create a `Job` from an untyped `dict` (YAML deserialization result).
    @classmethod
    def from_yaml_file(cls: Type[JobType], path: Path) -> JobType:
        with path.open(encoding="utf-8") as file:
            data = yaml.safe_load(file)

        return cls(
            output_dir=Path(data.get("output-dir", ".")),
            video_dir=Path(data.get("video-dir", ".")),
            videos=[Video.from_dict(video) for video in data.get("videos", [])],
        )

    # Run the batch job and create all requested clips.
    def run(self):
        for video in self.videos:
            video.write_clips(self.video_dir, self.output_dir)

#==============================================================================
# Main script
#==============================================================================

# Main entrypoint.
def main(argv: List[str]) -> int:
    try:
        # Get configuration from command-line arguments
        config = Config.from_argv(argv)
        # Deserialize the YAML job playbook and run it
        job = Job.from_yaml_file(config.job_path)
        job.run()
    except Error as ex:
        print(f"error: {ex}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
