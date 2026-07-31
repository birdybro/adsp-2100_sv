"""Independent original ADSP-2100 Type 26 stack-control action decoder.

This module decodes requested actions only. Actual stack underflow behavior is
still OQ-013 and belongs to the stateful stack models, not to instruction
decode.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


STACK_CONTROL_MASK = 0xFFFFE0
STACK_CONTROL_VALUE = 0x040000


class StackControlStatusOperation(IntEnum):
    """Original two-bit SPP field, retaining both no-change encodings."""

    NO_CHANGE_ZERO = 0
    NO_CHANGE_ONE = 1
    PUSH = 2
    POP = 3

    @property
    def changes_stack(self) -> bool:
        return self in {
            StackControlStatusOperation.PUSH,
            StackControlStatusOperation.POP,
        }


@dataclass(frozen=True)
class StackControlActions:
    """All parallel actions requested by one classified Type 26 word."""

    status_operation: StackControlStatusOperation
    count_pop: bool
    loop_pop: bool
    pc_pop: bool

    @property
    def has_effect(self) -> bool:
        return (
            self.status_operation.changes_stack
            or self.count_pop
            or self.loop_pop
            or self.pc_pop
        )

    @property
    def assembly_components(self) -> tuple[str, ...]:
        components: list[str] = []
        if self.status_operation is StackControlStatusOperation.PUSH:
            components.append("PUSH STS")
        elif self.status_operation is StackControlStatusOperation.POP:
            components.append("POP STS")
        if self.count_pop:
            components.append("POP CNTR")
        if self.pc_pop:
            components.append("POP PC")
        if self.loop_pop:
            components.append("POP LOOP")
        return tuple(components)


def decode_stack_control(opcode: int) -> StackControlActions | None:
    """Return Type 26 actions or ``None`` for every other 24-bit word."""

    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    if opcode & STACK_CONTROL_MASK != STACK_CONTROL_VALUE:
        return None
    return StackControlActions(
        status_operation=StackControlStatusOperation(opcode & 0x3),
        count_pop=bool(opcode & 0x4),
        loop_pop=bool(opcode & 0x8),
        pc_pop=bool(opcode & 0x10),
    )
