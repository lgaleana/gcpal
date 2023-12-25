import os
import sys
import threading
from datetime import datetime
from typing import Optional

from utils.io import print_system


LOG_DIR = "logs"

LOGS = []
lock = threading.Lock()


def log(skip_stdout: bool = False, **kwargs) -> None:
    for k, w in kwargs.items():
        str_to_log = f"{k}: {w}"

        with lock:
            LOGS.append(str_to_log)

        if not skip_stdout:
            print_system(str_to_log)


def dump(name: Optional[str] = None) -> None:
    if os.environ.get("TESTS", "") == "True":
        return

    name_prefix = _find_name_prefix_in_logs(name)
    _check_directory()

    now = datetime.now().strftime("%Y_%m_%d__%H_%M_%S")
    log_file = f"{LOG_DIR}/{name_prefix}{now}.txt"

    with open(log_file, "w") as f:
        f.write("\n".join(LOGS))


def interrupt_dump(signum, frame):
    log(feedback="interrupt")
    dump(name="query")
    sys.exit(0)


def _check_directory() -> None:
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)


def _find_name_prefix_in_logs(name: Optional[str] = None) -> str:
    if name:
        for log in LOGS:
            chunks = log.split(": ")
            if chunks[0] == name:
                name_prefix = "".join(chunks[1:]).replace(" ", "_")
                name_prefix += "_"
                return name_prefix
    return ""
