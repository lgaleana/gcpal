import os
import subprocess
import threading
from pydantic import BaseModel
from queue import Empty, Queue
from typing import ClassVar, List, Tuple, Type

from utils.io import print_system


assert "DOCKER_NAME" in os.environ
DOCKER_NAME = os.environ["DOCKER_NAME"]


process = subprocess.Popen(
    ["docker", "exec", "-i", DOCKER_NAME, "bash"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
)


COMMAND_EXECUTED = "COMMAND_EXECUTED\n"
TIMEOUT = 5


class StdOut(BaseModel):
    msg: str
    exit_signal: ClassVar[str] = "EXIT_STDOUT"


class StdErr(StdOut):
    exit_signal: ClassVar[str] = "EXIT_STDERR"


def execute(commands: List[str]) -> Tuple[List[str], List[str]]:
    global process
    assert process.stdin
    assert process.stdout
    assert process.stderr

    QUEUE = Queue[StdOut]()

    def _stream(pipe, q: Queue, output: Type[StdOut]) -> None:
        while True:
            line = pipe.readline()
            q.put(output(msg=line))
            if not line or output.exit_signal in line:
                break

    stdout = threading.Thread(target=_stream, args=(process.stdout, QUEUE, StdOut))
    stderr = threading.Thread(target=_stream, args=(process.stderr, QUEUE, StdErr))
    stdout.start()
    stderr.start()

    outputs = []
    errors = []
    try:
        for command in commands:
            process.stdin.write(f"{command}\n")
            process.stdin.write(f"echo {COMMAND_EXECUTED}")
            process.stdin.flush()

            output = QUEUE.get(timeout=TIMEOUT)
            while output.msg != COMMAND_EXECUTED:
                if isinstance(output, StdOut):
                    outputs.append(output.msg)
                else:
                    errors.append(output.msg)
                print_system(output.msg, end="")
                output = QUEUE.get(timeout=TIMEOUT)

        process.stdin.write(f"echo {StdOut.exit_signal}\n")
        process.stdin.write(f"{StdErr.exit_signal}\n")
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
