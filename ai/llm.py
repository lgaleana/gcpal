from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI

from utils.io import print_assistant

load_dotenv()

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


def next(
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
) -> Tuple[Optional[str], Optional[str]]:
    response = call(
        messages,
        model,
        temperature,
        stop,
        stream=True,
        tools=tools,
        tool_choice=tool_choice,
    )

    message = None
    tool = None
    for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            message = stream(delta, message)
        elif delta.tool_calls:
            tool = collect_tool(delta, tool)
    print_assistant()
    return message, tool


def stream(delta, message: Optional[str]):
    if message is None:
        message = ""
    message += delta.content
    print_assistant(delta.content, end="", flush=True)
    return message


def collect_tool(delta, tool: Optional[str]):
    if tool is None:
        tool = ""
    tool += delta.tool_calls[0].function.arguments
    print_assistant(".", end="", flush=True)
    return tool
