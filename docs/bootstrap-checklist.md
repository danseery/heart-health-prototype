# Bootstrap Checklist

Use this checklist after cloning the repository and before running the app or
deploying the dev environment.

## Required for local development

- Git
- Python 3.12 or newer
- Node.js 22 or newer
- npm

## Required for Azure dev bootstrap and deploys

- Azure CLI (`az`)
- GitHub CLI (`gh`)
- Terraform 1.9 or newer
- Docker, for building container images locally if you test deploy images outside GitHub Actions

## Required sign-ins

- `az login --tenant <tenant-id>`
- `gh auth login`

## Recommended checks

Run the bootstrap prerequisite check from the repo root:

```bash
./scripts/bootstrap-azure-oidc.sh --check-prereqs
```

On Windows PowerShell:

```powershell
.\scripts\bootstrap-azure-oidc.ps1 -CheckPrereqs
```

The check verifies that the expected command-line tools are available before the
Azure bootstrap script tries to create cloud resources or GitHub environment
settings.

## Install references

- Git: https://git-scm.com/downloads
- Python: https://www.python.org/downloads/
- Node.js: https://nodejs.org/
- Azure CLI: https://learn.microsoft.com/cli/azure/install-azure-cli
- GitHub CLI: https://cli.github.com/
- Terraform: https://developer.hashicorp.com/terraform/install
- Docker: https://docs.docker.com/get-docker/
