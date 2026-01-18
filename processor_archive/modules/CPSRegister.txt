module CPSRegister (
	// Set Condition code
	input should_set,
	input write_condition,
	
	// CPSR bits to be updated
	input [3:0] new_states,
	
	input clock,
	
	output reg [3:0] current_states_reg
	
);

	always@( negedge clock ) begin
			
		if (should_set & write_condition) begin
		
			current_states_reg <= new_states;
			
		end
		
	end

endmodule