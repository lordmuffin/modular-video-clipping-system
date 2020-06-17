"Configuration module."

import enum
import getopt
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Type, TypeVar

import yaml

from mvcs.error import Error

PrefsType = TypeVar("PrefsType", bound="Prefs")
class Prefs(NamedTuple):
    "User preferences to choose default behavior."

    # Default path to the job file.
    job_path: Path

    @classmethod
    def dict_key(cls: Type[PrefsType], field: str) -> str:
        "Get the untyped `dict` key name for a `Prefs` field."
        try:
            return {
                "job_path": "job-path",
            }[field]
        except KeyError:
            raise Error(f"invalid field: {field}")

    @classmethod
    def from_dict(cls: Type[PrefsType], data: Dict[str, Any]) -> PrefsType:
        "Create `Prefs` from an untyped `dict` (YAML deserialization result)."

        job_path = Path(str(data.get(cls.dict_key("job_path"), "clip.yaml")))

        unknown_keys = set(data.keys()) - set(cls.dict_key(k) for k in cls._fields)
        if unknown_keys:
            raise Error(f"unknown preferences: {unknown_keys}")

        return cls(job_path=job_path)

    @classmethod
    def from_yaml_file(cls: Type[PrefsType], path: Path) -> PrefsType:
        "Create a `Prefs` from a YAML file."

        with path.open(encoding="utf-8") as file:
            return cls.from_dict(yaml.safe_load(file))

@enum.unique
class Subcommand(enum.Enum):
    "Subcommand for selecting program execution type."

    # Add a new clip to the job file.
    CLIP = enum.auto()
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
    def from_argv(
            cls: Type[ConfigType],
            argv: List[str],
            *,
            prefs: Optional[Prefs] = None,
    ) -> ConfigType:
        "Get configuration by parsing the program arguments."

        # Use default preferences if not provided
        prefs = prefs if prefs is not None else Prefs.from_dict({})

        job_path = prefs.job_path
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
                    "clip": Subcommand.CLIP,
                    "help": Subcommand.HELP,
                    "run": Subcommand.RUN,
                }[args[0].lower()]
            except KeyError:
                raise Error(f"invalid subcommand: {args[0]}")

        return cls(job_path=job_path, subcommand=subcommand)
