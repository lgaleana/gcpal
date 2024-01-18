import argparse
import time
import traceback

from dotenv import load_dotenv

load_dotenv()

from agents import contributor
from workflows.write_pr import AGENT as CODER_AGENT, TOOL_FAIL_MSG
from tools import github
from tools.docker.commands import DockerRunner
from utils.io import user_input, print_system
from utils.state import Conversation, State
from workflows.actions.coder_actions import TestsError
from workflows.actions.contributor_actions import edit_pr, rollback


AGENT = "contributor"


def run(context_state: State, state: State, pr_number: int, git_branch: str) -> None:
    docker = DockerRunner(
        startup_commands=[
            "cd /home/app",
            "pwd",
            "source venv/bin/activate",
            "git checkout main",
            "git pull origin main --rebase",
        ]
    )

    conversation = state.conversation

    comments_since = github.get_comments_since(pr_number, "lgaleana-llm")
    conversation.add_user("You have new comments in the PR:")

    for comment in comments_since:
        print_system(comment)
        conversation.add_system(str(comment))

        ai_action = contributor.next_action(
            context_state.conversation, conversation, pr_number
        )
        if isinstance(ai_action, str):
            conversation.add_assistant(ai_action)
            user_message = user_input()
            if user_message == "y":
                github.reply_to_comment(pr_number, comment.id, reply=ai_action)
                print_system("Comment saved ::")
                conversation.add_system("Comment saved. Next comment...")
            else:
                print_system("Comment not saved.")
        else:
            tool = contributor.AmendPRParams(
                git_branch=git_branch,
                pr_url=f"https://github.com/lgaleana/email-sequences/pull/{pr_number}",
                **ai_action.arguments,
            )
            print_system(tool)
            conversation.add_tool(tool=ai_action)

            user_message = user_input()
            if user_message != "y":
                print_system("PR not amended.")
                return

            try:
                pr_url = edit_pr(tool, state.name, docker)
                conversation.add_tool_response(
                    tool_id=ai_action.id,
                    message=(f"PR amended successfully :: {pr_url}"),
                )
                print_system(pr_url)
            except Exception as e:
                print_system()
                print_system(f"!!!!! ERROR: {e}")
                traceback.print_tb(e.__traceback__)
                print_system()

                rollback(git_branch, docker)
                conversation.remove_last_failed_tool(TOOL_FAIL_MSG)

                conversation.add_tool_response(
                    tool_id=ai_action.id,
                    message=str(e),
                )
                if isinstance(e, TestsError):
                    conversation.add_user(TOOL_FAIL_MSG)

        state.persist()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("context", type=str)
    parser.add_argument("--name", type=str, default=None)
    args = parser.parse_args()

    states_dir = f"db/{AGENT}/"
    if args.name:
        state = State.load(args.name, AGENT)
    else:
        state = State(name=str(time.time()), agent=AGENT, conversation=Conversation())
    context_state = State.load(args.context, CODER_AGENT)

    run(context_state, state, 8, "SBX-51-create-email-schedule-endpoint")
