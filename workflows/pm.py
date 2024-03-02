import argparse
import time


from dotenv import load_dotenv

load_dotenv()

from agents import pm
from tools import jira
from utils.io import user_input, print_system
from utils.state import Conversation, State


AGENT = "pm"


def run(state: State, project: str) -> None:
    conversation = state.conversation

    while True:
        ai_action = pm.next_action(conversation)

        if isinstance(ai_action, str):
            conversation.add_assistant(ai_action)
            user_message = user_input()
            conversation.add_user(user_message)
        else:
            tool = pm.FileIssueParams.model_validate(ai_action.arguments)
            print_system(tool)
            conversation.add_tool(ai_action)

            issue = jira.create_issue(
                tool.type_,
                project,
                tool.title,
                tool.description,
                tool.parent_key,
            )
            print_system(issue)
            conversation.add_tool_response(
                tool_id=ai_action.id,
                message=f"Issue created successfuly. Key :: {issue['key']}.",
            )

        state.persist()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=str)
    parser.add_argument("--name", type=str, default=None)
    args = parser.parse_args()

    states_dir = f"db/{AGENT}/"
    if args.name:
        state = State.load(args.name, AGENT)
    else:
        state = State(name=str(time.time()), agent=AGENT, conversation=Conversation())

    run(state, args.project)
