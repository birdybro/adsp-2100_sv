"""Original ADSP-2100 eight-state logical processor-cycle labels."""

from __future__ import annotations

from enum import IntEnum


class LogicalPhase(IntEnum):
    """Externally observable processor states numbered as in the manuals."""

    STATE_1 = 0
    STATE_2 = 1
    STATE_3 = 2
    STATE_4 = 3
    STATE_5 = 4
    STATE_6 = 5
    STATE_7 = 6
    STATE_8 = 7
