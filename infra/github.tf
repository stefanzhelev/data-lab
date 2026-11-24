data "github_user" "me" {
  username = "" # the authenticated user
}

# ── Actions secrets used by .github/workflows ───────────────────────────────

locals {
  actions_secrets = {
    CLOUDFLARE_ACCOUNT_ID = var.account_id
    CLOUDFLARE_API_TOKEN  = cloudflare_account_token.pages_deploy.value
    R2_BUCKET             = var.bucket_name
    R2_ACCESS_KEY_ID      = cloudflare_account_token.r2_data.id
    R2_SECRET_ACCESS_KEY  = sha256(cloudflare_account_token.r2_data.value)
  }
}

resource "github_actions_secret" "ci" {
  # Keys are plain names; only the values are sensitive.
  for_each = toset(nonsensitive(keys(local.actions_secrets)))

  repository  = var.github_repo
  secret_name = each.key
  value       = local.actions_secrets[each.key]
}

# ── Environments for publish-datalab.yml (PyPI trusted publishing) ──────────

resource "github_repository_environment" "testpypi" {
  repository  = var.github_repo
  environment = "testpypi"
}

# Real PyPI releases wait for a manual approval.
resource "github_repository_environment" "pypi" {
  repository  = var.github_repo
  environment = "pypi"

  reviewers {
    users = [tonumber(data.github_user.me.id)]
  }
}
