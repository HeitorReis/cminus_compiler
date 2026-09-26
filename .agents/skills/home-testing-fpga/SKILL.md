---
name: home-testing-fpga
description: Configure, adapt, and validate the repository's home FPGA project for the RZ301 Cyclone IV EP4CE6 board, especially Quartus device selection, top-level ports, pin assignments, I/O standards, display multiplexing, and board bring-up. Do not use for the university DE2-115 project.
---

# Home FPGA testing

Keep the home-board implementation under `processor/Processor_home_testing/`
independent from the university project under `processor/Processor/`.

Before changing the home project, read
[references/rz301-board.md](references/rz301-board.md). It contains the curated
pin table, evidence hierarchy, interface differences, and validation criteria.

## Workflow

1. Inspect the home project's top-level RTL and QSF together. A QSF assignment
   is valid only when its target exists as a top-level port with the intended
   direction and width.
2. Confirm the fitted device is `EP4CE6E22C8`. Do not reuse DE2-115 package-pin
   names or the `EP4CE115F29C7` device setting.
3. Preserve the processor core when possible. Put board-specific adaptation,
   such as four-digit display multiplexing or reduced user input, in the home
   top-level wrapper or a clearly named home-only module.
4. Assign both the physical location and the applicable I/O standard. Reserve
   unused pins as input tri-stated.
5. Do not expose internal diagnostic buses as unconstrained physical outputs.
   Keep them internal, route selected bits to intended indicators, or mark them
   virtual only when that matches the debugging workflow.
6. Add a 50 MHz base-clock constraint when the home project has no valid SDC.
7. Validate the smallest useful scope first, then run a full Quartus compile
   when the toolchain is available. Check Analysis & Synthesis, Fitter pin
   warnings, resource fit on EP4CE6, and TimeQuest constraints before treating
   a generated SOF as hardware-ready.

## Boundaries

- Never modify `processor/Processor/` as a side effect of home-board work.
- Treat the supplied vendor bundle as read-only evidence. Use the curated
  reference first; consult a vendor example or schematic only for peripherals
  not covered there.
- Do not assume the RZ301 four-digit display is equivalent to the DE2-115's
  eight independent seven-segment displays.
- Do not invent a mapping for processor controls when the requested behavior
  does not identify reset, input strobe/value, stepping, or display selection.
  Document the missing behavioral choice separately from the known electrical
  pin mapping.
