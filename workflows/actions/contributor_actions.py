from agents.contributor import AmendPRParams
from tools.docker.commands import DockerRunner
from utils.io import print_system
from workflows.actions.coder_actions import create_or_edit_pr


def rollback(branch: str, docker: DockerRunner) -> None:
    print_system()
    print_system("!!!!! Rolling back...")
    docker.execute(
        [
            f"git checkout {branch}",
            "python3 -m pip uninstall -r requirements.txt -y",  # roll back packages
            "git restore .",  # roll back files
            "git clean -fd",  # roll back files
            "git reset --hard HEAD~1",  # roll back commit
            f"git push origin {branch} -f",  # roll back amend
            "git checkout main",
            "python3 -m pip install -r requirements.txt",  # roll back packages
        ]
    )
    print_system("Rollback successful...")


def edit_pr(tool: AmendPRParams, state_name: str, docker: DockerRunner) -> str:
    return create_or_edit_pr(tool, state_name, docker)
