import os
from unittest import TestCase

os.environ["DOCKER_NAME"] = "gcpal"

from utils.docker import execute


class DockerTests(TestCase):
    def test(self):
        assert execute(["cd home", "ls"]) == ([], [])
        assert execute(["pwd"]) == (["/home\n"], [])
        assert execute(["cd ..", "ls"]) == (
            [
                "bin\n",
                "boot\n",
                "dev\n",
                "etc\n",
                "home\n",
                "lib\n",
                "media\n",
                "mnt\n",
                "opt\n",
                "proc\n",
                "root\n",
                "run\n",
                "sbin\n",
                "srv\n",
                "sys\n",
                "tmp\n",
                "usr\n",
                "var\n",
            ],
            [],
        )
