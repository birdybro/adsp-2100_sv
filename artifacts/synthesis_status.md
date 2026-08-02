# Synthesis status

**Updated:** 2026-08-01

- Verilator 5.048 parses and lints the generated packages, class decoder,
  shared architectural-state execution boundary,
  original RESET/logical-phase owner,
  normal BR/BG phase controller and RESET-time native-pin wrapper,
  Type 1 dual-read action decoder,
  Type 2 action decoder and waited execution slice, Type 4 action and waited
  logical-DM slices,
  Type 5 action/logical/cache/native-PM execution, Type 6, Type 7, Type 8,
  Type 9, Type 10, Type 11, Type 12, Type 13, Type 14, Type 15,
  Type 16, Type 17, Type 19, Type 20, Type 22, Type 23, Type 24, Type 25, and
  Type 26
  decoders/integration slices, the standalone original four-pin interrupt
  recognizer, the standalone ordinary/PM-data HALT sequencer,
  the bounded NOP/Type 6/Type 7/Type 8/Type 9/Type 10/Type 11/Type 14/Type 15/Type 16/Type 17/Type 18/Type 19/Type 20/Type 21/Type 22/Type 23/Type 24/Type 25/Type 26 plus automatic-loop
  linear owner and its bounded normal-BR/BG, ordinary-fetch/HALT/TRAP, and
  structural ordinary-fetch/native-DM-wait compositions plus the Type 5/Type
  13 native-PM/HALT attachments,
  the shared-PM-owner selector and its normal-BR/BG composition, the
  attached retained-fetch, Type 5/cache, and Type 13/cache shared-PM/BR-BG
  compositions plus the combined three-real-client/shared-cache owner and its
  state-external Type 5/Type 13 action clients, the
  standalone and Type 13-integrated
  instruction cache, native PM and DM phase controllers and Type 13/Type 2/
  Type 4/Type 12 attachments,
  stack-control
  decoder/integration slice, Type 21
  decoder/integration slice, and source-backed
  condition, ALU, MAC, shifter, DAG, sequencer-flow, stateful register-file,
  stateful CNTR, stateful status/control, stateful status-stack, and stateful
  PC/count/loop stack plus bounded sequencer-integration RTL with `-Wall` and
  no warnings.
- Yosys is not installed in this environment. Original RESET/phase, normal
  BR/BG, standalone interrupt and HALT sequencing, bounded linear-owner,
  linear-owner/BR/BG,
  linear-owner/HALT, structural ordinary-fetch/native-DM-wait,
  shared-PM-owner, shared-PM-owner/BR-BG, and Type 5/Type 13 native-PM/HALT
  plus separate and combined retained-fetch/Type 5/Type 13 shared-PM/BR-BG
  synthesis scripts are wired into `make synth-yosys` for an equipped host.
- Quartus 17.0.2 full compilation of the bounded three-real-client/shared-
  cache/native-PM/BR-BG/HALT composition succeeds for Cyclone V
  `5CSEBA6U23I7`. It uses 8,156 ALMs, 3,036 fitted registers, three DSP blocks,
  and no block memory. Against its 20 ns virtual-pin smoke constraint,
  TimeQuest reports +1.340 ns worst multicorner setup, +0.165 ns worst hold,
  +9.045 ns worst minimum-pulse-width slack, 53.59 MHz worst slow-corner Fmax,
  and zero unconstrained clocks, ports, or paths. The verification-only
  aggregate `integration_conflict_o` observation is explicitly constrained for
  second-edge sampling; all architectural and owner-event outputs retain the
  one-cycle 50 MHz requirement. Expected non-timing warnings
  describe virtual-pin optimization, intentionally uninferred small/
  asynchronous arrays, and the Quartus Lite LogicLock license. Issue-boundary
  Type 8/Type 9 and Type 5 action registers, dedicated selected-bank PM-data
  DREG reads, fetched Type 8/Type 9/Type 14/Type 15/Type 16/Type 21/Type 23/Type 24/
  Type 25 reset-unknown
  validity propagation, and removal of a structurally redundant integration-local
  interrupt/action conflict cone close the old setup path without changing
  architectural issue, completion, old-value, or instruction-cycle behavior.
  Type 5/Type 13 completion outputs also select only their captured pending
  descriptors, eliminating an impossible live issue/decode-to-completion path.
  This qualifies common PM/cache structure, routed completion, retained retry,
  and grant-time masking for the three real clients plus their one
  architectural-state owner, sequential automatic Type 5/Type 13 issue, hit/
  recovery next-opcode installation, retirement-aligned interrupt entry,
  ordinary-fetch HALT, and Type 5/Type 13 forced-recovery HALT scheduling. It
  includes the Type 17 DREG/DAG/status/control/SB/PX validity sidecars and the
  implementation-only status-stack ASTAT/MSTAT/IMASK validity snapshots.
  OQ-016, TRAP/interrupt/HALT/BR cross-event priority, active-loop/DM
  composition, physical I/O, and whole-core timing closure remain outside it.
- Quartus 17.0.2 full compilation of the bounded fetched Type
  8/9/10/11/14/15/16/19/20/21/22/23/24/25/26 plus automatic-loop and active
  original-IRQ linear owner completes for Cyclone V `5CSEBA6U23I7`. It uses
  3,735 ALMs, 1,895 fitted registers, two DSP blocks,
  and no block memory. Against its 25 ns virtual-pin smoke constraint, worst
  multicorner setup slack is +5.337 ns, worst hold slack is +0.160 ns, worst
  slow-corner Fmax is 50.86 MHz, and TimeQuest
  reports zero unconstrained clocks, ports, or paths. The expected warnings
  describe virtual-pin optimization, intentionally uninferred tiny/asynchronous
  register arrays, fixed outputs of the bounded read-only PM interface, and the
  Quartus Lite LogicLock license. This qualifies the NOP/Type 6/Type 7/Type 8/Type 9/
  Type 10/Type 11/Type 14/Type 15/Type 16/Type 17/Type 18/Type 19/Type 20/Type 21/Type 22/Type 23/Type 24/Type 25/Type 26 plus automatic-loop and bounded
  interrupt ordinary-fetch owner, not reset-first-fetch, fetched-DM or PM-data
  IRQ priority, simultaneous events, PM data/cache, physical I/O, or whole-core
  timing closure. This bounded 25 ns constraint closes; it is not whole-core
  timing closure. A raw cycle-start DREG view and dedicated selected-bank PM-
  data read ports remove avoidable generic operand muxing, while issue-boundary
  Type 8/Type 9 action registers add no architectural instruction latency.
- Quartus 17.0.2 full compilation of the structural ordinary-fetch/native-DM-
  wait interrupt composition completes and closes at 25 ns on Cyclone V
  `5CSEBA6U23I7`. It uses 3,937 ALMs, 1,711 fitted registers, two DSP blocks,
  and no block memory. Worst multicorner setup slack is +1.850 ns, worst hold
  slack is +0.164 ns, worst slow-corner Fmax is 43.2 MHz, and TimeQuest reports
  zero unconstrained clocks, ports, or paths. Expected warnings describe
  virtual-pin optimization, intentionally uninferred small/asynchronous arrays,
  fixed outputs of the bounded interfaces, and the Quartus Lite LogicLock
  license. This qualifies the raw-DM cycle-control composition, not fetched DM
  instruction ownership, asynchronous IRQ synchronization, physical I/O, or
  whole-core timing closure.
- Quartus 17.0.2 full compilation of the retained Type 8/11/19/20/21/22/23/24/26-capable ordinary-
  fetch/shared-PM/BR-BG attachment succeeds for Cyclone V `5CSEBA6U23I7`.
  It uses 3,862 ALMs and 1,953 fitted registers, two DSP blocks, and no block
  memory. Against its stricter 20 ns virtual-pin smoke constraint, worst
  multicorner setup slack is +1.822 ns, worst hold slack is +0.165 ns, worst
  minimum-pulse-width slack is +9.049 ns, and worst slow-corner Fmax is 55.01
  MHz; TimeQuest reports zero unconstrained clocks, ports, or paths. Expected
  non-timing warnings concern virtual-pin optimization,
  intentionally uninferred tiny/asynchronous register arrays, fixed bounded-
  interface outputs, and the Quartus Lite LogicLock license. Retained fetch
  retry/routed completion, BR/BG output masking, and retained IRQ entry after
  grant remain functionally verified with raw Type 5/Type 13 descriptors; the
  unified three-client/cache/HALT composition and shared Type 8/Type 9 compute-
  datapath optimization are qualified separately; simultaneous raw-PM/IRQ
  priority, physical I/O, and whole-core timing closure remain open.
- Quartus 17.0.2 full compilation of the active-IRQ Type
  10/11/19/20/21/22/26 plus loop private-PM/BR-BG composition succeeds and
  closes at 25 ns. It uses 3,838 ALMs, 1,671 fitted registers, two DSPs, no
  block memory, +1.379 ns worst multicorner setup, +0.156 ns worst hold,
  42.34 MHz worst slow-corner Fmax, and zero unconstrained clocks, ports, or
  paths.
- Quartus 17.0.2 full compilation of the Type 10/11/19/20/21/22/26 plus
  automatic-loop active-IRQ ordinary-fetch/HALT/TRAP composition succeeds and
  closes at 25 ns. It uses 3,867 ALMs, 1,657 fitted registers, two DSPs, no block memory,
  +1.199 ns worst multicorner setup, +0.166 ns worst hold, 42.02 MHz worst
  slow-corner Fmax, and zero unconstrained clocks, ports, or paths.
- Quartus 17.0.2 full compilation of the bounded Type
  5/cache/shared-PM/BR-BG attachment passes for Cyclone V `5CSEBA6U23I7`.
  It uses 1,923 ALMs and 1,756 fitted registers, one DSP and no block memory.
  Against its 25 ns virtual-pin smoke constraint, worst multicorner setup
  slack is +3.950 ns, worst hold slack is +0.161 ns, worst slow-corner Fmax is
  47.51 MHz, and TimeQuest reports zero unconstrained clocks, ports, or paths.
  Expected warnings are limited to virtual-pin optimization and the Quartus
  Lite LogicLock license. This qualifies bounded Type 5 retry, routed
  completion, ordinary-fetch cache fill, PMDA qualification, and BR/BG output
  masking; unified Type 5/Type 13/fetch clients, physical I/O, and whole-core
  timing closure remain open.
- Quartus 17.0.2 full compilation of the bounded Type
  13/cache/shared-PM/BR-BG attachment passes for Cyclone V `5CSEBA6U23I7`.
  It uses 2,089 ALMs and 1,646 fitted registers, no block memory, and no DSP
  blocks. Against its 25 ns virtual-pin smoke constraint, worst multicorner
  setup slack is +8.194 ns, worst hold slack is +0.166 ns, worst slow-corner
  Fmax is 59.5 MHz, and TimeQuest reports zero unconstrained clocks, ports, or
  paths. Expected warnings are limited to virtual-pin optimization and the
  Quartus Lite LogicLock license. This qualifies the bounded Type 13 retry,
  routed completion, ordinary-fetch cache-fill, explicit PMDA qualifier, and
  BR/BG output-mask composition; ordinary-fetch/Type 5 architectural clients,
  complete event priority, physical I/O, and whole-core closure remain open.
- Quartus 17.0.2 full compilation of the bounded shared-PM-owner/BR-BG
  composition passes for Cyclone V `5CSEBA6U23I7`. It uses 190 ALMs and 84
  fitted registers, no block memory, and no DSP blocks. Against its 20 ns
  virtual-pin smoke constraint, worst multicorner setup slack is +11.053 ns,
  worst hold slack is +0.167 ns, worst slow-corner Fmax is 111.77 MHz, and
  TimeQuest reports zero unconstrained clocks, ports, or paths. Expected
  warnings are limited to virtual-pin optimization and the Quartus Lite
  LogicLock license. This qualifies shared descriptor issue inhibition and PM
  output masking; a Type 13 client is qualified separately above, while raw
  fetch/Type 5 clients, DM pins, physical I/O, and whole-core timing closure
  remain open.
- Quartus 17.0.2 full compilation of the bounded shared-PM-owner selector
  passes for Cyclone V `5CSEBA6U23I7`. It uses 160 ALMs and 77 fitted
  registers, no block memory, and no DSP blocks. Against its 20 ns virtual-pin
  smoke constraint, worst multicorner setup slack is +12.059 ns, worst hold
  slack is +0.168 ns, worst slow-corner Fmax is 125.93 MHz, and TimeQuest
  reports zero unconstrained clocks, ports, or paths. This qualifies the
  exactly-one selector plus one native PM controller and explicit descriptor
  PMDA propagation, not complete client attachment, request priority, physical
  I/O, or whole-core timing closure.
- Quartus 17.0.2 full compilation of the normal BR/BG controller passes for
  Cyclone V `5CSEBA6U23I7`. It uses 27 ALMs, 7 fitted registers, no block
  memory, and no DSP blocks. Against its 20 ns virtual-pin smoke constraint,
  worst multicorner setup slack is +12.350 ns, worst hold slack is +0.172 ns,
  worst slow-corner Fmax is 131.58 MHz, and TimeQuest reports zero
  unconstrained clocks, ports, or paths. The RESET-time asynchronous pin mux
  is intentionally a separate wrapper and this is not a whole-core result.
- Quartus 17.0.2 full compilation of the standalone ordinary/PM-data HALT
  sequencer passes for Cyclone V `5CSEBA6U23I7`. It uses 26 ALMs and 6 fitted
  registers, no block memory, and no DSP blocks. Against its 20 ns virtual-pin
  smoke constraint, worst multicorner setup slack is +12.584 ns, worst hold
  slack is +0.172 ns, worst slow-corner Fmax is 134.84 MHz, and TimeQuest
  reports zero unconstrained clocks, ports, or paths. This qualifies the
  four-state schedule and force-issue output; Type 5/Type 13 ownership is
  qualified in separate bounded projects, not in this standalone project,
  physical asynchronous input timing, or a whole core.
- Quartus 17.0.2 full compilation of the original RESET/logical-phase owner
  passes for Cyclone V `5CSEBA6U23I7`. It uses 26 ALMs, 15 registers, no block
  memory, and no DSP blocks. Against its 20 ns virtual-pin smoke constraint,
  worst multicorner setup slack is +12.432 ns, worst hold slack is +0.144 ns,
  worst slow-corner Fmax is 132.14 MHz, and TimeQuest reports zero
  unconstrained clocks, ports, or paths. This does not include reset-time PM
  pins or a whole core. Quartus also reports the expected constant
  `phase_valid_o`: portable synthesis cannot retain a runtime validity bit for
  an intentionally unspecified power-up state, so wrappers must assert RESET
  before consuming phase outputs.
- Quartus 17.0.2 full compilation of the bounded steady-state linear owner
  passes for Cyclone V `5CSEBA6U23I7`. It uses 885 ALMs, 1,020 fitted registers,
  no block memory, and no DSP blocks. Against its documented 25 ns virtual-pin
  smoke constraint, worst multicorner setup slack is +13.145 ns, worst hold
  slack is +0.166 ns, worst slow-corner Fmax is 84.35 MHz, and TimeQuest reports
  zero unconstrained clocks, ports, or paths. This is not a whole-core result.
- Quartus 17.0.2 full compilation of the bounded linear-owner/BR/BG
  composition passes for Cyclone V `5CSEBA6U23I7`. It uses 898 ALMs, 1,041
  fitted registers, no block memory, and no DSP blocks. Against its documented
  25 ns virtual-pin smoke constraint, worst multicorner setup slack is
  +12.845 ns, worst hold slack is +0.166 ns, worst slow-corner Fmax is
  82.27 MHz, and TimeQuest reports zero unconstrained clocks, ports, or paths.
  Expected warnings are limited to the Quartus Lite LogicLock license,
  constant outputs in this read-only bounded fetch path, and virtual-pin
  optimization. This is not multi-owner, physical-I/O, or whole-core timing
  closure.
- Quartus 17.0.2 full compilation of the bounded linear-owner/HALT
  composition passes for Cyclone V `5CSEBA6U23I7`. It uses 916 ALMs and 1,026
  fitted registers, no block memory, and no DSP blocks. Against its documented
  25 ns virtual-pin smoke constraint, worst multicorner setup slack is
  +12.809 ns, worst hold slack is +0.164 ns, worst slow-corner Fmax is
  82.03 MHz, and TimeQuest reports zero unconstrained clocks, inputs, outputs,
  or paths. Expected warnings are limited to the Quartus Lite LogicLock
  license, asynchronous-read small arrays, constant outputs in the bounded
  read-only owner, and virtual-pin optimization. This is ordinary-fetch HALT
  composition, not PM-data owner attachment, physical-I/O, multi-event, or
  whole-core timing closure.
- Quartus 17.0.2 full compilation of the combinational Type 3 direct-DM
  action decoder passes for Cyclone V `5CSEBA6U23I7` at a 20 ns virtual
  constraint. It uses 46 ALMs (32 combinational ALUTs) and no registers, RAM,
  or DSP blocks. Across four timing models, worst setup slack is +17.118 ns
  and worst hold slack is +0.237 ns, with zero unconstrained clocks, ports, or
  paths. The expected decoder-only LogicLock license warning does not affect
  compilation; this is action selection, not state/native-DM or whole-core
  timing closure.
- Quartus 17.0.2 Standard Fits of the bounded Type 3 logical state/transaction
  slice and native-DM attachment pass for Cyclone V `5CSEBA6U23I7` at 25 ns
  constraints. They use respectively 849 and 825 ALMs, 1,019 and 1,044 fitted
  registers, and no RAM or DSP blocks. Across four timing models their worst
  setup slacks are +11.556 and +11.702 ns, worst hold slacks are +0.167 and
  +0.160 ns, and worst slow-100C Fmax values are 74.38 and 75.20 MHz. Both
  have zero unconstrained clocks, inputs, outputs, or paths. Expected warnings
  are limited to virtual/incomplete pins, asynchronous small-array inference,
  constant bounded outputs, and the Quartus Lite LogicLock license. These are
  bounded-client fits, not whole-core, physical-I/O, or MiSTer timing closure.
- Quartus 17.0.2 full compilation of the combinational Type 1 dual-read
  action decoder passes for Cyclone V `5CSEBA6U23I7` at a 20 ns virtual
  constraint. It uses 53 ALMs and no registers, RAM, or DSP blocks. Across
  four timing models, worst setup slack is +11.769 ns and worst hold slack is
  +4.309 ns, with zero unconstrained clocks, ports, or paths. The
  constant-output and virtual-pin warnings are expected for this
  decoder-only project; this is action selection, not state, dual-bus, or
  whole-core timing closure.
- Quartus 17.0.2 full compilation of the combinational Type 4 action decoder
  passes for Cyclone V `5CSEBA6U23I7` at a 20 ns virtual constraint. It uses
  53 ALMs and no registers, RAM, or DSP blocks. Across four timing models,
  worst setup slack is +15.103 ns, worst hold slack is +0.286 ns, worst
  slow-corner Fmax is 204.21 MHz, and no paths are unconstrained. The
  constant-output and virtual-pin warnings are expected for this decoder-only
  project; this is not stateful execution or whole-core timing closure.
- Quartus 17.0.2 full compilation of the combinational Type 5 action decoder
  passes for Cyclone V `5CSEBA6U23I7` at a 20 ns virtual constraint. It uses
  51 ALMs and no registers, RAM, or DSP blocks. Across four timing models,
  worst setup slack is +12.323 ns, worst hold slack is +4.281 ns, worst
  slow-corner Fmax is 130.26 MHz, and no paths are unconstrained. The
  constant-output and virtual-pin warnings are expected for this decoder-only
  project; this is not state/cache/native-PM or whole-core timing closure.
- Quartus 17.0.2 Standard Fits of the bounded Type 5 logical execution,
  cache composition, and native-PM attachment pass for Cyclone V
  `5CSEBA6U23I7` at 25 ns virtual constraints. They use respectively 1,681,
  1,912, and 1,935 ALMs; 1,262, 1,672, and 1,757 fitted registers; one DSP
  block each; and no RAM. Across four timing models their worst setup slacks
  are +0.811, +4.571, and +3.967 ns; worst hold slacks are +0.166, +0.164,
  and +0.168 ns; worst slow-corner Fmax values are 41.34, 48.95, and
  47.54 MHz; and every project is fully constrained for setup and hold.
  Expected warnings are limited to virtual/incomplete pins, constant bounded-
  slice outputs/sources, and the Quartus Lite LogicLock license. These are
  bounded-client results; the native project now includes uncached interrupt-
  recognition deferral but not PC/status entry. They are not whole-core,
  physical-I/O, or MiSTer closure.
- Quartus 17.0.2 Standard Fit of the bounded Type 4 logical-DM slice passes
  for Cyclone V `5CSEBA6U23I7` at a 25 ns virtual constraint. It uses 1,677
  ALMs, 1,258 fitted registers, one DSP block, and no RAM. Across four timing
  models, worst setup slack is +3.644 ns, worst hold slack is +0.104 ns, and
  worst slow-corner Fmax is 46.83 MHz, with zero unconstrained clocks, inputs,
  outputs, or paths. An initial Auto Fit had a -0.215 ns multicorner hold
  failure; Standard Fit corrected placement and closed it without changing
  the constraint. Expected warnings are limited to virtual/incomplete pins,
  constant bounded-slice outputs/sources, and the Quartus Lite LogicLock
  license. This is logical one-clock compute/DAG/DM capture-and-commit
  evidence, not native phase, whole-core, physical-I/O, or MiSTer closure.
- Quartus 17.0.2 Standard Fit of the bounded Type 4/native-DM attachment
  passes for Cyclone V `5CSEBA6U23I7` at a 25 ns virtual constraint. It uses
  1,693 ALMs, 1,226 fitted registers, one DSP block, and no RAM. Across four
  timing models, worst setup slack is +1.121 ns, worst hold slack is +0.167 ns,
  and worst slow-corner Fmax is 41.88 MHz, with zero unconstrained clocks,
  inputs, outputs, or paths. Expected warnings are the virtual/incomplete-pin,
  asynchronous small-array, constant bounded-output, and Quartus Lite
  LogicLock messages. This qualifies one Type 4 client attachment, not
  whole-core ownership, physical-I/O timing, or MiSTer closure.
- Quartus 17.0.2 full compilation of the native DM phase controller passes
  for Cyclone V `5CSEBA6U23I7` at its 20 ns standalone constraint. It uses
  100 ALMs and 57 fitted registers with no RAM or DSP blocks. Across four
  timing models, worst setup slack is +11.895 ns, worst hold slack is
  +0.169 ns, and worst slow-corner Fmax is 123.38 MHz, with zero unconstrained
  clocks, ports, or paths. The sole warning is the expected Quartus Lite
  LogicLock license warning. This is bounded logical DM pin-phase evidence,
  not instruction attachment, physical-I/O timing sign-off, or MiSTer closure.
- Quartus 17.0.2 full compilation of the bounded Type 2/native-DM attachment
  passes for Cyclone V `5CSEBA6U23I7` at its 20 ns constraint. It uses 608
  ALMs and 466 fitted registers with no RAM or DSP blocks. Across four timing
  models, worst setup slack is +2.590 ns, worst hold slack is +0.159 ns, and
  worst slow-corner Fmax is 57.44 MHz, with zero unconstrained clocks, ports,
  or paths. Constant DM-read and virtual-pin warnings are expected for this
  write-only bounded project; this is not whole-core, physical-I/O, or MiSTer
  timing closure.
- Quartus 17.0.2 full compilation of the bounded Type 12/native-DM attachment
  passes for Cyclone V `5CSEBA6U23I7` at its 20 ns constraint. It uses 1,739
  ALMs and 1,139 fitted registers with no RAM or DSP blocks. Across four
  timing models, worst setup slack is +1.262 ns, worst hold slack is
  +0.167 ns, and worst slow-corner Fmax is 53.37 MHz, with zero unconstrained
  clocks, ports, or paths. Asynchronous register/DAG arrays remain in logic;
  this is bounded Type 12 phase-attachment evidence, not whole-core,
  physical-I/O, or MiSTer closure.
- Quartus 17.0.2 full compilation of the native PM phase controller passes
  for Cyclone V `5CSEBA6U23I7` at its 20 ns standalone constraint. It uses
  112 ALMs and 71 fitted registers with no RAM or DSP blocks. Across four
  timing models, worst setup slack is +12.825 ns, worst hold slack is
  +0.167 ns, and worst slow-corner Fmax is 139.37 MHz, with zero unconstrained
  clocks, ports, or paths. This is a bounded logical pin-phase fit, not
  Type 13/fetch attachment, physical I/O timing sign-off, or MiSTer closure.
- Quartus 17.0.2 full compilation of the bounded Type 13/cache/native-PM
  attachment passes for Cyclone V `5CSEBA6U23I7` at its 20 ns constraint. It
  uses 2,102 ALMs and 1,658 fitted registers with no RAM or DSP blocks. Across
  four timing models, worst setup slack is +3.666 ns, worst hold slack is
  +0.167 ns, and worst slow-corner Fmax is 61.22 MHz, with zero unconstrained
  clocks, ports, or paths. Quartus retains the asynchronous cache and DAG
  arrays in logic/registers; expected warnings also identify virtual pins and
  constant upper interrupt-vector bits. This qualifies bounded Type 13 phases
  and uncached interrupt-recognition deferral, not PC/status entry, whole-core,
  physical-I/O, or MiSTer closure.
- Quartus 17.0.2 Standard Fit of the bounded Type 13/cache/native-PM/HALT
  attachment passes for Cyclone V `5CSEBA6U23I7` at its 25 ns constraint. It
  uses 2,094 ALMs and 1,655 fitted registers with no RAM or DSP blocks. Across
  four timing models, worst setup slack is +7.946 ns, worst hold slack is
  +0.168 ns, and worst slow-corner Fmax is 58.64 MHz, with zero unconstrained
  clocks, ports, or paths. The expected warning is the Quartus Lite LogicLock
  license; asynchronous cache/DAG arrays remain in logic/registers. This is
  bounded Type 13/HALT handoff evidence, not shared-owner, physical-I/O, or
  MiSTer closure.
- Quartus 17.0.2 Standard Fit of the bounded Type 5/cache/native-PM/HALT
  attachment passes for Cyclone V `5CSEBA6U23I7` at its 25 ns constraint. It
  uses 1,946 ALMs and 1,768 fitted registers with no RAM and one DSP block.
  Across four timing models, worst setup slack is +3.651 ns, worst hold slack
  is +0.166 ns, and worst slow-corner Fmax is 46.84 MHz, with zero
  unconstrained clocks, ports, or paths. The expected warning is the Quartus
  Lite LogicLock license; asynchronous cache/DAG arrays remain in logic/
  registers. This is bounded Type 5/HALT handoff evidence, not shared-owner,
  physical-I/O, or MiSTer closure.
- Quartus 17.0.2 full compilation of the bounded Type 2 immediate-DM-write
  slice passes for Cyclone V `5CSEBA6U23I7` at its 20 ns standalone
  constraint. It uses 581 ALMs and 430 fitted registers with no RAM or DSP
  blocks. Across four timing models, worst setup slack is +3.590 ns, worst
  hold slack is +0.165 ns, and worst slow-corner Fmax is 60.94 MHz, with zero
  unconstrained clocks, ports, or paths. Constant DM-read/PM outputs and
  asynchronous-read DAG arrays are expected; this is bounded logical-write
  evidence, not native-pin or MiSTer timing closure.
- Quartus 17.0.2 full compilation of the standalone instruction cache passes
  for Cyclone V `5CSEBA6U23I7` at its 20 ns constraint. It uses 310 ALMs and
  429 fitted registers with no RAM or DSP blocks. Across four timing models,
  worst setup slack is +7.071 ns, worst hold slack is +0.140 ns, and worst
  slow-corner Fmax is 77.35 MHz, with zero unconstrained clocks, ports, or
  paths. Quartus reports the asynchronous-read 16-by-24 array as uninferred
  RAM; this is bounded cache-block evidence, not whole-core/MiSTer closure.
- Quartus 17.0.2 full compilation of the cache-integrated Type 13 boundary
  passes for Cyclone V `5CSEBA6U23I7` at 20 ns. It uses 1,937 ALMs and 1,446
  fitted registers with no RAM or DSP blocks. Across four timing models, worst
  setup slack is +2.615 ns, worst hold slack is +0.166 ns, and worst
  slow-corner Fmax is 57.52 MHz, with zero unconstrained clocks, ports, or
  paths. Quartus retains the asynchronous-read instruction-cache and DAG
  arrays in logic/registers; this is bounded composition evidence, not native
  PM-pin or MiSTer timing closure.
- Quartus 17.0.2 full compilation of the bounded Type 13 shifter-plus-PM
  transaction/cache-recovery slice passes for Cyclone V `5CSEBA6U23I7` at
  its 21 ns standalone constraint. It uses 1,640 ALMs and 1,002 fitted
  registers with no RAM or DSP blocks. Across four timing models, worst setup
  slack is +1.172 ns, worst hold slack is +0.168 ns, and worst slow-corner
  Fmax is 50.43 MHz, with zero unconstrained clocks, ports, or paths. The
  unassigned physical clock pin and constant DM-access output are expected in
  this virtual-pin smoke project; this is bounded logical PM/cache-recovery
  evidence, not an actual cache monitor, native-pin, or MiSTer timing claim.
- Quartus 17.0.2 full compilation of the bounded Type 12 shifter-plus-DM
  transaction slice passes for Cyclone V `5CSEBA6U23I7` at its 21 ns
  standalone constraint. It uses 1,704 ALMs and 1,091 fitted registers with
  no RAM or DSP blocks. Across four timing models, worst setup slack is
  +1.377 ns, worst hold slack is +0.166 ns, and worst slow-corner Fmax is
  50.96 MHz, with zero unconstrained clocks, ports, or paths. The one
  unassigned physical clock pin is expected in this virtual-pin smoke
  project; this is bounded logical-bus evidence, not native-pin or MiSTer
  timing closure.
- Quartus 17.0.2 full compilation of the bounded Type 23 DIVQ slice passes
  for Cyclone V `5CSEBA6U23I7` at its 20 ns standalone constraint. It uses
  316 ALMs and 341 fitted registers (338 design registers plus three routing
  duplicates), with no RAM or DSP blocks. Across four timing models, worst
  setup slack is +7.009 ns, worst hold slack is +0.164 ns, and worst
  slow-100C Fmax is 77.71 MHz, with zero unconstrained clocks, ports, or
  paths. This is bounded-slice evidence, not whole-core or MiSTer timing
  closure.
- Quartus 17.0.2 full compilation of the bounded Type 24 DIVS slice passes
  for Cyclone V `5CSEBA6U23I7` at its 20 ns standalone constraint. It uses
  351 ALMs and 381 fitted registers (372 design registers plus nine routing
  duplicates), with no RAM or DSP blocks. Across four timing models, worst
  setup slack is +8.448 ns, worst hold slack is +0.168 ns, and worst
  slow-corner Fmax is 86.81 MHz, with zero unconstrained clocks, ports, or
  paths. This is bounded-slice evidence, not whole-core or MiSTer timing
  closure.
- Quartus 17.0.2 full compilation of the bounded phase-aware Type 22 TRAP
  slice passes for Cyclone V `5CSEBA6U23I7` at its 20 ns standalone
  constraint. It uses 116 ALMs and 67 fitted registers (53 design registers
  plus fourteen routing duplicates), with no RAM or DSP blocks. Across four
  timing models, worst setup slack is +7.592 ns, worst hold slack is
  +0.069 ns, and worst slow-corner Fmax is 80.59 MHz, with zero unconstrained
  clocks, ports, or paths. This is bounded phase-controller evidence, not
  whole-core or MiSTer timing closure.
- Quartus 17.0.2 full compilation of the bounded Type 20 conditional-return
  slice passes for Cyclone V `5CSEBA6U23I7` at its 20 ns standalone
  constraint. It uses 318 ALMs and 417 fitted registers with no RAM or DSP
  blocks. Across four timing models, worst setup slack is +7.725 ns, worst
  hold slack is +0.136 ns, and worst slow-corner Fmax is 81.47 MHz, with zero
  unconstrained clocks, ports, or paths. This is bounded-slice evidence, not
  whole-core or MiSTer timing closure.
- Quartus 17.0.2 full compilation of the bounded Type 19 indirect-transfer
  slice passes for Cyclone V `5CSEBA6U23I7` at its 20 ns standalone
  constraint. It uses 353 ALMs and 400 fitted registers with no RAM or DSP
  blocks. Across four timing models, worst setup slack is +7.520 ns, worst
  hold slack is +0.045 ns, and worst slow-corner Fmax is 80.93 MHz, with zero
  unconstrained clocks, ports, or paths. This is bounded-slice evidence, not
  whole-core or MiSTer timing closure.
- Quartus 17.0.2 full compilation of the bounded Type 11 DO UNTIL setup slice
  passes for Cyclone V `5CSEBA6U23I7` at its 20 ns standalone constraint. It
  uses 308 ALMs and 402 fitted registers with no RAM or DSP blocks. Across
  four timing models, worst setup slack is +7.263 ns, worst hold slack is
  +0.074 ns, and worst slow-corner Fmax is 78.51 MHz, with zero unconstrained
  clocks, ports, or paths. This is bounded setup evidence, not whole-core or
  MiSTer timing closure.
- Quartus 17.0.2 full compilation of the bounded Type 10 direct-transfer slice
  passes for Cyclone V `5CSEBA6U23I7` at its 20 ns standalone constraint. It
  uses 284 ALMs and 334 fitted registers with no RAM or DSP blocks. Across
  four timing models, worst setup slack is +8.138 ns, worst hold slack is
  +0.167 ns, and worst slow-corner Fmax is 84.3 MHz, with zero unconstrained
  clocks, ports, or paths. This is bounded-slice evidence, not whole-core or
  MiSTer timing closure.
- Quartus 17.0.2 full compilation of the bounded Type 8 ALU/MAC-plus-MOVE
  slice passes for Cyclone V `5CSEBA6U23I7` at its documented 22 ns
  standalone constraint. It uses 983 ALMs, 693 fitted registers, one DSP
  block, and no RAM. Across four timing models, worst setup slack is +1.131
  ns, worst hold slack is +0.177 ns, and worst slow-corner Fmax is 47.92 MHz,
  with zero unconstrained clocks, ports, or paths. A 20 ns run missed setup by
  1.721 ns; the relaxed unit constraint is explicit evidence that this
  monolithic execution slice needs phase scheduling before any 50 MHz or
  MiSTer timing claim.
- Quartus 17.0.2 full compilation of the bounded Type 9 conditional-compute
  slice passes for Cyclone V `5CSEBA6U23I7` at its documented 22 ns
  standalone constraint. It uses 970 ALMs, 697 fitted registers, one DSP
  block, and no RAM. Across four timing models, worst setup slack is +1.140
  ns, worst hold slack is +0.165 ns, and worst slow-corner Fmax is 47.94 MHz,
  with zero unconstrained clocks, ports, or paths. The initial 20 ns fit
  missed setup by 1.735 ns and measured 46.01 MHz at the worst slow corner;
  this is bounded-slice evidence, not whole-core or MiSTer timing closure.
- Quartus 17.0.2 full compilation of the bounded Type 14 shifter-plus-MOVE
  slice passes for Cyclone V `5CSEBA6U23I7`. It uses 1,032 ALMs and 565
  fitted registers (502 design registers plus 63 fitter-created routing
  duplicates), with no RAM or DSP blocks. Across four timing models, worst
  setup slack is +3.041 ns and worst hold slack is +0.171 ns against 20 ns,
  with zero unconstrained clocks, ports, or paths. Constant no-PM/no-DM
  outputs, fail-closed unsupported encodings, and same-destination conflict
  suppression are asserted properties of the bounded slice.
- Quartus 17.0.2 full compilation of the bounded Type 16 conditional-shift
  slice passes for Cyclone V `5CSEBA6U23I7`. It uses 840 ALMs and 520 fitted
  registers with no RAM or DSP blocks. Across four timing models, worst setup
  slack is +2.304 ns and worst hold slack is +0.173 ns against 20 ns, with
  zero unconstrained clocks, ports, or paths. Constant no-PM/no-DM outputs and
  condition-false write suppression are asserted properties of the slice.
- Quartus 17.0.2 full compilation of the bounded Type 15 immediate-shift slice
  passes for Cyclone V `5CSEBA6U23I7`. It uses 774 ALMs and 501 fitted
  registers with no RAM or DSP blocks. Across four timing models, worst setup
  slack is +3.728 ns and worst hold slack is +0.057 ns against 20 ns, with
  zero unconstrained clocks, ports, or paths. Constant no-PM/no-DM and
  conflict outputs are asserted properties of this bounded instruction slice.
- Quartus 17.0.2 full compilation of the bounded Type 6 immediate-load slice
  passes for Cyclone V `5CSEBA6U23I7`. It uses 302 ALMs and 484 registers with
  no RAM or DSP blocks. Across four timing models, worst setup slack is +8.167
  ns and worst hold slack is +0.133 ns against 20 ns, with zero unconstrained
  clocks, ports, or paths. Constant no-PM/no-DM and conflict outputs are
  asserted properties of this bounded instruction slice.
- Quartus 17.0.2 full compilation of the bounded Type 7 immediate-load slice
  passes for Cyclone V `5CSEBA6U23I7`. It uses 572 ALMs and 886 fitted
  registers with no RAM or DSP blocks. Across four timing models, worst setup
  slack is +13.448 ns and worst hold slack is +0.185 ns against 25 ns; worst
  slow-100C Fmax is 86.57 MHz, and zero clocks, ports, or paths are
  unconstrained. Expected warnings are limited to virtual/incomplete pins,
  small asynchronous arrays, constant bounded outputs, and Quartus Lite
  LogicLock licensing. This is not whole-core or MiSTer timing closure.
- Quartus 17.0.2 full compilation of the generated class-decoder smoke project
  passes for Cyclone V `5CSEBA6U23I7`. The constrained virtual-pin fit uses 55
  ALMs, 63 combinational ALUTs, 0 registers, 0 RAM blocks, and 0 DSP blocks.
  Across four timing models, worst setup slack is 14.723 ns and worst hold
  slack is 0.407 ns against the 20 ns virtual I/O constraint, with zero
  unconstrained clocks, ports, or paths.
- Quartus 17.0.2 full compilation of the Type 17 internal-MOVE action decoder
  passes for Cyclone V `5CSEBA6U23I7`. It uses 42 ALMs, 24 combinational
  ALUTs, no registers, no RAM, and no DSPs. Across four timing models, worst
  setup slack is +15.704 ns and worst hold slack is +0.462 ns against 20 ns,
  with zero unconstrained clocks, ports, or paths.
- Quartus 17.0.2 full compilation of the bounded Type 17 state slice passes
  after extracting its reusable architectural-state owner for Cyclone V
  `5CSEBA6U23I7`. It uses 808 ALMs and 892 registers with no M10K or DSP
  blocks. Across four timing models, worst setup slack is +5.503 ns and worst
  hold slack is +0.168 ns against 20 ns; worst slow-corner Fmax is 68.98 MHz,
  with zero unconstrained clocks, ports, or paths. Constant no-PM/no-DM
  outputs and untouched stack-status fragments are expected properties of
  this bounded instruction slice.
- Quartus 17.0.2 full compilation of the Type 26 stack-control decoder passes
  for Cyclone V `5CSEBA6U23I7`. The constrained virtual-pin fit uses 25 ALMs,
  12 combinational ALUTs, 0 registers, 0 RAM blocks, and 0 DSP blocks. Across
  four timing models, worst setup slack is +17.244 ns and worst hold slack is
  +0.287 ns against the 20 ns virtual I/O constraint, with zero unconstrained
  clocks, ports, or paths.
- Quartus 17.0.2 full compilation of the stateful Type 26 integration slice
  passes. It uses 351 ALMs, 260 combinational logic ALUTs, exactly 465 design
  registers plus twelve fitter-created routing duplicates, no RAM, and no
  DSPs. The 465 design registers comprise the bounded PC/count/loop/status
  stack, CNTR, and live ASTAT/MSTAT/IMASK state. Across four timing models,
  worst setup is +10.550 ns and worst hold is +0.165 ns against 20 ns, with
  zero unconstrained clocks, ports, or paths.
- Quartus 17.0.2 full compilation of the bounded Type 25 MR-saturation slice
  passes. It uses 144 ALMs, exactly 92 design registers, no RAM, and no DSPs.
  Across four timing models, worst setup slack is +11.443 ns and worst hold
  slack is +0.246 ns against the 20 ns virtual I/O constraint, with zero
  unconstrained clocks, ports, or paths. Quartus reports
  `internal_conflict_o` as constant low; the bounded exclusive execution mux
  makes that signal an asserted invariant rather than an untested output.
- Quartus 17.0.2 full compilation of the bounded Type 18 mode-control slice
  passes. It uses 46 ALMs, 30 combinational ALUTs, exactly four MSTAT
  registers, no RAM, and no DSPs. Across four timing models, worst setup slack
  is +12.168 ns and worst hold slack is +0.173 ns against the 20 ns virtual
  I/O constraint, with zero unconstrained clocks, ports, or paths. Quartus
  reports `internal_conflict_o` constant low, matching its asserted invariant.
- Quartus 17.0.2 full compilation of the bounded Type 21 address-modify slice
  passes. It uses 526 ALMs, 543 design combinational ALUTs, exactly 360
  architectural data/valid registers plus fourteen fitter-created routing
  duplicates, no RAM, and no DSPs. Across four timing models, worst setup
  slack is +2.361 ns and worst hold slack is +0.185 ns against the 20 ns
  constraint, with zero unconstrained clocks, ports, or paths. Constant-low
  conflict and PM/DM data-access outputs are asserted properties of this
  bounded instruction.
- Quartus 17.0.2 full compilation of the condition-logic smoke project passes
  for Cyclone V `5CSEBA6U23I7`. The constrained virtual-pin fit uses 10 ALMs,
  6 combinational ALUTs, 0 registers, 0 RAM blocks, and 0 DSP blocks.
- TimeQuest reports zero unconstrained clocks, ports, or paths against a
  20 ns virtual I/O constraint. Across the four fitted timing models, the
  worst setup slack is 17.927 ns and worst hold slack is 0.283 ns. These are
  unit-level virtual-pin estimates, not whole-core Fmax or MiSTer closure.
- Quartus full compilation of the separately constrained ALU smoke project
  also passes. Its virtual-pin fit uses 161 ALMs, 196 combinational ALUTs,
  0 registers, 0 RAM blocks, and 0 DSP blocks. Across the four fitted timing
  models, worst setup slack is 9.686 ns and worst hold slack is 0.212 ns
  against the 20 ns virtual I/O constraint; setup and hold are fully
  constrained.
- Quartus full compilation of the separately constrained MAC smoke project
  passes. Its virtual-pin fit uses 228 ALMs, 228 combinational ALUTs, one DSP
  block, 0 registers, and 0 RAM blocks. Across the four fitted timing models,
  worst setup slack is 3.209 ns and worst hold slack is 0.418 ns against the
  20 ns virtual I/O constraint; setup and hold are fully constrained.
- Quartus full compilation of the separately constrained shifter smoke project
  passes. Its virtual-pin fit uses 374 ALMs, 580 combinational ALUTs, 0
  registers, 0 RAM blocks, and 0 DSP blocks. Across the four fitted timing
  models, worst setup slack is 8.795 ns and worst hold slack is 0.434 ns
  against the 20 ns virtual I/O constraint; setup and hold are fully
  constrained.
- Quartus full compilation of the separately constrained DAG smoke project
  passes. Its virtual-pin fit uses 172 ALMs, 305 combinational ALUTs, 0
  registers, 0 RAM blocks, and 0 DSP blocks. Across the four fitted timing
  models, worst setup slack is 7.201 ns and worst hold slack is 0.527 ns
  against the 20 ns virtual I/O constraint; setup and hold are fully
  constrained.
- Quartus full compilation of the separately constrained sequencer-flow smoke
  project passes. Its virtual-pin fit uses 74 ALMs, 44 combinational ALUTs, 0
  registers, 0 RAM blocks, and 0 DSP blocks. Across the four fitted timing
  models, worst setup slack is 14.139 ns and worst hold slack is 0.386 ns
  against the 20 ns virtual I/O constraint; setup and hold are fully
  constrained.
- Quartus full compilation of the separately constrained stateful CNTR smoke
  project passes. Its virtual-pin fit uses 72 ALMs, 49 combinational ALUTs,
  exactly 15 architectural registers plus seven fitter-created routing
  duplicates, no RAM, and no DSPs. Its virtual internal controls use the
  documented 5 ns registered-source assumption. Across four timing models,
  worst setup is +11.818 ns and worst hold is +0.171 ns against 20 ns, with
  zero unconstrained paths.
- Quartus full compilation of the bounded sequencer-integration project
  passes. It uses 388 ALMs, 383 fitted combinational ALUTs, exactly 381 design
  registers plus fourteen fitter-created routing duplicates, no RAM, and no
  DSPs. The 381 design registers are exactly the 366 PC/count/loop-stack bits
  plus the 15 CNTR data/valid bits. Across four timing models, worst setup is
  +6.776 ns and worst hold is +0.166 ns against 20 ns, with zero unconstrained
  clocks, ports, or paths.
- Quartus full compilation of the register-file smoke project passes with the
  DE10-Nano 50 MHz input constrained on `PIN_V11` and 356 virtual data/control
  pins. Analysis identifies exactly 554 design registers; deterministic
  Standard Fit seed 2 adds 55 secondary routing-optimization duplicates. The
  fit uses 1,084 ALMs, 1,353 combinational ALUTs, no RAM, and no DSPs. Across
  the four timing models, worst setup slack is 9.985 ns and worst hold slack is
  0.109 ns against the 20 ns constraint, with zero unconstrained clocks, ports,
  or paths.
- Quartus Lite emits its recurring unavailable-LogicLock warning; none of the
  projects uses LogicLock.
- Quartus full compilation of the status/control smoke project passes. It uses
  84 ALMs, 41 combinational ALUTs, exactly 21 architectural registers with no
  fitter-created register duplicates, no RAM, and no DSPs. Its virtual internal
  controls have an explicit 5 ns same-clock registered-source input-arrival
  assumption. Across four timing models, worst setup is +11.811 ns and worst
  hold is +0.169 ns against 20 ns, with zero unconstrained paths.
- Quartus full compilation of the status-stack smoke project passes. It uses 53
  ALMs, 30 combinational logic ALUTs, exactly 68 design registers plus one
  fitter-created routing duplicate, no RAM, and no DSPs. Its virtual internal
  controls use the same documented 5 ns registered-source assumption. Across
  four timing models, worst setup is +13.077 ns and worst hold is +0.172 ns
  against 20 ns, with zero unconstrained paths.
- Quartus full compilation of the PC/count/loop stack-storage smoke project
  passes. It uses 245 ALMs, 177 combinational logic ALUTs, exactly 366 design
  registers plus six fitter-created routing duplicates, no RAM, and no DSPs.
  Its virtual internal controls use the documented 5 ns registered-source
  assumption. Across four timing models, worst setup is +10.383 ns and worst
  hold is +0.162 ns against 20 ns, with zero unconstrained paths. Quartus
  reports the asynchronous-read arrays as intentionally uninferred RAM and
  flags constant SSTAT fragment bits 4/5; those bits belong to the separate
  status-stack slice.
- Quartus full compilation of the bounded MSTAT-consumer integration project
  passes. It uses 543 ALMs, 578 combinational ALUTs, 492 design implementation
  registers plus two fitter-created routing duplicates, no RAM, and no DSPs.
  The retained state comprises 480 observable DREG bits plus ASTAT/MSTAT; this
  top intentionally does not expose the other feedback/control registers.
  Across four timing models, worst setup is +5.529 ns and worst hold is
  +0.168 ns against 20 ns, with zero unconstrained paths.
- SymbiYosys and Yosys are not installed. `make formal` strictly lints the 74
  available assertion harnesses before reporting that proof execution is
  skipped.

There is no whole-core utilization, latch-count, Fmax, critical-path, or
timing-closure claim. `make synth-yosys` reports an explicit tool-availability
skip; `make synth-quartus` runs the bounded class-decode,
internal-move-decode, stack-control-decode, stack-control-integration,
Type-6 integration,
normal BR/BG bus control,
bounded NOP/Type-6/Type-7/Type-9/Type-14/Type-15/Type-16/Type-17/Type-18/Type-23/Type-25 linear ownership,
bounded linear-ownership/normal-BR/BG composition,
Type-8 integration,
Type-9 integration,
Type-2 integration,
Type-12 integration,
Type-13 base and cache-integrated integration,
Type-14 integration,
Type-15 integration,
Type-16 integration,
Type-18 integration,
Type-19 integration,
Type-20 integration,
Type-21 integration,
Type-22 integration,
Type-23 integration,
Type-24 integration,
Type-25 integration,
condition, ALU, MAC, shifter, DAG, sequencer-flow, CNTR, sequencer-stack,
sequencer-integration, register-file, status-register, and status-stack block
smoke projects plus the bounded MSTAT integration project.
