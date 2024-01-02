from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

from ai_tasks import pm as chat
from utils import jira
from utils.io import user_input, print_system
from utils.state import Conversation


def run(_conversation: List[Dict[str, Any]] = []) -> None:
    conversation = Conversation()
    while True:
        ai_action = chat.next_action(conversation)

        if isinstance(ai_action, str):
            conversation.add_assistant(ai_action)
            user_message = user_input()
            conversation.add_user(user_message)
        else:
            assert isinstance(ai_action, chat.Tool)
            conversation.add_tool(
                tool_id=ai_action.id,
                arguments=ai_action.arguments.model_dump_json(),
            )
            # issue = jira.create_issue(
            #     ai_action.arguments.type_,
            #     ai_action.arguments.title,
            #     ai_action.arguments.description,
            #     ai_action.arguments.parent_key,
            # )
            # print_system(issue)
            conversation.add_tool_response(
                tool_id=ai_action.id,
                message=f"Response :: done",
            )


if __name__ == "__main__":
    run()
