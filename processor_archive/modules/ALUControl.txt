module ALUControl (

	// Codes
	input [3:0] OpCode,
	input [1:0] TypeCode,
	input is_immediate,
	
	// Values
	input [31:0] immediate_value,
	input signed [31:0] RhValue,
	input signed [31:0] RoValue,
	input [31:0] peripheral_value,
	
	// Outputs
	output zero,
	output negative,
	output signed [31:0] result,
	
	output signed[31:0] r1_value,
	output signed [31:0] r2_value
	
);

	// ALU input
	reg [31:0] operand2;
	
	always@(*) begin
		
		if (is_immediate)
			operand2 = immediate_value;
		else
			operand2 = RoValue;
		
	end

	alu alu (
		.A(RhValue),
		.B(operand2),
		.peripheral_value(peripheral_value),
		.TypeCode(TypeCode),
		.OpCode(OpCode),
		.result(result),
		.negative(negative),
		.zero(zero),
		.r1_value(r1_value),
		.r2_value(r2_value)
		);
		
endmodule