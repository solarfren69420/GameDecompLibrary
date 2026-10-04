"""One-time, lossless import of the supplied sourced link list."""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = re.compile(r"https://(?:github\.com|gitlab\.com)/[^/\s]+/[^/\s]+$")


def progress(label):
    number = re.search(r"([\d.]+)%", label)
    kind = "unknown"
    if number:
        kind = "reported"
        if "maintainer description" in label or "project description" in label:
            kind = "claim"
        elif "matching functions" in label:
            kind = "functions"
    return {"decompiled": float(number[1]) if number and kind == "reported" else None,
            "linked": None, "kind": kind, "label": label}


def parse(source):
    lines = source.read_text().splitlines()
    category, group = "decomp", ""
    entries, discoveries = [], []
    for i, line in enumerate(lines):
        if line.startswith("RUST BINDINGS AND TOOLS"):
            category = "tool"
        elif line.startswith("RELATED PORTS / RECOMPILATIONS"):
            category = "related"
        elif line == "OTHER HOSTS — NOT GITHUB":
            category, group = "decomp", "Other hosts"
        elif line == "UNCONFIRMED ORIGINAL LINK":
            category, group = "unconfirmed", "Unconfirmed original link"
        elif line == "DIRECTORIES / DISCOVERY":
            category = "discovery"
        if i + 1 < len(lines) and re.fullmatch(r"-{3,}", lines[i + 1]):
            group = line
        if category == "discovery" and line.startswith("https://"):
            discoveries.append(line)
            continue
        if not URL.fullmatch(line):
            continue
        name = re.sub(r"^T\d+\. ", "", lines[i - 1])
        details = []
        for detail in lines[i + 1:]:
            if not detail.startswith("  "):
                break
            details.append(detail.strip())
        fields = {}
        for detail in details:
            if ": " in detail:
                key, value = detail.split(": ", 1)
                fields[key] = value
        target_blocks, current = [], None
        for detail in details:
            if detail.startswith("Target: "):
                current = {"name": detail[8:], "platform": "Not specified",
                           "progress": progress("Not published"), "notes": []}
                target_blocks.append(current)
            elif current and detail.startswith("Platform: "):
                platform, _, label = detail[10:].partition(" | ")
                current.update(platform=platform, progress=progress(label))
            elif current and detail.startswith("Note: "):
                current["notes"].append(detail[6:])
        metric = progress("Not published")
        platform = "Not specified"
        if details and re.search(r"[\d.]+% decompiled", details[0]):
            parts = details[0].split(" | ")
            platform = parts[1]
            metric = progress(" | ".join(parts[2:]))
            linked = re.search(r"([\d.]+)% fully linked", details[0])
            if linked:
                metric["linked"] = float(linked[1])
        elif target_blocks:
            platform = target_blocks[0]["platform"]
            if len(target_blocks) == 1:
                metric = target_blocks[0]["progress"]
            else:
                metric = progress("Multiple targets — see project details")
        if category == "tool":
            platform, metric = "Cross-platform / project-specific", progress("Not applicable to tools")
        if category == "related":
            name, _, project_type = name.partition(" | ")
            metric = progress("Not applicable to this project category")
        else:
            project_type = fields.get("Type", "Game decompilation" if category == "decomp" else "Unconfirmed project")
        sources = list(dict.fromkeys(v for k, v in fields.items()
                                    if k in ("Evidence", "Progress source")))
        # Multi-target records may cite more than one source.
        sources = list(dict.fromkeys(sources + [d.split(": ", 1)[1] for d in details
                                                if d.startswith(("Evidence: ", "Progress source: "))]))
        repo = "/".join(line.split("/")[3:])
        entry_id = re.sub(r"[^a-z0-9-]+", "-", repo.lower().replace("/", "--"))
        entries.append({"id": entry_id, "name": name, "url": line,
                        "category": category, "group": group, "platform": platform,
                        "type": project_type, "description": fields.get("Helps with", ""),
                        "progress": metric, "targets": target_blocks, "sources": sources,
                        "notes": details, "snapshot_date": "2026-10-04",
                        "report_date": fields.get("Report commit date", ""),
                        "report_commit": fields.get("Report commit", "")})
    return entries, discoveries


def main():
    source = Path(sys.argv[1])
    destination = ROOT / "data/projects"
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.glob("*.json")):
        raise SystemExit("Import refused: project files already exist. Edit those files instead.")
    entries, discoveries = parse(source)
    for entry in entries:
        (destination / (entry["id"] + ".json")).write_text(json.dumps(entry, indent=2, ensure_ascii=False) + "\n")
    archive = ROOT / "sources"
    archive.mkdir(exist_ok=True)
    shutil.copyfile(source, archive / source.name)
    (ROOT / "data/discovery.json").write_text(json.dumps(discoveries, indent=2) + "\n")
    from collections import Counter
    print(f"Imported {len(entries)} projects: {dict(Counter(e['category'] for e in entries))}")


if __name__ == "__main__":
    main()
