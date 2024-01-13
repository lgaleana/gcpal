import argparse
import json
import time

from dotenv import load_dotenv

load_dotenv()

from agents import contributor
from workflows.write_pr import AGENT as CODER_AGENT
from tools import github
from tools.docker import commands as docker
from utils.io import user_input, print_system
from utils.state import Conversation, State
from workflows.actions.coder_actions import TestsError
from workflows.actions.contributor_actions import edit_pr, rollback


AGENT = "contributor"


def run(context_state: State, state: State, pr_number: int, git_branch: str) -> None:
    docker.startup()
    docker.pr_coder()

    conversation = state.conversation

    comments_since = github.get_comments_since(pr_number, "lgaleana-llm")
    conversation.add_user("You have new comments in your PR:")
    comment = comments_since[-1]
    print_system(comment)
    conversation.add_user(str(comment))

    ai_action = contributor.next_action(context_state.conversation, conversation)
    if isinstance(ai_action, str):
        conversation.add_assistant(ai_action)
        user_message = user_input()
        if user_message == "y":
            github.reply_to_comment(pr_number, comment.id, reply=ai_action)
            print_system("Comment saved ::")
        else:
            print_system("Comment not saved.")
    else:
        tool = contributor.AmendPRParams(
            git_branch=git_branch,
            pr_url="https://github.com/lgaleana/email-sequences/pull/6",
            **ai_action.arguments,
        )
        print_system(tool)
        conversation.add_tool(
            tool_id=ai_action.id, arguments=json.dumps(ai_action.arguments)
        )

        user_message = user_input()
        if user_message != "y":
            print_system("PR not amended.")
            return

        try:
            pr_url = edit_pr(tool, state.name)
            conversation.add_tool_response(
                tool_id=ai_action.id,
                message=(f"PR amended successfully :: {pr_url}"),
            )
            print_system(pr_url)
        except Exception as e:
            print_system(f"!!!!! ERROR: {e}")
            rollback()
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
    parser.add_argument("context", type=str)
    parser.add_argument("name", type=str, default=None)
    args = parser.parse_args()

    states_dir = f"db/{AGENT}/"
    if args.name:
        state = State.load(args.name, AGENT)
    else:
        state = State(name=str(time.time()), agent=AGENT, conversation=Conversation())
    context_state = State.load(args.context, CODER_AGENT)

    run(context_state, state, 6, "SBX-50-database-schema")
