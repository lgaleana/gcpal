import os
from unittest import TestCase

os.environ["DOCKER_NAME"] = "gcpal"

from utils.docker import execute, state


class DockerTests(TestCase):
    def test(self):
        assert execute(["cd home", "ls"]) == ([], [])
        assert execute(["pwd"]) == (["/home"], [])
        assert execute(["cd ..", "ls"]) == (
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
            ],
            [],
        )
        assert [c.model_dump() for c in state.commands] == [
            {"command": "cd home", "is_success": True},
            {"command": "ls", "is_success": True},
            {"command": "pwd", "is_success": True},
            {"command": "cd ..", "is_success": True},
            {"command": "ls", "is_success": True},
        ]
