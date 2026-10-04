import os
from urllib.error import HTTPError
from github_api import api

repo = os.environ["GITHUB_REPOSITORY"]
labels = {
    "submission": ("0969da", "A proposed new library project"),
    "needs-review": ("d4a72c", "Awaiting maintainer review"),
    "approved": ("138447", "Maintainer approved: prepare a catalog pull request"),
    "catalog-update": ("8250df", "An existing entry needs a correction"),
}
for name, (color, description) in labels.items():
    try:
        api(f"/repos/{repo}/labels", "POST", {"name": name, "color": color, "description": description})
        print("Created label:", name)
    except HTTPError as error:
        if error.code != 422:
            raise
        print("Label already exists:", name)
