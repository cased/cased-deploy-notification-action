import os
import json
import builtins
import types
import importlib

import pytest

# Path hack so we can import entrypoint when run from repo root
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

import entrypoint  # noqa: E402, module after path change


class DummyResponse:
    def __init__(self, status_code=201, text="OK"):
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    # ensure we start with clean env for each test
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


def test_missing_only_api_key(monkeypatch):
    # Without API_KEY should fail
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.setenv("DEPLOYMENT_REQUEST", "foo")
    with pytest.raises(SystemExit):
        entrypoint.main()


def test_auto_generated_request(monkeypatch):
    monkeypatch.setenv("API_KEY", "abc")
    monkeypatch.setenv("GITHUB_REPOSITORY", "cased/app")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    monkeypatch.setenv("GITHUB_SHA", "deadbeefcafebabe1234")

    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["json"] = json
        return DummyResponse(201)

    monkeypatch.setattr(entrypoint.requests, "post", fake_post)

    entrypoint.main()
    assert "deployment_request" in captured["json"]
    assert captured["json"]["deployment_request"].startswith("Deployment")


def test_success_payload(monkeypatch):
    env = {
        "API_KEY": "abc123",
        "DEPLOYMENT_REQUEST": "Deploy main to prod",
        "STATUS": "pending",
        "REPOSITORY_FULL_NAME": "cased/app",
        "EVENT_METADATA": '{"env":"prod"}',
        "COMMIT_SHA": "deadbeef",
        "COMMIT_MESSAGE": "initial",
        "EXTERNAL_URL": "https://ci.example.com/1",
        "CASED_BASE_URL": "https://app.cased.com",
    }
    monkeypatch.setenv("GITHUB_REPOSITORY", "should-not-be-used")
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return DummyResponse(201)

    monkeypatch.setattr(entrypoint.requests, "post", fake_post)

    entrypoint.main()

    assert captured["url"].endswith("/api/v1/deployments/")
    assert captured["headers"]["Authorization"] == "Token abc123"
    payload = captured["json"]
    assert payload["deployment_request"] == env["DEPLOYMENT_REQUEST"]
    assert payload["status"] == "pending"
    assert payload["repository_full_name"] == env["REPOSITORY_FULL_NAME"]
    # event_metadata should be dict
    assert isinstance(payload["event_metadata"], dict) and payload["event_metadata"]["env"] == "prod"
    assert payload["commit_sha"] == env["COMMIT_SHA"]
    if "external_url" in payload:
        assert payload["external_url"] == env["EXTERNAL_URL"]


def test_invalid_metadata_passes_string(monkeypatch):
    monkeypatch.setenv("API_KEY", "abc")
    monkeypatch.setenv("DEPLOYMENT_REQUEST", "test")
    monkeypatch.setenv("EVENT_METADATA", "not-json")

    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["json"] = json
        return DummyResponse(201)

    monkeypatch.setattr(entrypoint.requests, "post", fake_post)

    entrypoint.main()
    assert captured["json"]["event_metadata"] == "not-json" 