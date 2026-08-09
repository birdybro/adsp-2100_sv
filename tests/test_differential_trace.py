from __future__ import annotations

from dataclasses import replace
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from sim.differential.model_trace_adapter import (
    adapt_model_trace_frame,
    snapshot_architectural_state,
)
from sim.reference_models.adsp2100_model import (
    ADSP2100Model,
    ArchitecturalState,
    ExactWord,
    UNKNOWN,
)
from tools.trace.adsp2100_trace import (
    DifferentialTraceFrame,
    TraceTransaction,
    TraceWord,
    compare_trace_frames,
    compare_trace_streams,
    trace_stream_from_ndjson,
    trace_stream_to_ndjson,
)
from tools.trace.reducer import reduce_failing_sequence
from tools.trace.compare_traces import main as compare_traces_main


ROOT = Path(__file__).resolve().parents[1]


def _frame(
    *,
    producer: str = "left",
    state: dict[str, TraceWord] | None = None,
    transaction_data: int = 0x123456,
) -> DifferentialTraceFrame:
    return DifferentialTraceFrame.create(
        producer=producer,
        retirement_index=0,
        pc_before=TraceWord.known(14, 4),
        pc_after=TraceWord.known(14, 5),
        opcode=TraceWord.known(24, 0),
        instruction_cycles=1,
        state={"pc": TraceWord.known(14, 5)} if state is None else state,
        transactions=(
            TraceTransaction(
                space="PM",
                kind="INSTRUCTION_FETCH",
                address=TraceWord.known(14, 5),
                width=24,
                data=TraceWord.known(24, transaction_data),
            ),
        ),
    )


class DifferentialTraceTests(unittest.TestCase):
    def test_word_known_unknown_and_partial_masks_are_canonical(self) -> None:
        self.assertEqual(
            TraceWord.known(8, 0xA5).to_dict(),
            {"width": 8, "value": "0xa5", "known_mask": "0xff"},
        )
        self.assertEqual(
            TraceWord.unknown(5).to_dict(),
            {"width": 5, "value": "0x00", "known_mask": "0x00"},
        )
        partial = TraceWord(width=4, value=0x5, known_mask=0x5)
        self.assertEqual(TraceWord.from_dict(partial.to_dict()), partial)
        with self.assertRaises(ValueError):
            TraceWord(width=4, value=0xA, known_mask=0x5)

    def test_frame_json_round_trip_is_deterministic(self) -> None:
        frame = _frame()
        encoded = frame.to_json()
        self.assertEqual(DifferentialTraceFrame.from_json(encoded), frame)
        self.assertEqual(DifferentialTraceFrame.from_json(encoded).to_json(), encoded)
        self.assertIn('"device":"original ADSP-2100"', encoded)
        self.assertIn('"schema_version":1', encoded)

    def test_frame_parser_rejects_noncanonical_or_extra_fields(self) -> None:
        value = _frame().to_dict()
        value["extra"] = True
        with self.assertRaisesRegex(ValueError, "keys differ"):
            DifferentialTraceFrame.from_dict(value)
        value = _frame().to_dict()
        value["pc_after"]["value"] = "0x5"
        with self.assertRaisesRegex(ValueError, "canonically padded"):
            DifferentialTraceFrame.from_dict(value)

    def test_comparison_ignores_producer_but_checks_all_state_by_default(self) -> None:
        left = _frame(producer="model", state={"ar": TraceWord.known(16, 1)})
        right = _frame(
            producer="rtl",
            state={
                "ar": TraceWord.known(16, 1),
                "ax0": TraceWord.known(16, 2),
            },
        )
        mismatch = compare_trace_frames(left, right)
        self.assertEqual(tuple(item.path for item in mismatch), ("state.ax0",))
        self.assertEqual(
            compare_trace_frames(left, right, requested_state=("ar",)), ()
        )

    def test_comparison_reports_known_mask_and_transaction_paths(self) -> None:
        left = _frame(state={"astat": TraceWord.unknown(8)})
        right = _frame(
            state={"astat": TraceWord.known(8, 0)}, transaction_data=0x654321
        )
        paths = {item.path for item in compare_trace_frames(left, right)}
        self.assertEqual(paths, {"state.astat", "transactions[0].data"})

    def test_stream_ndjson_round_trip_and_length_mismatch(self) -> None:
        frames = (_frame(), _frame(producer="second"))
        encoded = trace_stream_to_ndjson(frames)
        self.assertTrue(encoded.endswith("\n"))
        self.assertEqual(trace_stream_from_ndjson(encoded), frames)
        mismatch = compare_trace_streams(frames, frames[:1])
        self.assertEqual(mismatch[0].path, "frames.length")
        with self.assertRaisesRegex(ValueError, "blank trace line"):
            trace_stream_from_ndjson(encoded + "\n")

    def test_compare_cli_reports_a_stable_mismatch_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            left = Path(directory) / "left.ndjson"
            right = Path(directory) / "right.ndjson"
            left.write_text(trace_stream_to_ndjson((_frame(),)), encoding="utf-8")
            right.write_text(
                trace_stream_to_ndjson((_frame(transaction_data=0x654321),)),
                encoding="utf-8",
            )
            output = StringIO()
            with redirect_stdout(output):
                result = compare_traces_main((str(left), str(right)))
            self.assertEqual(result, 1)
            mismatch = json.loads(output.getvalue())
            self.assertEqual(
                mismatch["path"], "frames[0].transactions[0].data"
            )
            with redirect_stdout(StringIO()):
                self.assertEqual(
                    compare_traces_main((str(left), str(left))), 0
                )

    def test_compare_cli_is_directly_executable_from_repository(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/trace/compare_traces.py", "--help"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("differential retirement traces", result.stdout)

    def test_model_adapter_covers_unknown_state_and_fetch_transaction(self) -> None:
        model = ADSP2100Model()
        frame = model.step(0)
        adapted = adapt_model_trace_frame(frame, model.state)
        state = dict(adapted.state)
        self.assertEqual(state["pc"], TraceWord.known(14, 5))
        self.assertEqual(state["primary.ax0"], TraceWord.unknown(16))
        self.assertEqual(state["mstat"], TraceWord.known(4, 0))
        self.assertEqual(adapted.transactions[0].space, "PM")
        self.assertEqual(adapted.transactions[0].address, TraceWord.known(14, 5))
        self.assertIsNone(adapted.transactions[0].data)

    def test_model_snapshot_preserves_partial_validity_and_stack_entries(self) -> None:
        state = replace(
            ArchitecturalState.reset(),
            mstat=ExactWord(4, 0x5),
            mstat_valid_mask=0x5,
            pc_stack=(ExactWord(14, 0x123),),
            loop_stack=((ExactWord(14, 0x456), ExactWord(4, 0xA)),),
            count_stack=(ExactWord(14, 7),),
            status_stack=((UNKNOWN, ExactWord(4, 0x5), 0x5, UNKNOWN),),
        )
        snapshot = snapshot_architectural_state(state)
        self.assertEqual(snapshot["mstat"], TraceWord(4, 0x5, 0x5))
        self.assertEqual(snapshot["pc_stack.depth"], TraceWord.known(5, 1))
        self.assertEqual(snapshot["loop_stack.0.termination"], TraceWord.known(4, 0xA))
        self.assertEqual(snapshot["status_stack.0.astat"], TraceWord.unknown(8))
        self.assertEqual(snapshot["status_stack.0.mstat"], TraceWord(4, 0x5, 0x5))

    def test_model_adapter_rejects_mismatched_post_state(self) -> None:
        model = ADSP2100Model()
        frame = model.step(0)
        wrong_state = replace(model.state, pc=ExactWord(14, 6))
        with self.assertRaisesRegex(ValueError, "PC"):
            adapt_model_trace_frame(frame, wrong_state)

    def test_reducer_is_deterministic_and_one_minimal(self) -> None:
        program = (9, 3, 4, 7, 8, 3)
        predicate = lambda candidate: 3 in candidate and 7 in candidate
        first = reduce_failing_sequence(program, predicate)
        second = reduce_failing_sequence(program, predicate)
        self.assertEqual(first, second)
        self.assertEqual(first.items, (7, 3))
        for index in range(len(first.items)):
            candidate = first.items[:index] + first.items[index + 1 :]
            self.assertFalse(predicate(candidate))

    def test_reducer_requires_the_original_failure_signature(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not preserve"):
            reduce_failing_sequence((1, 2, 3), lambda _candidate: False)
        reduced = reduce_failing_sequence((1, 2), lambda _candidate: True)
        self.assertEqual(reduced.items, ())

    def test_machine_readable_schema_records_scope_and_exclusions(self) -> None:
        schema = json.loads(
            (
                ROOT
                / "docs/generated/adsp2100_differential_trace.yaml"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(schema["properties"]["schema_version"]["const"], 1)
        self.assertEqual(
            schema["properties"]["device"]["const"], "original ADSP-2100"
        )
        self.assertEqual(
            schema["comparison_contract"]["producer"],
            "PROVENANCE_ONLY_NOT_COMPARED",
        )
        self.assertIn("known_mask", schema["$defs"]["word"]["required"])
        self.assertIn("MAME_ADAPTER_COMPLETE", schema["excluded_claims"])


if __name__ == "__main__":
    unittest.main()
