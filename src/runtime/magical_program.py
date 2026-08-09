"""Authoritative public API for the experimental MagicalProgram-0 runtime."""

from .magical_program_contracts import (
    ProgramRuntimeContractRegistry,
    RuntimeContractRegistration,
    default_runtime_contracts,
)
from .magical_program_engine import MagicalProgramRuntime
from .magical_program_model import (
    BoundHostRecord,
    PreparedProgramEffect,
    PreparedProgramPlan,
    ProgramRuntimeError,
    ProgramRuntimeProfile,
    complete_runtime_state,
    complete_runtime_state_hash,
    program_sandbox_world,
    validate_program_execution_trace,
)

__all__ = [
    "BoundHostRecord",
    "MagicalProgramRuntime",
    "PreparedProgramEffect",
    "PreparedProgramPlan",
    "ProgramRuntimeContractRegistry",
    "ProgramRuntimeError",
    "ProgramRuntimeProfile",
    "RuntimeContractRegistration",
    "complete_runtime_state",
    "complete_runtime_state_hash",
    "default_runtime_contracts",
    "program_sandbox_world",
    "validate_program_execution_trace",
]
