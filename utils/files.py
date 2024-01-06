import os
import time
from typing import List

from ai_tasks.coder import File


DIFFS_DIR = "gcpal-docker/diffs"


def create_files(files: List[File], root_path: str) -> None:
    for file in files:
        full_path = f"{root_path}/{file.path}"
        intermediate_dirs, _ = os.path.split(full_path)
        if intermediate_dirs:
            os.makedirs(intermediate_dirs, exist_ok=True)
        with open(full_path, "w") as f:
            f.write(file.content)
