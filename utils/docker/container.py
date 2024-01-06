import os
import subprocess
from typing import List

from ai_tasks.coder import File
from utils.docker import commands


DOCKER_NAME = os.environ["DOCKER_NAME"]


def copy_files(files: List[File], root: str, container_path: str):
    for file in files:
        ogi_path = f"{root}/{file.path}"
        dst_path = f"{container_path}/{file.path}"
        intermediate_dirs, _ = os.path.split(dst_path)
        commands.execute_one(f"mkdir -p {intermediate_dirs}")
        subprocess.run(
            f"docker cp {ogi_path} {DOCKER_NAME}:{dst_path}",
            check=True,
            shell=True,
        )
