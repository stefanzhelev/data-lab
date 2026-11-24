# =============================================================================
# Cloudflare provider — R2 bucket, custom domain, Pages project (cloudflare.tf)
# =============================================================================

variable "account_id" {
  description = "Cloudflare account ID."
  type        = string
}

variable "zone_id" {
  description = "Zone ID of stefanzhelev.com."
  type        = string
}

variable "zone_name" {
  type    = string
  default = "stefanzhelev.com"
}

variable "bucket_name" {
  description = "R2 bucket served at data_domain."
  type        = string
}

variable "data_domain" {
  type    = string
  default = "data.stefanzhelev.com"
}

variable "lab_subdomain" {
  description = "Subdomain of the zone for the Pages site."
  type        = string
  default     = "lab"
}

variable "pages_project" {
  type    = string
  default = "stefanzhelev-datalab"
}

variable "extra_cors_origins" {
  description = "Additional origins allowed to fetch from the bucket (e.g. a future stefanzhelev.com/lab)."
  type        = list(string)
  default     = []
}

# =============================================================================
# GitHub provider — Actions secrets and deployment environments (github.tf)
# =============================================================================

variable "github_owner" {
  description = "GitHub user or org that owns the repo (sets the provider's owner)."
  type        = string
  default     = "stefanzhelev"
}

variable "github_token" {
  description = "Token for the github_owner account. Pass as TF_VAR_github_token (data-lab/.envrc reads it from the Keychain)."
  type        = string
  sensitive   = true
}

variable "github_repo" {
  description = "Repository that receives the Actions secrets and environments."
  type        = string
  default     = "data-lab"
}

# =============================================================================
# OpenTofu itself — state encryption (versions.tf), not tied to a provider
# =============================================================================

variable "state_passphrase" {
  description = "Passphrase for OpenTofu state encryption (min. 16 characters). Pass as TF_VAR_state_passphrase."
  type        = string
  sensitive   = true
}
