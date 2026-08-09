"""Single authoritative MagicalProgram-0 runtime engine."""
from __future__ import annotations

from typing import Any, Mapping

from src.evaluator.magical_program import MagicalProgramEvaluator
from .sandbox import SandboxWorld
from .magical_program_commit import commit_program, execute_program, replay_program
from .magical_program_contracts import (
    ProgramRuntimeContractRegistry,
    default_runtime_contracts,
)
from .magical_program_model import (
    PreparedProgramPlan,
    ProgramRuntimeProfile,
    complete_runtime_state,
)
from .magical_program_prepare import prepare_program, revalidate_program

_JSON = dict[str, Any]


class MagicalProgramRuntime:
    """One evaluator -> PREPARE -> COMMIT/abort -> replay implementation.

    Contract-specific executable behavior belongs to
    `ProgramRuntimeContractRegistry`; this core never branches on a contract ID.
    """

    def __init__(
        self,
        *,
        evaluator: MagicalProgramEvaluator | None = None,
        contracts: ProgramRuntimeContractRegistry | None = None,
        profile: ProgramRuntimeProfile = ProgramRuntimeProfile(),
    ) -> None:
        self.evaluator = evaluator or MagicalProgramEvaluator()
        self.contracts = contracts or default_runtime_contracts()
        self.profile = profile
        self._prepare_sequence = 0
        self._consumed_plan_ids: set[str] = set()

    def evaluate(
        self, program: Mapping[str, Any], *, world: SandboxWorld
    ) -> _JSON:
        return self.evaluator.evaluate_program(
            program,
            world_state=complete_runtime_state(world),
            history=world.history,
        )

    def prepare(
        self,
        program: Mapping[str, Any],
        report: Mapping[str, Any],
        world: SandboxWorld,
    ) -> PreparedProgramPlan:
        return prepare_program(self, program, report, world)

    def revalidate(
        self, prepared: PreparedProgramPlan, world: SandboxWorld
    ) -> _JSON:
        return revalidate_program(self, prepared, world)

    def commit(
        self, prepared: PreparedProgramPlan, world: SandboxWorld
    ) -> _JSON:
        return commit_program(self, prepared, world)

    def execute(
        self, program: Mapping[str, Any], world: SandboxWorld
    ) -> _JSON:
        return execute_program(self, program, world)

    def replay(
        self,
        program: Mapping[str, Any],
        initial_world: SandboxWorld,
        expected: Mapping[str, Any],
    ) -> _JSON:
        return replay_program(self, program, initial_world, expected)
