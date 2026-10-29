import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import httpx
import pytest
from fastapi.testclient import TestClient
from scos import gemini, config
from scos.db import connect, one, all_rows, insert, sha
from scos.policy import PolicyError
from scos.app import app
from helpers import ready_campaign, upstream_test_export


@pytest.fixture
def enabled(monkeypatch):
    for key, value in {
        "SCOS_AI_PROVIDER": "gemini",
        "SCOS_PAID_CALLS_DISABLED": "false",
        "SCOS_GEMINI_API_KEY": "test-only-gemini-key-never-real",
        "SCOS_GEMINI_MODEL": "gemini-3.8-flash",
        "SCOS_GEMINI_TASK_CAP_USD": "1",
        "SCOS_GEMINI_DAILY_CAP_USD": "2",
        "SCOS_GEMINI_MONTHLY_CAP_USD": "10",
    }.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def variant():
    with connect() as c:
        _, variants = ready_campaign(c)
        return next(v for v in variants if v["format"] == "short_9_16")


def provider(monkeypatch, alter=None):
    requests = []
    client_type = httpx.Client

    def handler(request):
        requests.append(request)
        assert request.url.host == "generativelanguage.googleapis.com" and "key" not in request.url.params
        payload = json.loads(request.content)
        assert "tools" not in payload
        snapshot = json.loads(payload["contents"][0]["parts"][0]["text"])
        claim = snapshot["approved_claims"][0]
        draft = {"sentences": [{"text": claim["text"], "kind": "factual", "claim_refs": [claim["id"]]}]}
        response = {
            "candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": json.dumps(draft)}]}}],
            "responseId": "synthetic-gemini-receipt",
            "modelVersion": "gemini-3.8-flash",
            "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 40, "thoughtsTokenCount": 10},
        }
        if alter:
            return alter(request, response, draft)
        return httpx.Response(200, json=response)

    monkeypatch.setattr(gemini.httpx, "Client", lambda **kw: client_type(transport=httpx.MockTransport(handler), **kw))
    return requests


def test_default_zero_cap_never_contacts_gemini(monkeypatch, variant):
    monkeypatch.setenv("SCOS_PAID_CALLS_DISABLED", "true")

    def forbidden(**kw):
        raise AssertionError("No provider request is allowed")

    monkeypatch.setattr(gemini.httpx, "Client", forbidden)
    with pytest.raises(PolicyError) as error:
        gemini.generate(variant["id"], config.OWNER_ID, "disabled-test-key")
    assert error.value.code == "AI_DISABLED"
    with connect() as c:
        assert one(c, "SELECT count(*) AS n FROM ai_draft_calls")["n"] == 0


def test_valid_draft_settles_two_holds_but_never_approves_script(enabled, variant, monkeypatch):
    seen = provider(monkeypatch)
    result = gemini.generate(variant["id"], config.OWNER_ID, "valid-draft-key")
    assert result["status"] == "succeeded" and len(seen) == 1
    with connect() as c:
        holds = all_rows(c, "SELECT * FROM cost_reservations")
        assert len(holds) == 2 and all(h["state"] == "settled" for h in holds)
        assert one(c, "SELECT count(*) AS n FROM scripts WHERE variant_id=%s", (variant["id"],))["n"] == 1
        assert one(c, "SELECT count(*) AS n FROM cost_events")["n"] == 1
        assert all(p["reserved_amount"] == 0 for p in all_rows(c, "SELECT * FROM budget_policies"))


def test_duplicate_request_does_not_spend_twice(enabled, variant, monkeypatch):
    seen = provider(monkeypatch)
    a = gemini.generate(variant["id"], config.OWNER_ID, "same-draft-key")
    b = gemini.generate(variant["id"], config.OWNER_ID, "same-draft-key")
    assert a["id"] == b["id"] and len(seen) == 1


def test_timeout_holds_budget_and_blocks_blind_retry(enabled, variant, monkeypatch):
    def timeout(request, *rest):
        raise httpx.ReadTimeout("synthetic timeout", request=request)

    seen = provider(monkeypatch, timeout)
    with pytest.raises(PolicyError):
        gemini.generate(variant["id"], config.OWNER_ID, "uncertain-draft-key")
    with pytest.raises(PolicyError) as error:
        gemini.generate(variant["id"], config.OWNER_ID, "new-retry-draft-key")
    assert error.value.code == "AI_OUTCOME_UNKNOWN" and len(seen) == 1
    with connect() as c:
        assert one(c, "SELECT status FROM ai_draft_calls")["status"] == "unknown"
        assert all(r["state"] == "unknown" for r in all_rows(c, "SELECT * FROM cost_reservations"))


@pytest.mark.parametrize("change", ["extra_action", "wrong_claim", "changed_fact", "invalid_json"])
def test_invalid_model_output_is_paid_accounted_but_never_applied(enabled, variant, monkeypatch, change):
    def alter(request, response, draft):
        if change == "extra_action":
            draft["publish"] = True
        if change == "wrong_claim":
            draft["sentences"][0]["claim_refs"] = [str(uuid4())]
        if change == "changed_fact":
            draft["sentences"][0]["text"] = "An unsupported factual replacement."
        response["candidates"][0]["content"]["parts"][0]["text"] = (
            "not json" if change == "invalid_json" else json.dumps(draft)
        )
        return httpx.Response(200, json=response)

    provider(monkeypatch, alter)
    result = gemini.generate(variant["id"], config.OWNER_ID, "invalid-output-" + change)
    assert result["status"] == "failed" and result["error_code"] == "AI_OUTPUT_INVALID"
    with connect() as c:
        assert all(h["state"] == "settled" for h in all_rows(c, "SELECT * FROM cost_reservations"))
        assert one(c, "SELECT count(*) AS n FROM scripts WHERE variant_id=%s", (variant["id"],))["n"] == 1


def test_missing_usage_keeps_conservative_hold(enabled, variant, monkeypatch):
    def alter(request, response, draft):
        response.pop("usageMetadata")
        return httpx.Response(200, json=response)

    provider(monkeypatch, alter)
    with pytest.raises(PolicyError) as error:
        gemini.generate(variant["id"], config.OWNER_ID, "missing-usage-key")
    assert error.value.code == "AI_USAGE_UNCERTAIN"
    with connect() as c:
        assert all(p["consumed_amount"] == 0 for p in all_rows(c, "SELECT * FROM budget_policies"))


@pytest.mark.parametrize("change", ["list", "usage_list", "negative", "bool", "oversized", "receipt"])
def test_malformed_usage_never_releases_budget(enabled, variant, monkeypatch, change):
    def alter(request, response, draft):
        if change == "list":
            return httpx.Response(200, json=[])
        if change == "usage_list":
            response["usageMetadata"] = []
        elif change == "receipt":
            response["responseId"] = {"invalid": True}
        else:
            response["usageMetadata"]["candidatesTokenCount"] = {"negative": -1, "bool": True, "oversized": 9000}[
                change
            ]
        return httpx.Response(200, json=response)

    provider(monkeypatch, alter)
    with pytest.raises(PolicyError) as error:
        gemini.generate(variant["id"], config.OWNER_ID, "malformed-usage-" + change)
    assert error.value.code == "AI_USAGE_UNCERTAIN"
    with connect() as c:
        assert one(c, "SELECT status FROM ai_draft_calls")["status"] == "unknown"
        assert all(h["state"] == "unknown" for h in all_rows(c, "SELECT * FROM cost_reservations"))


def test_invalid_caps_do_not_break_workspace_readiness(enabled, monkeypatch):
    monkeypatch.setenv("SCOS_GEMINI_DAILY_CAP_USD", "invalid")
    assert gemini.readiness()["ready"] is False


def test_thought_signature_is_not_treated_as_an_action(enabled, variant, monkeypatch):
    def alter(request, response, draft):
        response["candidates"][0]["content"]["parts"][0]["thoughtSignature"] = "synthetic-opaque-signature"
        return httpx.Response(200, json=response)

    provider(monkeypatch, alter)
    assert gemini.generate(variant["id"], config.OWNER_ID, "signature-draft-key")["status"] == "succeeded"


def test_monthly_cap_rollback_does_not_leave_daily_hold(enabled, variant, monkeypatch):
    monkeypatch.setenv("SCOS_GEMINI_MONTHLY_CAP_USD", "0.000001")
    seen = provider(monkeypatch)
    with pytest.raises(PolicyError) as error:
        gemini.generate(variant["id"], config.OWNER_ID, "monthly-cap-key")
    assert error.value.code == "BUDGET_EXCEEDED" and not seen
    with connect() as c:
        assert one(c, "SELECT count(*) AS n FROM ai_draft_calls")["n"] == 0
        assert one(c, "SELECT count(*) AS n FROM cost_reservations")["n"] == 0


def test_expired_pricing_and_changed_quote_never_call_provider(enabled, variant, monkeypatch):
    seen = provider(monkeypatch)
    with pytest.raises(PolicyError):
        gemini.generate(variant["id"], config.OWNER_ID, "stale-quote-key", "0" * 64)
    monkeypatch.setattr(gemini, "now", lambda: datetime(2030, 1, 1, tzinfo=timezone.utc))
    with pytest.raises(PolicyError):
        gemini.generate(variant["id"], config.OWNER_ID, "expired-price-key")
    assert not seen


def test_parallel_dual_policy_reservations_do_not_overspend(enabled, variant, monkeypatch):
    monkeypatch.setenv("SCOS_GEMINI_DAILY_CAP_USD", "1")
    monkeypatch.setenv("SCOS_GEMINI_MONTHLY_CAP_USD", "1")

    def request(i):
        try:
            with connect() as c:
                call = insert(
                    c,
                    "ai_draft_calls",
                    actor_id=config.OWNER_ID,
                    variant_id=variant["id"],
                    idempotency_key="parallel-" + str(i),
                    request_sha256=sha(str(i).encode()),
                    input_sha256=sha(str(i).encode()),
                    input_snapshot={},
                    model_id="gemini-3.8-flash",
                    price_snapshot={},
                    estimated_cost=Decimal(".75"),
                    status="submitting",
                )
                gemini.reserve(c, call, Decimal(".75"))
            return True
        except PolicyError:
            return False

    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(request, range(3)))
    assert sum(results) == 1
    with connect() as c:
        policies = all_rows(
            c, "SELECT * FROM budget_policies WHERE policy_key LIKE %s", (config.NAMESPACE + "-gemini-%",)
        )
        assert len(policies) == 2 and all(p["reserved_amount"] == Decimal(".75") for p in policies)


def test_applying_draft_requires_owner_action_and_revokes_export(enabled, variant, monkeypatch):
    with connect() as c:
        ex = upstream_test_export(c, variant)
    provider(monkeypatch)
    draft = gemini.generate(variant["id"], config.OWNER_ID, "draft-to-apply-key")
    with TestClient(app) as client:
        auth = client.post("/api/v1/auth/local", headers={"Origin": "http://127.0.0.1:3100"}).json()
        path = "/api/v1/ai/drafts/" + draft["id"] + "/apply"
        assert client.post(path).status_code == 403
        result = client.post(
            path,
            headers={
                "Origin": "http://127.0.0.1:3100",
                "X-CSRF-Token": auth["csrf_token"],
                "Idempotency-Key": "apply-exact-draft-key",
            },
        )
        assert result.status_code == 200, result.text
    with connect() as c:
        assert one(c, "SELECT status FROM exports WHERE id=%s", (ex["id"],))["status"] == "revoked"
        newest = one(c, "SELECT * FROM scripts WHERE variant_id=%s ORDER BY revision DESC LIMIT 1", (variant["id"],))
        assert newest["revision"] == 2 and newest["review_status"] == "draft"
