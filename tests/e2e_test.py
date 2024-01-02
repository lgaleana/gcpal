from unittest import TestCase

from chat_main import run


class Tests(TestCase):
    def test_fastapi(self):
        run(
            [
                {
                    "role": "assistant",
                    "content": "Hello! How can I assist you with your software development today?",
                },
                {"role": "user", "content": "i want to build a fastapi app"},
                {
                    "role": "assistant",
                    "content": 'Sure, I can guide you through the process of creating a FastAPI application. Here are the steps:\n\n1. **Install FastAPI**: FastAPI is a Python library, so you need to have Python installed on your system. You can install FastAPI using pip, Python\'s package installer. Here is the command to install FastAPI:\n\n```bash\npip install fastapi\n```\n\n2. **Install Uvicorn**: Uvicorn is an ASGI server that you will need to serve your FastAPI application. You can install it using pip as well:\n\n```bash\npip install uvicorn\n```\n\n3. **Create a new FastAPI application**: Now you can create a new FastAPI application. Here is a simple example of a FastAPI application:\n\n```python\nfrom fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/")\ndef read_root():\n    return {"Hello": "World"}\n```\n\nYou can save this code in a file named `main.py`.\n\n4. **Run the application**: You can run the FastAPI application using Uvicorn with the following command:\n\n```bash\nuvicorn main:app --reload\n```\n\nThis command tells Uvicorn to run your application (`main:app`) and to automatically reload the server whenever a change is detected in your code.\n\nLet me know if you need help with any of these steps!',
                },
                {"role": "user", "content": "build the app"},
            ]
        )

    def test_remove_command(self):
        run(
            [
                {
                    "role": "assistant",
                    "content": "Hello! How can I assist you with your software development today?",
                },
                {"role": "user", "content": "i want to build a fastapi app"},
                {
                    "role": "assistant",
                    "content": 'Sure, I can guide you through the process of creating a FastAPI application. Here are the steps:\n\n1. **Install FastAPI**: FastAPI is a Python library, so you need to have Python installed on your system. You can install FastAPI using pip, Python\'s package installer. Here is the command to install FastAPI:\n\n```bash\npip install fastapi\n```\n\n2. **Install Uvicorn**: Uvicorn is an ASGI server that you will need to serve your FastAPI application. You can install it using pip as well:\n\n```bash\npip install uvicorn\n```\n\n3. **Create a new FastAPI application**: Now you can create a new FastAPI application. Here is a simple example of a FastAPI application:\n\n```python\nfrom fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/")\ndef read_root():\n    return {"Hello": "World"}\n```\n\nYou can save this code in a file named `main.py`.\n\n4. **Run the application**: You can run the FastAPI application using Uvicorn with the following command:\n\n```bash\nuvicorn main:app --reload\n```\n\nThis command tells Uvicorn to run your application (`main:app`) and to automatically reload the server whenever a change is detected in your code.\n\nLet me know if you need help with any of these steps!',
                },
                {"role": "user", "content": "build the app"},
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "call_kUIXtOgV8qGyKfqrxYb7yDSy",
                            "type": "function",
                            "function": {
                                "name": "execute_shell",
                                "arguments": '{"commands":["pip install fastapi","pip install uvicorn","echo \'from fastapi import FastAPI\\n\\napp = FastAPI()\\n\\n@app.get(\\"/\\")\\ndef read_root():\\n    return {\\"Hello\\": \\"World\\"}\' > main.py","uvicorn main:app --reload"]}',
                            },
                        }
                    ],
                    "content": None,
                },
                {
                    "role": "tool",
                    "content": "Commands not executed. Reason :: user feedback.",
                    "tool_call_id": "call_kUIXtOgV8qGyKfqrxYb7yDSy",
                },
                {"role": "user", "content": "remove the uvicorn command"},
            ]
        )

    def test_load_conversation(self):
        run(
            [
                {
                    "role": "assistant",
                    "content": "Hello! How can I assist you with your software engineering tasks today?",
                },
                {"role": "user", "content": "i want to build a fastapi app"},
                {
                    "role": "assistant",
                    "content": "Great! FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints. Here are the steps to create a new FastAPI application:\n\n1. First, we need to create a new directory for your project. Let's call it `fastapi_app`.\n2. Then, we need to navigate into this new directory.\n3. We'll create a new virtual environment in this directory. This helps to keep the dependencies required by different projects separate by creating isolated python environments for them.\n4. We'll activate the virtual environment.\n5. After that, we'll install FastAPI and a ASGI server, such as Uvicorn.\n6. Finally, we'll create a new file `main.py` for your FastAPI application.\n\nLet's start by creating the new directory and setting up the virtual environment. Here are the shell commands for these steps:\n\n```shell\nmkdir fastapi_app\ncd fastapi_app\npython3 -m venv venv\nsource venv/bin/activate\npip install fastapi uvicorn\ntouch main.py\n```\n\nPlease note that these commands are for MacOS. If you're using a different operating system, the commands might be slightly different.",
                },
                {"role": "user", "content": "persist"},
                {
                    "role": "user",
                    "content": "Please persist the conversation into disk.",
                },
                {"role": "system", "content": "Conversation persisted successfully."},
                {
                    "role": "system",
                    "content": (
                        "Conversation loaded. Please resume the conversation where it was left. "
                        "Commands are only executed through the `execute_shell` tool."
                    ),
                },
            ]
        )
