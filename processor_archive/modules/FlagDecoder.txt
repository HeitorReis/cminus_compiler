module FlagDecoder (
	
	input [31:0] result_in,
	
	input zero,
	input negative,
	
	output [3:0] new_states
	
);

	assign new_states[3:2] = 2'b00;
	
	assign new_states[0] = zero;
	assign new_states[1] = negative;

endmodule