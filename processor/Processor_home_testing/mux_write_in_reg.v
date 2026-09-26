module mux_write_in_reg (
	input [31:0] ram_output, alu_result,
	input is_load_instruction,
	
	output [31:0] WriteData
);
	assign WriteData = (~{32{is_load_instruction}} & alu_result) | ({32{is_load_instruction}} & ram_output);
	
endmodule