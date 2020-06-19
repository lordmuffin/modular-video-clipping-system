"Configuration module."

import enum
import getopt
from collections import UserDict
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Type, TypeVar

import yaml

from mvcs.error import Error

ReplaceType = TypeVar("ReplaceType", bound="Replace")
class Replace(UserDict): # pylint: disable=too-many-ancestors
    "String replacement mapping."

    @classmethod
    def from_dict(cls: Type[ReplaceType], data: Dict[str, str]) -> ReplaceType:
        "Create `Replace` from an untyped `dict` (YAML deserialization result)."

        # Mostly arbitrary key-value string pairs are allowed
        for (key, value) in data.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise Error(f"bad mapping: {key}: {value}")
            if not key:
                raise Error(f"mapping key cannot be empty: {key}: {value}")

        return cls(data)

PrefsType = TypeVar("PrefsType", bound="Prefs")
class Prefs(NamedTuple):
    "User preferences to choose default behavior."

    # String replacement map for input and output filenames.
    filename_replace: Replace = Replace()
    # Default path to the job file.
    job_path: Path = Path("clip.yaml")
    # Default path to the output clips directory.
    output_dir: Path = Path(".")
    # Default path to the input video directory.
    video_dir: Path = Path(".")

    @classmethod
    def dict_key(cls: Type[PrefsType], field: str) -> str:
        "Get the untyped `dict` key name for a `Prefs` field."
        try:
            return {
                "filename_replace": "filename-replace",
                "job_path": "job-path",
                "output_dir": "output-dir",
                "video_dir": "video-dir",
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
                ("filename_replace", lambda x: Replace.from_dict(x)),
                ("output_dir", lambda x: Path(str(x))),
                ("video_dir", lambda x: Path(str(x))),
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
            data = yaml.safe_load(file)
            if data is None:
                return cls()
            if isinstance(data, dict):
                return cls.from_dict(data)
            raise Error(f"invalid prefs file: {data}")

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
    # String replacement map for input and output filenames.
    filename_replace: Replace
    # Default path to the output clips directory.
    output_dir: Path
    # Default path to the input video directory.
    video_dir: Path
    # mvcs subcommand.
    subcommand: Subcommand = Subcommand.HELP

    @classmethod
    def default(cls: Type[ConfigType], *, prefs: Optional[Prefs] = None) -> ConfigType:
        "Return a default config."

        prefs = prefs if prefs is not None else Prefs()
        return cls(
            job_path=prefs.job_path,
            filename_replace=prefs.filename_replace,
            output_dir=prefs.output_dir,
            video_dir=prefs.video_dir,
        )

    @classmethod
    # pylint: disable=too-many-branches
    def from_argv(
            cls: Type[ConfigType],
            argv: List[str],
            *,
            prefs: Optional[Prefs] = None,
    ) -> ConfigType:
        "Get configuration by parsing the program arguments."

        # Use default preferences if not provided
        prefs = prefs if prefs is not None else Prefs()

        config: Dict[str, Any] = {
            "job_path": prefs.job_path,
            "filename_replace": Replace(prefs.filename_replace),
            "output_dir": prefs.output_dir,
            "video_dir": prefs.video_dir,
        }

        try:
            opts, args = getopt.getopt(argv[1:], "hi:j:o:r:", longopts=[
                "filename-replace=",
                "help",
                "job-path=",
                "output-dir=",
                "video-dir=",
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
            elif opt in ("-i", "--video-dir"):
                if optarg:
                    config["video_dir"] = Path(optarg)
                else:
                    raise Error("video directory path cannot be empty")
            elif opt in ("-j", "--job-path"):
                if optarg:
                    config["job_path"] = Path(optarg)
                else:
                    raise Error("job path cannot be empty")
            elif opt in ("-o", "--output-dir"):
                if optarg:
                    config["output_dir"] = Path(optarg)
                else:
                    raise Error("output clip directory cannot be empty")
            elif opt in ("-r", "--filename-replace"):
                if optarg:
                    if optarg.startswith("=="):
                        config["filename_replace"]["="] = optarg[2:]
                    elif optarg.startswith("="):
                        raise Error(f"invalid replacement: {optarg}")
                    elif "=" in optarg:
                        (key, value) = optarg.split("=", maxsplit=1)
                        config["filename_replace"][key] = value
                    else:
                        raise Error(f"invalid replacement: {optarg}")
                else:
                    config["filename_replace"] = Replace(prefs.filename_replace)
            else:
                raise Error(f"unhandled option: {opt}")

        return cls(**config) # type: ignore
