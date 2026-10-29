# Hosted application backup and isolated recovery

`scripts/backup_hosted.py` backs up the new Supabase staging project's private SCOS schema and every object under its content-addressed `objects` prefix. It does not read other schemas or reuse a legacy application's backup. A PostgreSQL exported snapshot binds the dump and table checksums to the same transaction. Referenced media missing from the private bucket makes the backup fail.

Database, media and manifest files use authenticated AES-256-GCM encryption with fresh nonces and a dedicated 32-byte key. Project/schema/archive/file labels are authenticated, so moving encrypted bytes between objects or environments fails validation. The key is provided through `SCOS_BACKUP_ENCRYPTION_KEY` and is never stored in the archive. Keep a separate recoverable copy of that key in the owner's password manager; a backup cannot be recovered if the only key copy is lost. Archive folders are mode 0700; files are 0600. Retain their timestamp folder names when copying them.

Run with the isolated migration operator's existing SCOS configuration:

```sh
PYTHONPATH=services/api uv run python scripts/backup_hosted.py --output /private/backup/location --restore-drill
```

The restore drill starts a new pinned PostgreSQL 17 container with networking disabled and no exposed port or worker. It restores the schema, verifies every included table's row count and content checksum, decrypts/restores each media file and checks its SHA-256. It then removes the recovery container and its temporary volumes. Existing databases, buckets and original local processes are never restored over or stopped.

To verify an existing encrypted archive independently of the source services, provide the same project/schema configuration and key, then use:

```sh
PYTHONPATH=services/api uv run python scripts/backup_hosted.py --restore-from /private/backup/location/TIMESTAMP
```

The owner allowlist table is restored empty. Supabase Auth identities, provider settings and secrets are intentionally excluded. Reconnecting a recovered environment requires explicit owner configuration and new grants; recovery cannot silently activate publishing. Hosted auth configuration recovery, scheduled offsite replication, retention policy and regional failover remain separate release gates.

On 2026-10-29 the real staging backup and isolated restore passed for 48 included tables and three media objects (518600 bytes). This small empty-workspace drill proves schema/media recoverability, not the full production RPO/RTO at load. The encrypted archive and its separate key remain in the private local operator directory, outside GitHub and public build artifacts.
