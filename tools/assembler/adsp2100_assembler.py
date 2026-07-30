"""Deliberately partial ADSP-2100 assembler driven by verified ISA entries."""

from __future__ import annotations

from dataclasses import dataclass
import re

from tools.generators.validate_isa import load_database, validate_database


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


def assemble_statement(source: str) -> AssembledWord:
    statement = _normalize_statement(source)
    mnemonics = exact_mnemonics()
    if statement not in mnemonics:
        raise AssemblyError(
            f"unsupported or unverified ADSP-2100 statement: {statement!r}"
        )
    return AssembledWord(mnemonics[statement])
