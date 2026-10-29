# Gemini drafting and cost accounting

The script editor can quote and request a Gemini draft using only an approved research package. Generation does not change a script. The owner reviews the result and explicitly applies it as a new revision; existing export approvals are revoked. Factual output must cite approved claim IDs and exactly match an approved atomic statement. Unknown fields, tool calls and incomplete/invalid JSON are rejected. Editorial wording still needs human inspection.

## Configuration

Set a dedicated `SCOS_GEMINI_API_KEY` on the API service only. No key goes into browser code. The provider is `SCOS_AI_PROVIDER=gemini`; the model is configurable through `SCOS_GEMINI_MODEL` and must have a current entry in `providers/gemini-prices.json`.

Paid requests default to disabled. Enabling requires explicit owner-approved positive values for `SCOS_GEMINI_TASK_CAP_USD`, `SCOS_GEMINI_DAILY_CAP_USD`, `SCOS_GEMINI_MONTHLY_CAP_USD` and `SCOS_PAID_CALLS_DISABLED=false`. This implementation does not authorize any particular cap. No real paid call has been verified yet.

Pricing is sourced from Google's official Gemini pricing documentation, verified on 2026-10-29. The initial Gemini 3.8 Flash standard rate is $0.75 per million input tokens and $3.75 per million output/thinking tokens through 2026-12-31. The dated price entry expires at the announced rate change on 2027-01-01; calls then fail closed until prices are reviewed. Provider invoice adjustments/free-tier discounts can make actual billing lower than the conservative recorded amount.

## Durable boundary

Before contacting Google, the API commits the call intent and atomically reserves its upper bound against both UTC daily and monthly budgets. The bound includes prompt byte/framing allowance and a hard 4096-token combined output/thinking ceiling. Every request carries a client idempotency key and the quoted input hash. Concurrent reservations lock the budget rows; retries with the same key reuse the original call.

One provider request is made, without automatic retries, remote tools or caching. Valid usage and a provider response ID settle both holds but create one cost event. Invalid creative output is charged to the ledger when usage is known and is never applied. A timeout, malformed usage, oversized cost or uncertain response retains both holds and blocks a new request for the same input. A process crash leaves a durable submitting record and holds; it cannot silently release spend or trigger another request. Provider reconciliation is an operator action; uncertain calls must not be reset or deleted to retry.

`scos_0006` creates the call/reservation ledger. Apply it with the isolated migration credential and rerun `scripts/provision_supabase.py` before deploying a runtime that expects it.

Tests use synthetic Google responses and verify default-disabled behavior, dual-period concurrency, idempotency, timeouts, malformed usage, unsupported facts, expired pricing, stale quotes and explicit script application. These are not evidence of a successful real Gemini request.
