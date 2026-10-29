# Worker cancellation and recovery

Each attempt receives a lease owner, epoch and expiry. Heartbeats cannot revive an expired lease. Completion requires the same live lease and revalidated approved input hash. Each lease renders in a separate directory, so stale/reclaimed workers do not share incomplete FFmpeg files.

The owner can cancel queued jobs and active renders. Cancellation atomically revokes the lease. The worker observes this through its heartbeat and stops its process group, including FFmpeg, before registering any export. Storage operations already in progress finish or time out; the final fence still prevents approval. Uploaded orphan bytes remain immutable and do not become approved exports. Cancelling an in-flight publication is deliberately unavailable: its provider outcome must be reconciled.

Transient render/network timeouts retry with bounded backoff and the existing maximum-attempt limit. Exhausted attempts become dead letters. Deterministic policy failures are blocked. An explicit owner retry creates a new logical render only when its approved input hash still matches; it cannot revive a publication or silently change inputs. Concurrent identical render requests converge on one job through a transaction lock and database uniqueness.

Worker shutdown interrupts rendering and leaves a safe retry when a live lease can still be established. A killed worker's expired lease is recovered by another worker. No incomplete file is registered merely because it exists. Real process cancellation, expired fencing, three concurrent enqueues and retry exhaustion are tested. This is not a claim that every external-provider crash case has passed.
