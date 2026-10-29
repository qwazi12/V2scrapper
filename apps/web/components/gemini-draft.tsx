"use client";

import { useState } from "react";

interface Draft {
  id: string;
  status: string;
  error_code?: string;
  amount_usd?: string;
  output?: { sentences: { text: string; kind: string }[] };
}
interface Quote {
  input_sha256: string;
  maximum_cost_usd: string;
}

export function GeminiDraft({
  variantId,
  csrf,
  readiness,
  drafts,
  refresh,
}: {
  variantId: string;
  csrf: string;
  readiness?: { ready: boolean; model: string; blocked_reasons: string[] };
  drafts: Draft[];
  refresh: () => Promise<void>;
}) {
  const [quote, setQuote] = useState<Quote | null>(null);
  const [requestKey, setRequestKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function request(path: string, method: string, body?: unknown) {
    const response = await fetch(path, {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf,
        "Idempotency-Key": requestKey || crypto.randomUUID(),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
    const result = await response.json();
    if (!response.ok) throw Error(`${result.code}: ${result.message}`);
    return result;
  }

  async function run(action: "quote" | "generate" | "apply", id?: string) {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      if (action === "quote") {
        setQuote(
          await request(`/api/v1/variants/${variantId}/ai/quote`, "GET"),
        );
        setRequestKey(crypto.randomUUID());
      } else if (action === "generate" && quote) {
        const result: Draft = await request(
          `/api/v1/variants/${variantId}/ai/draft`,
          "POST",
          {
            expected_input_hash: quote.input_sha256,
          },
        );
        setQuote(null);
        setMessage(
          result.status === "succeeded"
            ? "Draft ready for your review. Apply it to create a new script revision."
            : `Draft ${result.status}. ${result.error_code || ""} Review the call record below.`,
        );
      } else if (action === "apply" && id) {
        await request(`/api/v1/ai/drafts/${id}/apply`, "POST");
        setQuote(null);
        setMessage(
          "New script revision saved for review. Earlier export approvals were revoked.",
        );
      }
    } catch (e) {
      // Keep the request key after network failure: retrying cannot create a second provider call.
      setError((e as Error).message);
    } finally {
      try {
        await refresh();
      } catch {
        setError(
          (previous) =>
            previous ||
            "Workspace refresh failed. Reconnect before continuing.",
        );
      }
      setBusy(false);
    }
  }

  return (
    <details>
      <summary>Draft with Gemini</summary>
      <p className="muted small">
        Draft from this campaign’s approved claims. Review the generated wording
        before applying it. Script approval and export approval remain separate
        steps.
      </p>
      {!readiness?.ready && (
        <p className="muted small">
          {readiness?.blocked_reasons.join(". ") || "Gemini is unavailable"}.
        </p>
      )}
      <div className="inline-actions">
        <button
          className="button secondary"
          disabled={busy || !readiness?.ready}
          onClick={() => run("quote")}
        >
          Estimate draft cost
        </button>
        {quote && (
          <button
            className="button"
            disabled={busy || !readiness?.ready}
            onClick={() => run("generate")}
          >
            Generate draft · up to ${quote.maximum_cost_usd}
          </button>
        )}
      </div>
      {quote && (
        <p className="muted small">
          Model: {readiness?.model}. UTC daily and monthly caps apply.
        </p>
      )}
      {error && <p role="alert">{error}</p>}
      {message && <p role="status">{message}</p>}
      {drafts.slice(0, 5).map((draft) => (
        <div className="panel" key={draft.id}>
          <p>
            Gemini draft · {draft.status.replaceAll("_", " ")}
            {draft.amount_usd ? ` · accounted cost $${draft.amount_usd}` : ""}
          </p>
          {draft.error_code && (
            <p className="muted small">{draft.error_code}</p>
          )}
          {["unknown", "submitting"].includes(draft.status) && (
            <p className="muted small">
              Budget remains reserved until this call is reconciled.
            </p>
          )}
          {draft.output?.sentences.map((line, i) => (
            <p key={i}>
              {line.text} <small className="muted">({line.kind})</small>
            </p>
          ))}
          {draft.status === "succeeded" && (
            <button
              className="button secondary"
              disabled={busy}
              onClick={() => run("apply", draft.id)}
            >
              Apply reviewed draft as new revision
            </button>
          )}
        </div>
      ))}
    </details>
  );
}
