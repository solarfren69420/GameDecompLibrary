"""Prepare a reviewed issue as a PR. Never merge or modify the default branch."""
import base64
import json
import os
import re
from datetime import date
from urllib.error import HTTPError
from urllib.parse import quote
from catalog import METHODS, load_projects, validate
from github_api import api

CATEGORY_MAP = {"Game decompilation": "decomp", "Binding or tool": "tool",
                "Port, recompilation, reimplementation or source release": "related"}


def fields_from_body(body):
    fields = {}
    for match in re.finditer(r"^### (.+)\n+([\s\S]*?)(?=^### |\Z)", body, re.MULTILINE):
        value = match[2].strip()
        fields[match[1].strip()] = "" if value == "_No response_" else value
    return fields


def percentage(value):
    if not value:
        return None
    if not re.fullmatch(r"\d+(?:\.\d+)?%?", value):
        raise ValueError("Use a single published percentage or leave the field blank")
    number = float(value.rstrip("%"))
    if not 0 <= number <= 100:
        raise ValueError("Percentages must be between 0 and 100")
    return number


def entry_from_issue(issue):
    fields = fields_from_body(issue.get("body") or "")
    required = ["Project name", "Repository URL", "Project category", "Platform / target", "What does it do?", "Evidence URL"]
    if any(not fields.get(k) for k in required):
        raise ValueError("Use the project submission form and complete its required fields")
    url = fields["Repository URL"].strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    if fields["Project category"] not in CATEGORY_MAP:
        raise ValueError("Invalid category")
    category = CATEGORY_MAP[fields["Project category"]]
    decompiled, linked = percentage(fields.get("Published progress %", "")), percentage(fields.get("Fully linked %", ""))
    if category != "decomp" and (decompiled is not None or linked is not None):
        raise ValueError("Tools and related projects must leave game-progress fields blank")
    entry_id = re.sub(r"[^a-z0-9-]+", "-", "--".join(url.split("/")[3:]).lower())
    metric = {"decompiled": decompiled, "linked": linked,
              "kind": "reported" if decompiled is not None or linked is not None else "unknown",
              "label": f"Published target: {decompiled}% decompiled; {linked}% fully linked" if decompiled is not None or linked is not None else "Not published"}
    entry = {"id": entry_id, "name": fields["Project name"], "url": url,
             "category": category, "group": "Community submissions", "platform": fields["Platform / target"],
             "type": fields["Project category"], "description": fields["What does it do?"],
             "progress": metric, "targets": [], "sources": [fields["Evidence URL"]],
             "notes": [fields["Notes / scope"]] if fields.get("Notes / scope") else [],
             "snapshot_date": date.today().isoformat(), "report_date": "", "report_commit": ""}
    method_names = [name.strip() for name in re.split(r",|\n", fields.get("Reconstruction methods", "")) if name.strip()]
    if method_names:
        by_label = {value["label"]: key for key, value in METHODS.items()}
        if any(name not in by_label for name in method_names):
            raise ValueError("Choose supported reconstruction methods")
        if not fields.get("Method evidence URL") or not fields.get("Method scope"):
            raise ValueError("Selected methods require their evidence URL and scope")
        entry["method_tags"] = [
            {"id": by_label[name], "source": fields["Method evidence URL"],
             "note": fields["Method scope"], "checked_at": date.today().isoformat()}
            for name in method_names
        ]
    validate(entry)
    return entry


def main():
    repo = os.environ["GITHUB_REPOSITORY"]
    actor = os.environ["SUBMISSION_ACTOR"]
    issue_number = int(os.environ["ISSUE_NUMBER"])
    permission = api(f"/repos/{repo}/collaborators/{quote(actor, safe='')}/permission")
    if permission.get("permission") not in {"admin", "write", "maintain"}:
        raise PermissionError("Only a repository maintainer can approve catalog submissions")
    issue = api(f"/repos/{repo}/issues/{issue_number}")
    if issue.get("pull_request") or issue.get("state") != "open":
        raise ValueError("Select an open project-submission issue")
    if "submission" not in {label["name"] for label in issue["labels"]}:
        raise ValueError("The issue must have the submission label")
    entry = entry_from_issue(issue)
    if any(p["url"].casefold() == entry["url"].casefold() for p in load_projects()):
        raise ValueError("This repository is already in the library; use the update form or edit its entry")
    default = api(f"/repos/{repo}")["default_branch"]
    head = api(f"/repos/{repo}/git/ref/heads/{quote(default, safe='')}")["object"]["sha"]
    branch = f"catalog/issue-{issue_number}"
    try:
        api(f"/repos/{repo}/git/refs", "POST", {"ref": "refs/heads/" + branch, "sha": head})
    except HTTPError as error:
        if error.code != 422:
            raise
        api(f"/repos/{repo}/git/ref/heads/{branch}")
    path = f"data/projects/{entry['id']}.json"
    payload = {"message": f"Add reviewed project from issue #{issue_number}", "branch": branch,
               "content": base64.b64encode((json.dumps(entry, ensure_ascii=False, indent=2) + "\n").encode()).decode()}
    try:
        existing = api(f"/repos/{repo}/contents/{path}?ref={quote(branch, safe='')}")
        payload["sha"] = existing["sha"]
    except HTTPError as error:
        if error.code != 404:
            raise
    api(f"/repos/{repo}/contents/{path}", "PUT", payload)
    prs = api(f"/repos/{repo}/pulls?head={quote(repo.split('/')[0]+':'+branch, safe='')}&state=open")
    if prs:
        print("Pull request already prepared:", prs[0]["html_url"])
        return
    try:
        pr = api(f"/repos/{repo}/pulls", "POST", {"title": "Add " + entry["name"], "head": branch, "base": default,
                 "body": f"Add a maintainer-reviewed submission to the library.\n\nRepository: {entry['url']}\nEvidence: {entry['sources'][0]}\n\nCloses #{issue_number}\n\nCatalog validation passed during preparation. This PR was created with GITHUB_TOKEN; run the catalog check manually if GitHub suppresses automatic checks for bot-created PRs."})
        print("Prepared:", pr["html_url"])
    except HTTPError as error:
        if error.code != 403:
            raise
        compare = f"https://github.com/{repo}/compare/{quote(default, safe='')}...{quote(branch, safe='')}?expand=1"
        api(f"/repos/{repo}/issues/{issue_number}/comments", "POST", {"body": "The approved entry is ready on a review branch. GitHub did not allow Actions to open a pull request; open it here: " + compare})
        print("Review branch prepared:", compare)


if __name__ == "__main__":
    main()
