locals {
  lab_domain = "${var.lab_subdomain}.${var.zone_name}"
}

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
