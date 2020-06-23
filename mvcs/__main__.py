#!/usr/bin/env python3

"Create clips from OBS captures using ffmpeg and YAML."

import sys
from pathlib import Path
from typing import List, Optional

import mvcs

def handle_clip(_config: mvcs.Config):
    "Handle the clip subcommand."

    yaml = "videos.yaml"

    mvcs.gen.check_template(yaml)
    print(_config.video_dir)
    print(_config.video_ext)
    # print(mvcs.gen.current_time())
    latest = mvcs.gen.latest_video(_config, mvcs.gen.current_time(), _config.video_ext, _config.video_dir)
    video = mvcs.gen.add_video(
        yaml,
        latest,
        0,
        "Video"
    )
    mvcs.gen.trigger_clip(
      _config,
      latest,
      10,
      10,
      yaml,
      latest,
      "CLIP IT!",
    )

def handle_help(_config: mvcs.Config):
    "Handle the help subcommand."

    prefs = mvcs.Prefs()
    for line in (
            "mvcs - multi-video clipping system",
            "",
            "USAGE:",
            "    mvcs [OPTIONS] [SUBCOMMAND]",
            "",
            "OPTIONS:",
            "    -h, --help",
            "        Print usage information",
            "    -i, --video-dir <PATH>",
            f"        Path to the input video directory (default: {prefs.video_dir})",
            "    -j, --job-path <PATH>",
            f"        Path to the clipping job YAML file (default: {prefs.job_path})",
            "    -o, --output-dir <PATH>",
            f"        Path to the output clips directory (default: {prefs.output_dir})",
            "    -r, --filename-replace <OLD>=<NEW>",
            "        Add a mapping to replace strings in input/output filenames,",
            "        e.g. `--filename-replace ' =_'` to replace spaces with underscores;",
            "        pass an empty string to clear the current mappings",
            "    --output-ext <EXTENSION>",
            f"        Output clip file extension (default: {prefs.output_ext})",
            "    --video-ext <EXTENSION>",
            f"        Input video file extension (default: {prefs.video_ext})",
            "    --video-filename-format <STRING>",
            f"        Input video filename format (default: {prefs.video_filename_format})",
            "",
            "SUBCOMMANDS:",
            "    clip    Add a new clip to the job file",
            "    help    Print usage information",
            "    run     Run the job file to process videos and produce clips",
    ):
        print(line, file=sys.stderr)

def handle_run(config: mvcs.Config):
    "Handle the run subcommand."
    # Deserialize the YAML job playbook and run it
    job = mvcs.Job.from_yaml_file(config)
    job.run(config)

def main(argv: Optional[List[str]] = None) -> int:
    "Main entrypoint."

    argv = argv if argv is not None else sys.argv
    try:
        # Get user preferences
        prefs_path = Path("~/.config/mvcs/prefs.yaml").expanduser()
        prefs = mvcs.Prefs.from_yaml_file(prefs_path) if prefs_path.is_file() else None

        # Get configuration from command-line arguments
        config = mvcs.Config.from_argv(argv, prefs=prefs)

        # Dispatch subcommand handler
        {
            mvcs.Subcommand.CLIP: handle_clip,
            mvcs.Subcommand.HELP: handle_help,
            mvcs.Subcommand.RUN: handle_run,
        }[config.subcommand](config)
    except mvcs.Error as ex:
        print(f"error: {ex}", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
