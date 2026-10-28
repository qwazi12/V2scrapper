import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg import sql
from .config import DATABASE_URL


def connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def encode(x):
    if isinstance(x, (UUID, Decimal)):
        return str(x)
    if isinstance(x, datetime):
        return x.isoformat()
    raise TypeError(type(x).__name__)


def clean(x):
    return json.loads(json.dumps(x, default=encode))


def sha(x):
    data = x if isinstance(x, bytes) else json.dumps(clean(x), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc)


def one(c, query, params=()):
    return c.execute(query, params).fetchone()


def all_rows(c, query, params=()):
    return c.execute(query, params).fetchall()


def insert(c, table, **values):
    values = {
        k: Jsonb(clean(v)) if isinstance(v, (dict, list)) and k not in ARRAY_COLUMNS else v for k, v in values.items()
    }
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
        sql.Identifier(table),
        sql.SQL(",").join(map(sql.Identifier, values)),
        sql.SQL(",").join(sql.Placeholder() for _ in values),
    )
    return one(c, query, tuple(values.values()))


ARRAY_COLUMNS = {"claim_ids", "source_ids", "scopes", "platforms", "permitted_uses", "tags", "visual_tags", "aliases"}


def audit(c, action, subject, actor=None, reason=None, details=None):
    insert(
        c,
        "audit_events",
        actor_user_id=actor,
        actor_type="user" if actor else "worker",
        action=action,
        subject_kind=action.split(".")[0],
        subject_id=str(subject),
        reason=reason,
        trace_id=uid(),
        details=details or {},
    )


def event(c, action, aggregate, revision=1, **payload):
    insert(
        c,
        "domain_events",
        aggregate_kind=action.split(".")[0],
        aggregate_id=aggregate,
        aggregate_revision=revision,
        event_type=action + ".v1",
        payload=payload,
    )
