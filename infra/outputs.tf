output "lab_url" {
  value = "https://${local.lab_domain}/"
}

output "pages_dev_url" {
  value = "https://${cloudflare_pages_project.lab.subdomain}/"
}
