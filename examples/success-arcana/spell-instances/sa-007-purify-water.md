# SUCCESS-ARCANA-007 — Purify Water

## Status

Design instance for pre-public archive Issue #77. Not yet an executable fixture.

## Intent

Remove a bounded set of identified contaminants from an existing water volume and place them into an accounted waste vessel. The spell does not treat “impurity” as a universal substance and does not silently destroy Matter.

## Reusable semantic pattern

```text
observation-guided selective Matter transfer
```

## Authoritative inputs

- source water `Ref<Matter>` and current composition Measurement;
- destination waste vessel with available capacity;
- explicit contaminant SpeciesID / MaterialClassID selection policy;
- selective Channel/transfer model identity and revision;
- maximum processed volume, contaminant mass, duration, and residual tolerance;
- Read/Transfer Capability, required Leases, Matter/Energy accounting, and SandboxProfile.

## High-level lowering

```text
RESOLVE source water and waste vessel
OBSERVE composition under an admitted measurement model
purely select contaminants covered by the explicit policy
CHANNEL / TRANSFER contaminant MatterPayload to the waste vessel
OBSERVE or validate the post-transfer composition
```

If a contaminant requires chemical transformation rather than separation, that path is a separate admitted RECONFIGURE plan with its own reaction/accounting contract.

## Required invariants

- composition estimate is not silently promoted to exact composition;
- only explicitly selected and sufficiently evidenced contaminants are transferred;
- source + transit + destination Matter accounting remains balanced;
- removed Matter remains in transit or destination and is not deleted;
- waste-vessel capacity and endpoint compatibility are checked before COMMIT;
- water entity identity is preserved only under an explicit IdentityPolicy where relevant;
- “safe to drink” is not inferred unless a domain-owned safety model and evidence establish it.

## Expected successful result

The admitted contaminant payload is removed from the source, appears in the waste vessel, and the source composition satisfies the declared residual bound. History records the transfer and all accounting evidence.

## Mandatory negative neighbors

- ambiguous or unsupported contaminant identity;
- insufficient observation resolution;
- waste vessel lacks capacity or endpoint compatibility;
- missing Matter ledger;
- requested contaminant not present within uncertainty bounds;
- attempt to interpret an omitted contaminant list as “remove everything harmful.”

## Generality check

The same selective-transfer contract should support desalination, filtration, pigment separation, or ore concentration without adding a `Purify Water` branch to core code.
