# RZ301 EP4CE6 board reference

Use this reference for `processor/Processor_home_testing/` only.

## Verified target

- Family: Cyclone IV E
- Device: `EP4CE6E22C8`
- On-board oscillator: 50 MHz on `PIN_23`
- General board I/O used by the vendor examples: `3.3-V LVTTL`
- Configuration device in the basic vendor examples: EPCS4
- Unused pins: reserve as input tri-stated

One old vendor example selects `EP4CE10E22C8`; the remaining basic and
peripheral examples, the bundle name, and the supplied board material identify
the home target as EP4CE6. If the physical FPGA marking differs, the marking
wins and the project must be reviewed before compilation or programming.

## Core user-interface pins

The vector mappings below follow the indexing used by the vendor example QSFs.

| Function | Top-level signal | FPGA location |
|---|---|---|
| 50 MHz clock | `CLOCK_50` | `PIN_23` |
| Reset button | `RESET_N` or documented equivalent | `PIN_25` |
| User input 0 | `KEY[0]` | `PIN_88` |
| User input 1 | `KEY[1]` | `PIN_89` |
| User input 2 | `KEY[2]` | `PIN_90` |
| User input 3 | `KEY[3]` | `PIN_91` |
| LED 0 / physical LED4 | `LED[0]` | `PIN_87` |
| LED 1 / physical LED3 | `LED[1]` | `PIN_86` |
| LED 2 / physical LED2 | `LED[2]` | `PIN_85` |
| LED 3 / physical LED1 | `LED[3]` | `PIN_84` |
| Digit select 0 / DIG1 | `DIG[0]` | `PIN_133` |
| Digit select 1 / DIG2 | `DIG[1]` | `PIN_135` |
| Digit select 2 / DIG3 | `DIG[2]` | `PIN_136` |
| Digit select 3 / DIG4 | `DIG[3]` | `PIN_137` |
| Segment 0 | `SEG[0]` | `PIN_128` |
| Segment 1 | `SEG[1]` | `PIN_121` |
| Segment 2 | `SEG[2]` | `PIN_125` |
| Segment 3 | `SEG[3]` | `PIN_129` |
| Segment 4 | `SEG[4]` | `PIN_132` |
| Segment 5 | `SEG[5]` | `PIN_126` |
| Segment 6 | `SEG[6]` | `PIN_124` |
| Segment 7 / decimal point | `SEG[7]` | `PIN_127` |

The vendor material labels `PIN_88..91` both as keys and dial switches. Treat
them as one four-bit input bank unless the physical board or a measured test
proves that the specific revision exposes distinct controls.

## Relevant QSF form

Use explicit assignments rather than relying on fitter defaults:

```tcl
set_global_assignment -name FAMILY "Cyclone IV E"
set_global_assignment -name DEVICE EP4CE6E22C8
set_global_assignment -name STRATIX_DEVICE_IO_STANDARD "3.3-V LVTTL"
set_global_assignment -name RESERVE_ALL_UNUSED_PINS "AS INPUT TRI-STATED"
set_location_assignment PIN_23 -to CLOCK_50
```

If a peripheral requires a different voltage standard, verify it against the
schematic and apply a per-pin or per-interface assignment rather than changing
unrelated board I/O. The supplied LM75A example is a known exception that uses
2.5 V.

## Differences from the university board

The university top level cannot be pinned unchanged:

- RZ301 has a multiplexed four-digit display: four digit-select lines and eight
  shared segment lines. The DE2-115 wrapper drives eight independent groups of
  seven segment lines.
- RZ301 provides four shared key/switch inputs plus a reset button, not the
  DE2-115 `SW[17:0]` interface.
- The home FPGA has far fewer logic elements and package pins. Internal
  `output_value[31:0]` and `pc[31:0]` buses must not be left as physical
  top-level outputs.

## Home processor interaction contract

The home wrapper uses the following verified project contract:

- `RESET_N` on `PIN_25` is the dedicated active-low processor reset.
- `KEY[2:0]` is an unsigned value from 0 through 7 and is zero-extended to
  32 bits before entering the processor core.
- `KEY[3]` is the active-low submit/strobe input. The existing control unit
  keeps an `IN` instruction blocked until it observes the submit signal's
  1-to-0 transition; do not replace this with automatic acknowledgement.
- Manual clock gating from the DE2-115 wrapper is not exposed on the RZ301.
- The four-digit display shows the processor `OUT` value using the board's
  multiplexed, active-low digit and segment lines.
- The single assigned LED is active-low and indicates the processor's
  conditional write signal.

## Validation

- QSF device, family, top-level entity, and source list agree.
- Every QSF `-to` target resolves to a top-level port.
- No physical pin is assigned more than once.
- Clock is on `PIN_23` and constrained to a 20 ns period in an SDC.
- Fitter reports no automatically placed user I/O and no incompatible I/O-bank
  voltage assignments.
- EP4CE6 resource usage fits with margin.
- Display digit order, segment order, and active polarity are confirmed on
  hardware with a minimal display test before processor output is trusted.
- Reset and user-input polarity are confirmed with a minimal bring-up test.
- An `IN` test proves that the PC remains blocked before submit, captures only
  values 0 through 7, and resumes on a new active-low submit event.

## Supplied evidence

Prefer these sources in order:

1. [Development board pin information.xlsx](<../RZ301 EP4CE6 development board/1-Altera Cyclone IV board V3.0/1- Schematic/01. Schematic diagram/Development board pin information.xlsx>)
2. [Development board schematic diagram V2.5.pdf](<../RZ301 EP4CE6 development board/1-Altera Cyclone IV board V3.0/1- Schematic/01. Schematic diagram/Development board schematic diagram V2.5.pdf>)
3. Vendor QSF examples inside [3-Experiment code.zip](<../RZ301 EP4CE6 development board/1-Altera Cyclone IV board V3.0/3-Experiment code.zip>)
4. [FAQ.pdf](<../RZ301 EP4CE6 development board/1-Altera Cyclone IV board V3.0/0-FPGA board Manual/FAQ.pdf>) and [Dev Board Manual.pdf](<../RZ301 EP4CE6 development board/1-Altera Cyclone IV board V3.0/2-Reference documentation/Dev Board Manual.pdf>)

Do not load unrelated e-books, component datasheets, drivers, or module archives
for ordinary pin-assignment work.
