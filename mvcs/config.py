"Configuration module."

import getopt
from pathlib import Path
from typing import List, NamedTuple, Type, TypeVar

from mvcs.error import Error

ConfigType = TypeVar("ConfigType", bound="Config")
class Config(NamedTuple):
    "Command-line configuration."

    # Path to the clip.yaml job file.
    job_path: Path

    @classmethod
    def from_argv(cls: Type[ConfigType], argv: List[str]) -> ConfigType:
        "Get configuration by parsing the program arguments."

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
