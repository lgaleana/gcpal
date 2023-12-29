import os
from unittest import TestCase

os.environ["DOCKER_NAME"] = "gcpal"

from utils import state

state.state = state.State()

from utils.docker import execute, execute_one, state as test_state


class DockerTests(TestCase):
    def test(self):
        assert execute_one("pwd") == "/home"
        assert [
            c.output
            for c in execute(["mkdir foo", "cd foo", "ls", "cd ..", "rm -r foo"])
        ] == [[], [], [], [], []]
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
        ) <= set(execute(["cd ..", "ls"])[1].output)
        assert [c.model_dump_json() for c in test_state.commands[:-1]] == [
            '{"command":"pwd","output":["/home"],"status":"SUCCESS"}',
            '{"command":"mkdir foo","output":[],"status":"SUCCESS"}',
            '{"command":"cd foo","output":[],"status":"SUCCESS"}',
            '{"command":"ls","output":[],"status":"SUCCESS"}',
            '{"command":"cd ..","output":[],"status":"SUCCESS"}',
            '{"command":"rm -r foo","output":[],"status":"SUCCESS"}',
            '{"command":"cd ..","output":[],"status":"SUCCESS"}',
        ]
