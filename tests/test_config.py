"Tests for the config module."

from pathlib import Path

import pytest # type: ignore

from mvcs.config import Config
from mvcs.error import Error

def test_config_from_argv_defaults():
    "A default config is returned when no command-line arguments are given."
    config = Config.from_argv([])
    assert config.job_path is not None and bool(config.job_path)

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
