"""Validate entries and build the dependency-free library and GitHub index."""
import argparse
import html
import json
import shutil
from collections import Counter
from pathlib import Path
from catalog import ROOT, load_projects, https_url

REPO = "https://github.com/solarfren69420/GameDecompLibrary"


def md(text):
    return html.escape(str(text)).replace("|", "\\|").replace("[", "\\[").replace("]", "\\]").replace("\n", " ")


def progress(entry):
    metric = entry["progress"]
    if metric["decompiled"] is not None:
        return f"{metric['decompiled']:g}%"
    if metric["kind"] == "claim":
        return "Maintainer completion claim"
    if metric["kind"] == "functions":
        return "100% matching functions"
    return "N/A" if entry["category"] in {"tool", "related"} else "Not published / see scope"


def build(update_docs=False):
    entries = load_projects()
    counts = Counter(e["category"] for e in entries)
    out = ROOT / "_site"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / "web", out)
    # Keep first-import prominence order; new community projects follow it.
    order_path = ROOT / "data/order.json"
    order = json.loads(order_path.read_text()) if order_path.exists() else []
    priorities = {entry_id: i for i, entry_id in enumerate(order)}
    entries.sort(key=lambda e: (priorities.get(e["id"], len(order)), e["name"].casefold()))
    discoveries = json.loads((ROOT / "data/discovery.json").read_text())
    if not isinstance(discoveries, list) or not all(isinstance(url, str) and https_url(url) for url in discoveries):
        raise ValueError("Discovery links must be HTTPS URLs")
    catalog = {"repository": REPO, "counts": dict(counts), "projects": entries,
               "discovery": discoveries,
               "latest_snapshot": max(e["snapshot_date"] for e in entries)}
    (out / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False) + "\n")
    (out / ".nojekyll").touch()
    if update_docs:
        titles = {"decomp": "Game decompilations", "tool": "Bindings and tools", "related": "Ports, recompilations and source releases", "unconfirmed": "Unconfirmed original links"}
        lines = ["# Full project catalog", "", "Generated from `data/projects/`. Edit an individual project file to update an entry.", "",
                 "Percentages describe a cited target and snapshot, not overall game completion. Linked progress is a separate metric. Unknown values are never zero. Build and test results are not asserted by this library.", "",
                 "[Submit a project](" + REPO + "/issues/new?template=add-project.yml) · [Browse the library](https://solarfren69420.github.io/GameDecompLibrary/)", ""]
        for category, title in titles.items():
            lines += [f"## {title}", ""]
            groups = list(dict.fromkeys(e["group"] for e in entries if e["category"] == category))
            for group in groups:
                lines += [f"### {md(group or 'Community submissions')}", "", "| Project / repository | Platform or type | Decompiled | Linked | Evidence / snapshot |", "| --- | --- | --- | --- | --- |"]
                for e in entries:
                    if e["category"] != category or e["group"] != group:
                        continue
                    linked = f"{e['progress']['linked']:g}%" if e['progress']['linked'] is not None else "—"
                    source = f"[Source]({e['sources'][0]})" if e["sources"] else "Unverified"
                    file = f"data/projects/{e['id']}.json"
                    platform = e["type"] if category in {"tool", "related"} else e["platform"]
                    lines.append(f"| [{md(e['name'])}]({e['url']}) · [details]({file}) | {md(platform)} | {progress(e)} | {linked} | {source} · {e['snapshot_date']} |")
                lines.append("")
        (ROOT / "CATALOG.md").write_text("\n".join(lines).rstrip() + "\n")
        path = ROOT / "README.md"
        readme = path.read_text()
        start, end = "<!-- catalog-stats:start -->", "<!-- catalog-stats:end -->"
        before, _, tail = readme.partition(start)
        _, _, after = tail.partition(end)
        block = f"\n**{len(entries)} projects** · {counts['decomp']} game projects · {counts['tool']} tools · {counts['related']} related projects · {counts['unconfirmed']} unconfirmed link\n"
        path.write_text(before + start + block + end + after)
    print(f"Validated {len(entries)} entries; built {out}")
    return catalog


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-docs", action="store_true")
    build(parser.parse_args().update_docs)
