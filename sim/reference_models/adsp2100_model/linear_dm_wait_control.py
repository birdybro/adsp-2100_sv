"""Bounded ordinary-fetch/native-DM wait-state, HALT, and BR/BG composition.

The composition owns fetched original Type 2 immediate DM writes, Type 3
direct-DM reads/writes, Type 4 ALU/MAC-plus-DM actions, and Type 12
shifter-plus-DM actions. It retains the raw DM descriptor as separately
labelled structural timing scaffolding. State-3 BR/HALT samples are retained
during an incomplete DM cycle, but grant/HALT-stop service waits for paired
PM/DM completion.
Simultaneous fetched and structural DM descriptors fail closed before either
the PM fetch or the shared native-DM controller accepts the instruction.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .data_bus import (
    DataBusCycleResult,
    DataBusRequest,
    DataBusState,
)
from .data_owner_bus import (
    DataBusOwner,
    DataOwnerBusCycleResult,
    DataOwnerBusState,
    apply_data_owner_bus_cycle,
)
from .bus_control import (
    BusControlCycleResult,
    BusControlMode,
    BusControlState,
    apply_bus_control_cycle,
)
from .halt_control import (
    HaltControlCycleResult,
    HaltControlMode,
    HaltControlState,
    apply_halt_control_cycle,
)
from .linear_core import (
    LinearCoreCycleResult,
    LinearCoreState,
    apply_linear_fetch_client_cycle,
    apply_linear_core_cycle,
)
from .model import ExactWord, UNKNOWN, _UnknownValue
from .phase import LogicalPhase


@dataclass(frozen=True)
class LinearDMWaitControlState:
    """Retained private-PM owner and one paired native-DM transaction."""

    core: LinearCoreState = field(default_factory=LinearCoreState.reset)
    dm_bus: DataBusState = field(default_factory=DataBusState.reset)
    dm_owner: DataBusOwner = DataBusOwner.NONE
    control: BusControlState = field(default_factory=BusControlState)
    halt: HaltControlState = field(default_factory=HaltControlState)

    @classmethod
    def reset(cls) -> "LinearDMWaitControlState":
        return cls()


@dataclass(frozen=True)
class LinearDMWaitControlCycleResult:
    state: LinearDMWaitControlState
    core: LinearCoreCycleResult
    dm_bus: DataBusCycleResult
    dm_owner_bus: DataOwnerBusCycleResult
    control: BusControlCycleResult
    halt: HaltControlCycleResult
    effective_phase_advance: bool = False
    architectural_phase_advance: bool = False
    interrupt_wait_sample: bool = False
    dm_companion_accepted: bool = False
    fetched_dm_accepted: bool = False
    phase_conflict: bool = False
    attachment_conflict: bool = False
    integration_conflict: bool = False
    halt_br_conflict: bool = False
    native_bg_n: bool = True
    native_bus_relinquished: bool = False


def apply_linear_dm_wait_control_cycle(
    state: LinearDMWaitControlState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    br_n: bool = True,
    halt_n: bool = True,
    irq_n: int = 0xF,
    instruction_setup: tuple[ExactWord, ExactWord] | None = None,
    dm_request: DataBusRequest | None = None,
    dm_ack: bool = True,
    dmd_read_data: ExactWord | _UnknownValue = UNKNOWN,
    pmd_read_data: ExactWord | _UnknownValue = UNKNOWN,
) -> LinearDMWaitControlCycleResult:
    """Apply one physical phase to the paired PM-fetch/native-DM boundary.

    A low DMACK sample at physical state 6 freezes the architectural PM owner
    before its state-7 completion. Physical phases continue to circulate.
    Each physical state-7 boundary still samples IRQ pins, but interrupt
    service is impossible until the later qualified PM/DM completion.
    """

    phase = LogicalPhase(phase)
    dm_waiting = bool(
        state.dm_bus.active
        and not state.dm_bus.response_valid
        and state.dm_bus.waiting
    )
    dm_in_progress = bool(
        state.dm_bus.active and not state.dm_bus.response_valid
    )
    halt_br_conflict = bool(
        not reset
        and (
            (not halt_n and not br_n)
            or (
                not halt_n
                and state.control.mode is not BusControlMode.IDLE
            )
            or (
                not br_n
                and state.halt.mode is not HaltControlMode.RUNNING
            )
        )
    )
    effective_halt_n = bool(
        True if reset else (
            halt_n if state.halt.mode is not HaltControlMode.RUNNING
            else (
                halt_n
                or state.control.mode is not BusControlMode.IDLE
                or not br_n
            )
        )
    )
    effective_br_n = bool(
        br_n if reset else (
            br_n if state.control.mode is not BusControlMode.IDLE
            else (
                br_n
                or state.halt.mode is not HaltControlMode.RUNNING
                or not halt_n
            )
        )
    )
    halt = apply_halt_control_cycle(
        state.halt,
        reset=reset,
        phase=phase,
        phase_advance=phase_advance,
        halt_n=effective_halt_n,
        dmack=dm_ack,
        pm_data_cycle=False,
        service_inhibit=dm_waiting,
    )
    effective_phase_advance = halt.effective_phase_advance
    architectural_phase_advance = bool(
        effective_phase_advance and not dm_waiting
    )
    interrupt_wait_sample = bool(
        effective_phase_advance
        and dm_waiting
        and phase is LogicalPhase.STATE_7
    )
    control = apply_bus_control_cycle(
        state.control,
        reset=reset,
        phase=phase,
        phase_advance=effective_phase_advance,
        br_n=effective_br_n,
        service_inhibit=dm_in_progress,
    )
    native_bg_n = br_n if reset else control.bg_n
    native_bus_relinquished = (
        (not br_n) if reset else control.bus_relinquished
    )

    preview = apply_linear_fetch_client_cycle(
        state.core,
        reset=reset,
        phase=phase,
        phase_advance=architectural_phase_advance,
        interrupt_sample_advance=interrupt_wait_sample,
        instruction_issue_inhibit=bool(
            control.instruction_issue_inhibit
            or halt.instruction_issue_inhibit
        ),
        bus_relinquished=native_bus_relinquished,
        irq_n=irq_n,
        instruction_setup=instruction_setup,
        pmd_read_data=pmd_read_data,
        dmd_read_data=dmd_read_data,
        fetched_type2_enabled=True,
        fetched_type3_enabled=True,
        fetched_type4_enabled=True,
        fetched_type12_enabled=True,
    )
    preflight_collision = bool(
        preview.fetched_dm_request_candidate is not None
        and dm_request is not None
        and not control.instruction_issue_inhibit
        and not halt.instruction_issue_inhibit
    )
    core = apply_linear_core_cycle(
        state.core,
        reset=reset,
        phase=phase,
        phase_advance=architectural_phase_advance,
        interrupt_sample_advance=interrupt_wait_sample,
        instruction_issue_inhibit=bool(
            control.instruction_issue_inhibit or preflight_collision
            or halt.instruction_issue_inhibit
        ),
        bus_relinquished=native_bus_relinquished,
        irq_n=irq_n,
        instruction_setup=instruction_setup,
        pmd_read_data=pmd_read_data,
        dmd_read_data=dmd_read_data,
        fetched_type2_enabled=True,
        fetched_type3_enabled=True,
        fetched_type4_enabled=True,
        fetched_type12_enabled=True,
    )
    ordinary_pm_issue = bool(
        core.instruction_issue and not state.core.interrupt_vectoring
    )
    fetched_request = core.fetched_dm_request
    fetched_owner_request = (
        preview.fetched_dm_request_candidate
        if preflight_collision
        else fetched_request
    )
    companion_owner_request = (
        dm_request
        if (
            preflight_collision
            or (
                ordinary_pm_issue
                and dm_request is not None
                and fetched_request is None
            )
        )
        else None
    )
    expected_dm_accept = bool(
        ordinary_pm_issue
        and ((fetched_request is not None) != (dm_request is not None))
    )
    dm_owner_bus = apply_data_owner_bus_cycle(
        DataOwnerBusState(bus=state.dm_bus, owner=state.dm_owner),
        reset=reset,
        phase=phase,
        phase_advance=effective_phase_advance,
        fetched_request=fetched_owner_request,
        companion_request=companion_owner_request,
        dm_ack=dm_ack,
        dmd_read_data=dmd_read_data,
        bus_relinquished=native_bus_relinquished,
    )
    dm_bus = dm_owner_bus.bus

    controls_present = dm_request is not None
    phase_conflict = bool(
        not reset
        and controls_present
        and not (
            effective_phase_advance
            and phase is LogicalPhase.STATE_8
            and not dm_waiting
        )
    )
    pairing_conflict = bool(
        not reset
        and controls_present
        and not phase_conflict
        and (not ordinary_pm_issue or preflight_collision)
    )
    completion_conflict = bool(
        not reset
        and state.dm_bus.active
        and not state.dm_bus.response_valid
        and (dm_bus.completion_event != core.bus.completion_event)
    )
    attachment_conflict = bool(
        pairing_conflict
        or completion_conflict
        or dm_owner_bus.request_conflict
        or dm_owner_bus.request_out_of_phase
        or (dm_bus.request_accepted != expected_dm_accept)
    )
    bus_protocol_active = bool(
        state.control.mode.value != 0 or control.request_recognized
    )
    bus_event_conflict = bool(
        not reset
        and bus_protocol_active
        and (
            core.trap_event
            or core.interrupt_recognition_event
            or core.interrupt_entry_event
            or core.interrupt_vector_issue_event
            or core.interrupt_vector_fetch_event
            or state.core.interrupt_vectoring
        )
    )
    halt_owner_conflict = bool(
        halt.halt_recognized
        and not (
            state.core.bus.active
            and not native_bus_relinquished
            and not reset
        )
    )
    halt_trap_conflict = bool(
        core.trap_event
        and (
            state.halt.mode is not HaltControlMode.RUNNING
            or halt.halt_stop_event
        )
    )

    return LinearDMWaitControlCycleResult(
        state=LinearDMWaitControlState(
            core=core.state,
            dm_bus=dm_bus.state,
            dm_owner=dm_owner_bus.state.owner,
            control=control.state,
            halt=halt.state,
        ),
        core=core,
        dm_bus=dm_bus,
        dm_owner_bus=dm_owner_bus,
        control=control,
        halt=halt,
        effective_phase_advance=effective_phase_advance,
        architectural_phase_advance=architectural_phase_advance,
        interrupt_wait_sample=interrupt_wait_sample,
        dm_companion_accepted=dm_owner_bus.companion_accepted,
        phase_conflict=phase_conflict,
        attachment_conflict=attachment_conflict,
        integration_conflict=bool(
            phase_conflict
            or attachment_conflict
            or core.phase_conflict
            or core.integration_conflict
            or core.internal_conflict
            or bus_event_conflict
            or halt_br_conflict
            or halt.phase_conflict
            or halt_owner_conflict
            or halt_trap_conflict
        ),
        halt_br_conflict=halt_br_conflict,
        native_bg_n=native_bg_n,
        native_bus_relinquished=native_bus_relinquished,
        fetched_dm_accepted=dm_owner_bus.fetched_accepted,
    )
