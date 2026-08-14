"""Deterministic sandbox runtime package.

The experimental MagicalProgram API is intentionally imported from
`src.runtime.magical_program` so evaluator/artifact imports do not create a
package-root cycle.
"""

from .engine import ReferenceRuntimeEngine, SandboxProfile
from .integrator import SyntheticReferenceIntegrator
from .execution_admission import (
    AdmissionWorld,
    ExecutionAdmissionError,
    ExecutionAdmissionRuntime,
)
from .sandbox import (
    PreparedPlan,
    RuntimeExecutionError,
    SandboxRuntime,
    SandboxWorld,
    canonical_sandbox_world,
)

__all__ = [
    "AdmissionWorld",
    "ExecutionAdmissionError",
    "ExecutionAdmissionRuntime",
    "PreparedPlan",
    "ReferenceRuntimeEngine",
    "RuntimeExecutionError",
    "SandboxProfile",
    "SandboxRuntime",
    "SandboxWorld",
    "SyntheticReferenceIntegrator",
    "canonical_sandbox_world",
]
