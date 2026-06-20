**Quarterly access review** — confirm standing access is still least-privilege.
See the policy: `reference-solution`/lab `governance/access-control.md`.

- [ ] **GitHub** — review collaborators/teams; remove anyone who left or changed role
- [ ] **GitHub** — branch protection on `main` still requires PR + CI + code-owner review
- [ ] **Cloud (GCP) IAM** — review roles; no human keys; break-glass access still justified
- [ ] **App admins** (`is_admin`) — list admins; remove any no longer needed
- [ ] **CI/CD secrets** — review repo/Actions secrets; rotate stale ones
- [ ] Record the review (who/when/decisions) in `governance/access-control.md`'s table — that table is the audit evidence

**Reviewer:** _____  **Date:** _____  **Accounts removed:** _____
