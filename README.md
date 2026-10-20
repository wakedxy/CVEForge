# CVEForge

Forging exploits from CVEs ,scripts, PoCs, and methodologies from the field.

A personal, curated knowledge base of CVE exploitation scripts, proof-of-concepts, and step-by-step methodologies collected during penetration testing engagements and security research. Each entry documents how a vulnerability is exploited, so it stays useful as a reference and not only as a tool.

---

## Motivation

During pentest and bug bounty engagements, it is common to identify a known CVE affecting a target but then struggle to find a PoC that is both safe and actually functional. Public PoCs are often incomplete, broken, outdated, or carry unclear side effects that make them risky to run against a real target.

This repository exists to solve that problem: it collects the PoCs that have been tested and used in real engagements, cleaned up and documented, so they can be reused reliably without having to rebuild them from scratch each time.

---

## Disclaimer

This repository is intended strictly for authorized security testing, research, and educational purposes.

- Use these materials only against systems you own or have explicit written permission to test.
- Unauthorized access to computer systems is illegal in most jurisdictions.
- The author assumes no liability for misuse or for any damage caused by the contents of this repository.
- PoCs are provided as-is, with no warranty, and may require adaptation to a specific target or environment.

By using anything here, you agree that you are solely responsible for your actions.

## Index

| CVE | Product / Component | Type | Status |
|-----|---------------------|------|--------|
| CVE-2026-65206 | Example product | RCE | Working PoC |
| CVE-YYYY-NNNNN | ... | LPE | Draft |

Keep this table updated as entries are added.

---

## Per-CVE Documentation

Each CVE directory follows the format defined in [`TEMPLATE.md`](./TEMPLATE.md):

- Summary — what it is, affected versions, CVSS
- Prerequisites — access level, configuration, dependencies
- Exploitation — step-by-step reproduction
- Detection / IoCs — how it looks from the defensive side
- Remediation — the fix, useful for reporting
- References — advisory, original research, patches

---

## Topics

cve, exploit, poc, penetration-testing, offensive-security, red-team, vulnerability-research

---

## Author

Maintained by WakedXY — Senior Penetration Tester.

---

## License

For personal and research use. Review applicable laws and disclosure policies before publishing any PoC.
