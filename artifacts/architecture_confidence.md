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
| Type 26 stack-control action decode | VERIFIED_PRIMARY | original combined syntax and Appendix A tables close all 32 action encodings and one-cycle selection; exhaustive model/RTL decode passes, while stateful effects and OQ-013 remain incomplete |
| Opcode field/function legality | UNKNOWN | class masks, field positions, finite code tables, register codes, NOP semantics, and bounded Type 26 action selection are closed; remaining legal combinations and instruction effects are not |
| IF/DO condition field and predicates | VERIFIED_PRIMARY | original Tables 4.1/4.3 and Appendix A; exhaustive model/RTL truth table |
| Standard ALU AMF results and flags | CORROBORATED | original compute/status chapters plus explicitly common family instruction reference |
| Standard MAC AMF results and MV | CORROBORATED | original compute chapter plus common family instruction reference; MAME rounding conflict SC-008 disclosed |
| Shifter SF functions | CORROBORATED | original compute chapter, Tables 2.4/2.5, and Appendix A; instruction integration incomplete |
| DAG arithmetic and ownership | CORROBORATED | original DAG chapter plus 1994 explicit original/later placement distinction; function integration incomplete |
| Sequencer next-PC/loop precedence | CORROBORATED | original program-control chapter and 636,512 model/RTL vectors; interrupts and phase/cycle integration incomplete |
| CNTR validity and CE transitions | CORROBORATED | original program-control chapter plus 50,022 model/RTL cycles; exact width, load semantics, cycle-start condition evaluation, post-decrement, restore/invalidate behavior, and reset invalidity implemented; conditional-CALL CE, decode, and empty-pop effects remain open |
| PC/count/loop stack storage | CORROBORATED | original program-control/status chapters plus 50,062 model/RTL cycles; exact depths, accepted LIFO actions, saturation, newest-push loss, sticky overflow, and SSTAT sources implemented; decode/interrupt connectivity and empty-pop effects incomplete |
| Bounded sequencer integration | CORROBORATED | original program-control chapter plus 50,011 model/RTL cycles connect IF/DO, flow, CNTR, and PC/count/loop stacks; PC state, decode, interrupts, OQ-012/OQ-013/OQ-018, and phase timing remain outside the boundary |
| Computational register banking | CORROBORATED | original compute/register/Appendix A sections, 58,307 DREG cycles, 50,120 full-bank/writeback cycles, and 50,112 MSTAT-consumer cycles; interrupt-adjacent selection and decode connectivity incomplete |
| MSTAT ordinary-cycle consumers | CORROBORATED | all four original mode bits are wired using primary-backed cycle-start read/cycle-end write ordering and 50,112 model/RTL cycles; OQ-015 retains the interrupt-adjacent boundary |
| Status/control storage and updates | CORROBORATED | original status/reset/interrupt/Appendix A sections plus 50,287 storage and 50,112 integration cycles; entry/restore transitions, MSTAT consumers, and all SSTAT storage sources implemented, while narrow reads, SSTAT composition, ICNTL consumers, stack connectivity, and interrupt recognition remain incomplete |
| Status-stack depth and accepted operations | CORROBORATED | original 1987 four-by-sixteen diagram plus original 1989 saturation/status rules and 50,037 model/RTL cycles; empty-pop effects and interrupt/RTI connectivity remain incomplete |
| Parallel old/new-value semantics | PROVISIONAL | partial manual extraction only |
| Empty-stack pop effects | UNKNOWN | pointer saturation is sourced, but popped data/register side effects are not |
| Full interrupt phase behavior | PROVISIONAL | recognition state known; all interactions incomplete |
| Atari 32 MHz input / 8 MHz instruction rate | VERIFIED_PRIMARY | Atari schematic plus original clock relation |
| ADSP vs ADSP II package equivalence | CORROBORATED | original engineer page and schematic sheets |
| Hard Drivin' host/SIM/SOM functional map | CORROBORATED | pinned MAME behavior; net transcription incomplete |
| PAL/GAL equations | UNKNOWN | applicable equations not acquired |

No provisional or inferred item may be promoted without new evidence and
corresponding test updates.
