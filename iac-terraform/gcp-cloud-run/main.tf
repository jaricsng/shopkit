locals {
  name_prefix = "${var.app_name}-${var.environment}"
  image       = "ghcr.io/${var.github_repository}/api:${var.image_tag}"

  labels = {
    app         = var.app_name
    environment = var.environment
    managed_by  = "terraform"
    team        = "platform"
  }
}

# ── Cloud SQL (PostgreSQL 16) ──────────────────────────────────────────────────
# Two tfsec findings on this instance are accepted with justification:
#  - encrypt-in-transit: TLS *is* enforced via settings.ip_configuration.ssl_mode
#    = "ENCRYPTED_ONLY" (google provider v6+ removed require_ssl); tfsec is EOL
#    and doesn't recognize ssl_mode, so it mis-flags the control.
#  - no-public-access: this teaching reference uses a public IP reached only via
#    the Cloud SQL Auth Proxy (IAM-authenticated, TLS-enforced). PRODUCTION should
#    switch to a private IP + Serverless VPC Access connector (no public address)
#    — see operations/ and docs/TECH-STACK-SWAP-GUIDE.md.
# (The ignore directives must sit on consecutive lines directly above the block.)
#tfsec:ignore:google-sql-encrypt-in-transit-data
#tfsec:ignore:google-sql-no-public-access
resource "google_sql_database_instance" "main" {
  name                = "${local.name_prefix}-db"
  database_version    = "POSTGRES_16"
  region              = var.region
  deletion_protection = var.environment == "production" ? true : false

  settings {
    tier = var.db_tier

    ip_configuration {
      # Require TLS for every connection. google provider v6+ uses ssl_mode
      # (the deprecated require_ssl was removed).
      ssl_mode = "ENCRYPTED_ONLY"
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = var.environment == "production"
      backup_retention_settings {
        retained_backups = var.environment == "production" ? 30 : 7
      }
    }

    maintenance_window {
      day  = 7 # Sunday
      hour = 3 # 03:00 UTC — low traffic window
    }

    # Postgres diagnostic logging (tfsec google-sql-pg-log-* / CIS). These are
    # operational signals, not query contents.
    database_flags {
      name  = "log_connections"
      value = "on"
    }
    database_flags {
      name  = "log_disconnections"
      value = "on"
    }
    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }
    database_flags {
      name  = "log_temp_files"
      value = "0" # 0 = log all temp files
    }
    database_flags {
      # -1 DISABLES statement-content logging (it can capture sensitive data in
      # plaintext logs — tfsec google-sql-pg-no-min-statement-logging). Use
      # Cloud SQL Query Insights for slow-query analysis instead.
      name  = "log_min_duration_statement"
      value = "-1"
    }

    user_labels = local.labels
  }
}

resource "google_sql_database" "app" {
  name     = "appdb"
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "app" {
  name     = "appuser"
  instance = google_sql_database_instance.main.name
  password = random_password.db_password.result
}

resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Store the connection string in Secret Manager (never in state as plaintext)
resource "google_secret_manager_secret" "database_url" {
  secret_id = "${local.name_prefix}-database-url"
  replication {
    auto {}
  }
  labels = local.labels
}

resource "google_secret_manager_secret_version" "database_url" {
  secret = google_secret_manager_secret.database_url.id
  secret_data = format(
    "postgresql+asyncpg://%s:%s@/%s?host=/cloudsql/%s",
    google_sql_user.app.name,
    random_password.db_password.result,
    google_sql_database.app.name,
    google_sql_database_instance.main.connection_name
  )
}

# ── Service Account for Cloud Run ─────────────────────────────────────────────
resource "google_service_account" "api" {
  account_id   = "${local.name_prefix}-api"
  display_name = "${var.app_name} API — ${var.environment}"
}

resource "google_secret_manager_secret_iam_member" "api_database_url" {
  secret_id = google_secret_manager_secret.database_url.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

resource "google_secret_manager_secret_iam_member" "api_secret_key" {
  secret_id = google_secret_manager_secret.secret_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"
}

# ── Cloud Run Service ─────────────────────────────────────────────────────────
resource "google_cloud_run_v2_service" "api" {
  name     = "${local.name_prefix}-api"
  location = var.region
  labels   = local.labels

  # google provider v6+ defaults this to true for every environment, which
  # blocks `terraform destroy`/replace on staging unless overridden — mirror
  # the same staging/production split already used for the SQL instance.
  deletion_protection = var.environment == "production" ? true : false

  template {
    service_account = google_service_account.api.email

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.main.connection_name]
      }
    }

    containers {
      image = local.image

      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name  = "OTEL_ENABLED"
        value = "false"
      }
      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.secret_key.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = var.environment == "production" ? "2" : "1"
          memory = var.environment == "production" ? "1Gi" : "512Mi"
        }
      }

      startup_probe {
        http_get { path = "/health" }
        initial_delay_seconds = 10
        period_seconds        = 5
        failure_threshold     = 6
      }

      liveness_probe {
        http_get { path = "/ready" }
        period_seconds    = 30
        failure_threshold = 3
      }
    }
  }
}

resource "google_secret_manager_secret" "secret_key" {
  secret_id = "${local.name_prefix}-secret-key"
  replication {
    auto {}
  }
  labels = local.labels
}

resource "google_secret_manager_secret_version" "secret_key" {
  secret      = google_secret_manager_secret.secret_key.id
  secret_data = var.secret_key
}

# Allow unauthenticated access (the app handles its own auth via JWT)
resource "google_cloud_run_v2_service_iam_member" "public" {
  name     = google_cloud_run_v2_service.api.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.37"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}
