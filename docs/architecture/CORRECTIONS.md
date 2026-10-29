# Corrections, rights changes and script history

An owner claim correction requires the expected claim revision and a written reason. It records the original claim in the audit history, increments the revision, clears the prior identity/evidence verdict and revokes dependent research packages, scripts, exports and packages. The corrected wording cannot reuse the old review.

Evidence verdicts can explicitly support, contradict, merely mention or leave a claim unknown. The cited passage must exist in its stored source. A changed verdict revokes dependent approvals and requires another claim review. Source invalidation retains the immutable source text/checksum and invalidates every linked claim and export; it does not overwrite the original passage.

Asset rights can be restricted with a reason. All prior rights reviews on that asset are withdrawn and every use is invalidated. The render-input snapshot includes license scope, validity window, derivative permission, proof, attribution and review timestamp. Directly changing these fields cannot leave an old export eligible. Future-dated and expired licenses fail the gate.

Script history exposes earlier wording and sentence additions/removals. Restoring an earlier version creates a new unapproved revision and revokes export approval; it never mutates the older text or reuses its approval. Optimistic revisions prevent stale double restores.

The API tests cover claim/source/rights invalidation, explicit contradictions, version restoration, future licenses and missing structured values. The real browser workflow saves revision 2, restores revision 1 as draft revision 3, verifies export revocation, and corrects a claim that then requires fresh evidence review. Live structured-source refresh, editorial brief history and full research conflict-resolution workflows remain incomplete.
