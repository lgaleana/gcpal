import json
import traceback
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

from ai_tasks import chat
from utils.io import user_input


def run() -> None:
    conversation = []
    while True:
        ai_action = chat.next_action(conversation)

        if not ai_action.tool:
            conversation.append({"role": "assistant", "content": ai_action.message})
            user_message = user_input()
            conversation.append({"role": "user", "content": user_message})
        else:
            print(ai_action.tool.dict())
            break


if __name__ == "__main__":
    run()
