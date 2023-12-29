import os
import subprocess
import threading
from pydantic import BaseModel
from queue import Empty, Queue
from typing import ClassVar, List, Type, Union

from utils.io import print_system
from utils.state import Command, CommandStatus, state


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


def execute(commands: List[str]) -> List[Command]:
    global process
    assert process.stdin

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

    executed_commands = []
    status = CommandStatus.SUCCESS
    # Iterate over commands
    for command in commands:
        process.stdin.write(f"{command}\n")
        process.stdin.write(f"echo {COMMAND_EXECUTED}\n")  # Signal of executed
        process.stdin.flush()
        print_system(f"# {command}")

        msgs = []
        try:  # Catch timeouts
            output = queue.get(timeout=TIMEOUT)
            # Iterate over the command stdout or stderr until COMMAND_EXECUTED
            while COMMAND_EXECUTED not in output.msg:
                msgs.append(output.msg)
                print_system(output.msg)
                if isinstance(output, StdErr) and ERROR_PREFIX in output.msg:
                    # Regular outputs sometimes get sent to stderr
                    # Real errors usually have an ERROR:  prefix
                    status = CommandStatus.ERROR
                    break
                output = queue.get(timeout=TIMEOUT)
        except Empty:
            # Close connection and re-create
            process.terminate()
            process = subprocess.Popen(
                ["docker", "exec", "-i", DOCKER_NAME, "bash"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            # Exit
            status = CommandStatus.TIMEOUT
            break
        finally:
            executed_command = Command(command=command, output=msgs, status=status)
            executed_commands.append(executed_command)
            _persist_command(executed_command)

        if executed_command.status != CommandStatus.SUCCESS:
            # Stop on error
            break

    # Signal to exit the threads
    assert process.stdin
    process.stdin.write(f"echo {StdOut.exit_signal}\n")
    process.stdin.write(f"{StdErr.exit_signal}\n")

    stdout.join()
    stderr.join()

    return executed_commands


def _persist_command(command: Command) -> None:
    state.commands.append(command)


def startup() -> List[Command]:
    return execute(
        [
            "eval $(ssh-agent -s)",
            "ssh-add /root/.ssh/github",
            "ssh-keyscan -H github.com >> /root/.ssh/known_hosts",
        ]
    )
