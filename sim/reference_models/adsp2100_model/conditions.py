"""Source-derived condition logic for the original ADSP-2100 model.

The implementation is intentionally independent from the machine-readable
condition database and the SystemVerilog expression tree. Tests tie all three
representations to hand-reviewed primary-source fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConditionInputs:
    """Raw status inputs named by the original condition-logic tables."""

    az: bool = False
    an: bool = False
    av: bool = False
    ac: bool = False
    as_flag: bool = False
    mv: bool = False
    not_counter_expired: bool = False


IF_CONDITION_MNEMONICS = (
    "EQ",
    "NE",
    "GT",
    "LE",
    "LT",
    "GE",
    "AV",
    "NOT AV",
    "AC",
    "NOT AC",
    "NEG",
    "POS",
    "MV",
    "NOT MV",
    "NOT CE",
    "TRUE",
)

DO_TERMINATION_MNEMONICS = (
    "NE",
    "EQ",
    "LE",
    "GT",
    "GE",
    "LT",
    "NOT AV",
    "AV",
    "NOT AC",
    "AC",
    "POS",
    "NEG",
    "NOT MV",
    "MV",
    "CE",
    "FOREVER",
)


def evaluate_if_condition(code: int, inputs: ConditionInputs) -> bool:
    """Evaluate the 4-bit standard IF condition against prior-cycle status."""

    if not 0 <= code < 16:
        raise ValueError("condition code must fit 4 bits")

    signed_less = inputs.an != inputs.av
    predicates = (
        inputs.az,
        not inputs.az,
        not (signed_less or inputs.az),
        signed_less or inputs.az,
        signed_less,
        not signed_less,
        inputs.av,
        not inputs.av,
        inputs.ac,
        not inputs.ac,
        inputs.as_flag,
        not inputs.as_flag,
        inputs.mv,
        not inputs.mv,
        inputs.not_counter_expired,
        True,
    )
    return predicates[code]


def evaluate_do_termination(code: int, inputs: ConditionInputs) -> bool:
    """Evaluate whether a DO UNTIL loop terminates at its end instruction.

    The manual states that DO UNTIL uses the inverse of the IF predicate at the
    same encoded field value. Thus code 0 means UNTIL NE while IF code 0 means
    EQ, and code 15 (FOREVER) never terminates.
    """

    return not evaluate_if_condition(code, inputs)
