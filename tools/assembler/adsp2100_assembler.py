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
    dreg_immediate = _assemble_dreg_immediate(statement)
    if dreg_immediate is not None:
        return AssembledWord(dreg_immediate)
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
