"use client";
import { useState } from "react";

interface Version {
  revision: number;
  text: string;
  review_status: string;
  changes: { kind: string; text: string }[];
}

export function ScriptHistory({
  variantId,
  revision,
  restore,
}: {
  variantId: string;
  revision: number;
  restore: (sourceRevision: number) => Promise<void>;
}) {
  const [versions, setVersions] = useState<Version[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(
        `/api/v1/variants/${variantId}/scripts/history`,
      );
      if (!response.ok) throw Error("Script history could not load.");
      setVersions((await response.json()).items);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <details
      onToggle={(e) => {
        if (e.currentTarget.open) load();
      }}
    >
      <summary>Compare earlier script revisions</summary>
      <p className="muted small">
        Restoring creates a new draft for review and revokes earlier export
        approvals.
      </p>
      {error && <p role="alert">{error}</p>}
      {busy && <p role="status">Loading revisions…</p>}
      {versions.map((version) => (
        <div className="panel" key={version.revision}>
          <strong>
            Revision {version.revision} ·{" "}
            {version.review_status.replaceAll("_", " ")}
          </strong>
          <p>{version.text}</p>
          {version.changes.map((change, i) => (
            <p className="muted small" key={i}>
              {change.kind === "added" ? "Added" : "Removed"}: {change.text}
            </p>
          ))}
          {version.revision < revision && (
            <button
              className="button secondary"
              disabled={busy}
              onClick={async () => {
                setBusy(true);
                try {
                  await restore(version.revision);
                  await load();
                } finally {
                  setBusy(false);
                }
              }}
            >
              Restore revision {version.revision} as new draft
            </button>
          )}
        </div>
      ))}
    </details>
  );
}
