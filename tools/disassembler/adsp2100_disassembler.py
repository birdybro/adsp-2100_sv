"""Deliberately partial ADSP-2100 disassembler with reserved-code reporting."""

from __future__ import annotations

from dataclasses import dataclass

from tools.generators.validate_mode_control import (
    decode_actions as decode_mode_control_actions,
    load_database as load_mode_control_database,
    validate_database as validate_mode_control_database,
)
from tools.generators.validate_isa import classify_opcode, load_database, validate_database


@dataclass(frozen=True)
class Disassembly:
    opcode: int
    text: str
    classification: str
    implemented: bool


def _disassemble_mode_control(opcode: int) -> str:
    database = load_mode_control_database()
    validate_mode_control_database(database)
    actions = decode_mode_control_actions(database, opcode)
    if actions is None:
        raise ValueError("opcode is not original Type 18")
    if actions["has_no_change_one_alias"] or not actions["has_effect"]:
        return f".WORD 0x{opcode:06x};"

    target_to_field = database["assembly"]["target_to_field"]
    field_to_key = {
        "SR_MCC": "sr",
        "BR_MCC": "br",
        "OL_MCC": "ol",
        "AS_MCC": "ar",
    }
    components: list[str] = []
    for target in database["assembly"]["clause_order"]:
        action = actions[field_to_key[target_to_field[target]]]
        if action == "DEACTIVATE":
            components.append(f"DIS {target}")
        elif action == "ACTIVATE":
            components.append(f"ENA {target}")
    return ", ".join(components) + ";"


def disassemble_word(opcode: int) -> Disassembly:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    database = load_database()
    validate_database(database)
    for instruction in database["instructions"]:
        mask = int(instruction["opcode_mask"], 16)
        value = int(instruction["opcode_value"], 16)
        if opcode & mask == value:
            text = instruction["algebraic_assembly_syntax"]
            if instruction["id"] == "MODE-CONTROL-TYPE-18":
                text = _disassemble_mode_control(opcode)
            return Disassembly(
                opcode=opcode,
                text=text,
                classification=f"TYPE_{classify_opcode(database, opcode)[0]['original_type']:02d}",
                implemented=True,
            )

    classes = classify_opcode(database, opcode)
    if classes:
        encoding_class = classes[0]
        if encoding_class["name"] == "reserved":
            classification = f"RESERVED_TYPE_{encoding_class['original_type']:02d}"
        else:
            classification = f"UNIMPLEMENTED_TYPE_{encoding_class['original_type']:02d}"
    else:
        classification = database["unshown_encoding_policy"]["classification"]
    return Disassembly(
        opcode=opcode,
        text=f".WORD 0x{opcode:06x};",
        classification=classification,
        implemented=False,
    )
