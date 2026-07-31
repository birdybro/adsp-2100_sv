#!/usr/bin/env python3
"""Generate deterministic Type 8 stateful model-versus-RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    ComputeMoveState,
    DREG,
    DREGWrite,
    ExactWord,
    apply_compute_move_cycle,
    decode_compute_move,
    read_dreg,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _opcode(
    z: int,
    amf: int,
    yop: int,
    xop: int,
    destination: DREG,
    source: DREG,
) -> int:
    return (
        0x280000
        | (z << 18)
        | (amf << 13)
        | (yop << 11)
        | (xop << 8)
        | (int(destination) << 4)
        | int(source)
    )


def _exact_or_zero(value: object) -> tuple[bool, int]:
    if isinstance(value, ExactWord):
        return True, value.value
    return False, 0


def _mr(bank: object) -> tuple[bool, int]:
    mr0, mr1, mr2 = bank.mr
    if not all(isinstance(value, ExactWord) for value in (mr0, mr1, mr2)):
        return False, 0
    return True, (mr2.value << 32) | (mr1.value << 16) | mr0.value


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = ComputeMoveState.reset()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        setup_astat: ExactWord | None = None,
        setup_mstat: ExactWord | None = None,
        setup_dreg: DREGWrite | None = None,
        setup_af: ExactWord | None = None,
        setup_mf: ExactWord | None = None,
        probe: DREG = DREG.AX0,
    ) -> None:
        nonlocal state
        result = apply_compute_move_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            setup_astat=setup_astat,
            setup_mstat=setup_mstat,
            setup_dreg=setup_dreg,
            setup_af=setup_af,
            setup_mf=setup_mf,
        )
        if result.boundary_valid and not (
            result.move_result_known and result.compute_result_known
        ):
            raise AssertionError("RTL vectors require known Type 8 inputs")

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
            (setup_af is not None, 1),
            (setup_af.value if setup_af is not None else 0, 16),
            (setup_mf is not None, 1),
            (setup_mf.value if setup_mf is not None else 0, 16),
            (False, 1),
            (int(probe), 4),
        ):
            stimulus = _append(stimulus, value, width)

        action = result.action
        reason = result.unsupported_reason
        class_z = (opcode >> 18) & 1 if result.class_valid else 0
        class_amf = (opcode >> 13) & 0x1F if result.class_valid else 0
        class_yop = (opcode >> 11) & 3 if result.class_valid else 0
        class_xop = (opcode >> 8) & 7 if result.class_valid else 0
        class_destination = (opcode >> 4) & 0xF if result.class_valid else 0
        class_source = opcode & 0xF if result.class_valid else 0
        is_mac = action is not None and action.is_mac
        if action is None:
            x_source = 0
            y_source = 0
        else:
            x_source = (
                (2 + action.xop if action.is_mac else action.xop)
                if action.xop <= 1
                else action.xop + 8
            )
            y_source = (
                (6 + action.yop if action.is_mac else 4 + action.yop)
                if action.yop <= 1
                else 0
            )
        events = 0
        for value, width in (
            (result.class_valid, 1),
            (result.action_valid, 1),
            (result.unsupported_subencoding, 1),
            (reason == "UNVERIFIED_AMF_ZERO", 1),
            (reason == "UNSUPPORTED_DESTINATION_COLLISION", 1),
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (False, 1),
            (is_mac, 1),
            (class_z, 1),
            (class_amf, 5),
            (class_yop, 2),
            (class_xop, 3),
            (x_source, 4),
            (y_source, 4),
            (class_destination, 4),
            (class_source, 4),
            (result.move_write, 1),
            (result.alu_write, 1),
            (result.mac_write, 1),
            (result.alu_status_write, 1),
            (result.mac_status_write, 1),
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
        af_known, af_value = _exact_or_zero(selected.af)
        mf_known, mf_value = _exact_or_zero(selected.mf)
        mr_known, mr_value = _mr(selected)
        astat_known = result.state.status.astat.is_fully_known
        astat_value = (
            result.state.status.astat.to_word().value if astat_known else 0
        )
        post_state = 0
        for value, width in (
            (probe_known, 1),
            (probe_value, 16),
            (af_known, 1),
            (af_value, 16),
            (mf_known, 1),
            (mf_value, 16),
            (mr_known, 1),
            (mr_value, 40),
            (astat_known, 1),
            (astat_value, 8),
            (result.state.status.mstat.value, 4),
            (result.state.status.alternate_bank, 1),
        ):
            post_state = _append(post_state, value, width)
        lines.append(f"{stimulus:025x} {events:011x} {post_state:027x}")
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
        emit(setup_af=ExactWord(16, 0xA100 + bank))
        emit(setup_mf=ExactWord(16, 0xB100 + bank))

    supported_count = 0
    for bank in (0, 1):
        emit(setup_mstat=ExactWord(4, bank))
        for z in range(2):
            for amf in range(1, 32):
                for yop in range(4):
                    for xop in range(8):
                        for destination in DREG:
                            for source in DREG:
                                opcode = _opcode(
                                    z,
                                    amf,
                                    yop,
                                    xop,
                                    destination,
                                    source,
                                )
                                if decode_compute_move(opcode) is None:
                                    continue
                                emit(
                                    execute=True,
                                    opcode=opcode,
                                    probe=DREG(
                                        (
                                            z + amf + yop + xop
                                            + int(destination) + int(source)
                                        )
                                        & 0xF
                                    ),
                                )
                                supported_count += 1
    if supported_count != 2 * 476_672:
        raise AssertionError(f"unexpected supported execution count {supported_count}")

    legal_words = [
        _opcode(z, amf, yop, xop, destination, source)
        for z in range(2)
        for amf in range(1, 32)
        for yop in range(4)
        for xop in range(8)
        for destination in DREG
        for source in DREG
        if decode_compute_move(
            _opcode(z, amf, yop, xop, destination, source)
        )
        is not None
    ]
    for _ in range(random_count):
        choice = rng.randrange(24)
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
            emit(setup_af=ExactWord(16, rng.randrange(1 << 16)), probe=probe)
        elif choice == 5:
            emit(setup_mf=ExactWord(16, rng.randrange(1 << 16)), probe=probe)
        elif choice < 19:
            emit(execute=True, opcode=rng.choice(legal_words), probe=probe)
        elif choice == 19:
            emit(
                execute=True,
                opcode=_opcode(
                    rng.randrange(2),
                    0,
                    rng.randrange(4),
                    rng.randrange(8),
                    DREG(rng.randrange(16)),
                    DREG(rng.randrange(16)),
                ),
                probe=probe,
            )
        elif choice == 20:
            emit(
                execute=True,
                opcode=_opcode(0, 0x10, 0, 0, DREG.AR, DREG.AX0),
                probe=probe,
            )
        elif choice == 21:
            emit(execute=True, opcode=0, probe=probe)
        elif choice == 22:
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
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x210008)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    lines = generate_lines(args.random_count, args.seed)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(lines)} Type 8 stateful vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
