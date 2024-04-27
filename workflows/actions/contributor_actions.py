from agents.contributor import AmendPRParams
from tools.docker.commands import DockerRunner
from tools.github import PullRequest
from utils.io import print_system
from workflows.actions.coder_actions import create_or_edit_pr


def rollback(pr: PullRequest, docker: DockerRunner) -> None:
    print_system()
    print_system("!!!!! Rolling back...")
    docker.execute(
        [
            f"git checkout {pr.head}",
            "python3 -m pip uninstall -r requirements.txt -y",  # roll back packages
            "git restore .",  # roll back files
            "git clean -fd",  # roll back files
        ]
    )
    rev = docker.execute_one("git rev-parse HEAD").output_str()
    print(rev)
    print(pr.commits)
    breakpoint()
    if rev != pr.commits[-1]:
        # We need to revert the last commit
        docker.execute(
            [
                "git reset --hard HEAD~1",
                f"git push origin {pr.head} -f",  # roll back amend
            ]
        )
    docker.execute(
        [
            "git checkout main",
            "python3 -m pip install -r requirements.txt",  # roll back packages
        ]
    )
    print_system("Rollback successful...")  # roll back commit


def edit_pr(
    tool: AmendPRParams, state_name: str, docker: DockerRunner, repo: str
) -> PullRequest:
    return create_or_edit_pr(tool, state_name, docker, repo)
