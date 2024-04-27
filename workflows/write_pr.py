import argparse
import time
import traceback

from dotenv import load_dotenv

load_dotenv()

from agents import coder
from ai_tools import sumamrize_test_failure
from tools import github
from tools import jira
from tools.docker.commands import DockerRunner
from utils.io import print_system
from utils.state import Conversation, State
from workflows.actions.coder_actions import create_pr, rollback, TestsError


AGENT = "coder"

TOOL_FAIL_MSG = "The commit was reverted. Fix the tests and re-create the PR. Go ahead."


def run(state: State, repo: str, ticket_key: str) -> None:
    tickets = jira.get_all_issues(ticket_key.split("-")[0])
    codebase = github.get_repo_files(repo=repo)
    active_ticket = jira.find_issue(tickets, ticket_key)
    assert active_ticket
    assert active_ticket.type_ in [
        "Subtask"
    ], "Tickets must be subtasks, found :: {active_ticket.type_}"

    docker = DockerRunner(
        startup_commands=[
            f"cd /home/{repo}",
            "pwd",
            "source venv/bin/activate",
            "git checkout main",
            "git pull origin main --rebase",
        ]
    )

    conversation = state.conversation

    # code_suggestion = suggest_code(active_ticket, codebase)

    while True:
        ai_action = coder.write_pr(active_ticket, conversation, codebase)
        if isinstance(ai_action, str):
            conversation.add_assistant(ai_action)
            # user_message = user_input()
            # conversation.add_user(user_message)
        else:
            arguments = ai_action.arguments[0]
            for arg in ai_action.arguments[1:]:
                arguments.update(arg)
            tool = coder.WritePRParams.model_validate(ai_action.arguments[0])
            print_system(tool)
            conversation.add_tool(tool=ai_action)

            try:
                state.pr = create_pr(tool, state.name, docker, repo=repo)
                conversation.add_tool_response(
                    tool_id=ai_action.id,
                    message=(f"PR created successfully :: {state.pr}"),
                )
                print_system(state.pr)
                break
            except Exception as e:
                print_system()
                print_system(f"!!!!! ERROR\n: {e}")
                traceback.print_tb(e.__traceback__)
                print_system()

                rollback(tool.git_branch, docker)
                if state.pr:
                    state.pr.commits.pop()

                if isinstance(e, TestsError):
                    conversation.remove_last_failed_tool(TOOL_FAIL_MSG)
                    conversation.add_tool_response(
                        tool_id=ai_action.id,
                        message=sumamrize_test_failure(
                            pr=tool, failure_msg=str(e), repo_files=codebase
                        ),
                    )
                    conversation.add_user(TOOL_FAIL_MSG)
                else:
                    conversation.add_tool_response(
                        tool_id=ai_action.id,
                        message=str(e),
                    )
        state.persist()

    conversation.remove_last_failed_tool(TOOL_FAIL_MSG)
    state.final_persist(ticket_key)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ticket", type=str)
    parser.add_argument("repo", type=str)
    parser.add_argument("--name", type=str, default=None)
    args = parser.parse_args()

    states_dir = f"db/{AGENT}/"
    if args.name:
        state = State.load(args.name, AGENT)
    else:
        state = State(
            name=str(time.time()), agent=AGENT, conversation=Conversation(), pr=None
        )

    run(state, repo=args.repo, ticket_key=args.ticket)
