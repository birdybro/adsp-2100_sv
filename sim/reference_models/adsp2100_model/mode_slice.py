"""Cycle-boundary integration model for the four original MSTAT consumers."""

from __future__ import annotations

from dataclasses import dataclass, field

from .alu import ALUResult, compute_alu
from .dag import DAGResult, compute_dag
from .model import ComputationalBank, ExactWord, KnownOrUnknown, UNKNOWN
from .registers import (
    ALURegisterWrite,
    DREG,
    DREGWrite,
    apply_computational_cycle,
    read_dreg,
)
from .status import (
    ALUStatusUpdate,
    ModeControl,
    StatusCycleInputs,
    StatusRegisters,
    apply_status_cycle,
)


@dataclass(frozen=True)
class ModeSliceState:
    status: StatusRegisters = field(default_factory=StatusRegisters.reset)
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)


@dataclass(frozen=True)
class ModeSliceInputs:
    reset: bool = False
    astat_move: ExactWord | None = None
    mstat_move: ExactWord | None = None
    mode_controls: tuple[ModeControl, ...] = (
        ModeControl.NO_CHANGE_ZERO,
        ModeControl.NO_CHANGE_ZERO,
        ModeControl.NO_CHANGE_ZERO,
        ModeControl.NO_CHANGE_ZERO,
    )
    read_address: DREG = DREG.AX0
    dreg_write: DREGWrite | None = None
    alu_execute: bool = False
    alu_amf: int = 0x10
    alu_x: int = 0
    alu_y: int = 0
    alu_feedback: bool = False
    dag_i: int = 0
    dag_m: int = 0
    dag_l: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "read_address", DREG(self.read_address))
        if self.astat_move is not None and self.astat_move.width != 8:
            raise ValueError("ASTAT move must be exactly 8 bits")
        if self.mstat_move is not None and self.mstat_move.width != 4:
            raise ValueError("MSTAT move must be exactly 4 bits")
        if len(self.mode_controls) != 4:
            raise ValueError("MSTAT requires four mode controls")
        object.__setattr__(
            self,
            "mode_controls",
            tuple(ModeControl(control) for control in self.mode_controls),
        )
        if self.alu_execute and not 0x10 <= self.alu_amf <= 0x1F:
            raise ValueError("active ALU operation requires a standard ALU AMF")
        if (
            self.alu_execute
            and self.dreg_write is not None
            and not self.alu_feedback
            and self.dreg_write.address == DREG.AR
        ):
            raise ValueError("ALU AR and direct AR writes collide")


@dataclass(frozen=True)
class ModeSliceObservation:
    read_data: KnownOrUnknown
    alu: ALUResult | None
    dag: DAGResult
    alternate_bank: bool
    bit_reverse: bool
    overflow_latch: bool
    saturate_ar: bool


@dataclass(frozen=True)
class ModeSliceCycleResult:
    observation: ModeSliceObservation
    state: ModeSliceState
    status_write_conflict: bool


def _known_astat_bit(state: StatusRegisters, bit: int) -> bool | None:
    value = state.astat.bits[bit]
    return None if value is UNKNOWN else bool(value)


def apply_mode_slice_cycle(
    state: ModeSliceState,
    inputs: ModeSliceInputs,
) -> ModeSliceCycleResult:
    """Observe cycle-start modes, then commit cycle-end state."""

    mstat = state.status.mstat.value
    alternate_bank = bool(mstat & 0x1)
    bit_reverse = bool(mstat & 0x2)
    overflow_latch = bool(mstat & 0x4)
    saturate_ar = bool(mstat & 0x8)
    selected = state.alternate if alternate_bank else state.primary
    read_data = read_dreg(selected, inputs.read_address)

    ac = _known_astat_bit(state.status, 3)
    av = _known_astat_bit(state.status, 2)
    alu = None
    if inputs.alu_execute:
        if ac is None or av is None:
            raise ValueError("active ALU integration requires known AC and AV")
        alu = compute_alu(
            inputs.alu_amf,
            inputs.alu_x,
            inputs.alu_y,
            carry_in=ac,
            previous_av=av,
            sticky_av=overflow_latch,
            saturate_ar=saturate_ar,
            destination_is_ar=not inputs.alu_feedback,
        )

    dag = compute_dag(
        inputs.dag_i,
        inputs.dag_m,
        inputs.dag_l,
        dag1=True,
        bit_reverse_enabled=bit_reverse,
    )
    observation = ModeSliceObservation(
        read_data=read_data,
        alu=alu,
        dag=dag,
        alternate_bank=alternate_bank,
        bit_reverse=bit_reverse,
        overflow_latch=overflow_latch,
        saturate_ar=saturate_ar,
    )

    status_result = apply_status_cycle(
        state.status,
        StatusCycleInputs(
            reset=inputs.reset,
            astat_move=inputs.astat_move,
            mstat_move=inputs.mstat_move,
            mode_controls=inputs.mode_controls,
            alu=(
                None
                if alu is None
                else ALUStatusUpdate(
                    alu.az,
                    alu.an,
                    alu.av,
                    alu.ac,
                    alu.as_value if alu.as_write else None,
                )
            ),
        ),
    )

    primary = state.primary
    alternate = state.alternate
    if not inputs.reset:
        register_result = apply_computational_cycle(
            primary,
            alternate,
            alternate_selected=alternate_bank,
            dreg_writes=(
                () if inputs.dreg_write is None else (inputs.dreg_write,)
            ),
            alu_write=(
                None
                if alu is None
                else ALURegisterWrite(
                    inputs.alu_feedback,
                    ExactWord(16, alu.destination_result),
                )
            ),
        )
        primary = register_result.primary
        alternate = register_result.alternate

    return ModeSliceCycleResult(
        observation=observation,
        state=ModeSliceState(status_result.state, primary, alternate),
        status_write_conflict=status_result.write_conflict,
    )
