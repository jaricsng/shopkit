# Metric-name decision (Module 04)

The kit ships a **deliberate, documented** mismatch (see the kit's
`docs/ASSET-CATALOG.md`):

- `recording_rules.yml` used the **pre-1.23** OTel name
  `http_server_duration_milliseconds` (milliseconds).
- `grafana/dashboards/starter-dashboard.json` queries the **stable (1.23+)** name
  `http_server_request_duration_seconds` (seconds).

Picking one is an adopter decision. **This reference resolves it toward the
stable, seconds-based convention** — the direction OTel is standardizing on.

## What we changed

1. **App emits the stable metric.** `docker-compose.yml` sets
   `OTEL_SEMCONV_STABILITY_OPT_IN=http`, so FastAPI instrumentation emits
   `http.server.request.duration` (seconds) with stable labels
   (`http_request_method`, `http_response_status_code`, `http_route`) — exactly
   what the Grafana dashboard already queries. **No dashboard change needed.**
2. **Recording rules follow.** `recording_rules.yml` now uses
   `http_server_request_duration_seconds` and the stable labels. This also fixed
   a latent unit bug: `app:request_p95_seconds` previously divided a millisecond
   value by 1000; with a seconds-based histogram it now reads true seconds.

## Verified (against a live stack)

| Signal | Result |
|--------|--------|
| App `/metrics/` | emits `http_server_request_duration_seconds_*` + stable labels |
| Prometheus `app` target | UP; dashboard queries return data (req-rate, P95 ≈ 9 ms, per-route) |
| Recording rules | all health `ok`; `app:request_p95_seconds` ≈ 0.009 **s** (correct unit) |
| Jaeger | service `shopkit`, traces present |

## The alternative (equally valid)

Keep the **old** millisecond name everywhere: leave the app on legacy semconv
and instead rewrite the dashboard's queries to
`http_server_duration_milliseconds` (dropping the `*1000` in the latency
panels). We chose the stable name because it's the forward-looking standard and
required no dashboard surgery. Your capstone should pick one **and write down
why** — that reasoning is the graded part, not the specific choice.
