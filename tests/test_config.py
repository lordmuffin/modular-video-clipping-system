"Tests for the config module."

from pathlib import Path

import pytest # type: ignore

from mvcs.config import Config, Prefs, Subcommand
from mvcs.error import Error

@pytest.mark.parametrize("prefs,expected", [
    # The default preferences are used when none is provided
    (None, Prefs()),
    # The default config respects user preferences when provided
    (
        Prefs(
            job_path=Path("/dev/null"),
        ),
        Prefs(
            job_path=Path("/dev/null"),
        ),
    ),
])
def test_config_from_argv_defaults(prefs, expected):
    "A default config is returned when no command-line arguments are given."
    config = Config.from_argv([], prefs=prefs)
    assert config.job_path == expected.job_path
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

@pytest.mark.parametrize("data,expected", [
    # Default preferences from an empty dict
    ({}, Prefs()),
    # Valid values override defaults
    (
        {
            "job-path": "/dev/null",
        },
        Prefs(job_path=Path("/dev/null")),
    ),
])
def test_prefs_from_dict(data, expected):
    "User preferences are deserialized from dicts correctly."
    prefs = Prefs.from_dict(data)
    assert prefs == expected

@pytest.mark.parametrize("data", [
    # Unknown preferences are invalid
    {"not-a-real-pref": "test"},
])
def test_prefs_from_dict_invalid(data):
    "Invalid user preferences are rejected."
    with pytest.raises(Error):
        Prefs.from_dict(data)
