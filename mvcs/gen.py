# Process incoming Request into YAML???

# More realistically a YAML Function/class for ingesting incoming data into yaml.

# Need something generic overall

# Also specific for our format.

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

import os.path
from os.path import isfile, join
from os import listdir
import yaml
from datetime import datetime
from mvcs.time import datetime_from_str, timedelta_from_str, timedelta_to_path_str


def generate_template(document):
    # Example YAML
    data = {
        'video-dir': 'c:/OBS Captures',
        'output-dir': 'c:/OBS Clips',
        'videos': []
    }

    print(yaml.safe_dump(data))
    stream = open(document, 'w')
    yaml.safe_dump(data, stream)
    stream.close()

def check_template(document):
    print("Checking for template: " + str(document))
    if os.path.isfile(document):
        print('YAML File detected.')

    else:
        print('Generating the file for you.')
        generate_template(document)
        check_template(document)

# def path_str(self, date: datetime.datetime, epoch: datetime.timedelta, title: str) -> str:
#     date_str = (date + epoch).strftime("%Y-%m-%d %H:%M:%S")
#     start_str = timedelta_to_path_str(self.start - epoch)
#     path_str = f"{date_str} - T+{start_str} - {title} - {self.title}.mkv"
#     return re.sub(r"[/\:]", "-", path_str.casefold())

def current_time(format):

    if format == "%CCYY-%MM-%DD_%hh-%mm-%ss":
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    elif format == "%CCYY-%MM-%DD %hh-%mm-%ss":
        return datetime.now().strftime("%Y-%m-%d %H-%M-%S")

def latest_video(date_time, extension, path):
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    extension = [item for item in onlyfiles if extension in item]
    print(extension)

    youngest = max(dt for dt in extension if dt < date_time)
    print(os.path.splitext(youngest)[0])
    return os.path.splitext(youngest)[0]

def add_video(document, date_time, epoch, title):
    with open(document, "r") as f:
        contents = yaml.safe_load(f)

    # Check for existing video.

    if contents['videos']:
        for video in contents['videos']:
            if video['date'] == date_time:
                print("Found Existing Video.")

                return "Found Existing Video."
    
    else:
        # Add Video
        print("Before: ", contents)
        print(date_time)
        data = {
            'date': date_time,
            'epoch': epoch,
            'title': title,
            'clips': []
        }

        contents['videos'].append(data)
        print("After: ", contents)

        with open(document, "w") as f:
            yaml.safe_dump(contents, f)

        return date_time

def add_clip(document, latest_video, window, title):
    with open(document, "r") as f:
        contents = yaml.safe_load(f)

    data = {
        'time': window,
        'title': title
    }

    for item in contents['videos']:
        if item['date'] == latest_video:
            print("Before: ", str(item))
            item['clips'].append(data)
            print("After: ", str(item))
        
    with open(document, "w") as f:
        yaml.safe_dump(contents, f)

def trigger_clip(config: Config, current_time, video_time, clip_before_length, clip_after_length, document, latest_video, title):
    src_name = datetime.strftime(config.video_filename_format)
    for (old, new) in config.filename_replace.items():
        src_name = src_name.replace(old, new)
    print(src_name)

    relative_time = datetime_from_str(video_time) - current_time
    start_window = relative_time - clip_before_length
    end_window = relative_time + clip_after_length


    
    # Fix if less than 0
    if start_window <= 0:
        start_window = 0

    window = str(start_window) + " - " + str(end_window)
    print(window)

    add_clip(document, latest_video, window, title)
