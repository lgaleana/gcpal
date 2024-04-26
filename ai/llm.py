from typing import Any, Dict, List, Optional, Union

import json
from pydantic import BaseModel
from openai import OpenAI

from utils.io import print_assistant


class RawTool(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]


client = OpenAI()


MODEL = "gpt-4"
TEMPERATURE = 0.0


def call(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    stop: Optional[str] = None,
    stream: bool = False,
    tools: Optional[List] = None,
    tool_choice="auto",
):
    if not model:
        model = MODEL
    if temperature is None:
        temperature = TEMPERATURE

    if tools is not None:
        return client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stop=stop,
            stream=stream,
            tools=tools,
            tool_choice=tool_choice,
        )
    return client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stop=stop,
        stream=stream,
    )


def gen(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    stop: Optional[str] = None,
) -> str:
    return call(messages, model, temperature, stop, stream=False)["choices"][0][
        "message"
    ]["content"]


def stream_next(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    stop: Optional[str] = None,
    tools: Optional[List] = None,
    tool_choice="auto",
) -> Union[str, RawTool]:
    response = call(
        messages,
        model,
        temperature,
        stop,
        stream=True,
        tools=tools,
        tool_choice=tool_choice,
    )

    first_chunk = next(response)
    if first_chunk.choices[0].delta.content is not None:
        return stream_text(first_chunk, response)
    return collect_tool(first_chunk, response)


def stream_text(first_chunk, response) -> str:
    message = first_chunk.choices[0].delta.content
    print_assistant(first_chunk.choices[0].delta.content, end="", flush=True)
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            message += chunk.choices[0].delta.content
            print_assistant(chunk.choices[0].delta.content, end="", flush=True)
    print_assistant()
    return message


def collect_tool(first_chunk, response) -> RawTool:
    tool_id = first_chunk.choices[0].delta.tool_calls[0].id
    tool_name = first_chunk.choices[0].delta.tool_calls[0].function.name
    arguments = first_chunk.choices[0].delta.tool_calls[0].function.arguments
    print_assistant(".", end="", flush=True)
    for chunk in response:
        if chunk.choices[0].delta.tool_calls:
            arguments += chunk.choices[0].delta.tool_calls[0].function.arguments
        print_assistant(".", end="", flush=True)
    print_assistant()

    # print(arguments)
    arguments = arguments.replace(r"\\'", "<ESCAPED_QUOTE>").replace(
        r"\'", "<ESCAPED_QUOTE>"
    )
    arg_dict = json.loads(arguments)
    arg_dict = unesacape_str(arg_dict)
    # print(json.dumps(arg_dict, indent=2))

    return RawTool(id=tool_id, name=tool_name, arguments=arg_dict)


def unesacape_str(val: Any) -> Any:
    if isinstance(val, str):
        return val.replace("<ESCAPED_QUOTE>", "\\'")
    if isinstance(val, List):
        return [unesacape_str(v) for v in val]
    if isinstance(val, Dict):
        return {k: unesacape_str(v) for k, v in val.items()}
    return val
