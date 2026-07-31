"""Deliberately partial ADSP-2100 disassembler with reserved-code reporting."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from tools.generators.validate_internal_move import (
    decode_internal_move,
    load_database as load_internal_move_database,
    validate_database as validate_internal_move_database,
)
from tools.generators.validate_condition_codes import (
    load_database as load_condition_database,
    validate_database as validate_condition_database,
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
from tools.assembler.adsp2100_assembler import _format_compute_operation


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


_SHIFTER_XOP_NAMES = {
    0: "SI",
    2: "AR",
    3: "MR0",
    4: "MR1",
    5: "MR2",
    6: "SR0",
    7: "SR1",
}


@lru_cache(maxsize=1)
def _if_condition_names() -> dict[int, str]:
    database = load_condition_database()
    validate_condition_database(database)
    return {
        entry["code"]: entry["mnemonic"]
        for entry in database["if_conditions"]
    }


def _format_register_shifter(sf: int, xop: int) -> str:
    source = _SHIFTER_XOP_NAMES[xop]
    if sf <= 0xB:
        operation = ("LSHIFT", "ASHIFT", "NORM")[sf >> 2]
        reference = "LO" if sf & 2 else "HI"
        combine_or = "SR OR " if sf & 1 else ""
        return f"SR = {combine_or}{operation} {source} ({reference})"
    if sf <= 0xE:
        reference = ("HI", "HIX", "LO")[sf - 0xC]
        return f"SE = EXP {source} ({reference})"
    return f"SB = EXPADJ {source}"


def _shift_move_destination_collision(sf: int, destination: int) -> bool:
    if sf <= 0xB:
        return destination in (14, 15)
    return sf <= 0xE and destination == 9


def _try_disassemble_shift_move(opcode: int) -> Disassembly | None:
    if opcode & 0xFF0000 != 0x100000:
        return None
    if opcode & 0x008000:
        classification = "UNVERIFIED_TYPE_14_UNUSED_X"
    else:
        sf = (opcode >> 11) & 0xF
        xop = (opcode >> 8) & 0x7
        destination = (opcode >> 4) & 0xF
        if xop not in _SHIFTER_XOP_NAMES:
            classification = "UNVERIFIED_TYPE_14_XOP"
        elif _shift_move_destination_collision(sf, destination):
            classification = "UNSUPPORTED_TYPE_14_DESTINATION_COLLISION"
        else:
            names = _dreg_code_to_name()
            text = (
                f"{_format_register_shifter(sf, xop)}, "
                f"{names[destination]} = {names[opcode & 0xF]};"
            )
            return Disassembly(
                opcode=opcode,
                text=text,
                classification="TYPE_14_BOUNDED_EXECUTION",
                implemented=True,
            )
    return Disassembly(
        opcode=opcode,
        text=f".WORD 0x{opcode:06x};",
        classification=classification,
        implemented=False,
    )


def _compute_move_destination_collision(
    z: int,
    amf: int,
    destination: int,
) -> bool:
    if z:
        return False
    if amf >= 0x10:
        return destination == 0xA
    return destination in (0xB, 0xC, 0xD)


def _try_disassemble_compute_move(opcode: int) -> Disassembly | None:
    if opcode & 0xF80000 != 0x280000:
        return None
    z = (opcode >> 18) & 1
    amf = (opcode >> 13) & 0x1F
    yop = (opcode >> 11) & 3
    xop = (opcode >> 8) & 7
    destination = (opcode >> 4) & 0xF
    if amf == 0:
        classification = "UNVERIFIED_TYPE_08_AMF_ZERO"
        implemented = False
        text = f".WORD 0x{opcode:06x};"
    elif _compute_move_destination_collision(z, amf, destination):
        classification = "UNSUPPORTED_TYPE_08_DESTINATION_COLLISION"
        implemented = False
        text = f".WORD 0x{opcode:06x};"
    else:
        computation = _format_compute_operation(z, amf, yop, xop)
        if computation is None:
            classification = "TYPE_08_BOUNDED_ALIAS"
            implemented = True
            text = f".WORD 0x{opcode:06x};"
        else:
            names = _dreg_code_to_name()
            classification = "TYPE_08_BOUNDED_EXECUTION"
            implemented = True
            text = (
                f"{computation}, {names[destination]} = "
                f"{names[opcode & 0xF]};"
            )
    return Disassembly(opcode, text, classification, implemented)


def _try_disassemble_conditional_compute(opcode: int) -> Disassembly | None:
    if opcode & 0xF800F0 != 0x200000:
        return None
    z = (opcode >> 18) & 1
    amf = (opcode >> 13) & 0x1F
    yop = (opcode >> 11) & 3
    xop = (opcode >> 8) & 7
    condition = opcode & 0xF
    if amf == 0:
        return Disassembly(
            opcode=opcode,
            text=f".WORD 0x{opcode:06x};",
            classification="TYPE_09_BOUNDED_NOP_ALIAS",
            implemented=True,
        )
    computation = _format_compute_operation(z, amf, yop, xop)
    if computation is None:
        return Disassembly(
            opcode=opcode,
            text=f".WORD 0x{opcode:06x};",
            classification="TYPE_09_BOUNDED_ALIAS",
            implemented=True,
        )
    prefix = "" if condition == 15 else f"IF {_if_condition_names()[condition]} "
    return Disassembly(
        opcode=opcode,
        text=f"{prefix}{computation};",
        classification="TYPE_09_BOUNDED_EXECUTION",
        implemented=True,
    )


def _try_disassemble_conditional_shift(opcode: int) -> Disassembly | None:
    if opcode & 0xFF80F0 != 0x0E0000:
        return None
    sf = (opcode >> 11) & 0xF
    xop = (opcode >> 8) & 0x7
    condition = opcode & 0xF
    if xop not in _SHIFTER_XOP_NAMES:
        return Disassembly(
            opcode=opcode,
            text=f".WORD 0x{opcode:06x};",
            classification="UNVERIFIED_TYPE_16_SUBENCODING",
            implemented=False,
        )
    prefix = "" if condition == 15 else f"IF {_if_condition_names()[condition]} "
    text = f"{prefix}{_format_register_shifter(sf, xop)};"
    return Disassembly(
        opcode=opcode,
        text=text,
        classification="TYPE_16_BOUNDED_EXECUTION",
        implemented=True,
    )


def _try_disassemble_immediate_shift(opcode: int) -> Disassembly | None:
    if opcode & 0xFF8000 != 0x0F0000:
        return None
    sf = (opcode >> 11) & 0xF
    xop = (opcode >> 8) & 0x7
    if sf > 7 or xop not in _SHIFTER_XOP_NAMES:
        return Disassembly(
            opcode=opcode,
            text=f".WORD 0x{opcode:06x};",
            classification="UNVERIFIED_TYPE_15_SUBENCODING",
            implemented=False,
        )
    operation = "ASHIFT" if sf & 4 else "LSHIFT"
    reference = "LO" if sf & 2 else "HI"
    combine_or = "SR OR " if sf & 1 else ""
    exponent = opcode & 0xFF
    signed_exponent = exponent - 256 if exponent & 0x80 else exponent
    return Disassembly(
        opcode=opcode,
        text=(
            f"SR = {combine_or}{operation} {_SHIFTER_XOP_NAMES[xop]} "
            f"BY {signed_exponent} ({reference});"
        ),
        classification="TYPE_15_BOUNDED_EXECUTION",
        implemented=True,
    )


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
    conditional_compute = _try_disassemble_conditional_compute(opcode)
    if conditional_compute is not None:
        return conditional_compute
    compute_move = _try_disassemble_compute_move(opcode)
    if compute_move is not None:
        return compute_move
    shift_move = _try_disassemble_shift_move(opcode)
    if shift_move is not None:
        return shift_move
    internal_move = _try_disassemble_internal_move(opcode)
    if internal_move is not None:
        return internal_move
    immediate_shift = _try_disassemble_immediate_shift(opcode)
    if immediate_shift is not None:
        return immediate_shift
    conditional_shift = _try_disassemble_conditional_shift(opcode)
    if conditional_shift is not None:
        return conditional_shift
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
