# Share a project or improve an entry

You can contribute with a GitHub account. Repository ownership is not required to suggest a useful public project. Please credit its upstream maintainers accurately.

## Submit without editing code

1. Search [the catalog](CATALOG.md) for the repository URL.
2. Open [Submit a GitHub project](https://github.com/solarfren69420/GameDecompLibrary/issues/new?template=add-project.yml).
3. Supply the repository, platform or target, description and evidence URL.
4. Leave percentages blank unless a game decompilation publishes a numerical metric for that exact target.

SolarFren reviews the issue, then prepares a catalog pull request. An issue is a submission, not automatic acceptance. Your GitHub account is the contact.

## Correct an entry

Use [Update or correct an entry](https://github.com/solarfren69420/GameDecompLibrary/issues/new?template=update-project.yml) and include an upstream source. You can also edit that project's JSON file and send a pull request. Preserve the prior sources when they explain a historical claim.

## Send a pull request

Copy [`examples/project.json`](examples/project.json) into `data/projects/owner--repository.json`, replace the example fields, and keep the file name equal to the `id` field. Use one entry per upstream repository; list multiple game targets under `targets` when one repository covers several titles.

| Field | Meaning |
| --- | --- |
| `category` | `decomp`, `tool`, `related`, or `unconfirmed` |
| `group` | Existing catalog group or `Community submissions` |
| `platform` | Platform plus version/region where useful; for tools, indicate scope |
| `progress.decompiled` / `progress.linked` | A cited number from 0–100, or `null` |
| `progress.kind` | `reported`, `unknown`, `claim`, or `functions` |
| `progress.label` | Original wording and denominator/scope qualifications |
| `sources` | HTTPS evidence URLs supporting scope and progress |
| `snapshot_date` | Date the source was checked, `YYYY-MM-DD` |
| `report_date` / `report_commit` | Underlying report timestamp and commit, if published |
| `notes` | Source wording, limitations and target-specific qualifications |
| `method_tags` | Optional method entries with `id`, HTTPS `source`, a scope `note` and `checked_at` date; see [`data/methods.json`](data/methods.json) for supported IDs |

Use `null` for unknown numerical values. Use `claim` with a null numeric value for qualitative completion statements, and `functions` for function-count progress. Put the exact wording in `progress.label` and `notes`. Tools, ports and source releases keep numeric game-progress fields null.

Method tags can overlap. A project may publish Ghidra pseudocode and also develop matching source. Do not infer either tag from a percentage or a mention of Ghidra alone. A matching tag describes the reconstruction target; it does not certify a finished game or human-only authorship. Leave `method_tags` empty when evidence is unclear. The submission form accepts methods only with an evidence URL and scope note; maintainer review still applies.

```json
"method_tags": [
  {
    "id": "matching-decompilation",
    "source": "https://github.com/owner/repository#readme",
    "note": "The upstream README describes source targeting the original compiled binary.",
    "checked_at": "2026-10-05"
  }
]
```

Run the checks if you have Python and Node:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py
node --check web/app.js
```

Only edit source records and the files you intend to change. GitHub Actions regenerates `CATALOG.md` and README counts after merge. The archived list in `sources/` records the original import.
