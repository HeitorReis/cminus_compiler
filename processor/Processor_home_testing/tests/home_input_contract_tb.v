`timescale 1ns/1ps

module home_input_contract_tb;

	reg clock;
	reg reset;
	reg submit;
	reg [31:0] instruction;
	wire halted;
	wire [31:0] pc;

	reg board_clock;
	reg board_reset_n;
	reg [3:0] board_keys;
	wire board_led;
	wire [3:0] board_digits;
	wire [7:0] board_segments;

	ControlUnit control(
		.instruction(instruction),
		.peripheral_signal(submit),
		.clock(clock),
		.fast_clock(1'b0),
		.reset(reset),
		.halt_temporarily_signal(halted),
		.TypeCode(),
		.Load(),
		.should_store_link(),
		.Rh(),
		.Ro(),
		.Rd(),
		.extended_immediate(),
		.is_immediate(),
		.OpCode(),
		.should_use_data_memory(),
		.CondField(),
		.set_cond_bit(),
		.should_branch(),
		.should_branch_to_link()
	);

	PC_main program_counter(
		.branch_value(32'd0),
		.link_value(32'd0),
		.should_branch(1'b0),
		.write_condition(1'b1),
		.should_branch_to_link(1'b0),
		.is_immediate(1'b0),
		.halt_temporarily_signal(halted),
		.clock(clock),
		.fast_clock(1'b0),
		.reset(reset),
		.instruction_address(pc)
	);

	Processor board_wrapper(
		.CLOCK_50(board_clock),
		.RESET_N(board_reset_n),
		.KEY(board_keys),
		.LED(board_led),
		.DIG(board_digits),
		.SEG(board_segments)
	);

	always #5 clock = ~clock;
	always #10 board_clock = ~board_clock;

	initial begin
		clock = 1'b0;
		reset = 1'b1;
		submit = 1'b1;
		instruction = 32'd0;
		board_clock = 1'b0;
		board_reset_n = 1'b1;
		board_keys = 4'b1101;

		#1;
		if (board_wrapper.peripheral_value !== 32'd5)
			$fatal(1, "KEY[2:0] was not zero-extended to value 5");

		@(negedge clock);
		#1;
		reset = 1'b0;
		// Type 00, opcode 1001 is IN. Apply it between clock edges so the
		// reset and instruction transitions cannot race the DUT.
		instruction[27:26] = 2'b00;
		instruction[23:20] = 4'b1001;

		@(posedge clock);
		#1;
		if (halted !== 1'b1)
			$fatal(1, "IN did not block before submit");

		repeat (2) begin
			@(negedge clock);
			#1;
			if (pc !== 32'd0)
				$fatal(1, "PC advanced while IN was blocked");
		end

		submit = 1'b0;
		@(posedge clock);
		#1;
		if (halted !== 1'b0)
			$fatal(1, "active-low submit event did not release IN");

		instruction = 32'd0;
		@(negedge clock);
		#1;
		if (pc !== 32'd1)
			$fatal(1, "PC did not resume after submit");

		$display("PASS: home IN contract");
		$finish;
	end

endmodule
