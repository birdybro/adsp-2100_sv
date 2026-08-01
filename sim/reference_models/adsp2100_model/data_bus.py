"""Independent logical-pin model of the original ADSP-2100 DM interface.

The model separates the eight externally timed substates from the processor
state-seven extension caused by DMACK.  A low sample on the enabled 6-to-7
edge retains the transaction through one complete additional substate cycle;
only a later high 6-to-7 sample permits completion and read sampling on the
following 7-to-8 edge.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .model import ExactWord, UNKNOWN
from .phase import LogicalPhase


DATA_ADDRESS_WIDTH = 14
DATA_WORD_WIDTH = 16


def _require_exact(value: ExactWord | object, width: int, name: str) -> None:
    if value is not UNKNOWN and (
        not isinstance(value, ExactWord) or value.width != width
    ):
        raise ValueError(f"{name} must be UNKNOWN or exactly {width} bits")


@dataclass(frozen=True)
class DataBusRequest:
    """One original-device DM read or write descriptor."""

    address: ExactWord | object = UNKNOWN
    write: bool = False
    write_data: ExactWord | object = UNKNOWN

    def __post_init__(self) -> None:
        _require_exact(self.address, DATA_ADDRESS_WIDTH, "DM address")
        _require_exact(self.write_data, DATA_WORD_WIDTH, "DM write data")

    @classmethod
    def read(cls, address: int) -> "DataBusRequest":
        return cls(address=ExactWord(DATA_ADDRESS_WIDTH, address))

    @classmethod
    def write_word(cls, address: int, data: int) -> "DataBusRequest":
        return cls(
            address=ExactWord(DATA_ADDRESS_WIDTH, address),
            write=True,
            write_data=ExactWord(DATA_WORD_WIDTH, data),
        )


@dataclass(frozen=True)
class DataBusState:
    active: bool = False
    address: ExactWord | object = UNKNOWN
    write: bool = False
    write_data: ExactWord | object = UNKNOWN
    waiting: bool = False
    acknowledged: bool = False
    response_valid: bool = False
    response_write: bool = False
    read_data: ExactWord | object = UNKNOWN

    def __post_init__(self) -> None:
        _require_exact(self.address, DATA_ADDRESS_WIDTH, "stored DM address")
        _require_exact(
            self.write_data, DATA_WORD_WIDTH, "stored DM write data"
        )
        _require_exact(self.read_data, DATA_WORD_WIDTH, "sampled DM read data")

    @classmethod
    def reset(cls) -> "DataBusState":
        return cls()


@dataclass(frozen=True)
class DataBusCycleResult:
    state: DataBusState
    request_ready: bool = False
    request_accepted: bool = False
    dmack_sample_event: bool = False
    dmack_accepted: bool = False
    wait_extension_event: bool = False
    completion_event: bool = False
    read_sample_event: bool = False
    transaction_active: bool = False
    waiting: bool = False
    bus_relinquished: bool = False
    address_output_enable: bool = False
    control_output_enable: bool = False
    data_output_enable: bool = False
    dms_n: bool = True
    dmrd_n: bool = True
    dmwr_n: bool = True
    address: int = 0
    address_known: bool = False
    write_data: int = 0
    write_data_known: bool = False


def apply_data_bus_cycle(
    state: DataBusState,
    *,
    reset: bool = False,
    phase: LogicalPhase | int = LogicalPhase.STATE_1,
    phase_advance: bool = True,
    request: DataBusRequest | None = None,
    dm_ack: bool = True,
    dmd_read_data: ExactWord | object = UNKNOWN,
    bus_relinquished: bool = False,
) -> DataBusCycleResult:
    """Apply one FPGA clock at the bounded native DM phase interface.

    ``phase`` identifies the physical eight-substate slot.  While ``waiting``
    is true, those slots continue to circulate, but the original processor's
    architectural state remains state seven.  The caller must present phases
    in order for authentic timing; the acknowledgement latch prevents an
    out-of-order state-seven clock from completing a request.
    """

    phase = LogicalPhase(phase)
    _require_exact(dmd_read_data, DATA_WORD_WIDTH, "DM read data")

    in_progress = state.active and not state.response_valid
    interface_active = state.active and not bus_relinquished and not reset
    request_ready = bool(
        not reset
        and not bus_relinquished
        and phase == LogicalPhase.STATE_8
        and phase_advance
        and (not state.active or state.response_valid)
    )
    request_accepted = request_ready and request is not None
    dmack_sample_event = bool(
        interface_active
        and in_progress
        and phase == LogicalPhase.STATE_6
        and phase_advance
    )
    dmack_accepted = dmack_sample_event and dm_ack
    wait_extension_event = dmack_sample_event and not dm_ack
    completion_event = bool(
        interface_active
        and in_progress
        and phase == LogicalPhase.STATE_7
        and phase_advance
        and state.acknowledged
        and not state.waiting
    )
    read_sample_event = completion_event and not state.write
    strobe_active = state.waiting or phase in (
        LogicalPhase.STATE_4,
        LogicalPhase.STATE_5,
        LogicalPhase.STATE_6,
        LogicalPhase.STATE_7,
    )
    write_drive_active = state.waiting or phase in (
        LogicalPhase.STATE_5,
        LogicalPhase.STATE_6,
        LogicalPhase.STATE_7,
        LogicalPhase.STATE_8,
    )
    address_known = isinstance(state.address, ExactWord)
    write_data_known = isinstance(state.write_data, ExactWord)

    result = DataBusCycleResult(
        state=state,
        request_ready=request_ready,
        request_accepted=request_accepted,
        dmack_sample_event=dmack_sample_event,
        dmack_accepted=dmack_accepted,
        wait_extension_event=wait_extension_event,
        completion_event=completion_event,
        read_sample_event=read_sample_event,
        transaction_active=state.active,
        waiting=in_progress and state.waiting,
        bus_relinquished=bus_relinquished,
        address_output_enable=interface_active,
        control_output_enable=interface_active,
        data_output_enable=(
            interface_active
            and in_progress
            and state.write
            and write_drive_active
        ),
        dms_n=not interface_active,
        dmrd_n=not (
            interface_active
            and in_progress
            and not state.write
            and strobe_active
        ),
        dmwr_n=not (
            interface_active
            and in_progress
            and state.write
            and strobe_active
        ),
        address=state.address.value if address_known else 0,
        address_known=interface_active and address_known,
        write_data=(state.write_data.value if write_data_known else 0),
        write_data_known=(
            interface_active
            and in_progress
            and state.write
            and write_drive_active
            and write_data_known
        ),
    )

    if reset:
        return replace(result, state=DataBusState.reset())

    next_state = state
    if dmack_sample_event:
        next_state = replace(
            next_state,
            waiting=not dm_ack,
            acknowledged=dm_ack,
        )
    if completion_event:
        next_state = replace(
            next_state,
            waiting=False,
            acknowledged=False,
            response_valid=True,
            response_write=state.write,
            read_data=(dmd_read_data if not state.write else UNKNOWN),
        )
    if request_ready:
        if request_accepted:
            assert request is not None
            next_state = DataBusState(
                active=True,
                address=request.address,
                write=request.write,
                write_data=request.write_data,
            )
        else:
            next_state = DataBusState.reset()

    return replace(result, state=next_state)
