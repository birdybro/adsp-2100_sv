#!/usr/bin/env python3
"""Generate deterministic Type 21 stateful model-versus-RTL vectors."""

from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sim.reference_models.adsp2100_model import (  # noqa: E402
    MODIFY_ADDRESS_VALUE,
    DAGRegisterKind,
    DAGRegisterSetup,
    DAGRegisterState,
    apply_modify_address_cycle,
    decode_modify_address,
)


def _append(packed: int, value: int | bool, width: int) -> int:
    return (packed << width) | int(value)


def generate_lines(random_count: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    state = DAGRegisterState()
    lines: list[str] = []

    def emit(
        *,
        reset: bool = False,
        execute: bool = False,
        opcode: int = 0,
        setup_write: bool = False,
        setup_kind: int = 0,
        setup_address: int = 0,
        setup_data: int = 0,
        probe_address: int = 0,
    ) -> None:
        nonlocal state
        setup_invalid = bool(
            not reset
            and setup_write
            and not execute
            and setup_kind == 3
        )
        setup = (
            DAGRegisterSetup(
                DAGRegisterKind(setup_kind),
                setup_address,
                setup_data,
            )
            if setup_write and setup_kind < 3
            else None
        )
        result = apply_modify_address_cycle(
            state,
            reset=reset,
            execute=execute,
            opcode=opcode,
            setup=setup,
        )
        selection = decode_modify_address(opcode)

        stimulus = 0
        for value, width in (
            (reset, 1),
            (execute, 1),
            (opcode, 24),
            (setup_write, 1),
            (setup_kind, 2),
            (setup_address, 3),
            (setup_data, 14),
            (probe_address, 3),
        ):
            stimulus = _append(stimulus, value, width)

        event = 0
        for value, width in (
            (result.boundary_valid, 1),
            (result.invalid_opcode, 1),
            (result.integration_conflict, 1),
            (setup_invalid, 1),
            (False, 1),
            (result.operands_valid, 1),
            (result.configuration_valid, 1),
            (result.writeback_valid, 1),
            (selection.dag if selection is not None else 0, 1),
            (selection.i_local if selection is not None else 0, 2),
            (selection.m_local if selection is not None else 0, 2),
            (selection.i_address if selection is not None else 0, 3),
            (selection.m_address if selection is not None else 0, 3),
            (False, 1),
            (False, 1),
        ):
            event = _append(event, value, width)

        selected_data = 0
        for value in (
            result.old_i,
            result.m_value,
            result.l_value,
            result.next_i,
        ):
            selected_data = _append(selected_data, value, 14)

        probe = 0
        for bank in (
            result.state.i,
            result.state.m,
            result.state.l,
        ):
            value = bank[probe_address]
            probe = _append(probe, value is not None, 1)
            probe = _append(probe, value if value is not None else 0, 14)

        lines.append(
            f"{stimulus:013x} {event:06x} "
            f"{selected_data:014x} {probe:012x}"
        )
        state = result.state

    emit(reset=True)
    emit(setup_write=True, setup_kind=3)

    # Establish all 24 registers without pretending reset supplies data.
    for address in range(8):
        emit(
            setup_write=True,
            setup_kind=int(DAGRegisterKind.I),
            setup_address=address,
            setup_data=0x0100 + address * 0x10,
            probe_address=address,
        )
        emit(
            setup_write=True,
            setup_kind=int(DAGRegisterKind.M),
            setup_address=address,
            setup_data=(address + 1) & 0x3FFF,
            probe_address=address,
        )
        emit(
            setup_write=True,
            setup_kind=int(DAGRegisterKind.L),
            setup_address=address,
            setup_data=0,
            probe_address=address,
        )

    # Execute every field-defined I/M pair in both DAGs.
    for payload in range(32):
        selection = decode_modify_address(MODIFY_ADDRESS_VALUE | payload)
        assert selection is not None
        emit(
            execute=True,
            opcode=MODIFY_ADDRESS_VALUE | payload,
            probe_address=selection.i_address,
        )

    # Directed circular wrap, negative linear update, invalid configuration,
    # unknown operand propagation, invalid opcode, and setup collision.
    for kind, value in (
        (DAGRegisterKind.I, 7),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 8),
    ):
        emit(
            setup_write=True,
            setup_kind=int(kind),
            setup_address=0,
            setup_data=value,
        )
    emit(execute=True, opcode=0x090000)
    emit(
        setup_write=True,
        setup_kind=int(DAGRegisterKind.I),
        setup_address=4,
        setup_data=0,
    )
    emit(
        setup_write=True,
        setup_kind=int(DAGRegisterKind.M),
        setup_address=4,
        setup_data=0x3FFF,
    )
    emit(
        setup_write=True,
        setup_kind=int(DAGRegisterKind.L),
        setup_address=4,
        setup_data=0,
    )
    emit(execute=True, opcode=0x090010, probe_address=4)

    for kind, value in (
        (DAGRegisterKind.I, 8),
        (DAGRegisterKind.M, 1),
        (DAGRegisterKind.L, 8),
    ):
        emit(
            setup_write=True,
            setup_kind=int(kind),
            setup_address=2,
            setup_data=value,
        )
    emit(execute=True, opcode=0x090008, probe_address=2)
    emit(reset=True, probe_address=7)
    emit(execute=True, opcode=0x09001F, probe_address=7)
    emit(execute=True, opcode=0x0A0000)
    emit(
        execute=True,
        opcode=0x090000,
        setup_write=True,
        setup_kind=int(DAGRegisterKind.I),
        setup_address=0,
        setup_data=0x1234,
    )

    for index in range(random_count):
        choice = rng.randrange(14)
        probe = rng.randrange(8)
        if choice == 0:
            emit(reset=True, probe_address=probe)
        elif choice < 7:
            emit(
                setup_write=True,
                setup_kind=rng.randrange(3),
                setup_address=rng.randrange(8),
                setup_data=rng.randrange(0x4000),
                probe_address=probe,
            )
        elif choice < 11:
            emit(
                execute=True,
                opcode=MODIFY_ADDRESS_VALUE | rng.randrange(32),
                probe_address=probe,
            )
        elif choice == 11:
            opcode = rng.randrange(0x1000000)
            if opcode & 0xFFFFE0 == MODIFY_ADDRESS_VALUE:
                opcode ^= 0x20
            emit(execute=True, opcode=opcode, probe_address=probe)
        elif choice == 12:
            emit(
                execute=True,
                opcode=MODIFY_ADDRESS_VALUE | rng.randrange(32),
                setup_write=True,
                setup_kind=rng.randrange(3),
                setup_address=rng.randrange(8),
                setup_data=rng.randrange(0x4000),
                probe_address=probe,
            )
        else:
            emit(probe_address=probe)
        if index != 0 and index % 997 == 0:
            emit(reset=True, probe_address=probe)

    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--random-count", type=int, default=50_000)
    parser.add_argument(
        "--seed",
        type=lambda value: int(value, 0),
        default=0x210021,
    )
    args = parser.parse_args()
    if args.random_count < 0:
        parser.error("--random-count cannot be negative")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    lines = generate_lines(args.random_count, args.seed)
    args.output.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(f"wrote {len(lines)} Type 21 stateful vectors to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
