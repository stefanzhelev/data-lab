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
  default = "data-lab"
}

variable "extra_cors_origins" {
  description = "Additional origins allowed to fetch from the bucket (e.g. a future stefanzhelev.com/lab)."
  type        = list(string)
  default     = []
}
