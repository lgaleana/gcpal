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


class Message(BaseModel):
    line: str


class Output(Message):
    pass


class Error(Message):
    pass


assert "DOCKER_NAME" in os.environ
DOCKER_NAME = os.environ["DOCKER_NAME"]

EOF = "<EOF>"
EXITCOMMAND = "exitcommand"
ERROR = "ERROR: "
TIMEOUT = 5


process = subprocess.Popen(
    ["docker", "exec", "-i", DOCKER_NAME, "bash"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
)


def execute(commands: List[str]) -> Tuple[List[str], List[str]]:
    global process
    assert process.stdin
    assert process.stdout
    assert process.stderr

    queue = Queue[Message]()
    is_ongoing = PipeStatus(stdout=True, stderr=True)

    for command in commands:
        process.stdin.write(f"{command}\n")
    process.stdin.write(f"echo '{EOF}'\n")
    process.stdin.flush()

    def _stdout(pipe, q: Queue) -> None:
        while True:
            line = pipe.readline()
            q.put(Output(line=line))
            if not line or line == f"{EOF}\n":
                is_ongoing.stdout = False
                break
            print_system(line, end="")

    def _stderr(pipe, q: Queue) -> None:
        while True:
            line = pipe.readline()
            q.put(Error(line=line))
            if not line or EXITCOMMAND in line:
                is_ongoing.stderr = False
                break
            print_system(line, end="")

    stdout = threading.Thread(target=_stdout, args=(process.stdout, queue))
    stderr = threading.Thread(target=_stderr, args=(process.stderr, queue))
    stdout.start()
    stderr.start()

    outputs = []
    errors = []
    try:
        while is_ongoing.stdout or is_ongoing.stderr:
            message = queue.get(timeout=TIMEOUT)
            if message.line == f"{EOF}\n":
                process.stdin.write(f"{EXITCOMMAND}\n")
                process.stdin.flush()
            elif EXITCOMMAND not in message.line:
                if isinstance(message, Output):
                    outputs.append(message.line)
                else:
                    errors.append(message.line)
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
        outputs.append(f"Process is hanging after {TIMEOUT}s. Connection restarted.")
        outputs.append("#pwd\n/home")

    stdout.join()
    stderr.join()

    return outputs, errors
