# Cased Deploy Notification Action

Easily send deployment events from any GitHub Actions workflow to **Cased** so you can monitor, audit and analyse them alongside the rest of your engineering data.

## Features
* **One-line drop-in** – just add this action to your workflow.
* Automatically fills repository & commit details from GitHub context.
* Accepts extra metadata (JSON) and external URLs (e.g. link to the CI job).
* No external dependencies – just an HTTPS call to Cased.

---

## Usage
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  workflow_dispatch:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      # … your build & deploy steps …

      - name: Notify Cased
        uses: cased/cased-deploy-notification-action@v1
        with:
          api_key: ${{ secrets.CASED_API_KEY }}
          event_metadata: '{"environment": "prod"}'  # optional JSON string
```

### Inputs
| Name | Required | Default | Description |
| ---- | -------- | ------- | ----------- |
| `api_key` | ✅ | – | Organization API key from Cased (`Settings → API Keys`). |
| `deployment_request` | ❌ | auto | Optional friendly description (if omitted, the action generates one). |
| `repository_full_name` | ❌ | `${{ github.repository }}` | Owner/repo to attribute deployment to. Required only if your org has multiple repos **and** you’re notifying from a different repo. |
| `status` | ❌ | `success` | Deployment status: pending, running, success, failure or cancelled. |
| `event_metadata` | ❌ | – | JSON string – anything you’d like to attach (version, environment, etc.). |
| `commit_sha` | ❌ | `${{ github.sha }}` | Commit being deployed. |
| `commit_message` | ❌ | – | Commit message. |
| `external_url` | ❌ | – | Link back to the deployment job / run. |
| `cased_base_url` | ❌ | `https://app.cased.com` | Alternate base URL (rarely needed). |

---

## How it works
The action runs a tiny Python container that sends a POST request to Cased:
```
POST /api/v1/deployments/
Authorization: Token <api_key>
```
with the payload accepted by Cased’s public deployments API. Your organization is resolved from the API key and a deployment event is recorded, triggering monitoring & notifications.

---

# Development & Testing
```bash
# Build the docker image locally
cd cased-deploy-notification-action
docker build -t cased-deploy-notifier .

# Run it manually
docker run --rm \
  -e API_KEY=your_key \
  -e DEPLOYMENT_REQUEST="Deploy test" \
  cased-deploy-notifier
```

---

## License
MIT