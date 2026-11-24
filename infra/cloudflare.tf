locals {
  lab_domain = "${var.lab_subdomain}.${var.zone_name}"
}

# ── R2 bucket behind data.stefanzhelev.com ──────────────────────────────────

# Created in the dashboard first, adopted here.
import {
  to = cloudflare_r2_bucket.data
  id = "${var.account_id}/${var.bucket_name}/default"
}

resource "cloudflare_r2_bucket" "data" {
  account_id = var.account_id
  name       = var.bucket_name

  lifecycle {
    prevent_destroy = true
  }
}

# The public custom domain (data.stefanzhelev.com) is NOT managed here: the
# provider cannot import cloudflare_r2_custom_domain, and it already exists
# (R2 → bucket → Settings → Custom Domains).

# Browsers only let the dashboards read files cross-origin with this policy.
# (Not importable either, but applying it simply replaces the bucket's policy.)
resource "cloudflare_r2_bucket_cors" "data" {
  account_id  = var.account_id
  bucket_name = cloudflare_r2_bucket.data.name
  rules = [{
    id = "data-lab-dashboards"
    allowed = {
      methods = ["GET", "HEAD"]
      origins = concat(
        ["https://${local.lab_domain}", "https://*.${var.pages_project}.pages.dev", "https://${var.pages_project}.pages.dev", "http://localhost:2718", "http://localhost:5173"],
        var.extra_cors_origins,
      )
      headers = ["*"]
    }
    expose_headers  = ["Content-Length", "Content-Range", "ETag"]
    max_age_seconds = 3600
  }]
}

# Serve the generated file index (scripts/build_data_index.py) at the bare root.
# Note: a zone allows one http_request_transform entrypoint ruleset. If the zone
# already has one, add this rule to it instead of creating a second ruleset.
resource "cloudflare_ruleset" "data_index" {
  zone_id     = var.zone_id
  name        = "data-lab: serve data index"
  description = "Rewrite ${var.data_domain}/ to /index.html"
  kind        = "zone"
  phase       = "http_request_transform"
  rules = [{
    ref         = "data_index_root"
    description = "Data index at ${var.data_domain}/"
    expression  = "(http.host eq \"${var.data_domain}\" and http.request.uri.path eq \"/\")"
    action      = "rewrite"
    action_parameters = {
      uri = {
        path = { value = "/index.html" }
      }
    }
    enabled = true
  }]
}

# ── Pages site at lab.stefanzhelev.com ──────────────────────────────────────

# Direct Upload project: GitHub Actions builds the site and runs
# `wrangler pages deploy`, so no git connection is configured here.
resource "cloudflare_pages_project" "lab" {
  account_id        = var.account_id
  name              = var.pages_project
  production_branch = "main"
}

resource "cloudflare_pages_domain" "lab" {
  account_id   = var.account_id
  project_name = cloudflare_pages_project.lab.name
  name         = local.lab_domain
}

resource "cloudflare_dns_record" "lab" {
  zone_id = var.zone_id
  name    = local.lab_domain
  type    = "CNAME"
  content = "${cloudflare_pages_project.lab.name}.pages.dev"
  proxied = true
  ttl     = 1
  comment = "data-lab Pages site (managed by stefanzhelev/data-lab infra/)"
}

# ── Scoped API tokens for GitHub Actions (stored as secrets in github.tf) ───

data "cloudflare_account_api_token_permission_groups_list" "all" {
  account_id = var.account_id
}

locals {
  # Permission group name → id. Names can repeat across scopes, so take the first.
  permission_group = { for g in data.cloudflare_account_api_token_permission_groups_list.all.result : g.name => g.id... }
  account_resource = "com.cloudflare.api.account.${var.account_id}"
  bucket_resource  = "com.cloudflare.edge.r2.bucket.${var.account_id}_default_${var.bucket_name}"
}

# Object read/write on the data bucket only. Its S3 credentials are derived from
# the token: access key ID = token ID, secret access key = SHA-256 of the value.
resource "cloudflare_account_token" "r2_data" {
  account_id = var.account_id
  name       = "data-lab CI: R2 ${var.bucket_name}"
  policies = [{
    effect = "allow"
    permission_groups = [
      { id = local.permission_group["Workers R2 Storage Bucket Item Read"][0] },
      { id = local.permission_group["Workers R2 Storage Bucket Item Write"][0] },
    ]
    resources = jsonencode({ (local.bucket_resource) = "*" })
  }]
}

# `wrangler pages deploy` only.
resource "cloudflare_account_token" "pages_deploy" {
  account_id = var.account_id
  name       = "data-lab CI: Pages deploy"
  policies = [{
    effect            = "allow"
    permission_groups = [{ id = local.permission_group["Pages Write"][0] }]
    resources         = jsonencode({ (local.account_resource) = "*" })
  }]
}
