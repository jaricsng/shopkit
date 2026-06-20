# TODO — placeholders `tools/scaffold.py` couldn't resolve for you

Everything app-name-shaped was already substituted. These rows need a
value only you have (credentials, routes, project IDs) or a decision
`scaffold.py` can't make for you.

| File | Placeholder | What to set it to |
|---|---|---|
| `.github/workflows/ci.yml` | `working-directory: backend` / `frontend` | Your repo's actual source directories |
| `.github/workflows/ci.yml` | `services: postgres:` block | Your actual database engine, if not Postgres — see `docs/TECH-STACK-SWAP-GUIDE.md` |
| `.github/workflows/publish.yml` | GCP deploy job's `if: false`, `deploy/gcp-deploy.sh` | Remove once Workload Identity Federation is configured; provide your own deploy script, or `terraform apply` directly |
| `iac-terraform/gcp-cloud-run/` | `terraform.tfvars`, GCS backend block | Your GCP project ID and a remote-state bucket (`app_name` is already set) |
| `.github/workflows/drift-detection.yml` | `if: false`, cloud auth + backend | Remove `if: false` once WIF + remote state are configured, to enable scheduled drift detection |
| `governance/policy-as-code/policy/terraform_guardrails.rego` | Example only | Adapt the resource checks to your own requirements, or delete the folder if you don't want a policy-as-code gate — see `governance/policy-as-code/README.md` |
| `security/manual-checks.sh` | `ENDPOINTS` configuration block | Your own auth/resource routes |
| `observability/prometheus.yml` | `job_name: app` | Only if your Compose service isn't named `app` |
| `load-testing/k6/*.js`, `load-testing/locust/locustfile.py` | Worked-example endpoint paths/payloads | Your own API's routes and request bodies |
| `catalog-info.yaml` | `project-slug` annotation, `owner: TODO-team` | Your repo's slug and your actual Backstage team reference |
| `.github/CODEOWNERS` | `@TODO-set-your-team-or-handle` | Your actual GitHub team or handle |
