module alu (
	input signed [31:0] A,
	input signed [31:0] B,
	input signed [31:0] peripheral_value,
	input [1:0] TypeCode,
	input [3:0] OpCode,
	output reg signed [31:0] result,
	output reg negative,
	output reg zero,
	
	// Test
	output [31:0] r1_value,
	output [31:0] r2_value
	); // inputs and outputs

	always @(*) begin
		 // Default assignment to prevent inferred latches
		 result = 32'b0;

		 // Use a case statement or if-else chain for TypeCode
		 case (TypeCode)
			  // Data Processing Instructions
			  2'b00: begin
					case (OpCode)
			
						4'b0000: result = A + B; // ADD
						4'b0001: result = A - B; // SUB
						4'b0010: result = A * B; // MUL
						4'b0011: result = A / B; // DIV
						4'b0100: result = A & B; // AND
						4'b0101: result = A | B; // OR
						4'b0110: result = A ^ B; // XOR
						4'b0111: result = -A;  // NOT
						4'b1000: result = B;  // MOV
						4'b1001: result = peripheral_value; // IN
						4'b1010: result = B; // OUT
			
						default: result = 32'b0;
					endcase
			  end

			  // Data Transfer Instructions (LDR/STR)
			  // For these, the ALU calculates the new data.
			  2'b01: begin
					if (OpCode == 4'b0001) begin // If Load
						result = A; // Pass RhValue through as the new data address
					end else if (OpCode == 4'b0000) begin // If Store
						result = A;
			  end end

			  // Branch Instructions
			  // For these, the ALU passes the offset (operand2) to the PC.
			  2'b11: begin
					result = B; // Pass operand2 through as the branch offset
			  end

			  // Default case for any other TypeCodes
			  default: begin
					result = 32'b0;
			  end
		 endcase
	end
	
	always@(*) begin
		if (result == 0)
			zero = 1;
		else
			zero = 0;
		
		if (result < 0)
			negative = 1;
		else
			negative = 0;
	end
	
	// Testing
	assign r1_value = A;
	assign r2_value = B;

endmodule