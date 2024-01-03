import base64
import os
import requests
from typing import List, NamedTuple, Optional


GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


class GithubFile(NamedTuple):
    name: str
    content: str


def get_repo_files() -> Optional[List[Optional[GithubFile]]]:
    response = requests.get(
        "https://api.github.com/repos/lgaleana/email-sequences/git/trees/main?recursive=1",
        headers=HEADERS,
    )

    file_contents = []
    if response.status_code == 200:
        repo_data = response.json()
        for file in repo_data["tree"]:
            if file["type"] == "blob":  # Make sure it's a file
                file_contents.append(get_file_contents(file["path"]))
        return file_contents

    return None


def get_file_contents(file_path: str) -> Optional[GithubFile]:
    response = requests.get(
        f"https://api.github.com/repos/lgaleana/email-sequences/contents/{file_path}",
        headers=HEADERS,
    )
    if response.status_code == 200:
        file_data = response.json()
        # Decode the base64 content
        content = base64.b64decode(file_data["content"]).decode("utf-8")
        return GithubFile(file_data["name"], content)

    return None
