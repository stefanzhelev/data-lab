# infra

Everything data-lab needs outside the repo, in one OpenTofu root applied locally. One file per provider.

| File | Manages |
|---|---|
| `cloudflare.tf` | R2 bucket (imported), its CORS policy, rewrite of `data.stefanzhelev.com/` → `/index.html`; Pages project `data-lab` with `lab.stefanzhelev.com`; two scoped API tokens for CI |
| `github.tf` | the Actions secrets the workflows read; `testpypi` and `pypi` environments (`pypi` needs your approval) |

The CI tokens are minted here and written straight into GitHub secrets, so no credential is ever copied by hand:

| Secret | Value |
|---|---|
| `CLOUDFLARE_API_TOKEN` | token limited to Pages Write |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | token limited to object read/write on the bucket (ID / SHA-256 of value) |
| `CLOUDFLARE_ACCOUNT_ID`, `R2_BUCKET` | from `terraform.tfvars` |

Not managed: the bucket's custom domain `data.stefanzhelev.com` (the provider can't import it), and the PyPI pending publishers (PyPI has no provider).

## Apply

Run from inside `~/Documents/GitHub-stefanzhelev/` so direnv supplies the `stefanzhelev` GitHub token.

```bash
cp backend.hcl.example backend.hcl && cp terraform.tfvars.example terraform.tfvars   # fill in
export CLOUDFLARE_API_TOKEN=...          # R2, Pages, DNS, Zone Rulesets edit + Account API Tokens edit
export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...           # R2 S3 keys for the state bucket
export TF_VAR_state_passphrase="$(security find-generic-password -s tofu-data-lab -w)"
tofu init -backend-config=backend.hcl && tofu plan && tofu apply
```

The state contains the minted tokens and is encrypted with that passphrase. Create it once with
`security add-generic-password -a "$USER" -s tofu-data-lab -w "$(openssl rand -base64 32)"`; without it the state can't be read.
