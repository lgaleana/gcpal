import argparse
import json
import os
import time
import traceback

from dotenv import load_dotenv

load_dotenv()

from agents import coder
from ai_tools import sumamrize_test_failure
from tools import github
from tools import jira
from tools.docker.commands import DockerRunner
from utils.io import user_input, print_system
from utils.state import Conversation, State
from workflows.actions.coder_actions import create_pr, rollback, TestsError


AGENT = "coder"

TOOL_FAIL_MSG = "Fix the tests and re-create the PR. Go ahead."


def run(state: State, ticket_key: str) -> None:
    tickets = jira.get_grouped_issues()
    codebase = github.get_repo_files()
    active_ticket = jira.find_issue(tickets, ticket_key)
    assert active_ticket
    docker = DockerRunner(
        startup_commands=[
            "cd /home/app",
            "pwd",
            "source venv/bin/activate",
            "git pull origin main --rebase",
            "git checkout main",
        ]
    )

    conversation = state.conversation

    while True:
        ai_action = coder.next_action(active_ticket, conversation, codebase)
        if isinstance(ai_action, str):
            conversation.add_assistant(ai_action)
            user_message = user_input()
            conversation.add_user(user_message)
        else:
            tool = coder.WritePRParams.model_validate(ai_action.arguments)
            print_system(tool)
            conversation.add_tool(tool=ai_action)

            user_message = user_input()
            if user_message != "y":
                conversation.add_tool_response(
                    tool_id=ai_action.id,
                    message=f"Didn't execute. Reason: user feedback :: {user_message}",
                )
                state.persist()
                continue

            try:
                pr_url = create_pr(tool, state.name, docker)
                conversation.add_tool_response(
                    tool_id=ai_action.id,
                    message=(f"PR created successfully :: {pr_url}"),
                )
                print_system(pr_url)
            except Exception as e:
                print_system()
                print_system(f"!!!!! ERROR\n: {e}")
                traceback.print_tb(e.__traceback__)
                print_system()

                rollback(tool.git_branch, docker)
                conversation.remove_last_failed_tool(TOOL_FAIL_MSG)

                if isinstance(e, TestsError):
                    conversation.add_tool_response(
                        tool_id=ai_action.id,
                        message=sumamrize_test_failure(pr=tool, failure_msg=str(e)),
                    )
                    conversation.add_user(TOOL_FAIL_MSG)
                else:
                    conversation.add_tool_response(
                        tool_id=ai_action.id,
                        message=str(e),
                    )

        state.persist()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--last", action="store_true")
    group.add_argument("name", nargs="?")
    args = parser.parse_args()

    states_dir = f"db/{AGENT}/"
    if args.last:
        states = os.listdir("db/coder/")
        states = [f for f in states if os.path.isfile(os.path.join(states_dir, f))]
        states.sort()
        name = states[-1].replace(".json", "")
        state = State.load(name, AGENT)
    elif args.name:
        state = State.load(args.name, AGENT)
    else:
        state = State(name=str(time.time()), agent=AGENT, conversation=Conversation())

    run(state, "SBX-51")
