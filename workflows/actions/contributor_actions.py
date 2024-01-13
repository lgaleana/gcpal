from agents.contributor import AmendPRParams
from tools.docker import commands as docker
from utils.io import print_system
from workflows.actions.coder_actions import create_or_edit_pr


def rollback() -> None:
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
        ]
    )
    print_system("Rollback successful...")


def edit_pr(tool: AmendPRParams, state_name: str) -> str:
    return create_or_edit_pr(tool, state_name)
