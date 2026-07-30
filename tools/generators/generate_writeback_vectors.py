#!/usr/bin/env python3
"""Generate stateful computational-register writeback vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    ALURegisterWrite,
    ComputationalBank,
    DREG,
    DREGWrite,
    ExactWord,
    MACRegisterWrite,
    ShifterRegisterWrite,
    UNKNOWN,
    apply_computational_cycle,
    read_dreg,
)


def _append(packed: int, value: int, width: int) -> int:
    return (packed << width) | value


def _pack_stimulus(
    *,
    alternate_selected: bool,
    read_address: DREG,
    dreg_write: DREGWrite | None = None,
    sb_move: int | None = None,
    alu_write: ALURegisterWrite | None = None,
    mac_write: MACRegisterWrite | None = None,
    shifter_sr: ExactWord | None = None,
    shifter_se: ExactWord | None = None,
    shifter_sb: ExactWord | None = None,
) -> int:
    packed = int(alternate_selected)
    packed = _append(packed, int(read_address), 4)
    packed = _append(packed, int(dreg_write is not None), 1)
    packed = _append(
        packed,
        0 if dreg_write is None else int(dreg_write.address),
        4,
    )
    packed = _append(
        packed,
        0 if dreg_write is None else dreg_write.data.value,
        16,
    )
    packed = _append(packed, int(sb_move is not None), 1)
    packed = _append(packed, 0 if sb_move is None else sb_move, 5)
    packed = _append(packed, int(alu_write is not None), 1)
    packed = _append(
        packed,
        0 if alu_write is None else int(alu_write.feedback),
        1,
    )
    packed = _append(
        packed,
        0 if alu_write is None else alu_write.data.value,
        16,
    )
    packed = _append(packed, int(mac_write is not None), 1)
    packed = _append(
        packed,
        0 if mac_write is None else int(mac_write.feedback),
        1,
    )
    packed = _append(
        packed,
        0 if mac_write is None else mac_write.data.value,
        40,
    )
    packed = _append(
        packed,
        int(shifter_sr is not None),
        1,
    )
    packed = _append(
        packed,
        0 if shifter_sr is None else shifter_sr.value,
        32,
    )
    packed = _append(
        packed,
        int(shifter_se is not None),
        1,
    )
    packed = _append(
        packed,
        0 if shifter_se is None else shifter_se.value,
        8,
    )
    packed = _append(
        packed,
        int(shifter_sb is not None),
        1,
    )
    packed = _append(
        packed,
        0 if shifter_sb is None else shifter_sb.value,
        5,
    )
    return packed


def _known(value: object, width: int) -> int:
    if value is UNKNOWN:
        raise ValueError("cannot compare an unknown register")
    if not isinstance(value, ExactWord) or value.width != width:
        raise ValueError(f"register is not exactly {width} bits")
    return value.value


def _pack_state(bank: ComputationalBank) -> int:
    packed = _known(bank.af, 16)
    packed = _append(packed, _known(bank.mf, 16), 16)
    mr = (
        (_known(bank.mr[2], 8) << 32)
        | (_known(bank.mr[1], 16) << 16)
        | _known(bank.mr[0], 16)
    )
    packed = _append(packed, mr, 40)
    packed = _append(packed, _known(bank.se, 8), 8)
    packed = _append(packed, _known(bank.sb, 5), 5)
    sr = (_known(bank.sr[1], 16) << 16) | _known(bank.sr[0], 16)
    return _append(packed, sr, 32)


def _pack_expected(
    read_value: object,
    bank: ComputationalBank,
    *,
    compare: bool,
    conflict: bool = False,
) -> int:
    packed = (int(compare) << 1) | int(conflict)
    if not compare:
        return packed << 133
    packed = _append(packed, _known(read_value, 16), 16)
    return _append(packed, _pack_state(bank), 117)


def _dreg(address: DREG, value: int) -> DREGWrite:
    return DREGWrite(address, ExactWord(16, value))


def generate_lines(random_count: int, seed: int) -> list[str]:
    primary = ComputationalBank()
    alternate = ComputationalBank()
    lines: list[str] = []

    def emit(
        *,
        alternate_selected: bool,
        read_address: DREG,
        dreg_write: DREGWrite | None = None,
        sb_move: int | None = None,
        alu_write: ALURegisterWrite | None = None,
        mac_write: MACRegisterWrite | None = None,
        shifter_write: ShifterRegisterWrite | None = None,
        compare: bool = True,
    ) -> None:
        nonlocal primary, alternate
        selected_before = alternate if alternate_selected else primary
        read_before = read_dreg(selected_before, read_address)
        stimulus = _pack_stimulus(
            alternate_selected=alternate_selected,
            read_address=read_address,
            dreg_write=dreg_write,
            sb_move=sb_move,
            alu_write=alu_write,
            mac_write=mac_write,
            shifter_sr=(
                None if shifter_write is None else shifter_write.sr
            ),
            shifter_se=(
                None if shifter_write is None else shifter_write.se
            ),
            shifter_sb=(
                None if shifter_write is None else shifter_write.sb
            ),
        )
        result = apply_computational_cycle(
            primary,
            alternate,
            alternate_selected=alternate_selected,
            read_addresses=(read_address,),
            dreg_writes=() if dreg_write is None else (dreg_write,),
            sb_move_data=(
                None if sb_move is None else ExactWord(16, sb_move)
            ),
            alu_write=alu_write,
            mac_write=mac_write,
            shifter_write=shifter_write,
        )
        expected = _pack_expected(
            read_before,
            selected_before,
            compare=compare,
        )
        lines.append(f"{stimulus:035x} {expected:034x}")
        primary, alternate = result.primary, result.alternate

    # Deterministic initialization is testbench setup, not architectural reset.
    for alternate_selected in (False, True):
        for address in DREG:
            value = (
                (0x2000 if not alternate_selected else 0xB000)
                | (int(address) << 4)
                | int(address)
            )
            emit(
                alternate_selected=alternate_selected,
                read_address=DREG.AX0,
                dreg_write=_dreg(address, value),
                compare=False,
            )
        emit(
            alternate_selected=alternate_selected,
            read_address=DREG.AX0,
            alu_write=ALURegisterWrite(
                True,
                ExactWord(16, 0x1AF0 if not alternate_selected else 0xAAF0),
            ),
            compare=False,
        )
        emit(
            alternate_selected=alternate_selected,
            read_address=DREG.AX0,
            mac_write=MACRegisterWrite(
                True,
                ExactWord(
                    40,
                    0x001F000000 if not alternate_selected else 0x00BF000000,
                ),
            ),
            compare=False,
        )
        emit(
            alternate_selected=alternate_selected,
            read_address=DREG.AX0,
            sb_move=0x0A if not alternate_selected else 0x1A,
            compare=False,
        )

    boundary16 = (0x0000, 0x0001, 0x7FFF, 0x8000, 0xFFFF)
    boundary40 = (
        0x0000000000,
        0x0000000001,
        0x007FFFFFFF,
        0xFF80000000,
        0xFFFFFFFFFF,
    )
    for alternate_selected in (False, True):
        for feedback in (False, True):
            for value in boundary16:
                emit(
                    alternate_selected=alternate_selected,
                    read_address=DREG.AR,
                    alu_write=ALURegisterWrite(
                        feedback,
                        ExactWord(16, value),
                    ),
                )
        for feedback in (False, True):
            for value in boundary40:
                emit(
                    alternate_selected=alternate_selected,
                    read_address=DREG.MR1,
                    mac_write=MACRegisterWrite(
                        feedback,
                        ExactWord(40, value),
                    ),
                )
        for value in (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
            emit(
                alternate_selected=alternate_selected,
                read_address=DREG.SR0,
                shifter_write=ShifterRegisterWrite(sr=ExactWord(32, value)),
            )
        for value in (0, 1, 0x7F, 0x80, 0xFF):
            emit(
                alternate_selected=alternate_selected,
                read_address=DREG.SE,
                shifter_write=ShifterRegisterWrite(se=ExactWord(8, value)),
            )
        for value in (0, 1, 0x0F, 0x10, 0x1F):
            emit(
                alternate_selected=alternate_selected,
                read_address=DREG.SE,
                shifter_write=ShifterRegisterWrite(sb=ExactWord(5, value)),
            )

    rng = random.Random(seed)
    addresses = list(DREG)
    for _ in range(random_count):
        alternate_selected = bool(rng.getrandbits(1))
        read_address = rng.choice(addresses)
        action = rng.randrange(4)
        alu_write = None
        mac_write = None
        shifter_write = None
        if action == 1:
            alu_write = ALURegisterWrite(
                bool(rng.getrandbits(1)),
                ExactWord(16, rng.randrange(1 << 16)),
            )
        elif action == 2:
            mac_write = MACRegisterWrite(
                bool(rng.getrandbits(1)),
                ExactWord(40, rng.randrange(1 << 40)),
            )
        elif action == 3:
            shifter_destination = rng.randrange(3)
            if shifter_destination == 0:
                shifter_write = ShifterRegisterWrite(
                    sr=ExactWord(32, rng.randrange(1 << 32))
                )
            elif shifter_destination == 1:
                shifter_write = ShifterRegisterWrite(
                    se=ExactWord(8, rng.randrange(1 << 8))
                )
            else:
                shifter_write = ShifterRegisterWrite(
                    sb=ExactWord(5, rng.randrange(1 << 5))
                )

        dreg_write = None
        if rng.getrandbits(1):
            candidates = addresses.copy()
            rng.shuffle(candidates)
            for address in candidates:
                if alu_write is not None and not alu_write.feedback:
                    if address == DREG.AR:
                        continue
                if mac_write is not None and not mac_write.feedback:
                    if address in (DREG.MR0, DREG.MR1, DREG.MR2):
                        continue
                if shifter_write is not None and shifter_write.sr is not None:
                    if address in (DREG.SR0, DREG.SR1):
                        continue
                if shifter_write is not None and shifter_write.se is not None:
                    if address == DREG.SE:
                        continue
                dreg_write = _dreg(address, rng.randrange(1 << 16))
                break

        sb_move = None
        if rng.randrange(4) == 0 and not (
            shifter_write is not None and shifter_write.sb is not None
        ):
            sb_move = rng.randrange(1 << 5)

        emit(
            alternate_selected=alternate_selected,
            read_address=read_address,
            dreg_write=dreg_write,
            sb_move=sb_move,
            alu_write=alu_write,
            mac_write=mac_write,
            shifter_write=shifter_write,
        )

    # Conflict vectors are clocked; the following vector proves that the
    # fail-closed RTL left every architectural register unchanged.
    conflicts = (
        {
            "dreg_write": _dreg(DREG.AR, 1),
            "alu_write": ALURegisterWrite(False, ExactWord(16, 2)),
        },
        {
            "dreg_write": _dreg(DREG.MR2, 1),
            "mac_write": MACRegisterWrite(False, ExactWord(40, 2)),
        },
        {
            "dreg_write": _dreg(DREG.SR0, 1),
            "shifter_sr": ExactWord(32, 2),
        },
        {
            "dreg_write": _dreg(DREG.SE, 1),
            "shifter_se": ExactWord(8, 2),
        },
        {
            "sb_move": 1,
            "shifter_sb": ExactWord(5, 2),
        },
        {
            "alu_write": ALURegisterWrite(True, ExactWord(16, 1)),
            "mac_write": MACRegisterWrite(True, ExactWord(40, 2)),
        },
        {
            "alu_write": ALURegisterWrite(True, ExactWord(16, 1)),
            "shifter_sr": ExactWord(32, 2),
        },
        {
            "mac_write": MACRegisterWrite(True, ExactWord(40, 1)),
            "shifter_se": ExactWord(8, 2),
        },
        {
            "shifter_sr": ExactWord(32, 1),
            "shifter_se": ExactWord(8, 2),
        },
        {
            "shifter_sr": ExactWord(32, 1),
            "shifter_sb": ExactWord(5, 2),
        },
        {
            "shifter_se": ExactWord(8, 1),
            "shifter_sb": ExactWord(5, 2),
        },
    )
    for controls in conflicts:
        stimulus = _pack_stimulus(
            alternate_selected=False,
            read_address=DREG.AX0,
            **controls,
        )
        expected = _pack_expected(
            read_dreg(primary, DREG.AX0),
            primary,
            compare=True,
            conflict=True,
        )
        lines.append(f"{stimulus:035x} {expected:034x}")
    emit(
        alternate_selected=False,
        read_address=DREG.AX0,
    )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--random-count", type=int, default=50000)
    parser.add_argument("--seed", type=int, default=0x2100B)
    args = parser.parse_args()
    if args.random_count < 0:
        parser.error("--random-count cannot be negative")
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"PASS wrote {len(lines)} writeback vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
