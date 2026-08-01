# Data address generator 1

**Status: source-backed arithmetic model and RTL function block**

DAG1 owns I0–I3, M0–M3, and L0–L3. Every register is 14 bits. DAG1 generates
DM addresses only and can bit-reverse them when MSTAT enables the mode
[ADI-UM-1989, printed pp. 3-1–3-2, 3-5].

Indirect access uses the current I value, then post-modifies it using any M from
the same DAG. M is signed; I and L are unsigned. L=0 selects linear addressing
[ADI-UM-1989, printed pp. 3-2–3-3].

Circular addressing uses:

`next = (I + M - base) modulo L + base`

The base has its lower N bits zero where N bits are required to represent L,
and the source requires `abs(M) <= L` so a single update wraps at most once
[ADI-UM-1989, printed pp. 3-3–3-4]. Behavior outside that documented
restriction is not yet defined.

This rule has an original-device edge that later-family implementations must
not import. For an exact power-of-two L, the original ADSP-2100 counts the bit
needed to represent the unsigned length itself. Thus L=8 clears four low base
bits and requires a multiple-of-16 base. All other ADSP-21xx processors covered
by the 1994 toolchain manual clear only three bits for this case
[ADI-UM-1989, printed pp. 3-3–3-4; ADI-ASM-1994, section 3.7.2.2, printed
pp. 3-29–3-32]. This is recorded against the later-family rule and pinned MAME
as SC-010.

Bit reverse reverses all 14 output address bits about the 6/7 boundary but
stores the post-modified I in normal order [ADI-UM-1989, printed p. 3-5].

The independent function model and portable combinational RTL now cover old-I
address output, signed post-modification, linear 14-bit wrap, circular
base/wrap arithmetic, and DAG1 bit reversal. A bounded integration slice
connects current MSTAT bit 1 to the bit-reverse input. MOVE/MODE CONTROL
updates become visible to DAG1 on the following cycle, so a simultaneous
address observation uses the pre-instruction MSTAT state
[ADI-UM-1989, printed pp. 2-6–2-7, 3-5, 4-22–4-23]. A diagnostic
`configuration_valid` result identifies inputs outside the documented
placement and modify restrictions; deterministic outputs for invalid inputs
are not architectural claims. Directed tests reproduce both original manual
sequences and the original L=8 placement, while the RTL regression checks all
16,384 bit-reversed addresses and 204,864 total unit vectors. The integration
regression adds all 16 MSTAT values and 50,112 mixed stateful cycles.

Register selection, I writeback gating, simultaneous data transfers,
multifunction ordering, alternate-bank interactions, stalls, loops, interrupts,
and external transaction timing remain outside this function block itself.
The bounded Type 2 slice now uses it for immediate DM writes: all DAG1 I/M
selections, normal-order post-modification, bit-reversed old-I address output,
arbitrary DMACK waits, and completion-only selected-I writeback pass directed
tests and the 50,035-clock logical model/RTL differential. A bounded native-DM
wrapper adds 50,027 clocks verifying state-8 old-value capture, full-cycle
waits, and state-7 completion-only postmodify. Whole-core event arbitration
remains outside that slice
[ADI-UM-1989, printed pp. 3-1–3-5, 5-9–5-12, 6-1, 6-12, A-1, and A-6].

The bounded Type 21 integration slice now supplies the missing stored-register
selection and writeback path for standalone MODIFY. With `G=0`, it maps the
two-bit I and M fields to I0–I3 and M0–M3, selects the L corresponding to I,
uses normal-order I arithmetic even when MSTAT bit-reverse mode is active, and
writes only the selected I at cycle end. Type 12 separately attaches DAG1 to
the native shifter-plus-DM transfer phases and commits its selected-I update
only at qualified completion. Other direct DM transfers and multifunction
instructions remain unattached
[ADI-UM-1989, printed pp. 3-1–3-5, 6-14–6-15, A-4, A-7–A-8].
