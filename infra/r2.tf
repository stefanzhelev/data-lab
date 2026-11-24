# Bucket: created in the dashboard first, adopted here.
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
