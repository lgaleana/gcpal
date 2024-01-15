import os
import subprocess
from typing import List

from agents.coder import File
from tools.docker.commands import DockerRunner


DOCKER_NAME = os.environ["DOCKER_NAME"]


def copy_files(files: List[File], root: str, container_path: str, docker: DockerRunner):
    for file in files:
        ogi_path = f"{root}/{file.path}"
        dst_path = f"{container_path}/{file.path}"
        intermediate_dirs, _ = os.path.split(dst_path)
        docker.execute_one(f"mkdir -p {intermediate_dirs}")
        subprocess.run(
            f"docker cp {ogi_path} {DOCKER_NAME}:{dst_path}",
            check=True,
            shell=True,
        )
