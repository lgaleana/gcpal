import base64
import os
import requests
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional


GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


class GithubFile(BaseModel):
    name: str
    content: str


class Commit(BaseModel):
    sha: str
    author: str
    date: datetime
    message: str


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
        return GithubFile(name=file_data["name"], content=content)

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


def print_repo():
    files = get_repo_files()
    if not files:
        return

    for file in files:
        if file:
            print(file.name)
            print("```")
            print(file.content)
            print("```")
            print()


def print_commits():
    commits = get_last_commits(10)
    for commit in commits:
        date = commit.date.strftime("%a %b %d %H:%M:%S %Y")
        print(
            f"commit {commit.sha}\nAuthor: {commit.author}\nDate:   {date}\n\n    {commit.message}\n"
        )
