from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepositoryTests(unittest.TestCase):
    def test_required_governance_files(self) -> None:
        for name in (
            "AGENTS.md",
            "README.md",
            "CHANGELOG.md",
            "TASKS.md",
            "LICENSE",
            "CONTRIBUTING.md",
            ".gitignore",
            ".gitattributes",
            "Makefile",
        ):
            self.assertTrue((ROOT / name).is_file(), name)

    def test_required_directory_layout(self) -> None:
        required = (
            "docs/architecture",
            "docs/research",
            "docs/references",
            "docs/timing",
            "docs/integration",
            "docs/decisions",
            "docs/generated",
            "docs/diagrams",
            "rtl/core",
            "rtl/packages",
            "rtl/wrappers",
            "sim/unit",
            "sim/instruction",
            "sim/compute",
            "sim/dag",
            "sim/sequencer",
            "sim/bus",
            "sim/interrupt",
            "sim/programs",
            "sim/differential",
            "sim/reference_models",
            "formal/properties",
            "formal/harnesses",
            "tools/assembler",
            "tools/disassembler",
            "tools/trace",
            "tools/reference",
            "tools/generators",
            "tools/converters",
            "scripts",
            "tests/asm",
            "tests/vectors",
            "tests/expected",
            "tests/traces",
            "tests/regressions",
            "tests/fuzz",
            "synthesis/yosys",
            "synthesis/quartus",
            "synthesis/mister",
            "third_party",
            "reference_cache",
            "build",
            "artifacts",
            ".github/workflows",
        )
        for name in required:
            self.assertTrue((ROOT / name).is_dir(), name)

    def test_required_documentation(self) -> None:
        required = (
            "docs/architecture/device_scope.md",
            "docs/architecture/device_feature_matrix.md",
            "docs/architecture/adsp2100_architecture.md",
            "docs/architecture/programmers_model.md",
            "docs/architecture/registers.md",
            "docs/architecture/instruction_set.md",
            "docs/architecture/opcode_map.md",
            "docs/architecture/multifunction_instructions.md",
            "docs/architecture/alu.md",
            "docs/architecture/mac.md",
            "docs/architecture/shifter.md",
            "docs/architecture/dag1.md",
            "docs/architecture/dag2.md",
            "docs/architecture/program_sequencer.md",
            "docs/architecture/memory_model.md",
            "docs/architecture/register_banks.md",
            "docs/architecture/loops_and_stacks.md",
            "docs/architecture/conditions.md",
            "docs/architecture/interrupts.md",
            "docs/architecture/reset_halt_bus_request.md",
            "docs/architecture/external_interface.md",
            "docs/architecture/pipeline.md",
            "docs/timing/instruction_cycles.md",
            "docs/timing/program_memory_cycles.md",
            "docs/timing/data_memory_cycles.md",
            "docs/timing/wait_states.md",
            "docs/timing/interrupt_timing.md",
            "docs/research/open_questions.md",
            "docs/research/source_conflicts.md",
            "docs/integration/hard_drivin_requirements.md",
            "docs/decisions/ADR-0001-reference-precedence.md",
            "docs/decisions/ADR-0002-original-device-scope.md",
            "docs/decisions/ADR-0003-cycle-model.md",
        )
        for name in required:
            self.assertTrue((ROOT / name).is_file(), name)

    def test_copyrighted_cache_and_build_products_are_ignored(self) -> None:
        for name in (
            "reference_cache/example/manual.pdf",
            "reference_cache/example/tool.exe",
            "build/example/output.vcd",
            "tests/local_roms/game.rom",
        ):
            result = subprocess.run(
                ["git", "check-ignore", "-q", name],
                cwd=ROOT,
                check=False,
            )
            self.assertEqual(result.returncode, 0, name)

    def test_no_reference_or_binary_payload_is_tracked(self) -> None:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        tracked = [Path(item.decode()) for item in result.stdout.split(b"\0") if item]
        forbidden = [
            path
            for path in tracked
            if (
                len(path.parts) > 1
                and path.parts[0] == "reference_cache"
                and path.name != ".gitkeep"
            )
            or path.suffix.lower() in {".rom", ".bin", ".exe", ".com"}
        ]
        self.assertEqual(forbidden, [])


if __name__ == "__main__":
    unittest.main()
