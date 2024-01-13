import json

from dotenv import load_dotenv

load_dotenv()

from agents import contributor
from agents.coder import WritePRParams
from workflows.coder import AGENT as CODER_AGENT
from tools import github
from tools.docker import commands as docker
from utils.io import user_input, print_system
from utils.state import Conversation, State


AGENT = "pr_coder"


def run(state: State) -> None:
    docker.startup()
    docker.pr_coder()

    conversation_context = state.conversation
    conversation = Conversation()

    comments_since = github.get_comments_since(6, "lgaleana-llm")
    conversation.add_user("You have new comments in your PR:")
    comment = comments_since[-1]
    conversation.add_user(
        f"{comment.author}: {comment.body}\n```{comment.diff_hunk}```"
    )

    while True:
        ai_action = contributor.next_action(conversation_context, conversation)
        if isinstance(ai_action, str):
            conversation.add_assistant(ai_action)
            user_message = user_input()
            conversation.add_user(
                f"{comment.author}: {user_message}\n```{comment.diff_hunk}```"
            )
        else:
            tool = contributor.AmendPRParams.model_validate(ai_action.arguments)
            print_system(tool)
            conversation.add_tool(
                tool_id=ai_action.id, arguments=json.dumps(ai_action.arguments)
            )
            user_message = user_input()


if __name__ == "__main__":
    state = State.load("1705016334.5167592", CODER_AGENT)
    run(state)
