# SUCCESS-ARCANA-006 — Levitation

## Status

Design instance for Issue #77. Not yet an executable fixture.

## Intent

Hold or move one existing object against gravity using a bounded force controller. The spell does not remove gravity and does not rewrite the object's mass.

## Reusable semantic pattern

```text
bounded force / pose controller
```

## Authoritative inputs

- target `Ref<Object>` and current state revision;
- object mass and pose Measurement;
- admitted force/actuation model;
- reaction anchor or other accounted momentum sink/source;
- maximum force, height, velocity, acceleration, duration, and working Region;
- Write Lease, actuation Capability, Energy/Momentum accounting, and ControllerTiming.

## High-level lowering

```text
RESOLVE target object and reaction anchor
OBSERVE mass, pose, velocity, and relevant environment state
CONSTRAIN target pose / vertical velocity under the admitted force model
ACTIVATE bounded LevitationController
perform later guarded actuation through ordinary transitions
DEACTIVATE and settle when the terminal condition is met
```

## Required invariants

- gravity remains active in the world model;
- controller force and acceleration remain bounded;
- momentum/reaction and Energy are accounted according to the admitted model;
- target selection does not grant authority;
- each actuation revalidates target revision, Capability, Lease, resources, and timing;
- an object above the valid mass limit fails rather than receiving infinite force;
- deactivation does not imply restoration to the original position.

## Expected successful result

The selected object rises to or remains at the requested bounded pose, with controller state represented as an authoritative active-effect projection. Energy and reaction accounting remain valid and deterministic replay reproduces the result.

## Mandatory negative neighbors

- target mass exceeds controller domain;
- missing reaction/accounting evidence;
- revoked Write Lease or actuation Capability;
- stale target state revision;
- requested height or duration exceeds profile bounds;
- timing requirement cannot be satisfied.

## Generality check

The same bounded force-controller contract should support slow fall, stabilized carrying, or fixed-position suspension without adding a `Levitation` branch to core code.
