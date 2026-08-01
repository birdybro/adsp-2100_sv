"""Type 2 immediate DM write attached to the original native DM phases.

The architectural Type 2 model and the pin-phase DM model remain independently
testable.  This composition accepts controls only on the enabled state-8 to
state-1 boundary and returns the physical state-7 completion event to the
instruction slice as its logical acknowledgement.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .data_bus import (
    DataBusCycleResult,
    DataBusRequest,
    DataBusState,
    apply_data_bus_cycle,
)
from .dm_write_immediate_slice import (
    DMWriteImmediateCycleResult,
    DMWriteImmediateState,
    apply_dm_write_immediate_cycle,
)
from .model import ExactWord, UNKNOWN
from .modify_address import DAGRegisterSetup
from .phase import LogicalPhase


@dataclass(frozen=True)
class DMWriteImmediateNativeState:
    core: DMWriteImmediateState = field(
        default_factory=DMWriteImmediateState.reset
    )
    bus: DataBusState = field(default_factory=DataBusState.reset)

    @classmethod
    def reset(cls) -> "DMWriteImmediateNativeState":
        return cls()


@dataclass(frozen=True)
class DMWriteImmediateNativeCycleResult:
    state: DMWriteImmediateNativeState
    core: DMWriteImmediateCycleResult
    bus: DataBusCycleResult
    issue_boundary: bool = False
    phase_conflict: bool = False
    attachment_conflict: bool = False
    integration_conflict: bool = False


def apply_dm_write_immediate_native_cycle(
    state: DMWriteImmediateNativeState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    bus_relinquished: bool = False,
    execute: bool = False,
    opcode: int = 0,
    dm_ack: bool = True,
    setup_mstat: ExactWord | None = None,
    setup_dag: DAGRegisterSetup | None = None,
) -> DMWriteImmediateNativeCycleResult:
    """Apply one FPGA clock of the bounded Type 2/native-DM attachment."""

    phase = LogicalPhase(phase)
    issue_boundary = bool(
        not reset
        and not bus_relinquished
        and phase_advance
        and phase == LogicalPhase.STATE_8
    )
    controls_present = bool(
        execute or setup_mstat is not None or setup_dag is not None
    )
    phase_conflict = not reset and controls_present and not issue_boundary

    # The current bus descriptor determines completion independently of a new
    # state-8 request.  Previewing this pure transition avoids duplicating the
    # DMACK/state-seven rules inside the architectural composition.
    bus_preview = apply_data_bus_cycle(
        state.bus,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        dm_ack=dm_ack,
        bus_relinquished=bus_relinquished,
    )
    core_result = apply_dm_write_immediate_cycle(
        state.core,
        reset=reset,
        execute=execute and issue_boundary,
        opcode=opcode,
        dm_ack=bus_preview.completion_event,
        setup_mstat=setup_mstat if issue_boundary else None,
        setup_dag=setup_dag if issue_boundary else None,
    )

    request: DataBusRequest | None = None
    if core_result.dm_select:
        request = DataBusRequest(
            address=(
                ExactWord(14, core_result.dm_address)
                if core_result.dm_address_known
                else UNKNOWN
            ),
            write=core_result.dm_write,
            write_data=(
                ExactWord(16, core_result.dm_write_data)
                if core_result.dm_write_data_known
                else UNKNOWN
            ),
        )
    bus_result = apply_data_bus_cycle(
        state.bus,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        request=request,
        dm_ack=dm_ack,
        bus_relinquished=bus_relinquished,
    )
    attachment_conflict = bool(
        core_result.accepted != bus_result.request_accepted
        or (
            core_result.accepted
            and not (issue_boundary and core_result.dm_select)
        )
        or core_result.instruction_complete
        != (bus_result.completion_event and core_result.dm_select)
    )
    return DMWriteImmediateNativeCycleResult(
        state=DMWriteImmediateNativeState(
            core=core_result.state,
            bus=bus_result.state,
        ),
        core=core_result,
        bus=bus_result,
        issue_boundary=issue_boundary,
        phase_conflict=phase_conflict,
        attachment_conflict=attachment_conflict,
        integration_conflict=(
            phase_conflict
            or attachment_conflict
            or core_result.integration_conflict
        ),
    )
