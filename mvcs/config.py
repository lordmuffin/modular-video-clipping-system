"Configuration module."

import enum
import getopt
from pathlib import Path
from typing import List, NamedTuple, Type, TypeVar

from mvcs.error import Error

@enum.unique
class Subcommand(enum.Enum):
    "Subcommand for selecting program execution type."

    # Show program usage and exit.
    HELP = enum.auto()
    # Run the job file to process videos and produce clips.
    RUN = enum.auto()

ConfigType = TypeVar("ConfigType", bound="Config")
class Config(NamedTuple):
    "Command-line configuration."

    # Path to the clip.yaml job file.
    job_path: Path
    # mvcs subcommand.
    subcommand: Subcommand

    @classmethod
    def from_argv(cls: Type[ConfigType], argv: List[str]) -> ConfigType:
        "Get configuration by parsing the program arguments."

        job_path = Path("clip.yaml")
        subcommand = Subcommand.HELP

        try:
            opts, args = getopt.getopt(argv[1:], "hj:", longopts=[
                "help",
                "job-path=",
            ])
        except getopt.GetoptError as ex:
            raise Error(ex)

        for opt, optarg in opts:
            if opt in ("-h", "--help"):
                subcommand = Subcommand.HELP
            elif opt in ("-j", "--job-path"):
                if optarg:
                    job_path = Path(optarg)
                else:
                    raise Error("job path cannot be empty")
            else:
                raise Error(f"unhandled option: {opt}")

        if args:
            try:
                subcommand = {
                    "help": Subcommand.HELP,
                    "run": Subcommand.RUN,
                }[args[0].lower()]
            except KeyError:
                raise Error(f"invalid subcommand: {args[0]}")

        return cls(job_path=job_path, subcommand=subcommand)
