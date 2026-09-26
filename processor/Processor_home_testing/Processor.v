module Processor(

	input CLOCK_50,
	input RESET_N,
	input [3:0] KEY,

	output LED,
	output [3:0] DIG,
	output [7:0] SEG

);

	wire divided_clock;
	wire fast_clock;
	freqDiv freq_divider(
		.CLOCK_50(CLOCK_50),
		.clk(divided_clock),
		.fast_clk(fast_clock)
	);

	// KEY[2:0] is the unsigned input value (0..7). KEY[3] is active-low
	// submit. ControlUnit keeps an IN instruction blocked until KEY[3]
	// makes the existing 1->0 transition.
	wire [31:0] peripheral_value;
	assign peripheral_value = {29'd0, KEY[2:0]};

	wire [31:0] output0;
	wire [31:0] output1;
	wire [31:0] output_value;
	wire [31:0] output3;
	wire [31:0] pc;
	wire write_condition;

	integrated processor_core(
		.clock(divided_clock),
		.fast_clock(fast_clock),
		.reset(~RESET_N),

		.peripheral_signal(KEY[3]),
		.peripheral_value(peripheral_value),

		.write_condition(write_condition),

		.output0(output0),
		.output1(output1),
		.output2(output_value),
		.output3(output3),
		.pc(pc)
	);

	// The board LEDs are active-low. LED indicates a successful conditional
	// write, matching LEDR[0] on the university board.
	assign LED = ~write_condition;

	home_display display(
		.clock(CLOCK_50),
		.reset_n(RESET_N),
		.number(output_value),
		.digit_select(DIG),
		.segments(SEG)
	);

endmodule
