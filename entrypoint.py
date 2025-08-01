#!/usr/bin/env python3
import json
import os
import sys
import logging
import requests

logging.basicConfig(level=logging.INFO, format="[cased-deploy-notification-action] %(levelname)s: %(message)s")

def getenv(name, default=""):
    val = os.getenv(name, default)
    return val.strip() if isinstance(val, str) else val

def main():
    api_key = getenv("API_KEY")
    deployment_request = getenv("DEPLOYMENT_REQUEST")

    if not api_key:
        logging.error("API_KEY is required")
        sys.exit(1)

    if not deployment_request:
        # Construct a sensible default description
        repo_full = getenv("REPOSITORY_FULL_NAME") or getenv("GITHUB_REPOSITORY", "repo")
        branch = getenv("GITHUB_REF_NAME") or getenv("GITHUB_REF", "").replace("refs/heads/", "")
        sha = getenv("COMMIT_SHA") or getenv("GITHUB_SHA", "")
        if sha:
            sha = sha[:7]

        parts = ["Deployment"]
        if branch:
            parts.append(branch)
        if sha:
            parts.append(f"({sha})")
        parts.append(f"to {repo_full}")
        deployment_request = " ".join(parts)

    base_url = getenv("CASED_BASE_URL") or "https://app.cased.com"
    endpoint = f"{base_url.rstrip('/')}/api/v1/deployments/"

    payload = {
        "deployment_request": deployment_request,
        "status": getenv("STATUS", "success"),
    }

    repo_full_name = getenv("REPOSITORY_FULL_NAME") or getenv("GITHUB_REPOSITORY")
    if repo_full_name:
        payload["repository_full_name"] = repo_full_name

    # Include ref if provided or infer from GitHub vars
    ref = getenv("REF") or getenv("GITHUB_REF_NAME") or getenv("GITHUB_REF", "")
    if ref:
        # Normalise to full refs/heads/ when it's a branch name
        if not ref.startswith("refs/") and len(ref) < 60:  # heuristic: likely branch
            ref = f"refs/heads/{ref}"
        payload["ref"] = ref

    # Determine GitHub run identifiers early
    github_run_id_val = getenv("RUN_ID") or getenv("GITHUB_RUN_ID")
    github_run_url_val = getenv("RUN_URL")
    if not github_run_url_val and github_run_id_val:
        github_run_url_val = (
            getenv("GITHUB_SERVER_URL", "https://github.com").rstrip("/") + "/" +
            getenv("GITHUB_REPOSITORY", "") + f"/actions/runs/{github_run_id_val}"
        )

    optional_fields = {
        "event_metadata": getenv("EVENT_METADATA"),
        "commit_sha": getenv("COMMIT_SHA") or getenv("GITHUB_SHA"),
        "commit_message": getenv("COMMIT_MESSAGE"),
        # External URL explicitly provided
        "external_url": getenv("EXTERNAL_URL"),

        # GitHub Actions run identifiers
        "github_run_id": github_run_id_val,
        "github_run_url": github_run_url_val,
        "workflow_id": getenv("WORKFLOW_ID"),
    }
    for k, v in optional_fields.items():
        if v:
            # Try to ensure event_metadata is valid JSON
            if k == "event_metadata":
                try:
                    payload[k] = json.loads(v)
                except json.JSONDecodeError:
                    logging.warning("EVENT_METADATA is not valid JSON; sending as string")
                    payload[k] = v
            else:
                payload[k] = v

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "cased-deploy-notification-action/0.1.0",
    }

    logging.info(f"Posting deployment event to {endpoint}")
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        logging.info("Notification sent successfully.")
    except requests.RequestException as e:
        logging.error(f"Failed to send deployment notification: {e}\nResponse: {getattr(e, 'response', None) and e.response.text}")
        sys.exit(1)

if __name__ == "__main__":
    main()
