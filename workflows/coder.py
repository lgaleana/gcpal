import argparse
import json
import os
import time

from dotenv import load_dotenv

load_dotenv()

from agents import coder
from tools import github
from tools import jira
from tools.docker import commands as docker
from utils.io import user_input, print_system
from utils.state import Conversation, State
from workflows.utils.coder import create_pr, rollback, TestsError


AGENT = "coder"


def run(state: State, ticket_key: str) -> None:
    tickets = jira.get_grouped_issues()
    codebase = github.get_repo_files()
    git_history = github.get_last_commits(n=10)
    active_ticket = jira.find_issue(tickets, ticket_key)
    assert active_ticket
    docker.startup()
    docker.coder()

    conversation = state.conversation

    while True:
        ai_action = coder.next_action(
            active_ticket, conversation, tickets, codebase, git_history
        )
        if isinstance(ai_action, str):
            conversation.add_assistant(ai_action)
            user_message = user_input()
            conversation.add_user(user_message)
        else:
            tool = coder.WritePRParams.model_validate(ai_action.arguments)
            print_system(tool)
            conversation.add_tool(
                tool_id=ai_action.id, arguments=json.dumps(ai_action.arguments)
            )

            user_message = user_input()
            if user_message != "y":
                conversation.add_tool_response(
                    tool_id=ai_action.id,
                    message=f"Didn't execute. Reason: user feedback :: {user_message}",
                )
                state.persist()
                continue

            try:
                pr_url = create_pr(tool, state.name)
                conversation.add_tool_response(
                    tool_id=ai_action.id,
                    message=(f"PR created successfully :: {pr_url}"),
                )
                print_system(pr_url)
            except Exception as e:
                print_system(f"!!!!! ERROR: {e}")
                rollback(tool.git_branch)
                conversation.add_tool_response(
                    tool_id=ai_action.id,
                    message=str(e),
                )
                if isinstance(e, TestsError):
                    conversation.add_user(
                        "Your tests had errors. Fix them and re-create the PR. Go."
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
