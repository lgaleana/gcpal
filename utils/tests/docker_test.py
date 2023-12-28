import os
from unittest import TestCase

os.environ["DOCKER_NAME"] = "gcpal"

from utils import state

state.state = state.State()

from utils.docker import execute, state as test_state


class DockerTests(TestCase):
    def test(self):
        assert execute(["pwd"]) == (["/home"], [])
        assert execute(["mkdir foo", "cd foo", "ls", "cd ..", "rm -r foo"]) == ([], [])
        assert set(
            [
                "bin",
                "boot",
                "dev",
                "etc",
                "home",
                "lib",
                "media",
                "mnt",
                "opt",
                "proc",
                "root",
                "run",
                "sbin",
                "srv",
                "sys",
                "tmp",
                "usr",
                "var",
            ]
        ) <= set(execute(["cd ..", "ls"])[0])
        assert [c.model_dump() for c in test_state.commands] == [
            {"command": "cd home", "is_success": True},
            {"command": "pwd", "is_success": True},
            {"command": "pwd", "is_success": True},
            {"command": "mkdir foo", "is_success": True},
            {"command": "cd foo", "is_success": True},
            {"command": "ls", "is_success": True},
            {"command": "cd ..", "is_success": True},
            {"command": "rm -r foo", "is_success": True},
            {"command": "cd ..", "is_success": True},
            {"command": "ls", "is_success": True},
        ]
