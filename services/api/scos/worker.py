"""Separate durable worker; every completion is fenced by its lease epoch."""

import signal
import threading
import time
from .db import connect, one, all_rows, insert, uid, event, audit
from .policy import variant_ready, export_ready, require
from .config import RUNTIME, validate
from . import storage

STOP = False


def claim_job(c, owner):
    # Ambiguous side effects are held, never blindly re-enqueued.
    stale = all_rows(
        c, "SELECT * FROM jobs WHERE status IN ('leased','running') AND lease_expires_at<now() FOR UPDATE SKIP LOCKED"
    )
    for job in stale:
        if job["kind"] == "mock_publish":
            c.execute(
                "UPDATE publication_attempts SET state='unknown',error_code='WORKER_LOST' WHERE id=%s AND state!='confirmed'",
                (job["aggregate_id"],),
            )
            c.execute(
                "UPDATE jobs SET status='blocked',last_error_code='PUBLICATION_UNCONFIRMED' WHERE id=%s", (job["id"],)
            )
        else:
            c.execute(
                "UPDATE jobs SET status=CASE WHEN attempt_count>=max_attempts THEN 'dead_letter' ELSE 'retry_wait' END,lease_owner=NULL WHERE id=%s",
                (job["id"],),
            )
    job = one(
        c,
        """SELECT * FROM jobs WHERE status IN ('queued','retry_wait') AND available_at<=now()
        AND attempt_count<max_attempts ORDER BY priority DESC,created_at FOR UPDATE SKIP LOCKED LIMIT 1""",
    )
    if not job:
        return None
    return one(
        c,
        """UPDATE jobs SET status='running',lease_owner=%s,lease_epoch=lease_epoch+1,
        lease_expires_at=now()+interval '60 seconds',heartbeat_at=now(),attempt_count=attempt_count+1
        WHERE id=%s RETURNING *""",
        (owner, job["id"]),
    )


def fenced(c, job):
    row = one(c, "SELECT * FROM jobs WHERE id=%s FOR UPDATE", (job["id"],))
    require(
        row
        and row["lease_epoch"] == job["lease_epoch"]
        and row["lease_owner"] == job["lease_owner"]
        and row["status"] == "running",
        "WORKER_LEASE_LOST",
        "Stale worker cannot complete this job",
    )


def heartbeat(job, done):
    while not done.wait(10):
        with connect() as c:
            c.execute(
                "UPDATE jobs SET heartbeat_at=now(),lease_expires_at=now()+interval '60 seconds' WHERE id=%s AND lease_epoch=%s AND lease_owner=%s AND status='running'",
                (job["id"], job["lease_epoch"], job["lease_owner"]),
            )


def process_render(job):
    from .media import render

    with connect() as c:
        variant, campaign, script, assets, snapshot = variant_ready(c, job["aggregate_id"])
        require(snapshot == job["input_hash"], "EXPORT_APPROVAL_STALE", "Inputs changed after the job was requested")
        for asset in assets:
            storage.read(asset["object_key"], asset["sha256"])
        insert(
            c,
            "job_events",
            job_id=job["id"],
            stage="render",
            event_type="progress",
            progress=10,
            message="Rendering original synthetic frames and local audio",
        )
    output, checks = render(RUNTIME / "renders" / str(job["id"]), variant, campaign, script, assets)
    with connect() as c:
        fenced(c, job)
        _, _, _, _, current = variant_ready(c, job["aggregate_id"])
        require(current == snapshot, "EXPORT_APPROVAL_STALE", "Inputs changed while rendering")
        status = "qa_failed" if any(st == "fail" for _, st, _ in checks) else "qa_passed"
        export = insert(
            c,
            "exports",
            variant_id=variant["id"],
            job_id=job["id"],
            format=variant["format"],
            input_snapshot_hash=snapshot,
            status=status,
            **output,
        )
        for name, st, value in checks:
            insert(
                c,
                "quality_checks",
                export_id=export["id"],
                check_name=name,
                status=st,
                severity="warning" if name == "editorial_review" else "blocker",
                observed_value=value,
                checker_version="scos-local-v1",
            )
        c.execute(
            "UPDATE jobs SET status='succeeded',output=%s::jsonb,lease_expires_at=NULL WHERE id=%s",
            ('{"export_id":"' + str(export["id"]) + '"}', job["id"]),
        )
        c.execute("UPDATE campaigns SET status='ready_for_approval' WHERE id=%s", (campaign["id"],))
        insert(
            c,
            "job_events",
            job_id=job["id"],
            stage="complete",
            event_type="progress",
            progress=100,
            message="Immutable export stored; technical QA complete; owner review required",
        )
        event(c, "render.completed", export["id"], sha256=export["sha256"])


def process_publish(job):
    with connect() as c:
        fenced(c, job)
        attempt = one(c, "SELECT * FROM publication_attempts WHERE id=%s FOR UPDATE", (job["aggregate_id"],))
        require(
            attempt and attempt["state"] == "scheduled", "PUBLICATION_UNCONFIRMED", "Attempt is no longer scheduled"
        )
        account = one(c, "SELECT * FROM social_accounts WHERE id=%s", (attempt["account_id"],))
        require(
            account["external_account_id"].startswith("scos-mock-"),
            "PUBLISHING_DISABLED",
            "Worker allows mock account IDs only",
        )
        ex = export_ready(c, attempt["export_id"], platform=account["platform"])
        c.execute("UPDATE publication_attempts SET state='submitting',submitted_at=now() WHERE id=%s", (attempt["id"],))
        insert(
            c,
            "publication_events",
            attempt_id=attempt["id"],
            kind="submission_intent",
            sanitized_response={"mode": "mock", "account_id": str(account["id"])},
        )
    # The mock provider journal commits independently, modeling remote acceptance.
    with connect() as remote:
        receipt = one(remote, "SELECT * FROM mock_provider_receipts WHERE intent_id=%s", (attempt["id"],))
        if not receipt:
            receipt = insert(
                remote,
                "mock_provider_receipts",
                intent_id=attempt["id"],
                external_post_id="scos-mock-post-" + str(attempt["id"]),
                account_id=attempt["account_id"],
                export_sha256=ex["sha256"],
            )
    with connect() as c:
        fenced(c, job)
        if attempt["provider_status"].get("simulate_response_lost"):
            c.execute(
                "UPDATE publication_attempts SET state='unknown',error_code='MOCK_RESPONSE_LOST' WHERE id=%s",
                (attempt["id"],),
            )
            c.execute(
                "UPDATE jobs SET status='blocked',last_error_code='PUBLICATION_UNCONFIRMED',last_error_summary='Mock provider accepted; acknowledgment deliberately lost. Reconcile before retry.' WHERE id=%s",
                (job["id"],),
            )
            event(c, "publication.unknown", attempt["id"], reason="mock_response_lost")
        else:
            c.execute(
                "UPDATE publication_attempts SET state='confirmed',external_post_id=%s,confirmed_at=now() WHERE id=%s",
                (receipt["external_post_id"], attempt["id"]),
            )
            c.execute("UPDATE jobs SET status='succeeded',lease_expires_at=NULL WHERE id=%s", (job["id"],))
            event(c, "publication.confirmed", attempt["id"], external_post_id=receipt["external_post_id"])
        insert(
            c,
            "publication_events",
            attempt_id=attempt["id"],
            kind="provider_result",
            sanitized_response={
                "mode": "mock",
                "response_lost": attempt["provider_status"].get("simulate_response_lost", False),
            },
        )


def dispatch_events(c):
    for ev in all_rows(
        c, "SELECT * FROM domain_events WHERE delivered_at IS NULL ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 50"
    ):
        c.execute(
            "INSERT INTO event_inbox_receipts(subscriber,event_id) VALUES('local-audit',%s) ON CONFLICT DO NOTHING",
            (ev["id"],),
        )
        c.execute(
            "UPDATE domain_events SET delivered_at=now(),delivery_attempts=delivery_attempts+1 WHERE id=%s", (ev["id"],)
        )


def tick(owner):
    with connect() as c:
        dispatch_events(c)
        job = claim_job(c, owner)
    if not job:
        return False
    done = threading.Event()
    thread = threading.Thread(target=heartbeat, args=(job, done), daemon=True)
    thread.start()
    try:
        if job["kind"] == "render":
            process_render(job)
        elif job["kind"] == "mock_publish":
            process_publish(job)
        else:
            raise ValueError("Unsupported job kind")
    except Exception as exc:
        from .policy import PolicyError

        code = exc.code if isinstance(exc, PolicyError) else type(exc).__name__
        message = exc.message if isinstance(exc, PolicyError) else str(exc)[:500]
        with connect() as c:
            # Preserve uncertainty for anything that may have reached a provider.
            row = one(c, "SELECT * FROM jobs WHERE id=%s FOR UPDATE", (job["id"],))
            if row["lease_epoch"] == job["lease_epoch"] and row["status"] == "running":
                if job["kind"] == "mock_publish":
                    c.execute(
                        "UPDATE publication_attempts SET state='unknown',error_code=%s WHERE id=%s AND state NOT IN ('confirmed','cancelled')",
                        (code, job["aggregate_id"]),
                    )
                c.execute(
                    "UPDATE jobs SET status='failed',last_error_code=%s,last_error_summary=%s,lease_expires_at=NULL WHERE id=%s",
                    (code, message, job["id"]),
                )
                audit(c, "job.failed", job["id"], details={"code": code, "message": message})
        print(f"Job {job['id']} failed: {code}: {message}", flush=True)
    finally:
        done.set()
        thread.join(timeout=1)
    return True


def main():
    validate()
    storage.init()
    owner = "scos-worker-" + uid()

    def stop(*_):
        global STOP
        STOP = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    print("SCOS local worker ready; live writes and paid calls disabled", flush=True)
    while not STOP:
        if not tick(owner):
            time.sleep(1)


if __name__ == "__main__":
    main()
