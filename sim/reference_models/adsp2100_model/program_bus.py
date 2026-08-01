"""Independent logical-pin model of the original ADSP-2100 PM interface.

This boundary models the source-defined state edges, pin polarities, read
sampling, write-data drive window, back-to-back select continuity, and output
masking while a separate arbiter relinquishes the bus.  It intentionally does
not model analog delays or decide which architectural requester owns PM.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .model import ExactWord, UNKNOWN
from .phase import LogicalPhase


PROGRAM_ADDRESS_WIDTH = 14
PROGRAM_WORD_WIDTH = 24


def _require_exact(value: ExactWord | object, width: int, name: str) -> None:
    if value is not UNKNOWN and (
        not isinstance(value, ExactWord) or value.width != width
    ):
        raise ValueError(f"{name} must be UNKNOWN or exactly {width} bits")


@dataclass(frozen=True)
class ProgramBusRequest:
    """One instruction fetch, PM-data read, or PM-data write descriptor."""

    address: ExactWord | object = UNKNOWN
    data_access: bool = False
    write: bool = False
    write_data: ExactWord | object = UNKNOWN

    def __post_init__(self) -> None:
        _require_exact(self.address, PROGRAM_ADDRESS_WIDTH, "PM address")
        _require_exact(self.write_data, PROGRAM_WORD_WIDTH, "PM write data")

    @classmethod
    def fetch(cls, address: int) -> "ProgramBusRequest":
        return cls(address=ExactWord(PROGRAM_ADDRESS_WIDTH, address))

    @classmethod
    def data_read(cls, address: int) -> "ProgramBusRequest":
        return cls(
            address=ExactWord(PROGRAM_ADDRESS_WIDTH, address),
            data_access=True,
        )

    @classmethod
    def data_write(cls, address: int, data: int) -> "ProgramBusRequest":
        return cls(
            address=ExactWord(PROGRAM_ADDRESS_WIDTH, address),
            data_access=True,
            write=True,
            write_data=ExactWord(PROGRAM_WORD_WIDTH, data),
        )


@dataclass(frozen=True)
class ProgramBusState:
    active: bool = False
    address: ExactWord | object = UNKNOWN
    data_access: bool = False
    write: bool = False
    write_data: ExactWord | object = UNKNOWN
    response_valid: bool = False
    response_write: bool = False
    read_data: ExactWord | object = UNKNOWN

    def __post_init__(self) -> None:
        _require_exact(self.address, PROGRAM_ADDRESS_WIDTH, "stored PM address")
        _require_exact(
            self.write_data, PROGRAM_WORD_WIDTH, "stored PM write data"
        )
        _require_exact(self.read_data, PROGRAM_WORD_WIDTH, "sampled PM read data")

    @classmethod
    def reset(cls) -> "ProgramBusState":
        return cls()


@dataclass(frozen=True)
class ProgramBusCycleResult:
    state: ProgramBusState
    request_ready: bool = False
    request_accepted: bool = False
    completion_event: bool = False
    read_sample_event: bool = False
    bus_relinquished: bool = False
    address_output_enable: bool = False
    control_output_enable: bool = False
    data_output_enable: bool = False
    pms_n: bool = True
    pmrd_n: bool = True
    pmwr_n: bool = True
    address: int = 0
    address_known: bool = False
    pmda: bool = False
    write_data: int = 0
    write_data_known: bool = False


def apply_program_bus_cycle(
    state: ProgramBusState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    request: ProgramBusRequest | None = None,
    pmd_read_data: ExactWord | object = UNKNOWN,
    bus_relinquished: bool = False,
) -> ProgramBusCycleResult:
    """Apply one FPGA clock at the bounded native PM phase interface.

    The implementation API samples requests on the enabled state-8-to-state-1
    edge because that is the data-book edge from which PMA, PMDA, and PMS
    become valid.  This is not a claim about an undocumented internal device
    latch.  The caller presents the current logical phase, as it does for
    other bounded phase-aware models.
    """

    phase = LogicalPhase(phase)
    _require_exact(pmd_read_data, PROGRAM_WORD_WIDTH, "PM read data")

    strobe_active = phase in (
        LogicalPhase.STATE_4,
        LogicalPhase.STATE_5,
        LogicalPhase.STATE_6,
        LogicalPhase.STATE_7,
    )
    write_drive_active = phase in (
        LogicalPhase.STATE_5,
        LogicalPhase.STATE_6,
        LogicalPhase.STATE_7,
        LogicalPhase.STATE_8,
    )
    interface_active = state.active and not bus_relinquished and not reset
    request_ready = bool(
        not reset
        and not bus_relinquished
        and phase == LogicalPhase.STATE_8
        and phase_advance
    )
    request_accepted = request_ready and request is not None
    completion_event = bool(
        interface_active
        and phase == LogicalPhase.STATE_7
        and phase_advance
    )
    read_sample_event = completion_event and not state.write

    address_known = isinstance(state.address, ExactWord)
    write_data_known = isinstance(state.write_data, ExactWord)
    result = ProgramBusCycleResult(
        state=state,
        request_ready=request_ready,
        request_accepted=request_accepted,
        completion_event=completion_event,
        read_sample_event=read_sample_event,
        bus_relinquished=bus_relinquished,
        address_output_enable=interface_active,
        control_output_enable=interface_active,
        data_output_enable=(
            interface_active and state.write and write_drive_active
        ),
        pms_n=not interface_active,
        pmrd_n=not (interface_active and not state.write and strobe_active),
        pmwr_n=not (interface_active and state.write and strobe_active),
        address=state.address.value if address_known else 0,
        address_known=interface_active and address_known,
        pmda=state.data_access if interface_active else False,
        write_data=(state.write_data.value if write_data_known else 0),
        write_data_known=(
            interface_active
            and state.write
            and write_drive_active
            and write_data_known
        ),
    )

    if reset:
        return replace(result, state=ProgramBusState.reset())

    next_state = state
    if completion_event:
        next_state = replace(
            next_state,
            response_valid=True,
            response_write=state.write,
            read_data=(pmd_read_data if not state.write else UNKNOWN),
        )

    if phase == LogicalPhase.STATE_8 and phase_advance:
        if request_accepted:
            assert request is not None
            next_state = ProgramBusState(
                active=True,
                address=request.address,
                data_access=request.data_access,
                write=request.write,
                write_data=request.write_data,
            )
        elif not bus_relinquished:
            next_state = ProgramBusState.reset()

    return replace(result, state=next_state)
