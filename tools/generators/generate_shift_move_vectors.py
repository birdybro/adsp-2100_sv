#!/usr/bin/env python3
"""Generate deterministic Type 14 stateful model-versus-RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    DREG,
    DREGWrite,
    ExactWord,
    ShiftMoveState,
    apply_shift_move_cycle,
    decode_shift_move,
    read_dreg,
)


LEGAL_XOPS = (0, 2, 3, 4, 5, 6, 7)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _opcode(sf: int, xop: int, destination: DREG, source: DREG) -> int:
    return (
        0x100000
        | (sf << 11)
        | (xop << 8)
        | (int(destination) << 4)
        | int(source)
    )


def _exact_or_zero(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return True, value.value
    return False, 0


def _sr(bank: object) -> tuple[bool, int]:
    sr0, sr1 = bank.sr
    if not isinstance(sr0, ExactWord) or not isinstance(sr1, ExactWord):
        return False, 0
    return True, (sr1.value << 16) | sr0.value


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = ShiftMoveState.reset()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        setup_astat: ExactWord | None = None,
        setup_mstat: ExactWord | None = None,
        setup_dreg: DREGWrite | None = None,
        setup_sb: ExactWord | None = None,
        probe: DREG = DREG.AX0,
    ) -> None:
        nonlocal state
        result = apply_shift_move_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            setup_astat=setup_astat,
            setup_mstat=setup_mstat,
            setup_dreg=setup_dreg,
            setup_sb=setup_sb,
        )
        if result.boundary_valid and not (
            result.move_result_known and result.shifter_result_known
        ):
            raise AssertionError("RTL vectors require known Type 14 inputs")

        stimulus = 0
        for value, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (setup_astat is not None, 1),
            (setup_astat.value if setup_astat is not None else 0, 8),
            (setup_mstat is not None, 1),
            (setup_mstat.value if setup_mstat is not None else 0, 4),
            (setup_dreg is not None, 1),
            (int(setup_dreg.address) if setup_dreg is not None else 0, 4),
            (setup_dreg.data.value if setup_dreg is not None else 0, 16),
            (setup_sb is not None, 1),
            (setup_sb.value if setup_sb is not None else 0, 5),
            (int(probe), 4),
        ):
            stimulus = _append(stimulus, value, width)

        action = result.action
        reason = result.unsupported_reason
        class_sf = (opcode >> 11) & 0xF if result.class_valid else 0
        class_xop = (opcode >> 8) & 0x7 if result.class_valid else 0
        class_destination = (opcode >> 4) & 0xF if result.class_valid else 0
        class_source = opcode & 0xF if result.class_valid else 0
        events = 0
        for value, width in (
            (result.class_valid, 1),
            (result.action_valid, 1),
            (result.unsupported_subencoding, 1),
            (reason == "UNVERIFIED_UNUSED_X", 1),
            (reason == "UNAVAILABLE_SHIFTER_XOP", 1),
            (reason == "UNSUPPORTED_DESTINATION_COLLISION", 1),
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (False, 1),
            (class_sf, 4),
            (class_xop, 3),
            (int(action.shifter_source) if action is not None else 0, 4),
            (class_destination, 4),
            (class_source, 4),
            (result.move_write, 1),
            (result.sr_write, 1),
            (result.se_write, 1),
            (result.sb_write, 1),
            (result.ss_write, 1),
            (False, 1),
            (False, 1),
        ):
            events = _append(events, value, width)

        selected = (
            result.state.alternate
            if result.state.status.alternate_bank
            else result.state.primary
        )
        probe_known, probe_value = _exact_or_zero(read_dreg(selected, probe))
        sr_known, sr_value = _sr(selected)
        se_known, se_value = _exact_or_zero(read_dreg(selected, DREG.SE))
        sb_known, sb_value = _exact_or_zero(selected.sb)
        astat_known = result.state.status.astat.is_fully_known
        astat_value = (
            result.state.status.astat.to_word().value if astat_known else 0
        )
        post_state = 0
        for value, width in (
            (probe_known, 1),
            (probe_value, 16),
            (sr_known, 1),
            (sr_value, 32),
            (se_known, 1),
            (se_value, 16),
            (sb_known, 1),
            (sb_value, 5),
            (astat_known, 1),
            (astat_value, 8),
            (result.state.status.mstat.value, 4),
            (result.state.status.alternate_bank, 1),
        ):
            post_state = _append(post_state, value, width)
        lines.append(f"{stimulus:018x} {events:09x} {post_state:022x}")
        state = result.state

    emit(reset=True)
    emit(setup_astat=ExactWord(8, 0x5D))
    for bank in (0, 1):
        emit(setup_mstat=ExactWord(4, bank))
        for destination in DREG:
            emit(
                setup_dreg=DREGWrite(
                    destination,
                    ExactWord(
                        16,
                        (0x1100 * (bank + 1) + 0x101 * int(destination))
                        & 0xFFFF,
                    ),
                ),
                probe=destination,
            )
        emit(setup_sb=ExactWord(5, 0x10 + bank))

    supported_count = 0
    for bank in (0, 1):
        emit(setup_mstat=ExactWord(4, bank))
        for sf in range(16):
            for xop in LEGAL_XOPS:
                for destination in DREG:
                    for source in DREG:
                        opcode = _opcode(sf, xop, destination, source)
                        if decode_shift_move(opcode) is None:
                            continue
                        emit(
                            execute=True,
                            opcode=opcode,
                            probe=DREG((sf + xop + int(destination) + int(source)) & 0xF),
                        )
                        supported_count += 1
    if supported_count != 2 * 25_648:
        raise AssertionError(f"unexpected supported execution count {supported_count}")

    legal_words = [
        _opcode(sf, xop, destination, source)
        for sf in range(16)
        for xop in LEGAL_XOPS
        for destination in DREG
        for source in DREG
        if decode_shift_move(_opcode(sf, xop, destination, source)) is not None
    ]
    for _ in range(random_count):
        choice = rng.randrange(23)
        probe = DREG(rng.randrange(16))
        if choice == 0:
            emit(setup_mstat=ExactWord(4, rng.randrange(16)), probe=probe)
        elif choice == 1:
            emit(setup_astat=ExactWord(8, rng.randrange(256)), probe=probe)
        elif choice < 4:
            destination = DREG(rng.randrange(16))
            emit(
                setup_dreg=DREGWrite(
                    destination,
                    ExactWord(16, rng.randrange(1 << 16)),
                ),
                probe=destination,
            )
        elif choice == 4:
            emit(setup_sb=ExactWord(5, rng.randrange(32)), probe=probe)
        elif choice < 17:
            emit(execute=True, opcode=rng.choice(legal_words), probe=probe)
        elif choice == 17:
            emit(
                execute=True,
                opcode=0x108000 | rng.randrange(0x8000),
                probe=probe,
            )
        elif choice == 18:
            emit(
                execute=True,
                opcode=_opcode(
                    rng.randrange(16),
                    1,
                    DREG(rng.randrange(16)),
                    DREG(rng.randrange(16)),
                ),
                probe=probe,
            )
        elif choice == 19:
            emit(
                execute=True,
                opcode=_opcode(0, 0, DREG.SR0, DREG(rng.randrange(16))),
                probe=probe,
            )
        elif choice == 20:
            emit(reset=True, probe=probe)
            emit(setup_astat=ExactWord(8, rng.randrange(256)), probe=probe)
        elif choice == 21:
            emit(
                execute=True,
                opcode=rng.choice(legal_words),
                setup_dreg=DREGWrite(
                    DREG(rng.randrange(16)),
                    ExactWord(16, rng.randrange(1 << 16)),
                ),
                probe=probe,
            )
        else:
            emit(
                setup_astat=ExactWord(8, rng.randrange(256)),
                setup_mstat=ExactWord(4, rng.randrange(16)),
                probe=probe,
            )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=30_000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x210014)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    lines = generate_lines(args.random_count, args.seed)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(lines)} Type 14 stateful vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
