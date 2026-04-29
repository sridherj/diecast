# Security Policy

## Reporting a vulnerability

Report security issues via the repo's
[private security advisory](https://github.com/sridherj/diecast/security/advisories)
tab. Please **do not** open a public GitHub issue for security
vulnerabilities, post to GitHub Discussions, or share details on social
channels before a fix has shipped.

When you file an advisory, include:

- A description of the issue and the impact you observed.
- Steps to reproduce, ideally a minimal proof-of-concept.
- The Diecast version (`cat VERSION`) and your environment.
- Any suggested mitigation, if you have one in mind.

We aim to acknowledge new advisories within **3 business days**.

## Supported versions

Diecast is pre-1.0. Only the latest tagged release receives security
fixes; older alpha and pre-release versions do not.

| Version           | Supported          |
|-------------------|--------------------|
| `0.1.x` (current) | :white_check_mark: |
| `< 0.1`           | :x:                |

## Disclosure policy

- We will acknowledge the report and confirm the issue scope with you.
- We will work on a fix in a private fork; you may be asked for help
  validating the patch.
- Once a fix has shipped on the supported release line, we will publish
  the advisory and credit the reporter unless they prefer otherwise.
- A best-effort target of **90 days from acknowledgement to public
  disclosure** applies. We will coordinate if more time is needed.

## Out of scope

- Issues in third-party agents or skills installed by Diecast users.
- Vulnerabilities in upstream Claude Code, Anthropic SDKs, or other
  dependencies — please report those to the upstream project directly.
- Self-inflicted misconfiguration (for example, disabling
  `bin/lint-anonymization` and committing private data).
