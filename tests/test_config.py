"Tests for the config module."

from pathlib import Path

import pytest # type: ignore

from mvcs.config import Config, Subcommand
from mvcs.error import Error

def test_config_from_argv_defaults():
    "A default config is returned when no command-line arguments are given."
    config = Config.from_argv([])
    assert config.job_path is not None and bool(config.job_path)
    assert config.subcommand == Subcommand.HELP

@pytest.mark.parametrize("opt", ["-j", "--job-path"])
def test_config_from_argv_job_path(opt):
    "The default path to the job file can be changed."
    path = Path("/dev/null")
    config = Config.from_argv(["", opt, str(path)])
    assert config.job_path == path

@pytest.mark.parametrize("path", [""])
def test_config_from_argv_job_path_invalid(path):
    "Invalid paths are rejected."
    with pytest.raises(Error):
        Config.from_argv(["", "--job-path", path])

@pytest.mark.parametrize("subcommand_str,expected", [
    ("clip", Subcommand.CLIP),
    ("help", Subcommand.HELP),
    ("run", Subcommand.RUN),
])
def test_config_from_argv_subcommand(subcommand_str, expected):
    "The subcommand is set from the first non-option argument."
    config = Config.from_argv(["", subcommand_str])
    assert config.subcommand == expected

@pytest.mark.parametrize("subcommand_str", [""])
def test_config_from_argv_subcommand_invalid(subcommand_str):
    "Invalid subcommands are rejected."
    with pytest.raises(Error):
        Config.from_argv(["", subcommand_str])
