# modular-video-clipping-system
MVCS

## Development/Installation

Install mvcs and its dependencies:

    $ poetry install

Run tests and code analysis:

    $ poetry run pytest --mypy --pylint

## Usage

Write a `clip.yaml` file describing where to find the OBS recordings, where to
save the clips to, and provide a list of source videos and the clips that
should be created. Run with `mvcs --help` for detailed CLI usage.

## Example YAML

Here is a sample `clip.yaml`.

    # Absolute path to the OBS recording directory (source videos)
    video-dir: "c:/OBS Captures"

    # Absolute path to the directory to save clips to (must already exist)
    output-dir: "c:/OBS Clips"

    # List of source videos (identified by timestamp-based naming convention)
    videos:
      - date: "2020-01-01T00:00:00"
        # Virtual "start" time in the source video (for output filename)
        epoch: "0"

        # Base title for all clips (for output filename)
        title: "video 1"

        # List of clips to create
        clips:
          - time: "0 - 5:00"
            title: "first five minutes of the video"
          - time: "1:30:00 - 1:30:01"
            title: "one second long"

      - date: "2020-01-02T00:00:00"
        epoch: "15"
        title: "video 2"
        clips:
          - time: "0 - 15"
            title: "before the epoch"
          - time: "15 - 30"
            title: "on the epoch"
          - time: "30 - 45"
            title: "after the epoch"

This file references two source videos:

1. `c:/OBS Captures/2020-01-01 00-00-00.mkv`
2. `c:/OBS Captures/2020-01-02 01-00-00.mkv`

From these, it will create five clips:

1. `c:/OBS Clips/2020-01-01 00-00-00 - t+0h00m00s - video 1 - first five minutes of the video.mkv`
2. `c:/OBS Clips/2020-01-01 00-00-00 - t+1h30m00s - video 1 - one second long.mkv`
3. `c:/OBS Clips/2020-01-02 00-00-15 - t+0h00m00s - video 2 - before the epoch.mkv`
4. `c:/OBS Clips/2020-01-02 00-00-15 - t+0h00m00s - video 2 - on the epoch.mkv`
5. `c:/OBS Clips/2020-01-02 00-00-15 - t+0h00m15s - video 2 - after the epoch.mkv`

Note the timestamp used in the output filename reflects the epoch-adjusted
virtual start time of the video, and the relative timestamp of each clip also
accounts for the epoch (but will never be negative).

## User preferences (defaults)

You can create `~/.config/mvcs/prefs.yaml` to configure the default behavior of
the program. Command-line options take precedence over values defined in the
preferences file. Here is a commented example `prefs.yaml` with all defaults
values:

    # String replacement map for input and output filenames
    filename-replace: {}

    # Default path to the clip.yaml (absolute or relative paths are fine)
    job-path: "clip.yaml"

## TODO
### Short Term
[X] Create Repo and start collab.

[X] user preferences via a yaml config (e.g. ~/.config/mvcs/config.yaml)

[ ] smart detection of existing clips, if you happen to run a playbook twice, it shouldn't overwrite (or prompt you to overwrite) your existing clip, it should skip it

[ ] Add "controller" to handle generating YAML for clipping in real time.

### Long Term
[ ] Analyze clips with something like OpenCV to determine matches.
