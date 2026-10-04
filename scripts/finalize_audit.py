"""Finalize this dated audit after source review; emit one self-contained README.

This is an explicit audit step, not part of ordinary catalog builds. New catalog
edits must not silently inherit the verification status of this dated snapshot.
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from catalog import ROOT, load_projects
from build import md

CACHE = Path('/tmp/game-decomp-source-audit')
REPO = 'https://github.com/solarfren69420/GameDecompLibrary'


def body(url):
    return (CACHE / (hashlib.sha256(url.encode()).hexdigest() + '.body')).read_text()


def main():
    records = load_projects()
    entries = {e['id']: e for e in records}
    path = ROOT / 'sources/audit-results.json'
    report = json.loads(path.read_text())
    changes = json.loads((ROOT / 'sources/audit-changes.json').read_text())
    for result in report['projects']:
        entry = entries[result['id']]
        metric = result['metric']
        if metric['status'] == 'manual-review-required':
            source = entry['sources'][0]
            text = body(source)
            if entry['progress']['kind'] == 'claim':
                readme_source = result['readme']['requested_url']
                wording = body(readme_source) if result['readme']['status'] == 200 else ''
                assert re.search(r'(?:complete|full) decompilation', wording + text, re.I), entry['id']
                metric['status'] = 'qualified-maintainer-claim'
                metric['note'] = 'Upstream full/complete wording confirmed; numeric values remain null. No matching-byte percentage inferred.'
            elif entry['progress']['kind'] == 'functions':
                assert '2951%2F2951-100%25' in text, entry['id']
                metric['status'] = 'confirmed-function-count'
                metric['note'] = 'Published 2951/2951 matching-function badge. Kept separate from byte/code-size metrics.'
            else:
                if source.endswith('.json'):
                    value = float(json.loads(text)['message'].rstrip('%'))
                elif entry['id'] == 'davidsm64--diddy-kong-racing':
                    value = float(re.search(r'Decomp progress \[us.v77\]: ([\d.]+)%', text)[1])
                    assert '69.02%' in text
                elif entry['id'] == 'banjo-decomp--banjo-kazooie':
                    value = float(re.search(r'^# Banjo-Kazooie \(([\d.]+)%\)', text)[1])
                else:
                    value = float(re.search(r'>([\d.]+)%</text>', text)[1])
                assert value == entry['progress']['decompiled'], entry['id']
                metric['status'] = 'confirmed-published-metric'
                metric['note'] = entry['progress']['label']
                metric['observed'] = {'decompiled': value, 'url': source, 'target': entry.get('report_target', '')}
                if entry['id'] in ('zeldaret--oot', 'zeldaret--mm'):
                    csv = body(entry['sources'][1]).strip().splitlines()[-1].split(',')
                    assert float(csv[3]) / float(csv[4]) * 100 == value
                    assert entry['report_commit'].endswith(csv[2])
                    metric['note'] += '; independently checked against the dashboard matching-code CSV and its stored commit.'
        assert metric['status'] not in ('needs-review', 'manual-review-required'), result['id']
        assert all(s['status'] == 200 for s in result['sources']), result['id']
        if result['id'] == 'skylaralbers--mkd-decomp-local-':
            result['scope_review'] = {'status': 'unconfirmed', 'note': 'Repository still returns HTTP 404; no progress or purpose claim verified.'}
        elif 'second_representation' in metric:
            assert metric['second_representation']['status'] == 'consistent', result['id']
            result['scope_review'] = {'status': 'project-platform-target-confirmed',
                                      'note': 'Tracker repository identity, platform, target, commit date and metric independently compared with its HTML report and JSON representation.'}
        else:
            result['scope_review'] = {'status': 'basic-purpose-reviewed',
                                      'note': 'Basic project purpose reviewed against upstream README or repository description. No build, compatibility or feature-completeness certification.'}
        result['catalog_snapshot'] = {'url': entry['url'], 'category': entry['category'], 'type': entry['type'],
                                      'platform': entry['platform'], 'progress': entry['progress'],
                                      'report_target': entry.get('report_target', ''), 'report_date': entry['report_date'],
                                      'sources': entry['sources']}
    report['method'] = 'Three passes: archive/schema preservation; upstream repository/README/evidence retrieval and basic-purpose review; tracker HTML versus JSON on commit-pinned targets, plus manual badge/README/CSV checks. No upstream build or gameplay verification.'
    report['changes'] = changes
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')

    counts = Counter(e['category'] for e in records)
    checked = {r['id']: r for r in report['projects']}
    audit_date = report['checked_at'][:10]
    lines = [
        '<p align="center"><a href="https://solarfren69420.github.io/GameDecompLibrary/"><img src="assets/library-card.png" alt="GameDecompLibrary: a golden librarian with a collection of game decompilation projects, tools and resources" width="100%"></a></p>', '',
        '# Game Decompilation Library — final accuracy report', '',
        f'**Audit date: {audit_date} (UTC).** This README contains the final report, corrections, limits and an entry-by-entry audit of the original 303-project snapshot. Later additions are documented separately below.', '',
        f'[Interactive library](https://solarfren69420.github.io/GameDecompLibrary/) · [Full catalog](CATALOG.md) · [Submit your GitHub]({REPO}/issues/new?template=add-project.yml) · [Suggest a correction]({REPO}/issues/new?template=update-project.yml)', '',
        '<!-- catalog-stats:start -->',
        f"**{len(records)} projects** · {counts['decomp']} game projects · {counts['tool']} tools · {counts['related']} related projects · {counts['unconfirmed']} unconfirmed link",
        '<!-- catalog-stats:end -->', '',
        'The artwork has no fixed counts. The totals above update with the catalog; use the links above to browse, submit a project or suggest a correction.', '',
        '## Result', '',
        '| Check | Result |', '| --- | --- |',
        '| Original catalog preservation | All 303 original project URLs retained; no repository silently removed |',
        '| Repository reachability | 302 reachable; 1 original URL still returns 404 and remains explicitly unconfirmed |',
        '| Listed evidence | All 713 recorded source checks succeeded, covering 712 distinct evidence URLs in this audited snapshot |',
        '| Tracker percentages | All 202 tracker records checked against HTML and structured JSON, including repository, platform, target, commit and report timestamp |',
        '| Other numerical metrics | 7 published badge/README metrics checked; Zelda code figures additionally checked against matching-code CSVs |',
        '| Completion wording | 4 full/complete maintainer claims preserved as qualitative claims with null numeric values |',
        '| Function counts | Star Fox 64’s 2951/2951 matching-function badge kept separate from matching-byte metrics |',
        '| Tools and related projects | All 71 tools and 11 related projects retain null game-decompilation percentages; basic purposes reviewed |',
        '| Refreshed reports | 12 newer tracker reports incorporated; 7 changed numerical percentages and 5 changed commit metadata only |',
        '| Library verification | 19 automated tests passed; browser checks passed for search, numeric precision, filters, pagination, source/edit links, shared links, empty state and mobile overflow |', '',
        '**The checked figures are published source claims and metrics, not measurements made by this library.** The audit supports the catalog’s links, attribution, basic categories and specifically scoped percentages. It does not certify that every upstream project builds, plays correctly, supports every version, or is complete.', '',
        '## What “triple checked” means', '',
        '1. **Import and structure:** compared the project URL set with the original archived list, checked duplicates and required fields, retained unknown values as `null`, and separated games, tools, related projects and the known missing link.',
        '2. **Primary sources:** retrieved upstream READMEs or repository pages and every cited evidence URL. Reviewed basic purpose and important source qualifications for tools, related projects and non-tracker entries. A successful HTTP response alone was never treated as proof of completion.',
        '3. **Published metrics:** compared all 202 tracker HTML headlines and linked percentages with their higher-precision JSON measures, repository identity, platform, version, commit and timestamp. Pinned the source URLs to those exact reports. Checked the seven supplemental numerical claims against their badges or READMEs, and checked Zelda’s target, code totals and stored report commits against dashboard metadata and CSVs.', '',
        'HTML and JSON are two representations of the same published report. They provide a consistency check, not an independent reconstruction of the original game binary. Live sources changed during the audit; commit-pinned evidence prevents those changes from silently invalidating the catalog’s snapshot.', '',
        'Where the tracker headline omits a fully-linked percentage, the table keeps `—`. A zero/default `complete_code_percent` in the JSON is not promoted into an independently established link-completion claim. This differs from a percentage explicitly published in the headline.', '',
        '## Refreshed tracker records', '',
        'These changes reflect newer upstream reports. Earlier imported values remain in the archived source list as historical snapshots; the existence of a newer report does not establish that the old snapshot was fabricated.', '',
        '| Project | Earlier decompiled / linked | Audited decompiled / linked | Target | Underlying report date (UTC) |',
        '| --- | --- | --- | --- | --- |']
    def values(metric):
        return ' / '.join(f'{metric[k]:g}%' if metric[k] is not None else 'not shown in headline' for k in ('decompiled', 'linked'))
    for change in changes:
        entry = entries[change['id']]
        lines.append(f"| [{md(entry['name'])}]({entry['sources'][0]}) | {values(change['before']['progress'])} | {values(change['after']['progress'])} | {md(change['after']['target'])} | {change['after']['date']} |")
    lines += ['', '## Corrections and source qualifications', '',
        '| Project or issue | Correction / qualification | Primary evidence |', '| --- | --- | --- |',
        '| Generic project type | Removed the blanket “Matching decompilation” type. A game decompilation is not automatically a byte-matching reconstruction. OpenGOAL and Sonic Mania have more specific project types. | Upstream READMEs in the per-entry checks below |',
        '| Ocarina of Time | The dashboard’s 100% code metric covers the **Master Quest debug ROM**. The stored report is from **2024-08-15**. The broader upstream README still calls the project WIP and says it does not produce a PC port. | [Dashboard metadata](https://zelda.deco.mp/assets/json/games.json), [matching-code CSV](https://zelda.deco.mp/assets/csv/progress-oot-matching.csv), [README](https://github.com/zeldaret/oot) |',
        '| Majora’s Mask | 100% is **code progress for the tracked US target**. The **2026-07-19** dashboard report contains incomplete byte matching in several asset categories. No overall game/asset completion is asserted. | [Matching CSV](https://zelda.deco.mp/assets/csv/progress-mm-matching.csv), [README](https://github.com/zeldaret/mm) |',
        '| Mario Kart 64 | Confirmed its 100.0% **total-progress badge**. The badge denominator was not independently established, so it is not presented as independently measured matching-byte telemetry. The README notes missing byte-matching tkmk00 compression tooling. | [Badge](https://n64decomp.github.io/mk64/total_progress.svg), [README](https://github.com/n64decomp/mk64) |',
        '| Diddy Kong Racing | The README publishes 100.00% decompilation for **us.v77**, while documentation is separately reported at 69.02%. | [README](https://github.com/davidsm64/diddy-kong-racing) |',
        '| Breath of the Wild | Confirmed the 17.489% badge and the **Switch 1.5.0** README target; the repository describes itself as experimental and WIP. | [Badge](https://botw.link/badges/progress.json), [README](https://github.com/zeldaret/botw) |',
        '| OpenGOAL | Jak 1 is described as polished/complete, Jak II as essentially complete but in beta, and Jak 3 as having substantial work left. No blanket trilogy percentage or matching-byte completion inferred. | [README](https://github.com/open-goal/jak-project) |',
        '| Super Mario 64, Perfect Dark, LEGO Island and Sonic Mania | Full/complete wording is a maintainer/project statement. Removed percentage-like wording from qualitative labels; numeric fields stay null. | Upstream READMEs / repository descriptions linked in the complete results below |',
        '| Mod Engine 2 | Added the upstream notice that development is discontinued and future work is in me3. | [README](https://github.com/soulsmods/ModEngine2) |',
        '| google/autocxx | Added Google’s notice that it no longer maintains the project; the upstream README points to alternatives and a fork. | [README](https://github.com/google/autocxx) |',
        '| icewind1991/vbsp | Preserved the GitHub URL and added its announced move to Codeberg. | [README](https://github.com/icewind1991/vbsp) |',
        '| unreal-rust | Added the README’s explicit proof-of-concept / not-ready-for-a-real-project qualification. | [README](https://github.com/MaikKlein/unreal-rust) |',
        '| Marathon Recompiled | Added the upstream pre-release notice that it is under active development and is not intended for public use before an official release. | [README](https://github.com/sonicnext-dev/MarathonRecomp) |',
        '| Proptest and Doom 3 BFG | Corrected the evidence paths to Proptest’s nested README and Doom 3 BFG’s README.txt. Added direct source evidence for related-project entries. | [Proptest README](https://github.com/proptest-rs/proptest/blob/main/proptest/README.md), [Doom README](https://github.com/id-Software/DOOM-3-BFG/blob/master/README.txt) |',
        '| Report URL with spaces/emoji | Properly encoded the Alchemy target name so its commit-pinned evidence URL can be retrieved. | Per-entry report below |',
        '| Library maintenance checks | Fixed the original preservation test to permit new submissions while still requiring every original URL to remain. Invalid calendar dates are now rejected. | [Catalog checks](tests/test_catalog.py) |', '',
        '## Known unresolved link', '',
        '[Mortal Kombat: Deception — skylaralbers/mkd-decomp-local-](https://github.com/skylaralbers/mkd-decomp-local-) still returns **HTTP 404**. The audit cannot distinguish a deleted, private, renamed or mistyped repository from that response. Its original link is preserved in the unconfirmed section, with no verified percentage.', '',
        '## Limits of this report', '',
        '- Reachability and source consistency were checked at the stated audit date. Future repository moves or reports can change the current state.',
        '- A decompiled percentage describes its published target and denominator. It is not overall asset, documentation, port or gameplay completion. “Fully linked” is a separate measure.',
        '- A badge value, a maintainer’s full/complete statement, a function count and a byte-based tracker measure are distinct kinds of evidence. Their values are not interchangeable.',
        '- Upstream projects were not built or gameplay-tested. No security, licensing-compliance or exhaustive feature/patch compatibility audit was performed.',
        '- Basic tool purpose was reviewed, not every API or supported title/version. Upstream maturity and maintenance qualifications are retained where found.',
        '- `null` means no comparable numeric claim verified in this audit; it does not mean zero and does not prove that no metric exists elsewhere.', '',
        '## Complete entry-by-entry results', '',
        'Every original entry is listed below. **Report checked** means the published metric, target and commit matched both report formats. **Published metric checked** means the cited badge/README value was checked with its stated scope. **Purpose reviewed** confirms basic categorization, not completeness or compatibility. `—` means no comparable numeric claim is made.', '']
    titles = {'decomp': 'Game projects', 'tool': 'Bindings and tools', 'related': 'Related projects', 'unconfirmed': 'Unconfirmed original link'}
    for category, title in titles.items():
        lines += [f'### {title}', '', '| Project | Platform / type | Decompiled | Linked | Target / scope | Audit result | Evidence |', '| --- | --- | --- | --- | --- | --- | --- |']
        for entry in sorted((e for e in records if e['category'] == category and e['id'] in checked), key=lambda e: e['name'].casefold()):
            result = checked[entry['id']]
            status = result['metric']['status']
            labels = {'confirmed': 'Report checked', 'confirmed-published-metric': 'Published metric checked', 'qualified-maintainer-claim': 'Qualitative claim only', 'confirmed-function-count': 'Function metric checked', 'no-numeric-claim': 'Purpose reviewed'}
            verdict = '404 — unconfirmed' if category == 'unconfirmed' else labels[status]
            metric = entry['progress']
            number = f"{metric['decompiled']:g}%" if metric['decompiled'] is not None else ('Claim only' if metric['kind'] == 'claim' else 'Function count' if metric['kind'] == 'functions' else '—')
            linked = f"{metric['linked']:g}%" if metric['linked'] is not None else '—'
            platform = entry['type'] if category in ('tool', 'related') else entry['platform']
            scope = entry.get('report_target') or ('Project-specific; no game percentage' if category in ('tool', 'related') else metric['label'])
            evidence = f"[Source]({entry['sources'][0]})" if entry['sources'] else 'Not available'
            lines.append(f"| [{md(entry['name'])}]({entry['url']}) | {md(platform)} | {number} | {linked} | {md(scope)} | {verdict} | {evidence} |")
        lines.append('')
    lines += ['## Submit, review and update', '',
        f'Anyone with a GitHub account can [submit a repository]({REPO}/issues/new?template=add-project.yml) or [request a correction]({REPO}/issues/new?template=update-project.yml). SolarFren reviews submissions. Applying the `approved` label prepares a review branch and pull request; merging adds the entry. If GitHub blocks automatic PR creation, the workflow posts a link to open the prepared branch as a PR.', '',
        'Edit an existing entry through the website’s **Edit entry** link or GitHub’s pencil in `data/projects/`. The catalog workflow validates records and regenerates the index after changes. New entries and later edits do **not** automatically inherit this dated audit’s verification status.', '',
        '## Website build and deployment', '',
        f'The workflow is in **[Actions → Build and update catalog]({REPO}/actions/workflows/catalog.yml)**, not the Pages template chooser. In [Settings → Pages]({REPO}/settings/pages), choose **GitHub Actions** as Source. Then open the workflow, click **Run workflow**, select `main`, and run it. New pushes to `main` also trigger it. The supplied Jekyll and Static HTML templates are unnecessary for this repository.', '',
        'Website address: **https://solarfren69420.github.io/GameDecompLibrary/**.', '',
        'The responsive static library includes search, platform/progress filters, sorting, pagination, project sources, report targets, shared project links and GitHub editing/submission links. Its build uses Python’s standard library. No database, API key or npm dependency is needed.', '',
        '## Repository social preview', '',
        "The blue, yellow and orange strip on GitHub's default preview represents this repository's Python, JavaScript and HTML file sizes. It does not indicate game decompilation progress.", '',
        "To replace that default card, download [the prepared social preview](assets/social-preview.jpg), open [Settings → General](https://github.com/solarfren69420/GameDecompLibrary/settings), and choose **Social preview → Edit → Upload an image…**. The JPEG is 1280 × 640 and under 1 MB, following [GitHub's image requirements](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/customizing-your-repositorys-social-media-preview). Committing artwork to the README does not activate this separate GitHub setting.", '',
        'The README uses your supplied artwork. The wider social preview uses the same theme without fixed numbers. The catalog workflow updates the text totals above, so adding repositories does not require redrawing the artwork.', '',
        '## Reproducible evidence and checks', '',
        'The readable final report is this single README. Supporting machine records include [per-source results and hashes](sources/audit-results.json), [before/after tracker records](sources/audit-changes.json) and the [unaltered original catalog](sources/game-decomp-github-linklist.txt). Source bodies are cached locally for the audit and are not copied into the public repository.', '',
        '```sh', 'python3 -m unittest discover -s tests -v', 'python3 scripts/build.py --update-docs', 'node --check web/app.js', '```', '',
        'For a new live audit, run `python3 scripts/audit_sources.py --refresh`. Without `--refresh`, the collector reuses this audit session’s local cache. This read-only collector distinguishes URL retrieval from semantic scope review. A fresh run does not certify claims automatically; review its findings before finalizing a new report.', '',
        'For local preview:', '', '```sh', 'python3 scripts/build.py', 'python3 -m http.server 8080 --directory _site', '```', '',
        'Additional operating instructions remain in [CONTRIBUTING.md](CONTRIBUTING.md) and [MAINTAINING.md](MAINTAINING.md).']
    # Keep separately reviewed community additions outside this dated audit.
    readme_path = ROOT / 'README.md'
    previous = readme_path.read_text()
    additions_heading = '## Additions outside the original audit\n'
    if additions_heading in previous:
        additions = previous.split(additions_heading, 1)[1].split('\n## Result\n', 1)[0]
        result_index = lines.index('## Result')
        lines[result_index:result_index] = [additions_heading.rstrip(), additions.rstrip(), '']
    readme_path.write_text('\n'.join(lines).rstrip() + '\n')
    print('Final report written to README.md:', dict(Counter(r['metric']['status'] for r in report['projects'])))


if __name__ == '__main__':
    main()
