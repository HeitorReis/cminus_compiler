# Arduino FPGA input module

This sketch converts a digit received over the Arduino serial port into the
home FPGA processor's parallel `IN` interface. Values are limited to `0` through
`7` and are zero-extended to 32 bits by the FPGA wrapper.

## Wiring

| Arduino default | FPGA signal | FPGA package pin | Purpose |
|---|---|---|---|
| D2 | `KEY[0]` | `PIN_88` | Value bit 0 (LSB) |
| D3 | `KEY[1]` | `PIN_89` | Value bit 1 |
| D4 | `KEY[2]` | `PIN_90` | Value bit 2 (MSB) |
| D5 | `KEY[3]` | `PIN_91` | Active-low submit/strobe |
| GND | GND | Board GND | Common reference |

Connect through the development board's header or expansion-board nets that
route to these FPGA pins; do not attempt to wire directly to the FPGA package.
The onboard keys/dial switches share these signals on the documented board
revision. Keep them inactive and ensure they cannot drive against the Arduino.

### Voltage warning

The FPGA interface is **3.3-V LVTTL**. Do not connect 5-V Arduino GPIO directly
to it. An Arduino Uno, classic Nano, or Mega requires a 5-to-3.3-V logic-level
shifter on all four Arduino-to-FPGA signals. A 3.3-V Arduino may connect directly
when its GPIO levels and board power arrangement are compatible. Always connect
grounds, and do not power the FPGA board from an Arduino GPIO or 3.3-V pin.

## Protocol

1. The Arduino holds submit high while idle.
2. It places the value on the three data lines and waits 3 ms.
3. It holds submit low for 5 ms, producing the falling edge expected by the
   processor.
4. It returns submit high and holds the data for another 3 ms.

The processor remains blocked at `IN` until step 3. There is currently no READY
or ACK wire from the FPGA, so send a serial digit only when the running program
is waiting for input. Sending a value before the processor reaches `IN` does not
queue it; another submit event will be required.

## Use

Open `io_module.ino` in the Arduino IDE, select the correct board and serial
port, then upload it. Open the Serial Monitor at **115200 baud** and send one
digit from `0` through `7`. Newline and whitespace are ignored. Send `?` or `h`
to print the command summary.

The default Arduino pins are declared at the top of the sketch and can be
changed without altering the FPGA protocol.
