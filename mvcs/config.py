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
    job_path: Path = Path("clip.yaml")

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

        prefs = {}
        # pylint: disable=unnecessary-lambda
        for (field, value_fn) in (
                ("job_path", lambda x: Path(str(x))),
        ):
            key = cls.dict_key(field)
            if key in data:
                prefs[field] = value_fn(data[key])

        unknown_keys = set(data.keys()) - set(cls.dict_key(k) for k in cls._fields)
        if unknown_keys:
            raise Error(f"unknown preferences: {unknown_keys}")

        return cls(**prefs) # type: ignore

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
    subcommand: Subcommand = Subcommand.HELP

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

        config: Dict[str, Any] = {
            "job_path": prefs.job_path,
        }

        try:
            opts, args = getopt.getopt(argv[1:], "hj:", longopts=[
                "help",
                "job-path=",
            ])
        except getopt.GetoptError as ex:
            raise Error(ex)

        if args:
            subcommand = {
                "clip": Subcommand.CLIP,
                "help": Subcommand.HELP,
                "run": Subcommand.RUN,
            }.get(args[0].lower())
            if subcommand is None:
                raise Error(f"invalid subcommand: {args[0]}")
            config["subcommand"] = subcommand

        for opt, optarg in opts:
            if opt in ("-h", "--help"):
                config["subcommand"] = Subcommand.HELP
            elif opt in ("-j", "--job-path"):
                if optarg:
                    config["job_path"] = Path(optarg)
                else:
                    raise Error("job path cannot be empty")
            else:
                raise Error(f"unhandled option: {opt}")

        return cls(**config) # type: ignore
