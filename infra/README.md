# infra

Cloudflare resources for data-lab, applied locally with OpenTofu.

| File | Manages |
|---|---|
| `r2.tf` | bucket (imported), CORS policy, rewrite of `data.stefanzhelev.com/` → `/index.html` |
| `pages.tf` | Pages project `data-lab`, `lab.stefanzhelev.com` domain and its CNAME |

Not managed: the bucket's custom domain `data.stefanzhelev.com` (the provider can't import it).

```bash
cp backend.hcl.example backend.hcl && cp terraform.tfvars.example terraform.tfvars   # fill in
export CLOUDFLARE_API_TOKEN=...                                  # token with R2, Pages, DNS, Rulesets edit
export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...           # R2 S3 keys for the state bucket
tofu init -backend-config=backend.hcl && tofu plan && tofu apply
```
