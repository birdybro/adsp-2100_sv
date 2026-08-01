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
from tools.generators.validate_direct_dm import (
    load_database as load_direct_dm_database,
    register_map as direct_dm_register_map,
    validate_database as validate_direct_dm_database,
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


def _split_top_level_clauses(statement: str) -> list[str]:
    """Split multifunction clauses without splitting I/M argument pairs."""

    clauses: list[str] = []
    start = 0
    depth = 0
    for index, character in enumerate(statement):
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth < 0:
                return []
        elif character == "," and depth == 0:
            clauses.append(statement[start:index].strip())
            start = index + 1
    if depth != 0:
        return []
    clauses.append(statement[start:].strip())
    return clauses


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


def _assemble_dm_write_immediate(statement: str) -> int | None:
    match = re.fullmatch(
        r"DM\s*\(\s*I([0-7])\s*,\s*M([0-7])\s*\)\s*=\s*"
        r"(?:(?:0X|H#)([0-9A-F]+)|(-?[0-9]+))",
        statement,
    )
    if match is None:
        return None
    i_address = int(match.group(1))
    m_address = int(match.group(2))
    if i_address // 4 != m_address // 4:
        raise AssemblyError("Type 2 I and M registers must use the same DAG")
    hexadecimal, decimal = match.group(3), match.group(4)
    value = int(hexadecimal, 16) if hexadecimal is not None else int(decimal, 10)
    if not -0x8000 <= value <= 0xFFFF:
        raise AssemblyError("Type 2 immediate must fit a 16-bit data word")
    dag = i_address // 4
    return (
        0xA00000
        | (dag << 20)
        | ((value & 0xFFFF) << 4)
        | ((i_address & 3) << 2)
        | (m_address & 3)
    )


@lru_cache(maxsize=1)
def _direct_dm_tables() -> tuple[int, dict[str, int], dict[str, int]]:
    database = load_direct_dm_database()
    validate_direct_dm_database(database)
    registers = direct_dm_register_map()
    readable = {
        metadata["register"]: code for code, metadata in registers.items()
    }
    writable = {
        name: code for name, code in readable.items() if name != "SSTAT"
    }
    return int(database["instruction"]["opcode_value"], 16), readable, writable


def _parse_direct_dm_address(hexadecimal: str | None, decimal: str | None) -> int:
    value = int(hexadecimal, 16) if hexadecimal is not None else int(decimal, 10)
    if not 0 <= value <= 0x3FFF:
        raise AssemblyError("Type 3 direct DM address must fit 14 bits")
    return value


def _assemble_direct_dm(statement: str) -> int | None:
    read = re.fullmatch(
        r"([A-Z][A-Z0-9]*)\s*=\s*DM\(\s*"
        r"(?:(?:0X|H#)([0-9A-F]+)|([0-9]+))\s*\)",
        statement,
    )
    write = re.fullmatch(
        r"DM\(\s*(?:(?:0X|H#)([0-9A-F]+)|([0-9]+))\s*\)\s*=\s*"
        r"([A-Z][A-Z0-9]*)",
        statement,
    )
    opcode, readable, writable = _direct_dm_tables()
    if read is not None:
        register_name, hexadecimal, decimal = read.groups()
        if register_name == "SSTAT":
            raise AssemblyError("SSTAT is read-only")
        if register_name not in writable:
            return None
        address = _parse_direct_dm_address(hexadecimal, decimal)
        register_code = writable[register_name]
        direction = 0
    elif write is not None:
        hexadecimal, decimal, register_name = write.groups()
        if register_name not in readable:
            return None
        address = _parse_direct_dm_address(hexadecimal, decimal)
        register_code = readable[register_name]
        direction = 1
    else:
        return None
    return (
        opcode | (direction << 20) | ((register_code >> 4) << 18)
        | (address << 4) | (register_code & 0xF)
    )


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


def _assemble_compute_dm(statement: str) -> int | None:
    """Assemble the source-closed original Type 4 action forms."""

    read = re.fullmatch(
        r"(?:(.+)\s*,\s*)?([A-Z][A-Z0-9]*)\s*=\s*"
        r"DM\s*\(\s*I([0-7])\s*,\s*M([0-7])\s*\)",
        statement,
    )
    write = re.fullmatch(
        r"DM\s*\(\s*I([0-7])\s*,\s*M([0-7])\s*\)\s*=\s*"
        r"([A-Z][A-Z0-9]*)(?:\s*,\s*(.+))?",
        statement,
    )
    if read is None and write is None:
        return None

    registers = _dreg_name_to_code()
    if read is not None:
        computation, register_name, i_text, m_text = read.groups()
        write_direction = 0
    else:
        assert write is not None
        i_text, m_text, register_name, computation = write.groups()
        write_direction = 1
    if register_name not in registers:
        return None

    i_address = int(i_text)
    m_address = int(m_text)
    if i_address // 4 != m_address // 4:
        raise AssemblyError("Type 4 I and M registers must use the same DAG")

    if computation is None:
        z, amf, yop, xop = 0, 0, 0, 0
    else:
        computation_fields = _compute_operation_codes().get(computation)
        if computation_fields is None:
            return None
        z, amf, yop, xop = computation_fields

    register = registers[register_name]
    if not write_direction and amf != 0 and _compute_move_destination_collision(
        z,
        amf,
        register,
    ):
        raise AssemblyError(
            "Type 4 read destination collides with computation destination"
        )

    return (
        0x600000
        | ((i_address // 4) << 20)
        | (write_direction << 19)
        | (z << 18)
        | (amf << 13)
        | (yop << 11)
        | (xop << 8)
        | (register << 4)
        | ((i_address & 3) << 2)
        | (m_address & 3)
    )


def _assemble_compute_pm(statement: str) -> int | None:
    """Assemble the source-closed original Type 5 action forms."""

    read = re.fullmatch(
        r"(?:(.+)\s*,\s*)?([A-Z][A-Z0-9]*)\s*=\s*"
        r"PM\s*\(\s*I([4-7])\s*,\s*M([4-7])\s*\)",
        statement,
    )
    write = re.fullmatch(
        r"PM\s*\(\s*I([4-7])\s*,\s*M([4-7])\s*\)\s*=\s*"
        r"([A-Z][A-Z0-9]*)(?:\s*,\s*(.+))?",
        statement,
    )
    if read is None and write is None:
        return None

    registers = _dreg_name_to_code()
    if read is not None:
        computation, register_name, i_text, m_text = read.groups()
        write_direction = 0
    else:
        assert write is not None
        i_text, m_text, register_name, computation = write.groups()
        write_direction = 1
    if register_name not in registers:
        return None

    if computation is None:
        z, amf, yop, xop = 0, 0, 0, 0
    else:
        computation_fields = _compute_operation_codes().get(computation)
        if computation_fields is None:
            return None
        z, amf, yop, xop = computation_fields

    register = registers[register_name]
    if not write_direction and amf != 0 and _compute_move_destination_collision(
        z,
        amf,
        register,
    ):
        raise AssemblyError(
            "Type 5 read destination collides with computation destination"
        )

    return (
        0x500000
        | (write_direction << 19)
        | (z << 18)
        | (amf << 13)
        | (yop << 11)
        | (xop << 8)
        | (register << 4)
        | ((int(i_text) & 3) << 2)
        | (int(m_text) & 3)
    )


def _assemble_compute_dual(statement: str) -> int | None:
    """Assemble original Type 1 ALU/MAC plus simultaneous DM/PM reads."""

    clauses = _split_top_level_clauses(statement)
    if len(clauses) not in (2, 3):
        return None
    dm_match = None
    pm_match = None
    computation = None
    for clause in clauses:
        match = re.fullmatch(
            r"([A-Z][A-Z0-9]*)\s*=\s*"
            r"DM\s*\(\s*I([0-3])\s*,\s*M([0-3])\s*\)",
            clause,
        )
        if match is not None:
            if dm_match is not None:
                return None
            dm_match = match
            continue
        match = re.fullmatch(
            r"([A-Z][A-Z0-9]*)\s*=\s*"
            r"PM\s*\(\s*I([4-7])\s*,\s*M([4-7])\s*\)",
            clause,
        )
        if match is not None:
            if pm_match is not None:
                return None
            pm_match = match
            continue
        if computation is not None:
            return None
        computation = clause
    if dm_match is None or pm_match is None:
        return None

    dm_names = {"AX0": 0, "AX1": 1, "MX0": 2, "MX1": 3}
    pm_names = {"AY0": 0, "AY1": 1, "MY0": 2, "MY1": 3}
    dm_name, dm_i_text, dm_m_text = dm_match.groups()
    pm_name, pm_i_text, pm_m_text = pm_match.groups()
    if dm_name not in dm_names:
        raise AssemblyError("Type 1 DM read destination must be AX0/AX1/MX0/MX1")
    if pm_name not in pm_names:
        raise AssemblyError("Type 1 PM read destination must be AY0/AY1/MY0/MY1")

    if computation is None:
        amf, yop, xop = 0, 0, 0
    else:
        computation_fields = _compute_operation_codes().get(computation)
        if computation_fields is None:
            return None
        z, amf, yop, xop = computation_fields
        if z:
            raise AssemblyError("Type 1 computation destination must be AR or MR")

    return (
        0xC00000
        | (pm_names[pm_name] << 20)
        | (dm_names[dm_name] << 18)
        | (amf << 13)
        | (yop << 11)
        | (xop << 8)
        | ((int(pm_i_text) & 3) << 6)
        | ((int(pm_m_text) & 3) << 4)
        | (int(dm_i_text) << 2)
        | int(dm_m_text)
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


def _assemble_shifter_dm(statement: str) -> int | None:
    """Assemble a source-closed original Type 12 shifter/DM operation."""

    if statement.count(",") != 2:
        return None
    read = re.fullmatch(
        r"(.+),\s*([A-Z][A-Z0-9]*)\s*=\s*DM\(I([0-7]),\s*M([0-7])\)",
        statement,
    )
    write = re.fullmatch(
        r"DM\(I([0-7]),\s*M([0-7])\)\s*=\s*"
        r"([A-Z][A-Z0-9]*),\s*(.+)",
        statement,
    )
    if read is not None:
        computation, dreg_name, i_name, m_name = read.groups()
        is_write = False
    elif write is not None:
        i_name, m_name, dreg_name, computation = write.groups()
        is_write = True
    else:
        return None

    parsed_shifter = _parse_register_shifter(computation.strip())
    registers = _dreg_name_to_code()
    if parsed_shifter is None or dreg_name not in registers:
        return None
    i_address = int(i_name)
    m_address = int(m_name)
    if i_address // 4 != m_address // 4:
        raise AssemblyError("Type 12 I and M registers must use the same DAG")
    sf, xop = parsed_shifter
    dreg = registers[dreg_name]
    if not is_write and _shift_move_destination_collision(sf, dreg):
        raise AssemblyError(
            "Type 12 DM read destination collides with shifter destination"
        )
    dag = i_address // 4
    return (
        0x120000
        | (dag << 16)
        | (int(is_write) << 15)
        | (sf << 11)
        | (xop << 8)
        | (dreg << 4)
        | ((i_address & 3) << 2)
        | (m_address & 3)
    )


def _assemble_shifter_pm(statement: str) -> int | None:
    """Assemble a source-closed original Type 13 shifter/PM operation."""

    if statement.count(",") != 2:
        return None
    read = re.fullmatch(
        r"(.+),\s*([A-Z][A-Z0-9]*)\s*=\s*PM\(I([0-7]),\s*M([0-7])\)",
        statement,
    )
    write = re.fullmatch(
        r"PM\(I([0-7]),\s*M([0-7])\)\s*=\s*"
        r"([A-Z][A-Z0-9]*),\s*(.+)",
        statement,
    )
    if read is not None:
        computation, dreg_name, i_name, m_name = read.groups()
        is_write = False
    elif write is not None:
        i_name, m_name, dreg_name, computation = write.groups()
        is_write = True
    else:
        return None

    parsed_shifter = _parse_register_shifter(computation.strip())
    registers = _dreg_name_to_code()
    if parsed_shifter is None or dreg_name not in registers:
        return None
    i_address = int(i_name)
    m_address = int(m_name)
    if i_address < 4 or m_address < 4:
        raise AssemblyError("Type 13 PM transfers require DAG2 I4-I7 and M4-M7")
    sf, xop = parsed_shifter
    dreg = registers[dreg_name]
    if not is_write and _shift_move_destination_collision(sf, dreg):
        raise AssemblyError(
            "Type 13 PM read destination collides with shifter destination"
        )
    return (
        0x110000
        | (int(is_write) << 15)
        | (sf << 11)
        | (xop << 8)
        | (dreg << 4)
        | ((i_address & 3) << 2)
        | (m_address & 3)
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
    dm_write_immediate = _assemble_dm_write_immediate(statement)
    if dm_write_immediate is not None:
        return AssembledWord(dm_write_immediate)
    direct_dm = _assemble_direct_dm(statement)
    if direct_dm is not None:
        return AssembledWord(direct_dm)
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
    compute_dual = _assemble_compute_dual(statement)
    if compute_dual is not None:
        return AssembledWord(compute_dual)
    compute_dm = _assemble_compute_dm(statement)
    if compute_dm is not None:
        return AssembledWord(compute_dm)
    compute_pm = _assemble_compute_pm(statement)
    if compute_pm is not None:
        return AssembledWord(compute_pm)
    shifter_dm = _assemble_shifter_dm(statement)
    if shifter_dm is not None:
        return AssembledWord(shifter_dm)
    shifter_pm = _assemble_shifter_pm(statement)
    if shifter_pm is not None:
        return AssembledWord(shifter_pm)
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
