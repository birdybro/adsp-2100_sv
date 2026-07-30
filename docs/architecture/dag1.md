# Data address generator 1

**Status: source-backed specification baseline**

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

Bit reverse reverses all 14 output address bits about the 6/7 boundary but
stores the post-modified I in normal order [ADI-UM-1989, printed p. 3-5].
Required tests enumerate all legal I/M pairings, I/L association, signed reads,
both wrap directions, non-power-of-two lengths, source examples, and
bit-reversed sequences.
