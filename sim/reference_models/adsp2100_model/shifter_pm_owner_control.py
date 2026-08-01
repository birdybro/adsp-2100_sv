"""Type 13 architectural client attached to shared PM ownership and BR/BG.

The Type 13/cache model retains its own data or recovery descriptor.  This
composition presents that retained descriptor only at an enabled state-8
boundary, routes only the Type 13 owner's completion back to the client, and
uses completed ordinary fetches to fill the same instruction cache.  Raw
ordinary-fetch and Type 5 descriptors remain external bounded requesters.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .model import ExactWord, UNKNOWN
from .modify_address import DAGRegisterSetup
from .phase import LogicalPhase
from .program_bus import ProgramBusRequest
from .program_owner_bus import ProgramBusOwner
from .program_owner_bus_control import (
    ProgramOwnerBusControlCycleResult,
    ProgramOwnerBusControlState,
    apply_program_owner_bus_control_cycle,
)
from .registers import DREGWrite
from .shifter_pm_cache import (
    ShifterPMCacheCycleResult,
    ShifterPMCacheState,
    apply_shifter_pm_cache_cycle,
)


@dataclass(frozen=True)
class ShifterPMOwnerControlState:
    core: ShifterPMCacheState = field(default_factory=ShifterPMCacheState.reset)
    interface: ProgramOwnerBusControlState = field(
        default_factory=ProgramOwnerBusControlState.reset
    )

    @classmethod
    def reset(cls) -> "ShifterPMOwnerControlState":
        return cls()


@dataclass(frozen=True)
class ShifterPMOwnerControlCycleResult:
    state: ShifterPMOwnerControlState
    core: ShifterPMCacheCycleResult
    interface: ProgramOwnerBusControlCycleResult
    issue_boundary: bool = False
    phase_conflict: bool = False
    fetch_cache_fill: bool = False
    type13_request_presented: bool = False
    type13_request_accepted: bool = False
    type13_retry_pending: bool = False
    attachment_conflict: bool = False
    integration_conflict: bool = False


def apply_shifter_pm_owner_control_cycle(
    state: ShifterPMOwnerControlState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    br_n: bool = True,
    fetch_request: ProgramBusRequest | None = None,
    type5_request: ProgramBusRequest | None = None,
    execute: bool = False,
    opcode: int = 0,
    pmd_read_data: ExactWord | object = UNKNOWN,
    next_fetch_address: ExactWord | object = UNKNOWN,
    setup_astat: ExactWord | None = None,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
    setup_sb: ExactWord | None = None,
    setup_dag: DAGRegisterSetup | None = None,
    setup_px: ExactWord | None = None,
) -> ShifterPMOwnerControlCycleResult:
    """Apply one bounded Type 13/shared-PM/BR-BG clock."""

    phase = LogicalPhase(phase)
    controls_present = bool(
        execute
        or setup_astat is not None
        or setup_mstat is not None
        or setup_dreg is not None
        or setup_sb is not None
        or setup_dag is not None
        or setup_px is not None
    )

    # Current-owner completion and BR/BG mode depend only on retained state,
    # not on a descriptor offered at this boundary.  A side-effect-free
    # preview therefore closes the otherwise combinational client/bus loop.
    preview = apply_program_owner_bus_control_cycle(
        state.interface,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        br_n=br_n,
        pmd_read_data=pmd_read_data,
    )
    issue_boundary = bool(
        not reset
        and not preview.control.instruction_issue_inhibit
        and not preview.native_bus_relinquished
        and phase == LogicalPhase.STATE_8
        and phase_advance
    )
    phase_conflict = bool(
        not reset and controls_present and not issue_boundary
    )

    retained_bus = state.interface.owner_bus.bus
    fetch_cache_fill = bool(
        preview.owner_bus.fetch_completion and not retained_bus.write
    )
    fetch_fill_address = (
        retained_bus.address
        if fetch_cache_fill and isinstance(retained_bus.address, ExactWord)
        else UNKNOWN
    )

    core = apply_shifter_pm_cache_cycle(
        state.core,
        reset=reset,
        execute=execute and issue_boundary,
        opcode=opcode,
        pm_read_data=pmd_read_data,
        next_fetch_address=next_fetch_address,
        force_instruction_fetch=False,
        pm_cycle_complete=preview.owner_bus.type13_completion,
        external_fetch_fill=fetch_cache_fill,
        external_fetch_address=fetch_fill_address,
        external_fetch_instruction=pmd_read_data,
        setup_astat=setup_astat if issue_boundary else None,
        setup_mstat=setup_mstat if issue_boundary else None,
        setup_dreg=setup_dreg if issue_boundary else None,
        setup_sb=setup_sb if issue_boundary else None,
        setup_dag=setup_dag if issue_boundary else None,
        setup_px=setup_px if issue_boundary else None,
    )

    type13_request: ProgramBusRequest | None = None
    if issue_boundary and core.core.pm_select:
        type13_request = ProgramBusRequest(
            address=(
                ExactWord(14, core.core.pm_address)
                if core.core.pm_address_known
                else UNKNOWN
            ),
            data_access=core.core.pm_data_access,
            write=core.core.pm_write,
            write_data=(
                ExactWord(24, core.core.pm_write_data)
                if core.core.pm_write_data_known
                else UNKNOWN
            ),
        )

    interface = apply_program_owner_bus_control_cycle(
        state.interface,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        br_n=br_n,
        fetch_request=fetch_request,
        type5_request=type5_request,
        type13_request=type13_request,
        pmd_read_data=pmd_read_data,
    )
    type13_presented = type13_request is not None
    type13_accepted = interface.owner_bus.type13_accepted
    type13_retry = bool(type13_presented and not type13_accepted)
    attachment_conflict = bool(
        interface.owner_bus.completion_owner
        != preview.owner_bus.completion_owner
        or type13_accepted
        and interface.owner_bus.accepted_owner
        != ProgramBusOwner.TYPE13_PM_DATA
        or preview.owner_bus.type13_completion
        and not (
            core.core.data_action_complete
            or core.core.instruction_complete
        )
    )

    return ShifterPMOwnerControlCycleResult(
        state=ShifterPMOwnerControlState(core.state, interface.state),
        core=core,
        interface=interface,
        issue_boundary=issue_boundary,
        phase_conflict=phase_conflict,
        fetch_cache_fill=fetch_cache_fill,
        type13_request_presented=type13_presented,
        type13_request_accepted=type13_accepted,
        type13_retry_pending=type13_retry,
        attachment_conflict=attachment_conflict,
        integration_conflict=bool(
            phase_conflict
            or attachment_conflict
            or core.integration_conflict
            or interface.owner_bus.request_conflict
            or interface.owner_bus.request_out_of_phase
        ),
    )
