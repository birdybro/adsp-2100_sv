# Architecture confidence

**Updated:** 2026-07-31

| Subject | Confidence | Basis / limitation |
|---|---|---|
| 24-bit PM, 16-bit DM, 14-bit addresses | VERIFIED_PRIMARY | original 1989 manual |
| Four input clocks/eight logical states per instruction | VERIFIED_PRIMARY | original 1989 manual |
| Reset PC `0x0004`, MSTAT/IMASK zero, ICNTL undefined | VERIFIED_PRIMARY | original 1989 manual |
| Original four-bit MSTAT boundary | VERIFIED_PRIMARY | original manual; later modes explicitly excluded |
| NOP `0x000000` | VERIFIED_PRIMARY | original Appendix A diagram |
| All 30 top-level opcode masks | CORROBORATED | primary diagrams transcribed, algebraically checked, and compared to pinned MAME layout |
| All 30 diagrammed field layouts | CORROBORATED | 106 primary-transcribed fields exactly partition 393 variable positions and match an independent visual-review fixture |
| Type 6 immediate DREG load | VERIFIED_PRIMARY | original pp. 1-2, 2-6–2-7, 2-15, 2-18, 6-1–6-2, 6-12–6-13, A-2, and A-9 close full field placement, one-cycle selected-bank write, no memory-data transfer, narrow storage, and MR1 sign-fill; exhaustive decode and 50,204 model/RTL cycles pass, while fetch/interrupt/bus timing remains open |
| Type 15 immediate LSHIFT/ASHIFT subset | CORROBORATED | original pp. 2-23–2-30, 6-11 Table 6.5, A-3, and A-7 close the eight immediate shift functions, seven X operands, signed count, SR feedback/writeback, SE preservation, and one-cycle no-data-memory action; exhaustive class partitioning and 58,709 model/RTL cycles pass, while SF 8–15, XOP 001 behavior, and fetch/interrupt/bus timing remain open |
| Type 16 conditional shifter | CORROBORATED | original pp. 2-20–2-35, 4-21, 4-25, 6-1–6-2, 6-11 Table 6.5, A-3, and A-6–A-7 close all sixteen SF values, seven X operands, condition gating, selected-bank/status writeback, false-path preservation, and one-cycle no-data-memory action; exhaustive class partitioning and 54,403 model/RTL cycles pass, while XOP 001 behavior and fetch/loop/interrupt/bus timing remain open |
| Type 17 internal-MOVE decode/execution | CORROBORATED | original pp. 2-6, 2-15, 2-18, 2-21, 3-2–3-3, 3-7, 4-4, 4-20–4-24, 6-1–6-2, 6-12, A-3, and A-9 close fields, register directions, known extensions, side effects, one-cycle no-memory action, and cycle-boundary ordering; the bounded slice passes all legal pair/bank executions and 59,430 RTL cycles, but OQ-016 status extension remains PROVISIONAL |
| Type 26 stack-control action decode | VERIFIED_PRIMARY | original combined syntax and Appendix A tables close all 32 action encodings and one-cycle selection; exhaustive model/RTL decode passes |
| Type 26 bounded stateful execution | CORROBORATED | original stack/status sections plus 50,015 model/RTL cycles verify cycle-start capture/restore and atomic cycle-end action combinations; automatic/interrupt arbitration, OQ-013, and phase/bus timing remain open |
| Type 25 conditional MR saturation | VERIFIED_PRIMARY | original pp. 2-18–2-19 and A-4 plus contemporary assembler listing close exact opcode, MV condition, both result limits, one-cycle status-preserving action, and selected-bank execution; exhaustive decode and 50,112 model/RTL cycles pass, while interrupt-adjacent and bus timing remain open |
| Type 18 mode control | VERIFIED_PRIMARY | original pp. 4-22–4-23, 6-14–6-15, A-3, and A-8 close all 256 original words, both no-change aliases, independent combined AS/OL/BR/SR actions, and one-cycle MSTAT update; exhaustive decode and 58,248 model/RTL cycles pass, while OQ-015 and bus timing remain open |
| Type 21 address modify | CORROBORATED | original pp. 3-1–3-5, 6-14–6-15, A-4, and A-7–A-8 close exact decode, same-DAG selection, no-memory behavior, and original address arithmetic; later p. 9-65 only corroborates explicit corresponding-L/writeback wording; all 32 words, exhaustive fail-closed decode, and 50,124 stateful model/RTL cycles pass, while data-transfer/multifunction/bus attachment remains open |
| Opcode field/function legality | UNKNOWN | class masks, field positions, finite code tables, register codes, Type 17/Type 26 action selection, and NOP/Type 6/Type 16/Type 18/Type 21/Type 25 semantics are closed within their explicit unsupported boundaries; Type 15 is source-closed only for 14,336 words; remaining legal combinations and instruction effects are not |
| IF/DO condition field and predicates | VERIFIED_PRIMARY | original Tables 4.1/4.3 and Appendix A; exhaustive model/RTL truth table |
| Standard ALU AMF results and flags | CORROBORATED | original compute/status chapters plus explicitly common family instruction reference |
| Standard MAC AMF results and MV | CORROBORATED | original compute chapter plus common family instruction reference; exact Type 25 saturation is independently VERIFIED_PRIMARY, while MAME rounding conflict SC-008 remains disclosed |
| Shifter SF functions | CORROBORATED | original compute chapter, Tables 2.4/2.5, and Appendix A; all Type 16 conditional forms and the Type 15 immediate subset are integrated, while multifunction forms and whole-core timing remain incomplete |
| DAG arithmetic and ownership | CORROBORATED | original DAG chapter plus 1994 explicit original/later placement distinction; standalone Type 21 storage/selection/writeback is integrated, while data-transfer, multifunction, and bus attachment remain incomplete |
| Sequencer next-PC/loop precedence | CORROBORATED | original program-control chapter and 636,512 model/RTL vectors; interrupts and phase/cycle integration incomplete |
| CNTR validity and CE transitions | CORROBORATED | original program-control chapter plus 50,022 model/RTL cycles; exact width, load semantics, cycle-start condition evaluation, post-decrement, restore/invalidate behavior, and reset invalidity implemented; conditional-CALL CE, decode, and empty-pop effects remain open |
| PC/count/loop stack storage | CORROBORATED | original program-control/status chapters plus 50,062 model/RTL cycles; exact depths, accepted LIFO actions, saturation, newest-push loss, sticky overflow, and SSTAT sources implemented; decode/interrupt connectivity and empty-pop effects incomplete |
| Bounded sequencer integration | CORROBORATED | original program-control chapter plus 50,011 model/RTL cycles connect IF/DO, flow, CNTR, and PC/count/loop stacks; PC state, decode, interrupts, OQ-012/OQ-013/OQ-018, and phase timing remain outside the boundary |
| Computational register banking | CORROBORATED | original compute/register/Appendix A sections, 58,307 DREG cycles, 50,120 full-bank/writeback cycles, and 50,112 MSTAT-consumer cycles; interrupt-adjacent selection and decode connectivity incomplete |
| MSTAT ordinary-cycle consumers | CORROBORATED | all four original mode bits are wired using primary-backed cycle-start read/cycle-end write ordering and 50,112 model/RTL cycles; OQ-015 retains the interrupt-adjacent boundary |
| Status/control storage and updates | CORROBORATED | original status/reset/interrupt/Appendix A sections plus 50,287 storage, 50,112 MSTAT-consumer, and 50,015 Type 26 cycles; manual status push/restore and SSTAT composition are bounded, while narrow reads, ICNTL consumers, and interrupt/RTI arbitration remain incomplete |
| Status-stack depth and accepted operations | CORROBORATED | original 1987 four-by-sixteen diagram plus original 1989 saturation/status rules, 50,037 storage cycles, and 50,015 Type 26 integration cycles; empty-pop effects and interrupt/RTI arbitration remain incomplete |
| Parallel old/new-value semantics | PROVISIONAL | partial manual extraction only |
| Empty-stack pop effects | UNKNOWN | pointer saturation is sourced, but popped data/register side effects are not |
| Full interrupt phase behavior | PROVISIONAL | recognition state known; all interactions incomplete |
| Atari 32 MHz input / 8 MHz instruction rate | VERIFIED_PRIMARY | Atari schematic plus original clock relation |
| ADSP vs ADSP II package equivalence | CORROBORATED | original engineer page and schematic sheets |
| Hard Drivin' host/SIM/SOM functional map | CORROBORATED | pinned MAME behavior; net transcription incomplete |
| PAL/GAL equations | UNKNOWN | applicable equations not acquired |

No provisional or inferred item may be promoted without new evidence and
corresponding test updates.
