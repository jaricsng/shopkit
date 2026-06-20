<!-- Change-management gate. The CI enforces most of this automatically; the
checklist is the human attestation that goes with the PR. -->

## What & why
<!-- One or two sentences: what changes, and the reason. -->

## Type
- [ ] Feature
- [ ] Fix
- [ ] Refactor / chore
- [ ] Docs
- [ ] Infra / CI

## Checklist
- [ ] **Tests** added/updated for the change (unit; integration/e2e if behavior changed)
- [ ] `make lint` and the test suite pass locally
- [ ] **No secrets** committed (detect-secrets clean; config via env, not code)
- [ ] **DB migrations** follow expand/contract; `check_migrations.py` passes (or destructive steps `migration-safety: ack`-ed with a reason)
- [ ] **Security** considered — authz/authn touched? input validated? see `SECURITY-FINDINGS.md`
- [ ] **Docs/runbooks** updated if behavior, ops, or SLOs changed
- [ ] **IaC** changes ran `terraform validate` + `tfsec` (or are not applicable)

## Rollout / rollback
<!-- Feature-flag? Migration ordering? How to roll back if this misbehaves? -->
