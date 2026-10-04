"""Small GitHub API client for Actions; credentials never enter catalog files."""
import json
import os
from urllib.request import Request, urlopen


def api(path, method="GET", data=None):
    request = Request("https://api.github.com" + path,
                      data=json.dumps(data).encode() if data is not None else None,
                      method=method,
                      headers={"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
                               "Accept": "application/vnd.github+json",
                               "X-GitHub-Api-Version": "2022-11-28",
                               "User-Agent": "GameDecompLibrary",
                               "Content-Type": "application/json"})
    with urlopen(request, timeout=30) as response:
        body = response.read()
        return json.loads(body) if body else None
