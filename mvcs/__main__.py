#!/usr/bin/env python3

"Create clips from OBS captures using ffmpeg and YAML."

import sys
from typing import List, Optional

import mvcs

def handle_clip(_config: mvcs.Config):
    "Handle the clip subcommand."

    mvcs.gen.check_template("test.yaml")
    latest = mvcs.gen.latest_video(mvcs.gen.current_time("%CCYY-%MM-%DD_%hh-%mm-%ss"), ".mp4", "./")
    mvcs.gen.add_clip(
        "test.yaml",
        latest,
        mvcs.gen.current_time("%CCYY-%MM-%DD_%hh-%mm-%ss"),
        "CLIP IT!",
    )

def handle_help(_config: mvcs.Config):
    "Handle the help subcommand."

    for line in (
            "mvcs - multi-video clipping system",
            "",
            "USAGE:",
            "    mvcs [OPTIONS] [SUBCOMMAND]",
            "",
            "OPTIONS:",
            "    -h, --help",
            "        Print usage information",
            "    -j, --job-path <PATH>",
            "        Path to the clipping job YAML file (default: clip.yaml)",
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
    job = mvcs.Job.from_yaml_file(config.job_path)
    job.run()

def main(argv: Optional[List[str]] = None) -> int:
    "Main entrypoint."

    argv = argv if argv is not None else sys.argv
    try:
        # Get configuration from command-line arguments
        config = mvcs.Config.from_argv(argv)

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
