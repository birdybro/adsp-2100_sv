# Architecture confidence

**Updated:** 2026-07-30

| Subject | Confidence | Basis / limitation |
|---|---|---|
| 24-bit PM, 16-bit DM, 14-bit addresses | VERIFIED_PRIMARY | original 1989 manual |
| Four input clocks/eight logical states per instruction | VERIFIED_PRIMARY | original 1989 manual |
| Reset PC `0x0004`, MSTAT/IMASK zero, ICNTL undefined | VERIFIED_PRIMARY | original 1989 manual |
| Original four-bit MSTAT boundary | VERIFIED_PRIMARY | original manual; later modes explicitly excluded |
| NOP `0x000000` | VERIFIED_PRIMARY | original Appendix A diagram |
| All 30 top-level opcode masks | CORROBORATED | primary diagrams transcribed, algebraically checked, and compared to pinned MAME layout |
| Opcode field/function legality | UNKNOWN | only class masks, register codes, and NOP semantics are closed |
| IF/DO condition field and predicates | VERIFIED_PRIMARY | original Tables 4.1/4.3 and Appendix A; exhaustive model/RTL truth table |
| Standard ALU AMF results and flags | CORROBORATED | original compute/status chapters plus explicitly common family instruction reference |
| Standard MAC AMF results and MV | CORROBORATED | original compute chapter plus common family instruction reference; MAME rounding conflict SC-008 disclosed |
| Shifter SF functions | CORROBORATED | original compute chapter, Tables 2.4/2.5, and Appendix A; instruction integration incomplete |
| Parallel old/new-value semantics | PROVISIONAL | partial manual extraction only |
| Stack underflow/overflow effects | UNKNOWN | status reporting known; effects not closed |
| Full interrupt phase behavior | PROVISIONAL | recognition state known; all interactions incomplete |
| Atari 32 MHz input / 8 MHz instruction rate | VERIFIED_PRIMARY | Atari schematic plus original clock relation |
| ADSP vs ADSP II package equivalence | CORROBORATED | original engineer page and schematic sheets |
| Hard Drivin' host/SIM/SOM functional map | CORROBORATED | pinned MAME behavior; net transcription incomplete |
| PAL/GAL equations | UNKNOWN | applicable equations not acquired |

No provisional or inferred item may be promoted without new evidence and
corresponding test updates.
