# drupal-jsonapi-oracle

PoC scripts abusing a **broken access control** weakness in Drupal's JSON:API: access
control is enforced on the returned *data*, but not on the `meta.count` aggregate nor the
`meta.omitted` listing. By playing with filters, an **unauthenticated** attacker can
enumerate webform submission IDs and reconstruct private file names **byte by byte** —
without ever reading the protected file content.

> ⚠️ **Authorized use only.** For scoped pentests, red-team and bug-bounty work with
> **explicit written permission**. Misuse is illegal; no liability is accepted.

## How it works

One primitive — a **count oracle**:

```
GET /<lang>/jsonapi/file/file?filter[uri.value][operator]=STARTS_WITH
    &filter[uri.value][value]=<prefix>&page[limit]=0   →  meta.count
```

- **Stage 1** (`enum-submission-ids.py`) — walks the `0-9` prefix tree under
  `private://webform/<form>/`, pruning empty/complete branches, to list submission IDs.
- **Stage 2** (`jsonapi-read.py`) — per sid, finds each name's first char over a full
  charset, then **binary-searches each byte** (`uri.value > <probe>`) until an extension
  (`.pdf`, `.docx`, …) or the length limit. Only counts are queried — never file content.

## Requirements

Python 3, standard library only. No dependencies.

## Usage

Same webform machine name in both stages (`<form>` in stage 1 = `-p` in stage 2).

```bash
# Stage 1 — enumerate submission IDs  →  sids.txt
./enum-submission-ids.py private_path -u https://target.example -o sids.txt

# Stage 2 — reconstruct file names     →  names.txt
./jsonapi-read.py -d sids.txt -p private_path -u https://target.example -o names.txt
```

### Key options

**`enum-submission-ids.py`** — `form` (positional), optional `prefix`, `-u/--url`,
`-o/--output` (`sids.txt`), `-m/--max-len` (`6`).

**`jsonapi-read.py`** — `-d/--ids-file` *(req)*, `-p/--private-dir` *(req)*, `-u/--url`,
`-o/--output`, `-l/--limit` (`70`), `--delay` (`0`), `--retries` (`5`), `--timeout` (`25`).

## OPSEC

Request-heavy (~8 req/char). Use `--delay`; stage 2 already backs off on `429`
(`Retry-After`) and network errors. The path is hard-coded as `<url>/fr/jsonapi/file/file` —
edit the source if the target isn't under `/fr/`.

## Remediation

Disable JSON:API if unused or restrict it to authenticated roles; keep core/module
updated; use **JSON:API Extras** to disable filtering on sensitive fields (`uri.value`);
ensure access checks also cover metadata/count paths; rate-limit JSON:API endpoints.

## License

MIT (add a `LICENSE` file).
