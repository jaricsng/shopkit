# Security Policy

> **Note:** ShopKit is a **teaching reference** for the DevSecOps capstone, not a
> production service. It uses test credentials, permissive local CORS, and
> intentionally simple choices. See `SECURITY-FINDINGS.md` for the accepted
> risks (no rate limiting, missing security headers, stateless JWT, etc.) and
> their production remediations.

## Reporting a vulnerability

Please report security issues **privately** — do not open a public issue.

- Email the maintainer, or
- Use GitHub's private vulnerability reporting (Security → *Report a vulnerability*).

Include steps to reproduce, affected endpoints/files, and impact. You'll get an
acknowledgement within a few days. Since this is example code, fixes are made on
a best-effort basis and folded back into the capstone material.

## Scope

In scope: the application code in `backend/` and `frontend/`, the IaC in
`iac-terraform/`, and the CI/CD workflows. Already-documented teaching tradeoffs
in `SECURITY-FINDINGS.md` are tracked issues, not new reports.

## Supported versions

`main` only. This is a single-branch teaching repo with no release/backport
process.
