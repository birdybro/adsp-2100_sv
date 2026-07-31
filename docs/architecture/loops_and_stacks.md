# Loops and stacks

**Status: original depths and storage implemented; bounded automatic
sequencer and manual Type 26 connectivity verified**

The original has four stack classes reported by SSTAT: PC, count, status, and
loop [ADI-UM-1989, printed p. 4-22]. Depths are 16 for the 14-bit PC stack,
four for the 14-bit count stack, four for the 16-bit status stack, and four for
the 18-bit loop stack [ADI-UM-1989, printed pp. 4-3–4-6;
ADI-DATABOOK-1987, printed pp. 2-21–2-22, Figure 6]. The status word packs
ASTAT[7:0], MSTAT[3:0], then IMASK[3:0], yielding exactly 16 bits
[ADI-UM-1989, printed p. 4-10].

On stack overflow, the pointer saturates, new items are lost while older data
is retained, and the overflow bit sticks until reset. Exactly four subsequent
valid pops empty a full status stack even after any number of overflowing
pushes, so empty and overflow can both be set [ADI-UM-1989, printed p. 4-22].
The value and register side effects of a pop attempted while already empty are
not documented and remain OQ-013.

The independent model and `rtl/core/adsp2100_status_stack.sv` implement the
original four-entry status LIFO, both no-change Spp codes,
manual/automatic-push-compatible storage, RTI/manual-pop-compatible output,
saturating depth, sticky overflow, and SSTAT bits 4/5. The independent
sequencer-stack model and `rtl/core/adsp2100_sequencer_stacks.sv` implement
the exact PC, count, and loop dimensions and SSTAT bits 0–3 and 6–7. Reset
clears all pointers and overflow bits without initializing stored data
[ADI-UM-1989, printed pp. 4-3–4-7, 4-10, 4-22, 5-13, A-10].

The original Type 26 action selection is now independently machine-readable
and executable. `SPP[1:0]` preserves both no-change encodings and selects
status push/pop; `CP`, `LP`, and `PP` independently select count-, loop-, and
PC-stack pops. The original grammar permits these clauses to be combined, and
the instruction remains one processor cycle [ADI-UM-1989, printed pp. 1-2,
6-14–6-15, A-4, A-8–A-10]. The Python action model and
`rtl/core/adsp2100_stack_control_decode.sv` cover all 32 encodings while
failing closed for every non-Type-26 word.

The independent composed model and
`rtl/core/adsp2100_stack_control_slice.sv` now execute those requests against
all four stack classes at one cycle boundary. PUSH STS captures cycle-start
ASTAT/MSTAT/IMASK; POP STS restores all three from the cycle-start status top;
POP CNTR restores the cycle-start count top; and POP PC/POP LOOP discard their
selected entries. All selected actions commit together at cycle end. Nine
directed/schema/random model checks and 50,015 model-versus-RTL cycles cover
combined actions, both no-effect aliases, valid/empty/full stacks, reset,
invalid opcodes, SSTAT composition, and fail-closed integration conflicts
[ADI-UM-1989, printed pp. 4-3–4-7, 4-9–4-10, 6-14–6-15,
A-4, A-8–A-10].

The sequencer storage exposes each current top with an explicit valid bit,
accepted pushes, valid pops, overflow events, and empty-pop indications. Its
SSTAT output is a fragment: bits 4/5 are zero and must be composed with the
status-stack fragment. The separate CNTR controller now generates a count-stack
push only when a load replaces a valid count, and generates a pop on true CE
or manual pop. A true CE test restores a valid stack top or invalidates CNTR
when the count stack is empty [ADI-UM-1989, printed pp. 4-4–4-5].
Same-stack simultaneous push/pop is suppressed globally with
`write_conflict_o`; this is a fail-closed integration safeguard, not a claimed
real-device illegal-encoding behavior.

An empty pop produces no valid data; zero on the RTL data output is an
explicitly non-architectural interface sentinel. The value and architectural
side effects remain OQ-013.

Nested loops cannot terminate on the same instruction because the comparator
checks one termination at a time [ADI-UM-1989, printed p. 4-8]. Premature loop
exit may require explicit stack pops [ADI-UM-1989, printed p. 4-7].

The instruction-boundary flow block implements the sourced precedence rule:
a taken jump, call, or return on the loop's final instruction performs only its
explicit flow/PC-stack action and suppresses implicit loop, count-stack, and
counter-test actions. A false explicit condition allows the normal loop back
or exit path.

The bounded sequencer slice connects that flow rule to PC/count/loop storage,
CNTR, and IF/DO condition evaluation. DO UNTIL setup pushes PC+1 and a loop
descriptor; loop back reads the current PC-stack top; loop exit atomically
pops the PC and loop stacks and, for true CE, restores or invalidates CNTR
while popping the count stack. Nested CE restoration and stack-depth
transitions match the independent model across 50,011 cycles.

Interrupt/RTI connectivity and arbitration between Type 26 and automatic
sequencer/interrupt actions remain outside this integration boundary. Every
empty-pop architectural side effect remains OQ-013. Conditional-CALL CE
remains OQ-012. Competing automatic/manual actions and DO setup on an active
outer loop's final instruction are rejected under OQ-018 instead of receiving
an invented priority.
