import time
from typing import Union

from agents.coder import WritePRParams
from agents.contributor import AmendPRParams
from tools import github
from tools.files import create_files, DIFFS_DIR
from tools.docker import commands, container
from utils.io import print_system
from utils.state import CommandStatus


class PRError(Exception):
    pass


class TestsError(PRError):
    pass


def create_or_edit_pr(
    tool: Union[WritePRParams, AmendPRParams],
    state_name: str,
    docker: commands.DockerRunner,
) -> str:
    # Create files locally first
    print_system("Copying files to container...")
    root_path = f"{DIFFS_DIR}/{state_name}/{time.time()}"
    create_files(tool.files + tool.test_files, root_path=root_path)

    # 1. Move to branch
    if isinstance(tool, WritePRParams):
        branch = docker.execute_one(f"git checkout -b {tool.git_branch}")
    else:
        branch = docker.execute_one(f"git checkout {tool.git_branch}")
    if branch.status == CommandStatus.ERROR or "fatal:" in branch.output_str():
        raise PRError(
            f"Error running :: `{branch.command}`. Error :: {branch.output_str()}"
        )

    # 2. Copy files to docker container
    container.copy_files(
        files=tool.files + tool.test_files,
        root=root_path,
        container_path=f"/home/app",
        docker=docker,
    )
    docker.execute_one("git status")

    # 3. Install new requirements
    pip = docker.execute_one("python3 -m pip install -r requirements.txt")
    if pip.status == CommandStatus.ERROR:
        raise PRError(f"Error running :: `{pip.command}`. Error :: {pip.output_str()}")

    # 4. Run tests
    pytest = docker.execute_one("python3 -m pytest")
    if (
        pytest.status == CommandStatus.ERROR
        or "= ERRORS =" in pytest.output_str()
        or "= FAILURES =" in pytest.output_str()
    ):
        raise TestsError(f"The tests failed :: {pytest.output_str()}")

    # 5. Create commit and push
    commit_commands = docker.execute(
        [
            "git add .",
            f'git commit -m "{tool.title}"',
            f"git push origin {tool.git_branch}",
        ]
    )
    for c in commit_commands:
        if c.status == CommandStatus.ERROR:
            raise PRError(f"Error running :: `{c.command}`. Error :: {c.output_str()}")

    if isinstance(tool, WritePRParams):
        # 6. Create PR
        pr_url = github.create_pr(
            head=tool.git_branch,
            base="main",
            title=tool.title,
            description=tool.description,
            test_plan="pytest",
        )
        return pr_url
    else:
        return tool.pr_url


def rollback(branch: str, docker: commands.DockerRunner) -> None:
    print_system()
    print_system("!!!!! Rolling back...")
    docker.execute(
        [
            "cd /home/app",
            "pwd",
            "source venv/bin/activate",
            "python3 -m pip uninstall -r requirements.txt -y",  # roll back packages
            "python3 -m pip install -r requirements.txt",  # roll back packages
            "git restore .",  # roll back files
            "git clean -fd",  # roll back files
            "git checkout main",  # roll back branch
            f"git branch -D {branch}",  # roll back branch
            f"git push origin --delete {branch}",  # rollb back github branch
        ]
    )
    print_system("Rollback successful...")


def create_pr(
    tool: WritePRParams, state_name: str, docker: commands.DockerRunner
) -> str:
    return create_or_edit_pr(tool, state_name, docker)
