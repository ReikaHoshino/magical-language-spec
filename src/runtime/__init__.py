"""Deterministic sandbox runtime package.

The experimental MagicalProgram API is intentionally imported from
`src.runtime.magical_program` so evaluator/artifact imports do not create a
package-root cycle.
"""

from .engine import ReferenceRuntimeEngine, SandboxProfile
from .integrator import SyntheticReferenceIntegrator
from .sandbox import (
    PreparedPlan,
    RuntimeExecutionError,
    SandboxRuntime,
    SandboxWorld,
    canonical_sandbox_world,
)

__all__ = [
    "PreparedPlan",
    "ReferenceRuntimeEngine",
    "RuntimeExecutionError",
    "SandboxProfile",
    "SandboxRuntime",
    "SandboxWorld",
    "SyntheticReferenceIntegrator",
    "canonical_sandbox_world",
]
