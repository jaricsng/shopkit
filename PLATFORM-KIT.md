# PLATFORM-KIT.md

Provenance record for this repo's adoption of `platform-starter-kit`.
Don't delete this even after dropping capabilities you don't need —
`tools/sync_check.py` reads the commit SHA below to tell you what's
changed upstream since you scaffolded.

- Generated: 2026-06-19 10:45 UTC
- Source kit commit: `5ba906377347b86bdd41dd561d1b874dc9038cc1`
- App name: `shopkit`
- Cloud target: `gcp`
- Capabilities included:
  - observability: True
  - security: True
  - load-testing: True
  - claude-commands: True
  - iac-terraform (gcp-cloud-run): True
  - governance/policy-as-code (example only, GCP-specific): True

Re-run `python3 tools/doctor.py .` periodically as you add your actual
application code — the gaps it reports now (no app code yet) are expected;
the ones it reports once you have a real service are not.

Run `python3 tools/sync_check.py . --kit-path /path/to/platform-starter-kit`
periodically to see what's changed in the kit since `5ba906377347`.
