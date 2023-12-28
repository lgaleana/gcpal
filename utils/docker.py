import os
import subprocess
import threading
from pydantic import BaseModel
from queue import Empty, Queue
from typing import ClassVar, List, Tuple, Type

from utils.io import print_system
from utils.state import Command, state


assert "DOCKER_NAME" in os.environ
DOCKER_NAME = os.environ["DOCKER_NAME"]


# Open "connection" with docker through the "-i" flag
process = subprocess.Popen(
    ["docker", "exec", "-i", DOCKER_NAME, "bash"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
)


COMMAND_EXECUTED = "COMMAND_EXECUTED"
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

    queue = Queue[StdOut]()

    def _stream(pipe, q: Queue, output: Type[StdOut]) -> None:
        # Wait for updates from docker
        while True:
            line = pipe.readline().strip()
            q.put(output(msg=line))  # Send message back to the main thread
            if not line or output.exit_signal in line:
                break

    # One thread for stdout, one thread for stderr
    stdout = threading.Thread(target=_stream, args=(process.stdout, queue, StdOut))
    stderr = threading.Thread(target=_stream, args=(process.stderr, queue, StdErr))
    stdout.start()
    stderr.start()

    outputs = []
    errors = []
    try:
        # Iterate over commands
        for command in commands:
            process.stdin.write(f"{command}\n")
            process.stdin.write(f"echo {COMMAND_EXECUTED}\n")  # Signal of executed
            process.stdin.flush()
            command_obj = Command(command=command)

            # Iterate over the command stdout or stderr
            output = queue.get(timeout=TIMEOUT)
            while output.msg != COMMAND_EXECUTED:
                if isinstance(output, StdOut):
                    outputs.append(output.msg)
                else:
                    command_obj.is_success = False
                    errors.append(output.msg)
                print_system(output.msg)
                output = queue.get(timeout=TIMEOUT)

            _persist_command(command_obj)

        # Signal to exit the threads
        process.stdin.write(f"echo {StdOut.exit_signal}\n")
        process.stdin.write(f"{StdErr.exit_signal}\n")
    except Empty:
        # Timeout
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


def _persist_command(command: Command) -> None:
    state.commands.append(command)
