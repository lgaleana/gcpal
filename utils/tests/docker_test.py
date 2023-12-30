import os
from unittest import TestCase

os.environ["DOCKER_NAME"] = "gcpal"

from utils import state

state.state = state.State()

from utils.docker import execute, execute_one, state as test_state, TIMEOUT


class DockerTests(TestCase):
    def test(self):
        assert execute_one("pwd").output_str() == "/home"
        assert [
            c.output
            for c in execute(["mkdir foo", "cd foo", "ls", "cd ..", "rm -r foo"])
        ] == [[], [], [], [], []]
        assert execute(["cd ..", "pwd"])[1].output_str() == "/"
        assert [c.model_dump_json() for c in test_state.commands] == [
            '{"command":"pwd","output":["/home"],"status":"SUCCESS"}',
            '{"command":"mkdir foo","output":[],"status":"SUCCESS"}',
            '{"command":"cd foo","output":[],"status":"SUCCESS"}',
            '{"command":"ls","output":[],"status":"SUCCESS"}',
            '{"command":"cd ..","output":[],"status":"SUCCESS"}',
            '{"command":"rm -r foo","output":[],"status":"SUCCESS"}',
            '{"command":"cd ..","output":[],"status":"SUCCESS"}',
            '{"command":"pwd","output":["/"],"status":"SUCCESS"}',
        ]

    def test_timeout(self):
        assert execute(["cd app", "git log"])[1].status != state.CommandStatus.TIMEOUT
        assert execute_one(f"sleep {TIMEOUT + 1}").status == state.CommandStatus.TIMEOUT
        assert execute_one("pwd").output_str() == "/home/app"
