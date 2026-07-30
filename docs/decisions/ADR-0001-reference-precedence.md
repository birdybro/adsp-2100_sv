# ADR-0001: Reference precedence and claim confidence

- **Status:** Accepted
- **Date:** 2026-07-30
- **Tasks:** REF-001, DEV-001, ISA-001

## Context

The name “ADSP-2100 family” spans devices with substantially different memory,
peripheral, interrupt, clock, and bus implementations. A late family manual can
describe common computation semantics while also describing facilities absent
from the original external-memory ADSP-2100. The original 1989 manual itself
directs the reader to the separate data sheet for electrical timing and the
Cross-Software Manual for the complete programming reference
[ADI-UM-1989, printed pp. 1-9–1-10].

## Decision

Claims use the authority order in `AGENTS.md`. Device applicability is evaluated
separately from source authority. A family-wide statement supports the original
device only when the publication explicitly includes it or an original-device
source independently corroborates it.

Each nontrivial claim carries a manifest reference, printed page/section, and
confidence. Emulator behavior is evidence for a conflict or differential test,
not an architectural source. Unknown and conflicting behavior is recorded
before implementation.

## Consequences

- Later IDLE, SPORT, timer, boot, DMA, host-port, overlay, and flag behavior is
  excluded until original-device applicability is proven.
- The original-device manual and contemporary data sheet/data-book take
  precedence over convenient later descriptions.
- Documentation is intentionally incomplete where page-level evidence has not
  yet been extracted.
