# SUCCESS-ARCANA-005 — Guiding Light

## Status

Design instance for Issue #77. Not yet an executable fixture.

## Intent

Sustain a small floating or anchored light source at bounded luminous output for a finite duration.

## Reusable semantic pattern

```text
persistent radiative controller
```

The spell uses an admitted emitter/controller contract. It does not create a new `LIGHT` or `RENDER` primitive.

## Authoritative inputs

- existing emitter artifact, prepared radiative medium, or admitted spell-effect subject;
- Energy reservoir;
- target pose or anchor;
- RadiativeEmitterModel and ObserverModel identities/revisions;
- maximum radiant power, duration, temperature, and movement speed;
- Capability, Lease, accounting, and timing evidence.

## High-level lowering

```text
RESOLVE emitter subject / anchor / Energy reservoir
OBSERVE current pose, temperature, and reservoir state
CHANNEL / TRANSFER bounded Energy
CONSTRAIN emitted power and optional bounded pose tracking
ACTIVATE RadiativeEmitterController
DEACTIVATE when duration, Energy, stop request, or safety guard terminates it
```

## Required invariants

- radiant Energy is continuously accounted and never inferred as free;
- luminous output is derived through an explicit ObserverModel when needed;
- controller registration grants no unlimited future authority;
- each later actuation remains inside power, pose, timing, and Capability bounds;
- loss of authority or Energy causes controlled failure/deactivation, not an infinite light source;
- physical emission is distinct from a non-physical display or diagnostic artifact.

## Expected successful result

The emitter becomes an authoritative active effect, produces bounded radiative output for the admitted duration, consumes the accounted Energy budget, and settles cleanly on deactivation.

## Mandatory negative neighbors

- missing Energy accounting;
- emitter temperature would exceed its valid domain;
- revoked actuation Capability;
- timing/jitter requirement unsatisfied;
- requested duration is unbounded;
- attempt to cast radiant flux directly into perceived brightness without an ObserverModel.

## Generality check

The same controller family should support a beacon, reading lamp, signal flare, or dimming enchantment without a `Guiding Light` special case in core code.
