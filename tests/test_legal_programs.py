from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sim.differential.legal_programs import (
    LegalProgram,
    generate_legal_program,
    run_model_program,
)
from sim.reference_models.adsp2100_model import ExactWord
from tools.trace.adsp2100_trace import (
    TraceWord,
    trace_stream_from_ndjson,
    trace_stream_to_ndjson,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CLASSES = {
    "NOP",
    "TYPE_06",
    "TYPE_07",
    "TYPE_09",
    "TYPE_15",
    "TYPE_16",
    "TYPE_17_DREG",
    "TYPE_18",
    "TYPE_21",
    "TYPE_23",
    "TYPE_24",
    "TYPE_25",
    "TYPE_26_NO_EFFECT",
}


class LegalProgramTests(unittest.TestCase):
    def test_generation_is_seeded_replayable_and_seed_sensitive(self) -> None:
        left = generate_legal_program(0x2100, 64)
        right = generate_legal_program(0x2100, 64)
        other = generate_legal_program(0x2101, 64)
        self.assertEqual(left, right)
        self.assertEqual(left.to_json(), right.to_json())
        self.assertNotEqual(left.words, other.words)

    def test_initial_prefix_covers_every_bounded_class(self) -> None:
        program = generate_legal_program(7, len(EXPECTED_CLASSES))
        self.assertEqual(set(program.classes), EXPECTED_CLASSES)
        self.assertTrue(all(0 <= word <= 0xFFFFFF for word in program.words))

    def test_canonical_corpus_round_trip_is_strict(self) -> None:
        program = generate_legal_program(0xABC, 24, origin=0x120)
        self.assertEqual(LegalProgram.from_json(program.to_json()), program)
        decoded = json.loads(program.to_json())
        decoded["seed"] = "0xabc"
        with self.assertRaisesRegex(ValueError, "canonically padded"):
            LegalProgram.from_dict(decoded)
        decoded = json.loads(program.to_json())
        decoded["instructions"][0]["class"] = "TYPE_10"
        with self.assertRaisesRegex(ValueError, "unsupported class"):
            LegalProgram.from_dict(decoded)

    def test_model_retires_seeded_programs_into_common_traces(self) -> None:
        for seed in range(32):
            program = generate_legal_program(seed, 128, origin=0x200)
            frames = run_model_program(program)
            self.assertEqual(len(frames), len(program.words))
            self.assertEqual(
                tuple(frame.opcode.value for frame in frames), program.words
            )
            for index, frame in enumerate(frames):
                self.assertEqual(frame.retirement_index, index)
                self.assertEqual(
                    frame.pc_before, TraceWord.known(14, 0x200 + index)
                )
                self.assertEqual(
                    frame.pc_after, TraceWord.known(14, 0x201 + index)
                )
                self.assertEqual(dict(frame.state)["pc"].value, 0x201 + index)
            self.assertEqual(
                trace_stream_to_ndjson(frames),
                trace_stream_to_ndjson(run_model_program(program)),
            )

    def test_initial_state_is_known_empty_and_replayable(self) -> None:
        program = generate_legal_program(9, 1, origin=0x345)
        first = program.initial_state()
        second = program.initial_state()
        self.assertEqual(first, second)
        self.assertEqual(first.pc, ExactWord(14, 0x345))
        self.assertEqual(first.sstat, ExactWord(8, 0x55))
        self.assertEqual(first.mstat_valid_mask, 0xF)
        self.assertEqual(first.pc_stack, ())
        self.assertEqual(first.loop_stack, ())
        self.assertEqual(first.count_stack, ())
        self.assertEqual(first.status_stack, ())

    def test_invalid_sizes_and_mislabeled_words_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            generate_legal_program(0, -1)
        with self.assertRaisesRegex(ValueError, "PM address"):
            generate_legal_program(0, 2, origin=0x3FFF)
        with self.assertRaisesRegex(ValueError, "does not match"):
            LegalProgram(seed=0, origin=4, words=(0,), classes=("TYPE_06",))
        with self.assertRaisesRegex(ValueError, "unsupported class"):
            LegalProgram(seed=0, origin=4, words=(0,), classes=([],))  # type: ignore[arg-type]
        for bad_integer in (False, 1.0, "1"):
            with self.subTest(bad_integer=bad_integer):
                with self.assertRaises(ValueError):
                    generate_legal_program(bad_integer, 1)  # type: ignore[arg-type]
                with self.assertRaises(ValueError):
                    generate_legal_program(0, bad_integer)  # type: ignore[arg-type]

    def test_machine_readable_contract_records_exact_scope(self) -> None:
        contract = json.loads(
            (
                ROOT / "docs/generated/adsp2100_legal_programs.yaml"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(contract["schema_version"], 1)
        self.assertEqual(set(contract["emitted_classes"]), EXPECTED_CLASSES)
        self.assertEqual(contract["execution_targets"], ["INDEPENDENT_MODEL"])
        self.assertEqual(
            contract["replay_cli"], "tools/trace/run_legal_program.py"
        )
        self.assertIn("RTL_PROGRAM_EXECUTION", contract["excluded_claims"])

    def test_cli_generates_and_replays_byte_stable_trace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            corpus = Path(directory) / "program.json"
            generated_trace = Path(directory) / "generated.ndjson"
            replayed_trace = Path(directory) / "replayed.ndjson"
            generated = subprocess.run(
                [
                    sys.executable,
                    "tools/trace/run_legal_program.py",
                    "--seed",
                    "0x2100",
                    "--length",
                    "32",
                    "--origin",
                    "0x120",
                    "--program-out",
                    str(corpus),
                    "--trace-out",
                    str(generated_trace),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(generated.returncode, 0, generated.stderr)
            self.assertEqual(generated.stdout, "")
            program = LegalProgram.from_json(corpus.read_text(encoding="utf-8"))
            self.assertEqual(program.seed, 0x2100)
            self.assertEqual(program.origin, 0x120)
            self.assertEqual(len(program.words), 32)
            trace_stream_from_ndjson(generated_trace.read_text(encoding="utf-8"))

            replayed = subprocess.run(
                [
                    sys.executable,
                    "tools/trace/run_legal_program.py",
                    "--program-in",
                    str(corpus),
                    "--trace-out",
                    str(replayed_trace),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(replayed.returncode, 0, replayed.stderr)
            self.assertEqual(
                replayed_trace.read_bytes(), generated_trace.read_bytes()
            )

    def test_cli_defaults_to_trace_stdout_and_fails_closed(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "tools/trace/run_legal_program.py",
                "--seed",
                "7",
                "--length",
                "3",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(trace_stream_from_ndjson(result.stdout)), 3)

        missing_length = subprocess.run(
            [
                sys.executable,
                "tools/trace/run_legal_program.py",
                "--seed",
                "7",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(missing_length.returncode, 2)
        self.assertEqual(
            json.loads(missing_length.stderr),
            {"error": "--length is required with --seed"},
        )


if __name__ == "__main__":
    unittest.main()
