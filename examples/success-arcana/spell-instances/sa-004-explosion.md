# SUCCESS-ARCANA-004 — Explosion

## Status

Executable experimental fixture for pre-public archive Issue #77 and pre-public archive Issue #80. It remains outside the stable required surface.

## Intent

Release a prepared, finite Energy budget into a bounded target region to produce the light-novel-standard high-output explosion without creating Energy, deleting the surrounding medium, or granting unbounded destructive authority.

## Reusable semantic pattern

```text
bounded one-shot dynamics
```

The spell instance MUST use a versioned blast/dynamics contract. `Explosion` is an instance name, not a dispatcher key or a new MKI primitive.

## Authoritative inputs

- caster / spell-instance identity;
- target point or bounded Region;
- prepared Energy reservoir;
- admitted surrounding-medium model;
- blast DynamicsModel identity and revision;
- exact Energy budget;
- maximum radius, overpressure, duration, and affected mass;
- Capability and any required Lease for the selected Region/effect class;
- accounting and SandboxProfile evidence.

## High-level lowering

```text
RESOLVE target Region and Energy reservoir
OBSERVE current medium state required by the admitted model
CHANNEL / TRANSFER the exact admitted Energy payload
RECONFIGURE the local thermodynamic state or
ACTIVATE a bounded blast DynamicsProcess
DEACTIVATE / settle when the model-defined duration ends
```

The initial atomic group accounts for the reservoir debit and the activation of the blast effect. Later pressure/thermal transitions are committed under the admitted DynamicsModel and current guards.

## Required invariants

- total released Energy equals the debited and accounted Energy budget;
- radius and duration remain finite and profile-bounded;
- scheduler tick width does not redefine physical propagation;
- affected entities are selected by bounded Region/effect scope, not by name or narrative hostility;
- ordinary spell authority does not mutate physical laws;
- failure before initial COMMIT leaves WorldState and History unchanged;
- overload or model-domain failure does not silently increase power.

## Expected successful result

A committed Event records the exact Energy release and blast-effect activation. The reservoir is debited, the bounded region evolves under the admitted model, and replay reproduces the same committed result under the same world/profile evidence.

## Mandatory negative neighbors

- insufficient Energy reservoir;
- target Region outside Capability scope;
- missing or incompatible blast model;
- radius/overpressure above SandboxProfile limit;
- stale target or medium revision;
- attempt to infer unlimited area from an omitted radius.

## Generality check

The same bounded one-shot dynamics contract should support a pressure burst, flash discharge, or controlled demolition instance without adding an `Explosion` branch to evaluator/runtime core.
