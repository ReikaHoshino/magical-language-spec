# Reaction Kinetics and Equilibrium Reference — v0.6.2

**Status:** normative kinetics/equilibrium contract; equations and model examples are informative unless explicitly required.

## Purpose

ReactionRuleに対する速度論、反応経路、触媒、可逆反応、平衡modelのcontractと
definition ownershipを定義する。

## Non-goals

- 具体rate parameterやworld chemistry datasetを固定しない。
- overall stoichiometryからrate lawを暗黙推論しない。
- numerical integrator approximationを物理法則と同一視しない。

## Depends on

- `scope-and-ownership.md`
- `matter.md`
- `quantities.md`
- `registry.md`
- `runtime-time.md`

## Key invariants

```text
Stoichiometry != RateLaw
ReactionRule != ReactionPathway
Kinetics != Thermodynamics
Catalyst != equilibrium shift
Continuous physical time != runtime tick
```

## 1. Scope

本資料は `ReactionRule` に対する速度論、反応経路、触媒、可逆反応、平衡モデルを定義する。

中心原則:

```text
Stoichiometry != RateLaw
ReactionRule != ReactionPathway
Kinetics != Thermodynamics
Catalyst != equilibrium shift
Continuous physical time != runtime tick
```

## 2. ReactionRate types

```text
ReactionExtentRate       : mol s^-1
VolumetricReactionRate   : mol m^-3 s^-1
SurfaceReactionRate      : mol m^-2 s^-1
```

`ReactionExtentRate = dξ/dt`。

volume/surfaceで正規化されたrateはbasisを明示する。

## 3. KineticContext

```text
KineticContext {
    composition
    thermodynamic_state
    volume?
    surface_area?
    structure?
    catalyst_state?
    fields?
    observed_at
    revision_set
}
```

これはsnapshotでありlive stateではない。

## 4. RateLaw

```text
RateLaw<C> {
    input_contract
    parameter_set
    valid_domain
    evaluate(context : C) -> RateEstimate
}
```

`RateLaw` は実験式、elementary mass-action、surface model等を表現できる。

一般のoverall reactionについてreaction orderをstoichiometric coefficientから暗黙推論しない。

## 5. RateEstimate

```text
RateEstimate<R> {
    value
    uncertainty
    basis
    valid_until?
    assumptions
}
```

rate parameterが不足する場合は `Indeterminate` 相当の評価を許す。

## 6. RateConstantModel

```text
RateConstantModel {
    evaluate(context) -> RateConstantEstimate
    valid_domain
}
```

Arrhenius型は一つの標準model候補:

```text
k(T) = A exp(-Ea / (R T))
```

- `A`: pre-exponential factor。
- `Ea`: activation energy。
- `R`: molar gas constant。
- `T`: absolute temperature。

`A` のdimensionはrate law依存。

Arrhenius式をすべての反応へ強制しない。

## 7. ReactionPathway

```text
ReactionPathway<R> {
    id
    overall_rule
    steps : [ElementaryStep]
    kinetic_model
    catalyst_requirements
    valid_domain
    accounting_profile
}
```

同一overall ReactionRuleに複数Pathwayを登録可能。

## 8. ElementaryStep

```text
ElementaryStep {
    id
    stoichiometry
    reversible
    kinetic_model
    intermediates
    accounting_profile
}
```

`elementary=true` 等の明示契約があるstepでのみ、registry-defined mass-action modelを安全に利用できる。

## 9. ReactionNetwork

```text
ReactionNetwork {
    species
    steps
    pathways
}
```

step `j` のextent rateを `dξ_j/dt` とすると:

```text
dn_i/dt = Σ_j ν_i,j (dξ_j/dt)
```

副反応/競合pathwayを同じnetwork上で評価可能にする。

## 10. CatalystModel

```text
CatalystModel {
    id
    requirement
    affected_pathways
    kinetic_modifiers
    state_model
    recovery_condition
    valid_domain
}
```

触媒はkinetic pathwayを変更する。overall ReactionRuleのthermodynamic equilibriumを直接書き換える契約ではない。

ideal catalytic cycleではcatalystはstep内に現れてもoverall net stoichiometryで回収される。

## 11. CatalystState

```text
CatalystState {
    kinetic_activity
    occupied_sites?
    surface_state?
    poison_fraction?
    structure_revision?
}
```

`kinetic_activity` はthermodynamic activityと別概念。

触媒失活/被毒/表面変化をrateへ反映できる。

## 12. Heterogeneous catalyst

surface reactionでは必要に応じて:

```text
surface_area
active_site_density
surface_coverage
```

等をKineticContextへ要求できる。

rate basisは `SurfaceReactionRate` を利用可能。

## 13. Inhibitor

反応速度を低下させるmodelは:

```text
InhibitorModel
```

としてCatalystModelと分離可能。

## 14. Reversible kinetics

```text
ReversibleKineticModel {
    forward
    reverse
}
```

```text
dξ_net/dt = dξ_forward/dt - dξ_reverse/dt
```

forward/reverse parameterは別々に保持できる。

## 15. ThermodynamicActivity

平衡計算は濃度だけに固定せず:

```text
ThermodynamicActivity<SpeciesID>
ActivityModel
```

を使う。

ActivityModelはstandard state / phase / non-ideality等の契約を持つ。

## 16. ReactionQuotient

stoichiometric number `ν_i` とactivity `a_i` から:

```text
Qr = Π_i a_i ^ ν_i
```

を構成する。

## 17. EquilibriumModel

```text
EquilibriumModel<R> {
    activity_model
    standard_state
    evaluate_K(context) -> EquilibriumConstant
    valid_domain
}
```

同じthermodynamic convention下で:

```text
Qr ≈ K
```

を平衡判定の一つの表現とする。

比較にはexplicit toleranceを使う。

## 18. Dynamic equilibrium

thermodynamically consistentなreversible kinetic modelでは平衡近傍で:

```text
forward_rate ≈ reverse_rate
net_rate ≈ 0
```

となる。

これはmicroscopic reaction eventが停止することを意味しない。

## 19. Catalyst and equilibrium

同じoverall reactionとthermodynamic conditionではCatalystModelは `K` を変更しない。

```text
Catalyst changes pathway/rate
Catalyst does not directly change equilibrium constant
```

平衡組成を変えるには、別reservoir、Matter removal、external work、Temperature/Pressure変更等をsystem/accountingへ明示する。

## 20. EquilibriumAssessment

```text
EquilibriumAssessment {
    current_quotient
    equilibrium_constant
    predicted_equilibrium_extent?
    tolerance
    model_uncertainty
}
```

`predicted_equilibrium_extent` はmodel/data不足時にunknownでもよい。

## 21. PreparedReactionPlan

v0.6.2で次を追加する。

```text
PreparedReactionPlan {
    rule
    pathway
    kinetic_model
    equilibrium_model?
    catalyst_requirements
    required_leases
    required_capabilities
    limiting_species
    predicted_rate
    predicted_duration
    equilibrium_assessment?
    energy_accounting
    uncertainty
    assumptions
}
```

このplanはCOMMIT前のdry-run評価データとして利用できる。

## 22. Feasibility status

```text
Feasible
ConditionallyFeasible
Infeasible
Indeterminate
```

情報不足は `Indeterminate` として明示する。

## 23. Energy notes

activation barrierとnet reaction energyを分離する。

```text
ActivationEnergy != EnergyConsumed
```

触媒によるbarrier/pathway変更を、そのまま「必要総EnergyがEaだけ減る」と解釈してはならない。

将来のFeasibility reportでは:

```text
thermodynamic/reaction energy
channel overhead
control overhead
observation/information cost
losses/efficiency
kinetic constraints
```

を分離する。

## 24. Runtime time model

kineticsのnormative意味はcontinuous-time rate:

```text
dξ/dt
```

で定義する。

runtime tick / integration algorithmはv0.6.2では未固定。

したがって:

```text
physical rate != integration step
```

である。

数値実装では将来、integration error / temporal tolerance / deterministic replayを別仕様で定義する。

## 25. Related files

- [`matter.md`](matter.md): Composition / ReactionRule / reaction accounting。
- [`registry.md`](registry.md): model registryとcompatibility。
- [`semantics.md`](semantics.md): PREPARE / COMMIT / runtime。
- [`types.md`](types.md): 型一覧。
- [`../TODO.md`](../TODO.md): Feasibility evaluator / internal tick等の後続作業。
