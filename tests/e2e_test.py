from unittest import TestCase

from main import run


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

    def test_persist_conversation(self):
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
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": "call_t5nyiRm0o9IV7YE357wOlrrt",
                            "type": "function",
                            "function": {
                                "name": "execute_shell",
                                "arguments": '{"id":"call_t5nyiRm0o9IV7YE357wOlrrt","name":"execute_shell","arguments":{"commands":["pip install fastapi","pip install uvicorn","echo \'from fastapi import FastAPI\\n\\napp = FastAPI()\\n\\n@app.get(\\"/\\")\\ndef read_root():\\n    return {\\"Hello\\": \\"World\\"}\' > main.py"]}}',
                            },
                        }
                    ],
                    "content": None,
                },
                {
                    "role": "tool",
                    "content": "Commands executed successfully.",
                    "tool_call_id": "call_t5nyiRm0o9IV7YE357wOlrrt",
                },
                {
                    "role": "assistant",
                    "content": "Great! The FastAPI application has been created successfully. The application is in a file named `main.py`. You can run the application using the following command:\n\n```bash\nuvicorn main:app --reload\n```\n\nThis command tells Uvicorn to run your application (`main:app`) and to automatically reload the server whenever a change is detected in your code. Let me know if you need further assistance!",
                },
                {"role": "user", "content": "persist conversation"},
            ]
        )
