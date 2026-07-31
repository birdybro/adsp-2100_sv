"""Deliberately partial ADSP-2100 disassembler with reserved-code reporting."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from tools.generators.validate_internal_move import (
    decode_internal_move,
    load_database as load_internal_move_database,
    validate_database as validate_internal_move_database,
)
from tools.generators.validate_mode_control import (
    decode_actions as decode_mode_control_actions,
    load_database as load_mode_control_database,
    validate_database as validate_mode_control_database,
)
from tools.generators.validate_modify_address import (
    decode_selection as decode_modify_address_selection,
    load_database as load_modify_address_database,
    validate_database as validate_modify_address_database,
)
from tools.generators.validate_isa import classify_opcode, load_database, validate_database
from tools.generators.validate_isa_fields import (
    load_database as load_isa_fields_database,
    validate_database as validate_isa_fields_database,
)


@dataclass(frozen=True)
class Disassembly:
    opcode: int
    text: str
    classification: str
    implemented: bool


@lru_cache(maxsize=1)
def _internal_move_database() -> dict[str, object]:
    database = load_internal_move_database()
    validate_internal_move_database(database)
    return database


def _try_disassemble_internal_move(
    opcode: int,
) -> Disassembly | None:
    decoded = decode_internal_move(_internal_move_database(), opcode)
    if decoded is None:
        return None
    if not decoded["legal"]:
        return Disassembly(
            opcode=opcode,
            text=f".WORD 0x{opcode:06x};",
            classification="RESERVED_TYPE_17_SUBENCODING",
            implemented=False,
        )
    return Disassembly(
        opcode=opcode,
        text=(
            f"{decoded['destination_register']} = "
            f"{decoded['source_register']};"
        ),
        classification="TYPE_17_BOUNDED_EXECUTION",
        implemented=True,
    )


@lru_cache(maxsize=1)
def _dreg_code_to_name() -> dict[int, str]:
    database = load_isa_fields_database()
    validate_isa_fields_database(database)
    table = next(item for item in database["tables"] if item["id"] == "DREG")
    return {entry["code"]: entry["name"] for entry in table["values"]}


def _disassemble_dreg_immediate(opcode: int) -> str:
    register = _dreg_code_to_name()[opcode & 0xF]
    data = (opcode >> 4) & 0xFFFF
    return f"{register} = 0x{data:04x};"


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


def _disassemble_modify_address(opcode: int) -> str:
    database = load_modify_address_database()
    validate_modify_address_database(database)
    selection = decode_modify_address_selection(database, opcode)
    if selection is None:
        raise ValueError("opcode is not original Type 21")
    return (
        f"MODIFY (I{selection['i_address']}, "
        f"M{selection['m_address']});"
    )


def disassemble_word(opcode: int) -> Disassembly:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    database = load_database()
    validate_database(database)
    internal_move = _try_disassemble_internal_move(opcode)
    if internal_move is not None:
        return internal_move
    for instruction in database["instructions"]:
        mask = int(instruction["opcode_mask"], 16)
        value = int(instruction["opcode_value"], 16)
        if opcode & mask == value:
            text = instruction["algebraic_assembly_syntax"]
            if instruction["id"] == "MODE-CONTROL-TYPE-18":
                text = _disassemble_mode_control(opcode)
            elif instruction["id"] == "MODIFY-ADDRESS-TYPE-21":
                text = _disassemble_modify_address(opcode)
            elif instruction["id"] == "LOAD-DREG-IMMEDIATE-TYPE-6":
                text = _disassemble_dreg_immediate(opcode)
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
