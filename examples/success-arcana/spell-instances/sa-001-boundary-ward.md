# SUCCESS-ARCANA-001 — Sevenfold Boundary Reflection Ward

## Status

Design instance for pre-public archive Issue #77. Not yet an executable fixture.

## Intent

Maintain a bounded Region boundary that admits authorized entrants and applies a finite, model-governed reflection impulse to unauthorized crossings.

## Reusable semantic pattern

```text
persistent bounded boundary controller
```

The ward name and `SA-001` identity are fixture metadata only. Runtime dispatch MUST select a versioned boundary-controller contract rather than this spell ID.

## Authoritative inputs

- protected Region and current revision;
- reaction Anchor or accounted momentum sink/source;
- admission policy and EntryCapability evidence;
- boundary/contact model identity and revision;
- coefficient of restitution;
- maximum target mass, incident momentum, impulse, and Energy;
- sample/event timing bounds;
- controller Capability, Lease, accounting, overload, and termination policy.

## High-level lowering

```text
RESOLVE protected Region, Anchor, and crossing subject
QUERY admission evidence
OBSERVE position and momentum required by the contact model
CONSTRAIN bounded boundary-response behavior
ACTIVATE BoundaryReflectionController
for each admitted actuation:
  TRANSITION subject momentum
  TRANSITION equal/opposite Anchor reaction
  account dissipated Energy
DEACTIVATE on expiry, revocation, stop, or safety failure
```

The implementation must not teleport the subject merely to place it outside the Region. Reflection is represented through the admitted contact/impulse model.

## Required invariants

- authorized entrants are unaffected;
- target selection or Region ownership does not fabricate authority;
- every later actuation revalidates Capability, Lease, target state, timing, and resource bounds;
- target and reaction momentum changes are jointly accounted;
- overload never produces unbounded impulse;
- controller registration grants no unlimited future authority;
- deactivation does not erase committed crossing or reflection history.

## Expected successful result

An authorized subject crosses unchanged. An unauthorized in-domain subject receives the finite reflected momentum predicted by the admitted model, while the Anchor reaction and dissipated Energy are recorded atomically. Replay reproduces the same events.

## Mandatory negative neighbors

- revoked or expired controller Capability;
- missing reaction Anchor/accounting evidence;
- target mass or momentum outside the model domain;
- stale Region or target revision;
- unsatisfied timing bound;
- request for unlimited duration or impulse.

## Generality check

The same contract family should support a safety rail, pressure boundary, collision buffer, or access-controlled membrane without adding a spell-specific core branch.
