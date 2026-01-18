module output_manager(
	
	input clock, fast_clock,
	input update_output_reg_signal,
	
	input [31:0] value,
	output reg [31:0] output_value
	
);

	reg [31:0] output_reg;
	
	always@ (posedge clock) begin
		
		if (update_output_reg_signal) begin
			output_reg <= value;
		end
	
	end
	
	always@ (posedge fast_clock) begin
		
		output_value <= output_reg;
	
	end
	
endmodule