module CPSR_module	(

	input [31:0] ALUresult,
	
	input set_cond_bit,
	
	input zero,
	input negative,
	
	input [3:0] Cond_field,
	
	input clock,
	
	output write_condition,
	
	output [3:0] current_flags // Test
	
);

	wire [3:0] currrent_flags;
	wire [3:0] new_flags;

	FlagVerifier FlagVerifier(

		.cond_field(Cond_field),
		.flags(currrent_flags),
		
		.write_condition(write_condition)

	);

	CPSRegister CPSRegister(
		// Set Condition code
		.should_set(set_cond_bit),
		.write_condition(write_condition),
		
		// CPSR bits to be updated
		.new_states(new_flags),
		
		.clock(clock),
		
		.current_states_reg(currrent_flags)
	);


	FlagDecoder FlagDecoder(
		
		.result_in(ALUresult),
		
		.zero(zero),
		.negative(negative),
		
		.new_states(new_flags)
		
	);

endmodule