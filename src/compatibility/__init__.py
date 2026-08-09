"""Reference compatibility admission gate for the v0.10 conformance path.

Domain-specific compatibility decisions remain owned by their declared profiles.
This package only aggregates already-produced decision envelopes for a consumer
that requires a set of domains.
"""

from .admission import (
    AdmissionStatus,
    CompatibilityAdmissionError,
    CompatibilityAdmissionResult,
    admit_compatibility_decisions,
)
from .evolution import (
    CompatibilityEvolutionError,
    MigrationExecutionResult,
    execute_migration,
    select_migration,
    validate_evolution_policy,
    validate_release_change,
)

__all__ = [
    "AdmissionStatus",
    "CompatibilityAdmissionError",
    "CompatibilityAdmissionResult",
    "admit_compatibility_decisions",
    "CompatibilityEvolutionError",
    "MigrationExecutionResult",
    "execute_migration",
    "select_migration",
    "validate_evolution_policy",
    "validate_release_change",
]
