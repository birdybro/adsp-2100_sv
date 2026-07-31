#!/usr/bin/env python3
"""Generate deterministic original Type 9 model-versus-RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    ConditionInputs,
    ConditionalComputeState,
    DREG,
    DREGWrite,
    ExactWord,
    apply_conditional_compute_cycle,
    evaluate_if_condition,
    read_dreg,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def _opcode(z: int, amf: int, yop: int, xop: int, condition: int) -> int:
    return (
        0x200000
        | (z << 18)
        | (amf << 13)
        | (yop << 11)
        | (xop << 8)
        | condition
    )


def _condition_outcomes(condition: int) -> dict[bool, tuple[int, bool]]:
    outcomes: dict[bool, tuple[int, bool]] = {}
    for astat in range(256):
        for not_ce in (False, True):
            value = evaluate_if_condition(
                condition,
                ConditionInputs(
                    az=bool(astat & 0x01),
                    an=bool(astat & 0x02),
                    av=bool(astat & 0x04),
                    ac=bool(astat & 0x08),
                    as_flag=bool(astat & 0x10),
                    mv=bool(astat & 0x40),
                    not_counter_expired=not_ce,
                ),
            )
            outcomes.setdefault(value, (astat, not_ce))
    return outcomes


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
    state = ConditionalComputeState.reset()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        not_ce: bool = False,
        setup_astat: ExactWord | None = None,
        setup_mstat: ExactWord | None = None,
        setup_dreg: DREGWrite | None = None,
        setup_af: ExactWord | None = None,
        setup_mf: ExactWord | None = None,
        probe: DREG = DREG.AX0,
    ) -> None:
        nonlocal state
        result = apply_conditional_compute_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            not_counter_expired=not_ce,
            setup_astat=setup_astat,
            setup_mstat=setup_mstat,
            setup_dreg=setup_dreg,
            setup_af=setup_af,
            setup_mf=setup_mf,
        )
        if result.boundary_valid and not result.result_known:
            raise AssertionError("RTL vectors require known Type 9 inputs")

        stimulus = 0
        for value, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (not_ce, 1),
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
            (int(probe), 4),
        ):
            stimulus = _append(stimulus, value, width)

        action = result.action
        class_z = (opcode >> 18) & 1 if result.class_valid else 0
        class_amf = (opcode >> 13) & 0x1F if result.class_valid else 0
        class_yop = (opcode >> 11) & 3 if result.class_valid else 0
        class_xop = (opcode >> 8) & 7 if result.class_valid else 0
        class_condition = opcode & 0xF if result.class_valid else 0
        is_mac = action is not None and action.is_mac
        is_alu = action is not None and action.is_alu
        if action is None or action.is_nop:
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
            (False, 1),
            (result.nop_action, 1),
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (False, 1),
            (result.condition_true, 1),
            (is_mac, 1),
            (is_alu, 1),
            (class_z, 1),
            (class_amf, 5),
            (class_yop, 2),
            (class_xop, 3),
            (class_condition, 4),
            (x_source, 4),
            (y_source, 4),
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
        lines.append(f"{stimulus:025x} {events:010x} {post_state:027x}")
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
                        (0x1200 * (bank + 1) + 0x101 * int(destination))
                        & 0xFFFF,
                    ),
                ),
                probe=destination,
            )
        emit(setup_af=ExactWord(16, 0xA200 + bank))
        emit(setup_mf=ExactWord(16, 0xB200 + bank))

    outcomes = [_condition_outcomes(condition) for condition in range(16)]
    execution_count = 0
    for bank in (0, 1):
        emit(setup_mstat=ExactWord(4, bank))
        for z in range(2):
            for amf in range(32):
                for yop in range(4):
                    for xop in range(8):
                        for condition in range(16):
                            for expected in (False, True):
                                if expected not in outcomes[condition]:
                                    continue
                                astat, not_ce = outcomes[condition][expected]
                                emit(setup_astat=ExactWord(8, astat))
                                emit(
                                    execute=True,
                                    opcode=_opcode(z, amf, yop, xop, condition),
                                    not_ce=not_ce,
                                    probe=DREG((z + amf + yop + xop + condition) & 0xF),
                                )
                                execution_count += 1
    if execution_count != 126_976:
        raise AssertionError(f"unexpected Type 9 execution count {execution_count}")

    for _ in range(random_count):
        choice = rng.randrange(10)
        if choice < 5:
            emit(
                execute=True,
                opcode=_opcode(
                    rng.randrange(2),
                    rng.randrange(32),
                    rng.randrange(4),
                    rng.randrange(8),
                    rng.randrange(16),
                ),
                not_ce=bool(rng.randrange(2)),
                probe=DREG(rng.randrange(16)),
            )
        elif choice == 5:
            emit(setup_astat=ExactWord(8, rng.randrange(256)))
        elif choice == 6:
            emit(setup_mstat=ExactWord(4, rng.randrange(16)))
        elif choice == 7:
            emit(
                setup_dreg=DREGWrite(
                    DREG(rng.randrange(16)), ExactWord(16, rng.randrange(1 << 16))
                ),
                probe=DREG(rng.randrange(16)),
            )
        elif choice == 8:
            emit(execute=True, opcode=0x280000, probe=DREG(rng.randrange(16)))
        else:
            opcode = _opcode(0, 0x13, 0, 0, 15)
            emit(
                execute=True,
                opcode=opcode,
                setup_astat=ExactWord(8, rng.randrange(256)),
            )

    emit(reset=True)
    emit(setup_astat=ExactWord(8, 0))
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=30_000)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=0x210009)
    args = parser.parse_args()
    lines = generate_lines(args.random_count, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"PASS generated {len(lines)} Type 9 vectors seed=0x{args.seed:x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
