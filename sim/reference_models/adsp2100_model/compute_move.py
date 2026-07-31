"""Independent bounded original ADSP-2100 Type 8 execution model."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from .alu import ALUResult, compute_alu
from .mac import MACResult, compute_mac
from .model import ComputationalBank, ExactWord, UNKNOWN
from .registers import (
    ALURegisterWrite,
    DREG,
    DREGWrite,
    MACRegisterWrite,
    apply_computational_cycle,
    apply_dreg_cycle,
    read_dreg,
)
from .status import (
    ALUStatusUpdate,
    ASTATBit,
    ASTATState,
    StatusCycleInputs,
    StatusRegisters,
    apply_status_cycle,
)


COMPUTE_MOVE_CLASS_MASK = 0xF80000
COMPUTE_MOVE_CLASS_VALUE = 0x280000

ALU_X_DREG = (
    DREG.AX0,
    DREG.AX1,
    DREG.AR,
    DREG.MR0,
    DREG.MR1,
    DREG.MR2,
    DREG.SR0,
    DREG.SR1,
)
MAC_X_DREG = (
    DREG.MX0,
    DREG.MX1,
    DREG.AR,
    DREG.MR0,
    DREG.MR1,
    DREG.MR2,
    DREG.SR0,
    DREG.SR1,
)


@dataclass(frozen=True)
class ComputeMoveAction:
    z: int
    amf: int
    yop: int
    xop: int
    move_destination: DREG
    move_source: DREG

    @property
    def is_mac(self) -> bool:
        return self.amf < 0x10

    @property
    def destination_feedback(self) -> bool:
        return bool(self.z)


def is_compute_move_class(opcode: int) -> bool:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    return opcode & COMPUTE_MOVE_CLASS_MASK == COMPUTE_MOVE_CLASS_VALUE


def compute_move_unsupported_reason(opcode: int) -> str | None:
    """Classify Type 8 words excluded from the bounded execution subset."""

    if not is_compute_move_class(opcode):
        return None
    z = (opcode >> 18) & 1
    amf = (opcode >> 13) & 0x1F
    destination = DREG((opcode >> 4) & 0xF)
    if amf == 0:
        return "UNVERIFIED_AMF_ZERO"
    if z == 0 and amf >= 0x10 and destination == DREG.AR:
        return "UNSUPPORTED_DESTINATION_COLLISION"
    if z == 0 and amf < 0x10 and destination in (
        DREG.MR0,
        DREG.MR1,
        DREG.MR2,
    ):
        return "UNSUPPORTED_DESTINATION_COLLISION"
    return None


def decode_compute_move(opcode: int) -> ComputeMoveAction | None:
    if not is_compute_move_class(opcode):
        return None
    if compute_move_unsupported_reason(opcode) is not None:
        return None
    return ComputeMoveAction(
        z=(opcode >> 18) & 1,
        amf=(opcode >> 13) & 0x1F,
        yop=(opcode >> 11) & 0x3,
        xop=(opcode >> 8) & 0x7,
        move_destination=DREG((opcode >> 4) & 0xF),
        move_source=DREG(opcode & 0xF),
    )


@dataclass(frozen=True)
class ComputeMoveState:
    primary: ComputationalBank = field(default_factory=ComputationalBank)
    alternate: ComputationalBank = field(default_factory=ComputationalBank)
    status: StatusRegisters = field(default_factory=StatusRegisters.reset)

    @classmethod
    def reset(cls) -> "ComputeMoveState":
        return cls()


@dataclass(frozen=True)
class ComputeMoveCycleResult:
    state: ComputeMoveState
    action: ComputeMoveAction | None = None
    unsupported_reason: str | None = None
    class_valid: bool = False
    action_valid: bool = False
    unsupported_subencoding: bool = False
    boundary_valid: bool = False
    invalid_opcode: bool = False
    integration_conflict: bool = False
    move_result_known: bool = False
    compute_result_known: bool = False
    move_write: bool = False
    alu_write: bool = False
    mac_write: bool = False
    alu_status_write: bool = False
    mac_status_write: bool = False
    pm_data_access: bool = False
    dm_access: bool = False


def _selected_bank(state: ComputeMoveState) -> ComputationalBank:
    return state.alternate if state.status.alternate_bank else state.primary


def _replace_selected_bank(
    state: ComputeMoveState,
    bank: ComputationalBank,
) -> ComputeMoveState:
    if state.status.alternate_bank:
        return replace(state, alternate=bank)
    return replace(state, primary=bank)


def _replace_pair(
    pair: tuple[object, object],
    index: int,
    value: object,
) -> tuple[object, object]:
    updated = list(pair)
    updated[index] = value
    return (updated[0], updated[1])


def _invalidate_dreg(bank: ComputationalBank, destination: DREG) -> ComputationalBank:
    if destination in (DREG.AX0, DREG.AX1):
        return replace(bank, ax=_replace_pair(bank.ax, int(destination), UNKNOWN))
    if destination in (DREG.MX0, DREG.MX1):
        return replace(
            bank,
            mx=_replace_pair(bank.mx, int(destination) - int(DREG.MX0), UNKNOWN),
        )
    if destination in (DREG.AY0, DREG.AY1):
        return replace(
            bank,
            ay=_replace_pair(bank.ay, int(destination) - int(DREG.AY0), UNKNOWN),
        )
    if destination in (DREG.MY0, DREG.MY1):
        return replace(
            bank,
            my=_replace_pair(bank.my, int(destination) - int(DREG.MY0), UNKNOWN),
        )
    if destination == DREG.SI:
        return replace(bank, si=UNKNOWN)
    if destination == DREG.SE:
        return replace(bank, se=UNKNOWN)
    if destination == DREG.AR:
        return replace(bank, ar=UNKNOWN)
    if destination == DREG.MR0:
        return replace(bank, mr=(UNKNOWN, bank.mr[1], bank.mr[2]))
    if destination == DREG.MR1:
        return replace(bank, mr=(bank.mr[0], UNKNOWN, UNKNOWN))
    if destination == DREG.MR2:
        return replace(bank, mr=(bank.mr[0], bank.mr[1], UNKNOWN))
    return replace(
        bank,
        sr=_replace_pair(bank.sr, int(destination) - int(DREG.SR0), UNKNOWN),
    )


def _invalidate_astat(
    status: StatusRegisters,
    bits_to_invalidate: tuple[ASTATBit, ...],
) -> StatusRegisters:
    bits = list(status.astat.bits)
    for bit in bits_to_invalidate:
        bits[int(bit)] = UNKNOWN
    return replace(status, astat=ASTATState(tuple(bits)))


def _invalidate_compute_result(
    state: ComputeMoveState,
    action: ComputeMoveAction,
) -> ComputeMoveState:
    bank = _selected_bank(state)
    if action.is_mac:
        if action.destination_feedback:
            bank = replace(bank, mf=UNKNOWN)
        else:
            bank = replace(bank, mr=(UNKNOWN, UNKNOWN, UNKNOWN))
        status = _invalidate_astat(state.status, (ASTATBit.MV,))
    else:
        if action.destination_feedback:
            bank = replace(bank, af=UNKNOWN)
        else:
            bank = replace(bank, ar=UNKNOWN)
        affected = (ASTATBit.AZ, ASTATBit.AN, ASTATBit.AV, ASTATBit.AC)
        if action.amf == 0x1F:
            affected += (ASTATBit.AS,)
        status = _invalidate_astat(state.status, affected)
    return replace(_replace_selected_bank(state, bank), status=status)


def _known_mr(bank: ComputationalBank) -> ExactWord | None:
    mr0, mr1, mr2 = bank.mr
    if not all(isinstance(value, ExactWord) for value in (mr0, mr1, mr2)):
        return None
    assert isinstance(mr0, ExactWord)
    assert isinstance(mr1, ExactWord)
    assert isinstance(mr2, ExactWord)
    return ExactWord(40, (mr2.value << 32) | (mr1.value << 16) | mr0.value)


def _read_y(bank: ComputationalBank, action: ComputeMoveAction) -> object:
    if action.yop == 3:
        return ExactWord(16, 0)
    if action.is_mac:
        return bank.mf if action.yop == 2 else bank.my[action.yop]
    return bank.af if action.yop == 2 else bank.ay[action.yop]


def _known_alu_result(
    state: ComputeMoveState,
    action: ComputeMoveAction,
) -> ALUResult | None:
    bank = _selected_bank(state)
    x = read_dreg(bank, ALU_X_DREG[action.xop])
    y = _read_y(bank, action)
    needs_x = action.amf not in (0x10, 0x11, 0x14, 0x15, 0x18)
    needs_y = action.amf not in (0x1B, 0x1F)
    needs_carry = action.amf in (0x12, 0x16, 0x1A)
    if needs_x and not isinstance(x, ExactWord):
        return None
    if needs_y and not isinstance(y, ExactWord):
        return None
    carry = state.status.astat.bit(ASTATBit.AC)
    previous_av = state.status.astat.bit(ASTATBit.AV)
    if needs_carry and carry is UNKNOWN:
        return None
    if state.status.overflow_latch and previous_av is UNKNOWN:
        return None
    return compute_alu(
        action.amf,
        0 if not isinstance(x, ExactWord) else x.value,
        0 if not isinstance(y, ExactWord) else y.value,
        carry_in=False if carry is UNKNOWN else bool(carry),
        previous_av=False if previous_av is UNKNOWN else bool(previous_av),
        sticky_av=state.status.overflow_latch,
        saturate_ar=state.status.saturate_ar,
        destination_is_ar=not action.destination_feedback,
    )


def _known_mac_result(
    state: ComputeMoveState,
    action: ComputeMoveAction,
) -> MACResult | None:
    bank = _selected_bank(state)
    x = read_dreg(bank, MAC_X_DREG[action.xop])
    y = _read_y(bank, action)
    if not isinstance(x, ExactWord) or not isinstance(y, ExactWord):
        return None
    mr = _known_mr(bank)
    needs_mr = action.amf in (0x02, 0x03) or action.amf >= 0x08
    if needs_mr and mr is None:
        return None
    return compute_mac(action.amf, x.value, y.value, 0 if mr is None else mr.value)


def _apply_actions(
    state: ComputeMoveState,
    action: ComputeMoveAction,
    move_data: ExactWord | None,
    compute: ALUResult | MACResult | None,
) -> ComputeMoveState:
    dreg_writes = () if move_data is None else (
        DREGWrite(action.move_destination, move_data),
    )
    alu_write = None
    mac_write = None
    status_inputs = StatusCycleInputs()
    if isinstance(compute, ALUResult):
        alu_write = ALURegisterWrite(
            action.destination_feedback,
            ExactWord(16, compute.destination_result),
        )
        status_inputs = StatusCycleInputs(
            alu=ALUStatusUpdate(
                compute.az,
                compute.an,
                compute.av,
                compute.ac,
                compute.as_value if compute.as_write else None,
            )
        )
    elif isinstance(compute, MACResult):
        mac_write = MACRegisterWrite(
            action.destination_feedback,
            ExactWord(40, compute.result),
        )
        status_inputs = StatusCycleInputs(mac_mv=compute.mv)
    registers = apply_computational_cycle(
        state.primary,
        state.alternate,
        alternate_selected=state.status.alternate_bank,
        dreg_writes=dreg_writes,
        alu_write=alu_write,
        mac_write=mac_write,
    )
    status = apply_status_cycle(state.status, status_inputs).state
    updated = ComputeMoveState(registers.primary, registers.alternate, status)
    if move_data is None:
        updated = _replace_selected_bank(
            updated,
            _invalidate_dreg(_selected_bank(updated), action.move_destination),
        )
    if compute is None:
        updated = _invalidate_compute_result(updated, action)
    return updated


def apply_compute_move_cycle(
    state: ComputeMoveState,
    *,
    reset: bool = False,
    execute: bool = False,
    opcode: int = 0,
    setup_astat: ExactWord | None = None,
    setup_mstat: ExactWord | None = None,
    setup_dreg: DREGWrite | None = None,
    setup_af: ExactWord | None = None,
    setup_mf: ExactWord | None = None,
) -> ComputeMoveCycleResult:
    """Apply one reset, deterministic setup, or Type 8 instruction boundary."""

    for name, value, width in (
        ("ASTAT", setup_astat, 8),
        ("MSTAT", setup_mstat, 4),
        ("AF", setup_af, 16),
        ("MF", setup_mf, 16),
    ):
        if value is not None and value.width != width:
            raise ValueError(f"{name} setup must be exactly {width} bits")
    class_valid = is_compute_move_class(opcode)
    unsupported_reason = compute_move_unsupported_reason(opcode)
    action = decode_compute_move(opcode)
    setup_count = sum(
        value is not None
        for value in (setup_astat, setup_mstat, setup_dreg, setup_af, setup_mf)
    )
    conflict = bool(
        not reset and ((execute and setup_count != 0) or setup_count > 1)
    )
    invalid = bool(not reset and execute and action is None)
    boundary = bool(
        not reset and execute and action is not None and setup_count == 0
    )
    common = {
        "action": action,
        "unsupported_reason": unsupported_reason,
        "class_valid": class_valid,
        "action_valid": action is not None,
        "unsupported_subencoding": class_valid and action is None,
    }
    if reset:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(reset=True),
        ).state
        return ComputeMoveCycleResult(replace(state, status=status), **common)
    if conflict or invalid:
        return ComputeMoveCycleResult(
            state,
            invalid_opcode=invalid,
            integration_conflict=conflict,
            **common,
        )
    if setup_astat is not None or setup_mstat is not None:
        status = apply_status_cycle(
            state.status,
            StatusCycleInputs(astat_move=setup_astat, mstat_move=setup_mstat),
        ).state
        return ComputeMoveCycleResult(replace(state, status=status), **common)
    if setup_dreg is not None:
        registers = apply_dreg_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            writes=(setup_dreg,),
        )
        return ComputeMoveCycleResult(
            ComputeMoveState(registers.primary, registers.alternate, state.status),
            **common,
        )
    if setup_af is not None or setup_mf is not None:
        registers = apply_computational_cycle(
            state.primary,
            state.alternate,
            alternate_selected=state.status.alternate_bank,
            alu_write=None if setup_af is None else ALURegisterWrite(True, setup_af),
            mac_write=None if setup_mf is None else MACRegisterWrite(
                True,
                ExactWord(40, setup_mf.value << 16),
            ),
        )
        return ComputeMoveCycleResult(
            ComputeMoveState(registers.primary, registers.alternate, state.status),
            **common,
        )
    if not boundary:
        return ComputeMoveCycleResult(state, **common)

    assert action is not None
    bank = _selected_bank(state)
    move_source = read_dreg(bank, action.move_source)
    move_data = move_source if isinstance(move_source, ExactWord) else None
    compute = (
        _known_mac_result(state, action)
        if action.is_mac
        else _known_alu_result(state, action)
    )
    updated = _apply_actions(state, action, move_data, compute)
    return ComputeMoveCycleResult(
        updated,
        boundary_valid=True,
        move_result_known=move_data is not None,
        compute_result_known=compute is not None,
        move_write=True,
        alu_write=not action.is_mac,
        mac_write=action.is_mac,
        alu_status_write=not action.is_mac,
        mac_status_write=action.is_mac,
        **common,
    )
