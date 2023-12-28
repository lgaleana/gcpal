import os
from unittest import TestCase

os.environ["DOCKER_NAME"] = "gcpal"
os.environ["ENV"] = "TEST"

from utils.docker import execute, payload


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
        assert payload == [
            {
                "command": "cd home",
                "output": {"msg": "COMMAND_EXECUTED", "type_": "stdout"},
            },
            {"command": "ls", "output": {"msg": "COMMAND_EXECUTED", "type_": "stdout"}},
            {
                "command": "pwd",
                "output": {"msg": "COMMAND_EXECUTED", "type_": "stdout"},
            },
            {
                "command": "cd ..",
                "output": {"msg": "COMMAND_EXECUTED", "type_": "stdout"},
            },
            {"command": "ls", "output": {"msg": "COMMAND_EXECUTED", "type_": "stdout"}},
        ]
