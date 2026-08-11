# Temporal and Causal Authority

**Status:** current normative owner for historical access, Restore, Rewind, committed-history mutation authority, and direct future observation. Rewind execution remains unsupported/deferred by the current reference implementation and outside the v1 stable required conformance surface.

## Purpose

This document preserves and translates the released v0.5 temporal/causal contract into the current authority model without claiming an implementation that does not exist.

It owns:

- read-only historical references;
- Restore versus Rewind;
- authority and validation for committed-history mutation;
- Replay versus Rewind;
- direct future observation versus prediction;
- temporal/causal diagnostics and current conformance classification.

## Non-goals

- define a new MKI data-plane primitive;
- make Rewind an ordinary `RECONFIGURE`, lower World Kernel `TRANSITION`, rollback, or replay mode;
- define a production history-rewrite algorithm or storage format;
- grant causal authority from Energy, magic power, syntax, registry metadata, evidence, or a sandbox allowance;
- add Rewind or direct future observation to the current reference implementation;
- promote this deferred surface into the v1 required 4-class / 65-case conformance manifest.

## Key invariants

```text
Restore != Rewind
Replay != Rewind
ordinary RECONFIGURE != committed-history mutation
historical observation != current Ref acquisition
prediction != direct future observation
Energy/resource magnitude != temporal/causal authority
authorization success != causal validity
HistoryMutationDenied != TemporalAuthorityError != CausalityCycleError
```

## 1. Model and normative ownership

Current world execution retains:

```text
C = <Σ,H,Ω,P>
H = (E,≺)
```

where `H` is the committed Event set and its causal relation. Ordinary execution appends committed Events. Backdating `effective_at`, replaying evidence, restoring a past-like state in the present, or compensating for an effect does not rewrite existing `H`.

This document is the single current normative owner for mutation authority over existing committed `H`. `semantics.md`, `runtime-time.md`, `types.md`, `errors.md`, `security-sandbox.md`, and `terminology.md` provide cross-domain summaries and indexes only.

## 2. Historical access

```text
HistoricalRef<T>
HistoricalMeasurement<Q>
```

are read-only views of admitted historical evidence. They:

- do not become current `Ref<T>` merely by being observed;
- do not prove current identity, existence, liveness, Capability, Lease, or authority;
- cannot be used as a write handle into `Σ` or `H`;
- remain subject to the current profile's visibility, disclosure, privacy, and causal-access policy.

Ordinary historical access may expose admitted Event logs, committed snapshots, and identity history. The exact read capability is profile-owned; absence of an explicit admitted access contract fails closed rather than being inferred from visibility or evidence possession.

## 3. Restore

Restore reconstructs a state equal or similar to an earlier state **in the present**. It is a forward operation:

```text
current Σ
  -> validated present-world effects
  -> new restoration Event appended to H
```

A Restore may use ordinary admitted current-world operations only when it independently satisfies their type, identity, Capability, Lease, conservation/accounting, model/profile, and COMMIT obligations. It does not delete, replace, or retroactively alter prior Events.

```text
Restore success != history rewritten
```

## 4. Rewind / committed-history mutation

Rewind mutates existing committed `H` itself. It is not:

- Restore;
- deterministic replay;
- ordinary `RECONFIGURE`;
- an emergency-stop rollback;
- compensation by a later Event;
- a backdated `effective_at` value.

The released v0.5 authority specialization remains canonical under the current generic capability family:

```text
Capability<Target,Domain,Operation>

Capability<History,Causality,Rewrite>
```

The latter means an active, in-scope authority to request mutation of committed history under an explicitly admitted causal-rewrite profile. It is not created by Energy, magic power, resource availability, syntax, confidence, evidence, registry metadata, WorldIndex visibility, or sandbox configuration.

Every supporting implementation MUST also require current identity/scope, Lease or equivalent lifetime ownership where the profile requires it, compatibility, stop-fence, accounting, and policy evidence. These obligations may further restrict or deny the operation; the Capability alone does not make a proposed rewrite valid.

The current reference implementation publishes no Rewind ingress, evaluator lowering, runtime executor, or history-rewrite profile. A Rewind request therefore fails closed as `HistoryMutationDenied`. This unsupported status does not erase or redefine the normative v0.5 meaning.

## 5. Causal validation and atomicity

If a future implementation admits committed-history mutation, it MUST validate the proposed `H'=(E',≺')` before authoritative mutation.

At minimum:

- `≺'` remains acyclic and satisfies the admitted causal-order invariants;
- referenced Events and identities remain valid under the rewrite profile;
- the mutation is all-or-none with respect to the authoritative history boundary;
- failure leaves committed `H` unchanged;
- audit evidence records the authority/profile/revision and rejection or commit result without treating that record as authority.

A proposed rewrite that creates a causal cycle fails as `CausalityCycleError`. More Energy or a larger resource budget cannot convert that failure into success.

## 6. Diagnostics

```text
HistoryMutationDenied
```

The request would mutate committed history but no admitted rewrite operation/profile exists, the current implementation does not support it, or policy denies history mutation. No authoritative mutation occurs.

```text
TemporalAuthorityError
```

An admitted temporal/causal operation was recognized, but required temporal/causal authority is missing, inactive, expired, out of scope, or cannot be authoritatively revalidated. Energy/resource availability is irrelevant to this result. No authoritative mutation or direct future observation occurs.

```text
CausalityCycleError
```

The proposed causal relation is cyclic or violates the admitted causal-order contract. Authorization does not waive this validation. No authoritative mutation occurs.

General current-world authority failures may continue to use `AuthorityError`; implementations MUST NOT collapse the three diagnostics above when their distinct conditions are known.

## 7. Prediction and direct future observation

Prediction computes a possible future from current state/model inputs and produces non-authoritative derived evidence.

Direct observation of future state is causal-layer access. It is distinct from ordinary Read authority, prediction, simulation, and replay. The current specification defines no stable public direct-future-observation operation or reference implementation. A request without an explicit admitted causal-access contract fails closed as `TemporalAuthorityError`.

```text
prediction result != observed future truth
ordinary Read != direct future observation authority
```

## 8. Replay boundary

Deterministic replay reconstructs and compares execution in another runtime or simulation instance under compatible recorded inputs and decisions. It does not mutate the original world's committed `H` and cannot be used as a Rewind transport.

```text
DeterministicReplay != Rewind
```

## 9. v1 stable / deferred classification

The semantic distinctions and fail-closed boundary in this document are normative. Actual Rewind execution and direct future observation are **unsupported/deferred** by the current reference implementation and are not members of the v1 stable required conformance surface.

Therefore this reconciliation:

- does not change the four stable conformance classes;
- does not change the 65 required stable cases;
- does not add a Rewind executor, schema ingress, MKI operation, or compatibility profile;
- does not claim executable compatibility with a v0.5 history-rewrite implementation;
- preserves the v0.5 meaning for any future explicitly promoted profile and conformance work.

Promotion requires a separate versioned contract, machine-readable profile/schema, negative and positive conformance evidence, compatibility decision, and explicit stable-scope review. Until then, fail closed.
