# infra

Everything data-lab needs outside the repo, in one OpenTofu root applied locally. One file per provider.

| File | Manages |
|---|---|
| `cloudflare.tf` | R2 bucket (imported), its CORS policy, rewrite of `data.stefanzhelev.com/` → `/index.html`; Pages project `stefanzhelev-datalab` (`var.pages_project`) with `lab.stefanzhelev.com`; two scoped API tokens for CI |
| `github.tf` | the Actions secrets the workflows read; `testpypi` and `pypi` environments (`pypi` needs your approval) |

The CI tokens are minted here and written straight into GitHub secrets, so no credential is ever copied by hand:

| Secret | Value |
|---|---|
| `CLOUDFLARE_API_TOKEN` | token limited to Pages Write; used by the `deploy` job in `ci.yml` |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | token limited to object read/write on the bucket (ID / SHA-256 of value); used by the `deploy` job in `ci.yml` to upload files over Pages' 25 MiB limit to `lab-assets/` |
| `CLOUDFLARE_ACCOUNT_ID`, `R2_BUCKET` | from `terraform.tfvars` |

Not managed: the bucket's custom domain `data.stefanzhelev.com` (the provider can't import it), and the PyPI pending publishers (PyPI has no provider).

## Apply

`data-lab/.envrc` (direnv) sets all of the below from `.env` and the Keychain. Without direnv, export them by hand.
The GitHub token is a required variable on purpose, so tofu never runs as whatever `GH_TOKEN` the shell happens to have.

```bash
cp backend.hcl.example backend.hcl && cp terraform.tfvars.example terraform.tfvars   # fill in
export CLOUDFLARE_API_TOKEN=...          # R2, Pages, DNS, Zone Rulesets edit + Account API Tokens edit
export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...           # R2 S3 keys for the state bucket
export TF_VAR_state_passphrase="$(security find-generic-password -s tofu-data-lab -w)"
export TF_VAR_github_token="$(security find-generic-password -s gh-stefanzhelev -w)"
tofu init -backend-config=backend.hcl && tofu plan && tofu apply
```

The state contains the minted tokens and is encrypted with that passphrase. Create it once with
`security add-generic-password -a "$USER" -s tofu-data-lab -w "$(openssl rand -base64 32)"`; without it the state can't be read.
