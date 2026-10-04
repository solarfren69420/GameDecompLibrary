"""Shared catalog validation. Unknown progress stays unknown."""
import json
import math
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = {"decomp", "tool", "related", "unconfirmed"}


def https_url(value):
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password


def validate(entry):
    for key in ("id", "name", "url", "category", "group", "platform", "type", "description", "snapshot_date"):
        if not isinstance(entry.get(key), str):
            raise ValueError(f"{key} must be text")
    if not entry["name"].strip() or len(entry["name"]) > 300:
        raise ValueError("Project name must contain 1–300 characters")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", entry["id"]):
        raise ValueError("Invalid project ID")
    if not re.fullmatch(r"https://(?:github\.com|gitlab\.com)/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", entry["url"]):
        raise ValueError("Use a full GitHub or GitLab repository URL")
    if entry["category"] not in CATEGORIES:
        raise ValueError("Unknown project category")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", entry["snapshot_date"]):
        raise ValueError("snapshot_date must be YYYY-MM-DD")
    for key in ("sources", "notes"):
        if not isinstance(entry.get(key), list) or not all(isinstance(x, str) for x in entry[key]):
            raise ValueError(f"{key} must be a list of text values")
    if any(not https_url(x) for x in entry["sources"]):
        raise ValueError("Evidence URLs must use HTTPS")
    if entry.get("report_commit") and not https_url(entry["report_commit"]):
        raise ValueError("Invalid report commit URL")
    if not isinstance(entry.get("targets"), list):
        raise ValueError("targets must be a list")
    validate_progress(entry["progress"], entry["sources"], entry["category"])
    for target in entry["targets"]:
        if not all(isinstance(target.get(k), str) for k in ("name", "platform")):
            raise ValueError("Targets must have a name and platform")
        if not isinstance(target.get("notes"), list) or not all(isinstance(n, str) for n in target["notes"]):
            raise ValueError("Target notes must be text")
        validate_progress(target["progress"], entry["sources"], entry["category"])


def validate_progress(metric, sources, category):
    if metric.get("kind") not in {"reported", "unknown", "claim", "functions"}:
        raise ValueError("Invalid metric kind")
    if not isinstance(metric.get("label"), str):
        raise ValueError("Progress label must be text")
    for key in ("decompiled", "linked"):
        value = metric.get(key)
        if value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100:
                raise ValueError("Progress must be null or a number from 0 to 100")
            if metric["kind"] != "reported" or category != "decomp" or not sources:
                raise ValueError("Numeric progress requires a reported game metric and an evidence URL")


def load_projects():
    entries, urls = [], set()
    for path in sorted((ROOT / "data/projects").glob("*.json")):
        entry = json.loads(path.read_text())
        try:
            validate(entry)
            if path.stem != entry["id"]:
                raise ValueError("File name must match project ID")
            if entry["url"].lower() in urls:
                raise ValueError("Duplicate repository URL")
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{path.name}: {exc}") from exc
        urls.add(entry["url"].lower())
        entries.append(entry)
    if not entries:
        raise ValueError("Catalog is empty")
    return entries
