"""Read-only upstream audit. Reachability and factual scope are distinct checks.

Fetched source bodies are cached outside the repository. This script never updates
project records or treats a successful HTTP request as semantic verification.
"""
import argparse
import concurrent.futures
import hashlib
import html
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from catalog import ROOT, load_projects

CACHE = Path('/tmp/game-decomp-source-audit')
REFRESH = False


def fetch(url):
    key = hashlib.sha256(url.encode()).hexdigest()
    body_path, meta_path = CACHE / (key + '.body'), CACHE / (key + '.json')
    if meta_path.exists() and not REFRESH:
        result = json.loads(meta_path.read_text())
        result['body'] = body_path.read_text() if body_path.exists() else ''
        return result
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'GameDecompLibrary-source-audit/1.0'}), timeout=35) as response:
                body = response.read().decode('utf-8', errors='replace')
                result = {'status': response.status, 'requested_url': url, 'final_url': response.geturl(),
                          'sha256': hashlib.sha256(body.encode()).hexdigest(), 'bytes': len(body.encode()),
                          'retrieved_at': datetime.now(timezone.utc).isoformat()}
            body_path.write_text(body)
            meta_path.write_text(json.dumps(result))
            return {**result, 'body': body}
        except HTTPError as error:
            if error.code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 * (attempt + 1))
                continue
            result = {'status': error.code, 'requested_url': url, 'error': str(error)}
            meta_path.write_text(json.dumps(result))
            return {**result, 'body': ''}
        except Exception as error:
            if attempt < 2:
                time.sleep(1)
                continue
            return {'status': None, 'requested_url': url, 'error': str(error), 'body': ''}


def without_body(result):
    return {k: v for k, v in result.items() if k != 'body'}


def audit(entry):
    result = {'id': entry['id'], 'name': entry['name'], 'repository_url': entry['url'], 'category': entry['category']}
    repo_path = '/'.join(entry['url'].split('/')[3:])
    if 'github.com/' in entry['url']:
        readme_url = f'https://raw.githubusercontent.com/{repo_path}/HEAD/README.md'
    else:
        readme_url = entry['url'] + '/-/raw/HEAD/README.md'
    readme = fetch(readme_url)
    if readme['status'] != 200:
        for alternative in entry['sources']:
            if 'raw.githubusercontent.com/' in alternative or '/-/raw/' in alternative:
                candidate = fetch(alternative)
                if candidate['status'] == 200:
                    readme, readme_url = candidate, alternative
                    break
    result['readme'] = without_body(readme)
    if readme['status'] == 200:
        result['repository'] = {'status': 'reachable-via-readme', 'evidence_url': readme_url}
        titles = re.findall(r'^#{1,3}\s+(.+)$', readme['body'], re.M)
        result['readme_headings'] = titles[:12]
    else:
        repository = fetch(entry['url'])
        result['repository'] = without_body(repository)
    result['sources'] = []
    tracker_result = None
    for url in entry['sources']:
        response = fetch(url)
        result['sources'].append(without_body(response))
        if 'decomp.dev/' in url and response['status'] == 200 and tracker_result is None:
            body = response['body']
            title = re.search(r'<h3 class="report-title">(.*?)</h3>', body, re.S)
            text = html.unescape(re.sub('<[^>]+>', '', title[1])) if title else ''
            metric = re.search(r'([\d.]+)% decompiled', text)
            linked = re.search(r'<h4[^>]*>([\d.]+)% fully linked</h4>', body)
            commit = re.search(r'https://github\.com/[^"<>]+/commit/[a-f0-9]{40}', body)
            target = re.search(r'<summary>([^<]+)</summary><ul><li><a href="/[^"<>]+">', body)
            actual = {'decompiled': float(metric[1]) if metric else None,
                      'linked': float(linked[1]) if linked else None,
                      'report_commit': html.unescape(commit[0]) if commit else None,
                      'target': html.unescape(target[1]) if target else None,
                      'published_title': text, 'url': url}
            expected = entry['progress']
            matches = actual['decompiled'] == expected['decompiled'] and actual['linked'] == expected['linked']
            commit_matches = not entry['report_commit'] or entry['report_commit'] == actual['report_commit']
            tracker_result = {'status': 'confirmed' if metric and matches and commit_matches else 'needs-review',
                              'observed': actual,
                              'catalog': {'decompiled': expected['decompiled'], 'linked': expected['linked'],
                                          'report_commit': entry['report_commit']}}
            overview_url = url + '.json?mode=overview'
            overview = fetch(overview_url)
            result['sources'].append(without_body(overview))
            if overview['status'] == 200:
                data = json.loads(overview['body'])
                measures = data.get('measures', {})
                precise = measures.get('matched_code_percent')
                precise_linked = measures.get('complete_code_percent')
                commit_data = data.get('commit') or {}
                api_commit = entry['url'] + '/commit/' + commit_data.get('sha', '')
                independently_matches = (precise is not None and actual['decompiled'] is not None
                                         and abs(precise - actual['decompiled']) <= 0.00501
                                         and (actual['linked'] is None or (precise_linked is not None and abs(precise_linked - actual['linked']) <= 0.00501))
                                         and api_commit.casefold() == (actual['report_commit'] or '').casefold())
                tracker_result['second_representation'] = {
                    'status': 'consistent' if independently_matches else 'needs-review',
                    'url': overview_url, 'sha256': overview.get('sha256'),
                    'matched_code_percent': precise, 'complete_code_percent': precise_linked,
                    'report_date': commit_data.get('timestamp'), 'report_commit': api_commit,
                    'platform': data.get('platform'), 'default_version': data.get('default_version'),
                    'name': data.get('name'), 'repo_url': data.get('repo_url')}
                if not independently_matches:
                    tracker_result['status'] = 'needs-review'
    if tracker_result:
        result['metric'] = tracker_result
    else:
        result['metric'] = {'status': 'manual-review-required' if entry['progress']['decompiled'] is not None or entry['progress']['kind'] in ('claim','functions') else 'no-numeric-claim'}
    result['scope_review'] = 'not-automatically-verified'
    return result


def main():
    global REFRESH
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=5)
    parser.add_argument('--refresh', action='store_true', help='Fetch fresh source bodies instead of reusing this audit session cache')
    args = parser.parse_args()
    REFRESH = args.refresh
    CACHE.mkdir(exist_ok=True)
    entries = load_projects()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(audit, entry): entry for entry in entries}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            if len(results) % 25 == 0 or result['metric']['status'] == 'needs-review':
                print(f"Audited {len(results)}/{len(entries)}: {result['id']} / {result['metric']['status']}", flush=True)
    out = ROOT / 'sources/audit-results.json'
    out.write_text(json.dumps({'checked_at': datetime.now(timezone.utc).isoformat(),
                              'method': 'Upstream README/source retrieval; independently parsed tracker headline, linked metric and report commit. HTTP success alone is not a scope verification.',
                              'projects': sorted(results, key=lambda r: r['id'])}, indent=2, ensure_ascii=False) + '\n')
    from collections import Counter
    print('Metric results:', dict(Counter(r['metric']['status'] for r in results)), flush=True)
    print('Saved', out, flush=True)


if __name__ == '__main__':
    main()
