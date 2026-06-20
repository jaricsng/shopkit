**Annual DR review & sign-off** — see `governance/business-continuity-dr.md`.

The **rebuild-from-code** DR test is automated (`.github/workflows/dr-restore-test.yml`,
runs monthly) — check its recent runs first. This issue is the human sign-off +
the parts that aren't automated.

- [ ] Review the automated rebuild-from-code test results (time-to-ready vs RTO)
- [ ] **Real backup restore** exercised (Cloud SQL → scratch), RTO/RPO recorded
- [ ] Region-failover plan reviewed/tested
- [ ] Off-platform data copy verified
- [ ] RTO/RPO targets still match business needs
- [ ] Record results in `governance/business-continuity-dr.md`'s DR test log

**Reviewer:** _____  **Date:** _____  **RTO/RPO actual:** _____
