"""Deliberately partial ADSP-2100 disassembler with reserved-code reporting."""

from __future__ import annotations

from dataclasses import dataclass

from tools.generators.validate_isa import classify_opcode, load_database, validate_database


@dataclass(frozen=True)
class Disassembly:
    opcode: int
    text: str
    classification: str
    implemented: bool


def disassemble_word(opcode: int) -> Disassembly:
    if not 0 <= opcode <= 0xFFFFFF:
        raise ValueError("opcode must fit 24 bits")
    database = load_database()
    validate_database(database)
    for instruction in database["instructions"]:
        mask = int(instruction["opcode_mask"], 16)
        value = int(instruction["opcode_value"], 16)
        if opcode & mask == value:
            return Disassembly(
                opcode=opcode,
                text=instruction["algebraic_assembly_syntax"],
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
