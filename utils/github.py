import base64
import os
import requests
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional


GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


class GithubFile(BaseModel):
    path: str
    content: str

    def __str__(self) -> str:
        return f"{self.path}\n" "```\n" f"{self.content}\n" "```"


class Commit(BaseModel):
    sha: str
    author: str
    date: datetime
    message: str

    def __str__(self) -> str:
        date = self.date.strftime("%a %b %d %H:%M:%S %Y")
        return (
            "commit {self.sha}\n"
            f"Author: {self.author}\n"
            f"Date:   {date}\n\n"
            f"    {self.message}"
        )


def get_repo_files() -> List[Optional[GithubFile]]:
    response = requests.get(
        "https://api.github.com/repos/lgaleana/email-sequences/git/trees/main?recursive=1",
        headers=HEADERS,
    )
    response.raise_for_status()

    file_contents = []
    repo_data = response.json()
    for file in repo_data["tree"]:
        if file["type"] == "blob":  # Make sure it's a file
            file_contents.append(get_file_contents(file["path"]))
    return file_contents


def get_file_contents(file_path: str) -> Optional[GithubFile]:
    response = requests.get(
        f"https://api.github.com/repos/lgaleana/email-sequences/contents/{file_path}",
        headers=HEADERS,
    )
    if response.status_code == 200:
        file_data = response.json()
        # Decode the base64 content
        content = base64.b64decode(file_data["content"]).decode("utf-8")
        return GithubFile(path=file_path, content=content)

    return None


def get_last_commits(n: int):
    response = requests.get(
        "https://api.github.com/repos/lgaleana/email-sequences/commits"
    )
    response.raise_for_status()
    commits = response.json()
    return [
        Commit(
            sha=c["sha"],
            author=c["commit"]["author"]["name"],
            date=datetime.fromisoformat(c["commit"]["author"]["date"]),
            message=c["commit"]["message"],
        )
        for c in commits[:n]
    ]
