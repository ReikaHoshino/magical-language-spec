# SUCCESS-ARCANA-002 — Crimson Thread Substitution

## Status

Design instance for pre-public archive Issue #77. Not yet an executable fixture.

## Intent

Treat a bounded reversible injury by decomposing it into transferable Energy/Matter components and non-conserved structural descriptors, then stabilizing and repairing the patient without treating “damage” as a conserved substance.

## Reusable semantic pattern

```text
staged observation-guided reconfiguration
```

Hair or thread acts only as correspondence/resolver evidence. It is not patient identity, authority, or a permanent bidirectional causal link.

## Authoritative inputs

- patient `Ref<Organism>` and current state revision;
- correspondence evidence with explicit uncertainty;
- medical/consent Capability and required Leases;
- admitted observation, tissue, structural, and biochemical models;
- Energy sink, waste reservoir, donor Matter, and their capacities;
- `IdentityPolicy<Organism>`;
- treatment bounds, stage ordering, accounting, and SandboxProfile.

## Treatment decomposition

```text
TreatmentDecomposition {
  excess_thermal_energy
  removable_fluid_or_matter
  chemical_state_deviation
  reversible_structural_deviation
  irreversible_information_loss
  uncertainty
}
```

## High-level lowering

```text
RESOLVE patient and treatment resources
OBSERVE injury state under admitted models

Stabilize:
  CHANNEL / TRANSFER bounded Energy and removable Matter to sinks

Repair:
  RECONFIGURE tissue using donor Matter and admitted tissue rules
  preserve patient identity under IdentityPolicy<Organism>

Manifest:
  RECONFIGURE a proxy from a provenance-bearing DamageDescriptor
```

Each stage has its own guarded commit boundary. A later failure does not relabel earlier successful stabilization as rollback.

## Required invariants

- injury is not registered as a conserved TransferKind;
- correspondence evidence does not create identity, Capability, Lease, or reverse causality;
- Energy, Matter, Momentum, and other applicable ledgers remain balanced;
- irreversible information loss is not silently reconstructed;
- patient identity is preserved only under the admitted IdentityPolicy;
- proxy manifestation is a separate reconfiguration from patient treatment;
- destroying the proxy after completion has no implicit effect on the patient.

## Expected successful result

A small, explicitly bounded injury is stabilized and repaired using admitted resources and models. The patient retains identity, sinks and donor stores reflect exact accounting, and the proxy records a descriptor-derived manifestation without a reverse link.

## Mandatory negative neighbors

- ambiguous correspondence evidence;
- missing consent or medical authority;
- insufficient sink capacity or donor Matter;
- unsupported tissue model;
- identity-critical or irreversible information loss;
- attempt to transfer an abstract “wound” payload;
- attempt to establish a permanent reverse proxy relation.

## Generality check

The same staged reconfiguration pattern should support cooling a burn, closing a simple cut, replacing damaged material in an artifact, or controlled biological grafting without a `Crimson Thread` core branch.
