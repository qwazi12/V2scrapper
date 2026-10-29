from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import pytest
from scos.db import connect, one, all_rows, insert, now
from scos.config import OWNER_ID
from scos.commands import command
from scos.policy import PolicyError
from scos.worker import claim_job, fenced, process_publish, dispatch_events, tick
from helpers import ready_campaign, upstream_test_export


def test_lost_mock_response_reconciles_without_second_submission():
    with connect() as c:
        _, variants = ready_campaign(c)
        variant = next(v for v in variants if v["format"] == "short_9_16")
        ex = upstream_test_export(c, variant)
        account = one(c, "SELECT * FROM social_accounts WHERE platform='youtube'")
        package = command(c, "package.create", ex["id"], {"account_id": str(account["id"])}, OWNER_ID)
        attempt = command(
            c,
            "publish.mock",
            package["id"],
            {"external_account_id": account["external_account_id"], "simulate_response_lost": True},
            OWNER_ID,
        )
    with connect() as c:
        job = claim_job(c, "test-worker")
    process_publish(job)
    with connect() as c:
        assert one(c, "SELECT state FROM publication_attempts WHERE id=%s", (attempt["id"],))["state"] == "unknown"
        with pytest.raises(PolicyError):
            command(c, "publish.mock", package["id"], {"external_account_id": account["external_account_id"]}, OWNER_ID)
        result = command(c, "publish.reconcile", attempt["id"], {}, OWNER_ID)
        assert result["state"] == "confirmed"
        assert result["submit_count"] == 1
        assert one(c, "SELECT count(*) AS n FROM mock_provider_receipts")["n"] == 1


def test_expired_publish_job_is_held_not_retried(conn):
    job = insert(
        conn,
        "jobs",
        kind="mock_publish",
        aggregate_kind="publication_attempt",
        input_hash="test",
        payload={},
        status="running",
        lease_owner="lost",
        lease_epoch=1,
        attempt_count=1,
        max_attempts=1,
        lease_expires_at=now() - timedelta(seconds=1),
    )
    assert claim_job(conn, "new-worker") is None
    assert one(conn, "SELECT status FROM jobs WHERE id=%s", (job["id"],))["status"] == "blocked"


def test_stale_worker_is_fenced(conn):
    insert(conn, "jobs", kind="render", input_hash="fenced", payload={}, max_attempts=3)
    first = claim_job(conn, "worker-one")
    conn.execute("UPDATE jobs SET lease_expires_at=now()-interval '1 second' WHERE id=%s", (first["id"],))
    second = claim_job(conn, "worker-two")
    assert second["lease_epoch"] > first["lease_epoch"]
    with pytest.raises(PolicyError) as e:
        fenced(conn, first)
    assert e.value.code == "WORKER_LEASE_LOST"


def test_duplicate_events_have_one_inbox_receipt(conn):
    from scos.db import event, uid

    event(conn, "test.created", uid(), example="safe")
    dispatch_events(conn)
    conn.execute("UPDATE domain_events SET delivered_at=NULL")
    dispatch_events(conn)
    assert one(conn, "SELECT count(*) AS n FROM event_inbox_receipts")["n"] == 1


def test_parallel_budget_reservations_cannot_overspend():
    with connect() as c:
        c.execute("UPDATE budget_policies SET limit_amount=5")

    def reserve(_):
        try:
            with connect() as c:
                command(c, "budget.reserve", None, {"amount": 4}, OWNER_ID)
            return "reserved"
        except PolicyError:
            return "blocked"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reserve, range(2)))
    assert sorted(results) == ["blocked", "reserved"]
    with connect() as c:
        assert one(c, "SELECT reserved_amount FROM budget_policies")["reserved_amount"] == 4


def test_parallel_workers_claim_one_job():
    with connect() as c:
        insert(c, "jobs", kind="render", input_hash="one-job", payload={}, max_attempts=2)

    def claim(i):
        with connect() as c:
            return claim_job(c, "worker-" + str(i))

    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = list(pool.map(claim, range(3)))
    assert sum(j is not None for j in jobs) == 1


def test_parallel_identical_renders_have_one_logical_job():
    with connect() as c:
        _, variants = ready_campaign(c)
        variant = variants[0]

    def enqueue(_):
        with connect() as c:
            return command(c, "render", variant["id"], {}, OWNER_ID)["id"]

    with ThreadPoolExecutor(max_workers=3) as pool:
        ids = list(pool.map(enqueue, range(3)))
    assert len(set(ids)) == 1
    with connect() as c:
        assert one(c, "SELECT count(*) AS n FROM jobs")["n"] == 1


def test_expired_lease_cannot_complete_before_it_is_reclaimed(conn):
    insert(conn, "jobs", kind="render", input_hash="expired", payload={})
    job = claim_job(conn, "worker-expired")
    conn.execute("UPDATE jobs SET lease_expires_at=now()-interval '1 second' WHERE id=%s", (job["id"],))
    with pytest.raises(PolicyError) as error:
        fenced(conn, job)
    assert error.value.code == "WORKER_LEASE_LOST"


def test_transient_render_retries_then_dead_letters(monkeypatch):
    from scos import worker
    import httpx

    with connect() as c:
        job = insert(c, "jobs", kind="render", input_hash="retry", payload={}, max_attempts=2)

    def fail(*args):
        raise httpx.ReadTimeout("synthetic storage timeout")

    monkeypatch.setattr(worker, "process_render", fail)
    tick("retry-worker")
    with connect() as c:
        assert one(c, "SELECT status FROM jobs WHERE id=%s", (job["id"],))["status"] == "retry_wait"
        c.execute("UPDATE jobs SET available_at=now() WHERE id=%s", (job["id"],))
    tick("retry-worker")
    with connect() as c:
        row = one(c, "SELECT * FROM jobs WHERE id=%s", (job["id"],))
        assert row["status"] == "dead_letter" and row["attempt_count"] == 2
        assert one(c, "SELECT count(*) AS n FROM exports")["n"] == 0
    assert tick("retry-worker") is False


def test_owner_cancellation_stops_real_ffmpeg_and_fences_partial_output(monkeypatch):
    from scos import media
    import threading

    with connect() as c:
        _, variants = ready_campaign(c)
        job = command(c, "render", variants[0]["id"], {}, OWNER_ID)
    started = threading.Event()

    def slow_render(work, *args):
        work.mkdir(parents=True, exist_ok=True)
        started.set()
        media.run(
            [
                "ffmpeg",
                "-y",
                "-v",
                "error",
                "-re",
                "-f",
                "lavfi",
                "-i",
                "color=c=blue:s=320x240:r=10",
                "-t",
                "10",
                "-c:v",
                "libx264",
                str(work / "partial.mp4"),
            ]
        )
        raise AssertionError("Cancelled FFmpeg must not reach export completion")

    monkeypatch.setattr(media, "render", slow_render)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(tick, "cancel-worker")
        assert started.wait(5)
        with connect() as c:
            cancelled = command(c, "job.cancel", job["id"], {}, OWNER_ID)
            assert cancelled["status"] == "cancelled"
        assert future.result(timeout=8)
    with connect() as c:
        row = one(c, "SELECT * FROM jobs WHERE id=%s", (job["id"],))
        assert row["status"] == "cancelled" and row["lease_owner"] is None
        assert one(c, "SELECT count(*) AS n FROM exports")["n"] == 0
        retry = command(c, "job.retry", job["id"], {"expected_lease_epoch": row["lease_epoch"]}, OWNER_ID)
        assert retry["id"] != job["id"] and retry["status"] == "queued"
        assert retry["input_hash"] == job["input_hash"]


def test_dead_render_lease_exhaustion_is_not_reclaimed(conn):
    job = insert(
        conn,
        "jobs",
        kind="render",
        input_hash="exhausted",
        payload={},
        max_attempts=1,
        attempt_count=1,
        status="running",
        lease_owner="dead-worker",
        lease_epoch=1,
        lease_expires_at=now() - timedelta(seconds=1),
    )
    assert claim_job(conn, "new-worker") is None
    assert one(conn, "SELECT status FROM jobs WHERE id=%s", (job["id"],))["status"] == "dead_letter"


def test_reply_repeated_send_is_idempotent(conn):
    command(conn, "community.fixture", None, {}, OWNER_ID)
    thread = one(conn, "SELECT * FROM comment_threads LIMIT 1")
    reply = command(conn, "reply.save", thread["id"], {"text": "Thank you for the thoughtful question."}, OWNER_ID)
    command(conn, "reply.approve", reply["id"], {"expected_hash": reply["draft_hash"]}, OWNER_ID)
    a = command(conn, "reply.send_mock", reply["id"], {"expected_hash": reply["draft_hash"]}, OWNER_ID)
    b = command(conn, "reply.send_mock", reply["id"], {"expected_hash": reply["draft_hash"]}, OWNER_ID)
    assert a["external_reply_id"] == b["external_reply_id"]


def test_unknown_metrics_remain_null(conn):
    command(conn, "analytics.fixture", None, {}, OWNER_ID)
    rows = all_rows(conn, "SELECT * FROM analytics_observations WHERE metric='average_view_duration'")
    assert len(rows) == 3
    assert all(r["value"] is None and r["missing_reason"] for r in rows)
