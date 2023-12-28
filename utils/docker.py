import os
import subprocess
import threading
from pydantic import BaseModel
from queue import Empty, Queue
from typing import List, Tuple

from utils.io import print_system


class PipeStatus(BaseModel):
    stdout: bool = True
    stderr: bool = True


assert "DOCKER_NAME" in os.environ
DOCKER_NAME = os.environ["DOCKER_NAME"]

EOF = "<EOF>"
EXITCOMMAND = "exitcommand"
ERROR = "ERROR: "


process = subprocess.Popen(
    ["docker", "exec", "-i", DOCKER_NAME, "bash"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
)


def execute(commands: List[str]) -> List[str]:
    global process
    assert process.stdin
    assert process.stdout
    assert process.stderr

    queue = Queue[str]()
    is_ongoing = PipeStatus(stdout=True, stderr=True)

    for command in commands:
        process.stdin.write(f"{command}\n")
    process.stdin.write(f"echo '{EOF}'\n")
    process.stdin.flush()

    def _stdout(pipe, q: Queue) -> None:
        while True:
            line = pipe.readline()
            q.put(line)
            if not line or line == f"{EOF}\n":
                is_ongoing.stdout = False
                break
            print_system(line, end="")

    def _stderr(pipe, q: Queue) -> None:
        while True:
            line = pipe.readline()
            q.put(line)
            if not line or EXITCOMMAND in line:
                is_ongoing.stderr = False
                break
            print_system(line, end="")

    stdout = threading.Thread(target=_stdout, args=(process.stdout, queue))
    stderr = threading.Thread(target=_stderr, args=(process.stderr, queue))
    stdout.start()
    stderr.start()

    outputs = []
    try:
        while is_ongoing.stdout or is_ongoing.stderr:
            output = queue.get(timeout=len(commands) * 5)
            if output == f"{EOF}\n":
                process.stdin.write(f"{EXITCOMMAND}\n")
                process.stdin.flush()
            elif EXITCOMMAND not in output:
                outputs.append(output)
    except Empty:
        process.terminate()
        process = subprocess.Popen(
            ["docker", "exec", "-i", DOCKER_NAME, "bash"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        outputs.append("Process is hanging. Connection restarted.")
        outputs.append("#pwd\n/home")

    stdout.join()
    stderr.join()

    return outputs
