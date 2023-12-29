import os
import subprocess
import threading
from pydantic import BaseModel
from queue import Empty, Queue
from typing import ClassVar, List, Tuple, Type, Union

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
    universal_newlines=True,
)


COMMAND_EXECUTED = "COMMAND_EXECUTED"
ERROR_PREFIX = "ERROR_LINE: "
TIMEOUT = 5


class StdOut(BaseModel):
    msg: str
    exit_signal: ClassVar[str] = "EXIT_STDOUT"


class StdErr(BaseModel):
    msg: str
    exit_signal: ClassVar[str] = "EXIT_STDERR"


def execute(commands: List[str]) -> Tuple[List[str], List[str]]:
    global process
    assert process.stdin
    assert process.stdout
    assert process.stderr

    queue = Queue()

    def _stream(pipe, q: Queue, output: Type[Union[StdOut, StdErr]]) -> None:
        # Wait for updates from docker
        while True:
            line = pipe.readline().strip()
            q.put(output(msg=line))  # Send message back to the main thread
            if (not line and process.poll() is not None) or output.exit_signal in line:
                break

    # One thread for stdout, one thread for stderr
    stdout = threading.Thread(target=_stream, args=(process.stdout, queue, StdOut))
    stderr = threading.Thread(target=_stream, args=(process.stderr, queue, StdErr))
    stdout.start()
    stderr.start()

    outputs = []
    errors = []
    try:
        commands.append("pwd")
        # Iterate over commands
        for command in commands:
            process.stdin.write(f"{command}\n")
            process.stdin.write(f"echo {COMMAND_EXECUTED}\n")  # Signal of executed
            process.stdin.flush()
            print_system(f"# {command}")
            outputs.append(f"# {command}")

            # Iterate over the command stdout or stderr
            output = queue.get(timeout=TIMEOUT)
            while COMMAND_EXECUTED not in output.msg:
                print_system(output.msg)
                if isinstance(output, StdOut):
                    outputs.append(output.msg)
                else:
                    errors.append(output.msg)
                    if ERROR_PREFIX in output.msg:
                        # Regular errors sometimes get sent to stderr
                        # Real errors usually have an ERROR:  prefix
                        break
                output = queue.get(timeout=TIMEOUT)

            if ERROR_PREFIX in output.msg:
                # Exit on error
                _persist_command(Command(command=command, is_success=False))
                break
            _persist_command(Command(command=command, is_success=True))

        # Signal to exit the threads
        process.stdin.write(f"echo {StdOut.exit_signal}\n")
        process.stdin.write(f"{StdErr.exit_signal}\n")

        stdout.join()
        stderr.join()
    except Empty:
        # Timeout
        process.terminate()
        stdout.join()
        stderr.join()

        process = subprocess.Popen(
            ["docker", "exec", "-i", DOCKER_NAME, "bash"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        outputs.append(f"Process is hanging after {TIMEOUT}s. Connection restarted.")
        outputs_, _ = execute([])
        outputs.extend(outputs_)

    return outputs, errors


def _persist_command(command: Command) -> None:
    state.commands.append(command)
