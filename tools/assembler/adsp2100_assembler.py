"""Deliberately partial ADSP-2100 assembler driven by verified ISA entries."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import re

from tools.generators.validate_internal_move import (
    load_database as load_internal_move_database,
    register_map as internal_move_register_map,
    validate_database as validate_internal_move_database,
)
from tools.generators.validate_condition_codes import (
    load_database as load_condition_database,
    validate_database as validate_condition_database,
)
from tools.generators.validate_mode_control import (
    load_database as load_mode_control_database,
    validate_database as validate_mode_control_database,
)
from tools.generators.validate_modify_address import (
    load_database as load_modify_address_database,
    validate_database as validate_modify_address_database,
)
from tools.generators.validate_isa import load_database, validate_database
from tools.generators.validate_isa_fields import (
    load_database as load_isa_fields_database,
    validate_database as validate_isa_fields_database,
)


class AssemblyError(ValueError):
    pass


@dataclass(frozen=True)
class AssembledWord:
    value: int

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 0xFFFFFF:
            raise ValueError("program word must fit 24 bits")

    def to_bytes(self) -> bytes:
        """Return a project-local three-byte big-endian program-word stream."""

        return self.value.to_bytes(3, byteorder="big")


def _normalize_statement(source: str) -> str:
    without_c_comments = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    without_line_comments = without_c_comments.split("//", 1)[0]
    statement = without_line_comments.strip()
    if statement.endswith(";"):
        statement = statement[:-1].rstrip()
    if not statement:
        raise AssemblyError("empty statement")
    return " ".join(statement.upper().split())


def exact_mnemonics() -> dict[str, int]:
    database = load_database()
    validate_database(database)
    result: dict[str, int] = {}
    for instruction in database["instructions"]:
        if instruction["opcode_mask"] != "0xffffff":
            continue
        syntax = _normalize_statement(instruction["algebraic_assembly_syntax"])
        value = int(instruction["opcode_value"], 16)
        if syntax in result:
            raise AssemblyError(f"ambiguous exact syntax in ISA database: {syntax}")
        result[syntax] = value
    return result


def _assemble_raw_word(statement: str) -> int | None:
    match = re.fullmatch(r"\.WORD\s+(?:0X([0-9A-F]+)|H#([0-9A-F]+))", statement)
    if match is None:
        return None
    value = int(match.group(1) or match.group(2), 16)
    if not 0 <= value <= 0xFFFFFF:
        raise AssemblyError(".WORD value must fit one 24-bit program word")
    return value


@lru_cache(maxsize=1)
def _dreg_name_to_code() -> dict[str, int]:
    database = load_isa_fields_database()
    validate_isa_fields_database(database)
    table = next(item for item in database["tables"] if item["id"] == "DREG")
    return {entry["name"]: entry["code"] for entry in table["values"]}


def _assemble_dreg_immediate(statement: str) -> int | None:
    match = re.fullmatch(
        r"([A-Z][A-Z0-9]*)\s*=\s*(?:(?:0X|H#)([0-9A-F]+)|(-?[0-9]+))",
        statement,
    )
    if match is None:
        return None
    destination, hexadecimal, decimal = match.groups()
    registers = _dreg_name_to_code()
    if destination not in registers:
        return None
    value = int(hexadecimal, 16) if hexadecimal is not None else int(decimal, 10)
    if not -0x8000 <= value <= 0xFFFF:
        raise AssemblyError("Type 6 immediate must fit a 16-bit data word")
    return 0x400000 | ((value & 0xFFFF) << 4) | registers[destination]


_SHIFTER_XOP_CODES = {
    "SI": 0,
    "AR": 2,
    "MR0": 3,
    "MR1": 4,
    "MR2": 5,
    "SR0": 6,
    "SR1": 7,
}

_ALU_XOP_NAMES = (
    "AX0", "AX1", "AR", "MR0", "MR1", "MR2", "SR0", "SR1",
)
_MAC_XOP_NAMES = (
    "MX0", "MX1", "AR", "MR0", "MR1", "MR2", "SR0", "SR1",
)
_ALU_YOP_NAMES = ("AY0", "AY1", "AF", "0")
_MAC_YOP_NAMES = ("MY0", "MY1", "MF", "0")


def _format_compute_operation(z: int, amf: int, yop: int, xop: int) -> str | None:
    """Return the field-exact canonical algebraic form for a sourced AMF."""

    if not (0 <= z <= 1 and 1 <= amf <= 0x1F):
        return None
    if amf < 0x10:
        destination = "MF" if z else "MR"
        x = _MAC_XOP_NAMES[xop]
        y = _MAC_YOP_NAMES[yop]
        if yop == 3:
            if amf == 4 and xop == 0:
                return f"{destination} = 0"
            return None
        if amf <= 3:
            operation = ("", "", "MR + ", "MR - ")[amf]
            return f"{destination} = {operation}{x} * {y} (RND)"
        mode = ("SS", "SU", "US", "UU")[(amf - 4) & 3]
        if amf < 8:
            operation = ""
        elif amf < 12:
            operation = "MR + "
        else:
            operation = "MR - "
        return f"{destination} = {operation}{x} * {y} ({mode})"

    destination = "AF" if z else "AR"
    x = _ALU_XOP_NAMES[xop]
    y = _ALU_YOP_NAMES[yop]
    if amf in (0x10, 0x11, 0x14, 0x15, 0x18) and xop != 0:
        return None
    if amf in (0x1B, 0x1F) and yop != 0:
        return None
    expressions = {
        0x10: f"PASS {y}",
        0x11: f"{y} + 1",
        0x12: f"{x} + {y} + C",
        0x13: f"PASS {x}" if yop == 3 else f"{x} + {y}",
        0x14: f"NOT {y}",
        0x15: f"-{y}",
        0x16: f"{x} - {y} + C - 1",
        0x17: f"{x} - {y}",
        0x18: f"{y} - 1",
        0x19: f"-{x}" if yop == 3 else f"{y} - {x}",
        0x1A: f"{y} - {x} + C - 1",
        0x1B: f"NOT {x}",
        0x1C: f"{x} AND {y}",
        0x1D: f"{x} OR {y}",
        0x1E: f"{x} XOR {y}",
        0x1F: f"ABS {x}",
    }
    return f"{destination} = {expressions[amf]}"


@lru_cache(maxsize=1)
def _compute_operation_codes() -> dict[str, tuple[int, int, int, int]]:
    result: dict[str, tuple[int, int, int, int]] = {}
    for z in range(2):
        for amf in range(1, 0x20):
            for yop in range(4):
                for xop in range(8):
                    operation = _format_compute_operation(z, amf, yop, xop)
                    if operation is None:
                        continue
                    if operation in result:
                        raise AssemblyError(
                            f"ambiguous canonical computation: {operation}"
                        )
                    result[operation] = (z, amf, yop, xop)
    return result


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


def _assemble_compute_move(statement: str) -> int | None:
    if statement.count(",") != 1:
        return None
    computation, move = (clause.strip() for clause in statement.split(","))
    computation_fields = _compute_operation_codes().get(computation)
    parsed_move = re.fullmatch(
        r"([A-Z][A-Z0-9]*)\s*=\s*([A-Z][A-Z0-9]*)",
        move,
    )
    if computation_fields is None or parsed_move is None:
        return None
    destination_name, source_name = parsed_move.groups()
    registers = _dreg_name_to_code()
    if destination_name not in registers or source_name not in registers:
        return None
    z, amf, yop, xop = computation_fields
    destination = registers[destination_name]
    if _compute_move_destination_collision(z, amf, destination):
        raise AssemblyError(
            "Type 8 move destination collides with computation destination"
        )
    return (
        0x280000
        | (z << 18)
        | (amf << 13)
        | (yop << 11)
        | (xop << 8)
        | (destination << 4)
        | registers[source_name]
    )


@lru_cache(maxsize=1)
def _if_condition_codes() -> dict[str, int]:
    database = load_condition_database()
    validate_condition_database(database)
    return {
        entry["mnemonic"]: entry["code"]
        for entry in database["if_conditions"]
    }


@lru_cache(maxsize=1)
def _do_termination_codes() -> dict[str, int]:
    database = load_condition_database()
    validate_condition_database(database)
    return {
        entry["mnemonic"]: entry["code"]
        for entry in database["do_until_termination_conditions"]
    }


def _split_if_prefix(statement: str) -> tuple[int, str] | None:
    for mnemonic, code in sorted(
        _if_condition_codes().items(),
        key=lambda item: len(item[0]),
        reverse=True,
    ):
        prefix = f"IF {mnemonic} "
        if statement.startswith(prefix):
            return code, statement[len(prefix):]
    if statement.startswith("IF "):
        return None
    return 15, statement


def _parse_register_shifter(body: str) -> tuple[int, int] | None:
    shift = re.fullmatch(
        r"SR\s*=\s*(SR OR\s+)?(ASHIFT|LSHIFT|NORM)\s+"
        r"([A-Z][A-Z0-9]*)\s+\((HI|LO)\)",
        body,
    )
    if shift is not None:
        combine_or, operation, source, reference = shift.groups()
        if source not in _SHIFTER_XOP_CODES:
            return None
        sf = {"LSHIFT": 0, "ASHIFT": 4, "NORM": 8}[operation]
        if reference == "LO":
            sf |= 2
        if combine_or is not None:
            sf |= 1
        return sf, _SHIFTER_XOP_CODES[source]

    exponent = re.fullmatch(
        r"SE\s*=\s*EXP\s+([A-Z][A-Z0-9]*)\s+\((HI|HIX|LO)\)",
        body,
    )
    if exponent is not None:
        source, reference = exponent.groups()
        if source not in _SHIFTER_XOP_CODES:
            return None
        sf = {"HI": 0xC, "HIX": 0xD, "LO": 0xE}[reference]
        return sf, _SHIFTER_XOP_CODES[source]

    expadj = re.fullmatch(
        r"SB\s*=\s*EXPADJ\s+([A-Z][A-Z0-9]*)",
        body,
    )
    if expadj is not None:
        source = expadj.group(1)
        if source not in _SHIFTER_XOP_CODES:
            return None
        return 0xF, _SHIFTER_XOP_CODES[source]
    return None


def _assemble_conditional_shift(statement: str) -> int | None:
    prefixed = _split_if_prefix(statement)
    if prefixed is None:
        return None
    condition, body = prefixed
    parsed = _parse_register_shifter(body)
    if parsed is None:
        return None
    sf, xop = parsed
    return 0x0E0000 | (sf << 11) | (xop << 8) | condition


def _assemble_conditional_compute(statement: str) -> int | None:
    """Assemble a canonical original Type 9 conditional ALU/MAC action."""

    if "," in statement:
        return None
    prefixed = _split_if_prefix(statement)
    if prefixed is None:
        return None
    condition, body = prefixed
    computation = _compute_operation_codes().get(body)
    if computation is None:
        return None
    z, amf, yop, xop = computation
    return (
        0x200000
        | (z << 18)
        | (amf << 13)
        | (yop << 11)
        | (xop << 8)
        | condition
    )


def _assemble_direct_jump(statement: str) -> int | None:
    """Assemble a bounded original Type 10 direct JUMP or CALL."""

    prefixed = _split_if_prefix(statement)
    if prefixed is None:
        return None
    condition, body = prefixed
    match = re.fullmatch(
        r"(JUMP|CALL)\s+(?:(?:0X|H#)([0-9A-F]+)|([0-9]+))",
        body,
    )
    if match is None:
        return None
    operation, hexadecimal, decimal = match.groups()
    address = int(hexadecimal, 16) if hexadecimal is not None else int(decimal, 10)
    if not 0 <= address <= 0x3FFF:
        raise AssemblyError("direct program address must fit 14 bits")
    call = operation == "CALL"
    if call and condition == 0xE:
        raise AssemblyError("conditional CALL NOT CE remains unresolved under OQ-012")
    return 0x180000 | (int(call) << 18) | (address << 4) | condition


def _assemble_indirect_jump(statement: str) -> int | None:
    """Assemble a bounded original Type 19 DAG2-indirect JUMP or CALL."""

    prefixed = _split_if_prefix(statement)
    if prefixed is None:
        return None
    condition, body = prefixed
    match = re.fullmatch(r"(JUMP|CALL)\s+\(\s*I([4-7])\s*\)", body)
    if match is None:
        return None
    operation, i_name = match.groups()
    call = operation == "CALL"
    if call and condition == 0xE:
        raise AssemblyError("conditional CALL NOT CE remains unresolved under OQ-012")
    i_local = int(i_name) - 4
    return 0x0B0000 | (i_local << 6) | (int(call) << 4) | condition


def _assemble_conditional_return(statement: str) -> int | None:
    """Assemble an original Type 20 conditional RTS or RTI."""

    prefixed = _split_if_prefix(statement)
    if prefixed is None:
        return None
    condition, body = prefixed
    if body not in ("RTS", "RTI"):
        return None
    return 0x0A0000 | (int(body == "RTI") << 4) | condition


def _assemble_conditional_trap(statement: str) -> int | None:
    """Assemble an original Type 22 conditional TRAP."""

    prefixed = _split_if_prefix(statement)
    if prefixed is None:
        return None
    condition, body = prefixed
    if body != "TRAP":
        return None
    return 0x080000 | condition


def _assemble_divide_sign(statement: str) -> int | None:
    """Assemble a source-closed original Type 24 DIVS primitive."""

    match = re.fullmatch(
        r"DIVS\s+(AY1|AF)\s*,\s*(AX0|AX1|AR|MR0|MR1|MR2|SR0|SR1)",
        statement,
    )
    if match is None:
        return None
    upper, divisor = match.groups()
    yop = {"AY1": 1, "AF": 2}[upper]
    xop = _ALU_XOP_NAMES.index(divisor)
    return 0x060000 | (yop << 11) | (xop << 8)


def _assemble_divide_quotient(statement: str) -> int | None:
    """Assemble a source-closed original Type 23 DIVQ primitive."""

    match = re.fullmatch(
        r"DIVQ\s+(AX0|AX1|AR|MR0|MR1|MR2|SR0|SR1)",
        statement,
    )
    if match is None:
        return None
    xop = _ALU_XOP_NAMES.index(match.group(1))
    return 0x071000 | (xop << 8)


def _assemble_do_until(statement: str) -> int | None:
    """Assemble an original Type 11 hardware-loop setup instruction."""

    match = re.fullmatch(
        r"DO\s+(?:(?:0X|H#)([0-9A-F]+)|([0-9]+))"
        r"(?:\s+UNTIL\s+(.+))?",
        statement,
    )
    if match is None:
        return None
    hexadecimal, decimal, mnemonic = match.groups()
    address = int(hexadecimal, 16) if hexadecimal is not None else int(decimal, 10)
    if not 0 <= address <= 0x3FFF:
        raise AssemblyError("DO terminal program address must fit 14 bits")
    if mnemonic is None:
        termination = 15
    else:
        terminations = _do_termination_codes()
        if mnemonic not in terminations:
            raise AssemblyError(f"unknown DO UNTIL termination condition: {mnemonic}")
        termination = terminations[mnemonic]
    return 0x140000 | (address << 4) | termination


def _shift_move_destination_collision(sf: int, destination: int) -> bool:
    if sf <= 0xB:
        return destination in (14, 15)
    return sf <= 0xE and destination == 9


def _assemble_shift_move(statement: str) -> int | None:
    if statement.count(",") != 1:
        return None
    computation, move = (clause.strip() for clause in statement.split(","))
    parsed_shifter = _parse_register_shifter(computation)
    parsed_move = re.fullmatch(
        r"([A-Z][A-Z0-9]*)\s*=\s*([A-Z][A-Z0-9]*)",
        move,
    )
    if parsed_shifter is None or parsed_move is None:
        return None
    destination_name, source_name = parsed_move.groups()
    registers = _dreg_name_to_code()
    if destination_name not in registers or source_name not in registers:
        return None
    sf, xop = parsed_shifter
    destination = registers[destination_name]
    source = registers[source_name]
    if _shift_move_destination_collision(sf, destination):
        raise AssemblyError(
            "Type 14 move destination collides with shifter destination"
        )
    return (
        0x100000
        | (sf << 11)
        | (xop << 8)
        | (destination << 4)
        | source
    )


def _assemble_immediate_shift(statement: str) -> int | None:
    match = re.fullmatch(
        r"SR\s*=\s*(SR OR\s+)?(A|L)SHIFT\s+"
        r"([A-Z][A-Z0-9]*)\s+BY\s+"
        r"(?:(?:0X|H#)([0-9A-F]+)|(-?[0-9]+))\s+"
        r"\((HI|LO)\)",
        statement,
    )
    if match is None:
        return None
    combine_or, operation, source, hexadecimal, decimal, reference = (
        match.groups()
    )
    if source not in _SHIFTER_XOP_CODES:
        return None
    if hexadecimal is not None:
        exponent = int(hexadecimal, 16)
        if not 0 <= exponent <= 0xFF:
            raise AssemblyError("Type 15 hexadecimal exponent must fit 8 bits")
    else:
        exponent = int(decimal, 10)
        if not -128 <= exponent <= 127:
            raise AssemblyError("Type 15 decimal exponent must be signed 8-bit")
    sf = 4 if operation == "A" else 0
    if reference == "LO":
        sf |= 2
    if combine_or is not None:
        sf |= 1
    return (
        0x0F0000
        | (sf << 11)
        | (_SHIFTER_XOP_CODES[source] << 8)
        | (exponent & 0xFF)
    )


@lru_cache(maxsize=1)
def _internal_move_tables() -> tuple[int, dict[str, int], dict[str, int]]:
    database = load_internal_move_database()
    validate_internal_move_database(database)
    registers = internal_move_register_map()
    readable = {
        metadata["register"]: code
        for code, metadata in registers.items()
    }
    writable = {
        name: code
        for name, code in readable.items()
        if name != "SSTAT"
    }
    return int(database["instruction"]["opcode_value"], 16), readable, writable


def _assemble_internal_move(statement: str) -> int | None:
    match = re.fullmatch(
        r"([A-Z][A-Z0-9]*)\s*=\s*([A-Z][A-Z0-9]*)",
        statement,
    )
    if match is None:
        return None
    destination_name, source_name = match.groups()
    opcode, readable, writable = _internal_move_tables()
    if destination_name == "SSTAT":
        raise AssemblyError("SSTAT is read-only")
    if destination_name not in writable or source_name not in readable:
        return None
    destination_code = writable[destination_name]
    source_code = readable[source_name]
    return (
        opcode
        | ((destination_code >> 4) << 10)
        | ((source_code >> 4) << 8)
        | ((destination_code & 0xF) << 4)
        | (source_code & 0xF)
    )


def _assemble_mode_control(statement: str) -> int | None:
    clauses = [clause.strip() for clause in statement.split(",")]
    parsed: list[tuple[str, str]] = []
    for clause in clauses:
        match = re.fullmatch(r"(ENA|DIS)\s+([A-Z_]+)", clause)
        if match is None:
            return None
        parsed.append((match.group(1), match.group(2)))

    database = load_mode_control_database()
    validate_mode_control_database(database)
    target_to_field = database["assembly"]["target_to_field"]
    if any(target not in target_to_field for _, target in parsed):
        return None
    targets = [target for _, target in parsed]
    if len(set(targets)) != len(targets):
        raise AssemblyError("MODE CONTROL target may appear only once")

    fields = {field["id"]: field for field in database["fields"]}
    opcode = int(database["instruction"]["opcode_value"], 16)
    action_code = {"DIS": 2, "ENA": 3}
    for action, target in parsed:
        field = fields[target_to_field[target]]
        opcode |= action_code[action] << field["lsb"]
    return opcode


def _assemble_modify_address(statement: str) -> int | None:
    match = re.fullmatch(
        r"MODIFY\s*\(\s*I([0-7])\s*,\s*M([0-7])\s*\)",
        statement,
    )
    if match is None:
        return None
    i_address = int(match.group(1))
    m_address = int(match.group(2))
    if i_address // 4 != m_address // 4:
        raise AssemblyError("MODIFY I and M registers must use the same DAG")

    database = load_modify_address_database()
    validate_modify_address_database(database)
    opcode = int(database["instruction"]["opcode_value"], 16)
    dag = i_address // 4
    return (
        opcode
        | (dag << 4)
        | ((i_address & 0x3) << 2)
        | (m_address & 0x3)
    )


def assemble_statement(source: str) -> AssembledWord:
    statement = _normalize_statement(source)
    raw_word = _assemble_raw_word(statement)
    if raw_word is not None:
        return AssembledWord(raw_word)
    # Type 9 precedes the general DREG-immediate parser so its canonical
    # `AR = -0` negate-zero spelling round-trips to the source opcode.
    conditional_compute = _assemble_conditional_compute(statement)
    if conditional_compute is not None:
        return AssembledWord(conditional_compute)
    direct_jump = _assemble_direct_jump(statement)
    if direct_jump is not None:
        return AssembledWord(direct_jump)
    indirect_jump = _assemble_indirect_jump(statement)
    if indirect_jump is not None:
        return AssembledWord(indirect_jump)
    conditional_return = _assemble_conditional_return(statement)
    if conditional_return is not None:
        return AssembledWord(conditional_return)
    conditional_trap = _assemble_conditional_trap(statement)
    if conditional_trap is not None:
        return AssembledWord(conditional_trap)
    divide_quotient = _assemble_divide_quotient(statement)
    if divide_quotient is not None:
        return AssembledWord(divide_quotient)
    divide_sign = _assemble_divide_sign(statement)
    if divide_sign is not None:
        return AssembledWord(divide_sign)
    do_until = _assemble_do_until(statement)
    if do_until is not None:
        return AssembledWord(do_until)
    dreg_immediate = _assemble_dreg_immediate(statement)
    if dreg_immediate is not None:
        return AssembledWord(dreg_immediate)
    immediate_shift = _assemble_immediate_shift(statement)
    if immediate_shift is not None:
        return AssembledWord(immediate_shift)
    conditional_shift = _assemble_conditional_shift(statement)
    if conditional_shift is not None:
        return AssembledWord(conditional_shift)
    compute_move = _assemble_compute_move(statement)
    if compute_move is not None:
        return AssembledWord(compute_move)
    shift_move = _assemble_shift_move(statement)
    if shift_move is not None:
        return AssembledWord(shift_move)
    internal_move = _assemble_internal_move(statement)
    if internal_move is not None:
        return AssembledWord(internal_move)
    mode_control = _assemble_mode_control(statement)
    if mode_control is not None:
        return AssembledWord(mode_control)
    modify_address = _assemble_modify_address(statement)
    if modify_address is not None:
        return AssembledWord(modify_address)
    mnemonics = exact_mnemonics()
    if statement not in mnemonics:
        raise AssemblyError(
            f"unsupported or unverified ADSP-2100 statement: {statement!r}"
        )
    return AssembledWord(mnemonics[statement])
