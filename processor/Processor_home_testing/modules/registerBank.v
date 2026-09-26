module registerBank ( // Inputs are Rh, Ro (Op2), Clock, TypeCode, WriteData (to Rd), Rd

	// Addresses
	input [4:0] RhAddress,
	input [4:0] RoAddress,
	input [4:0] RdAddress,
	
	// Values
	input [31:0] WriteData,
	input [31:0] new_LinkValue,
	
	// Codes
	input store_link_signal,
	input store_reg_signal,
	
	// Clock
	input clock, fast_clock,
	
	input reset,
	
	// Outputs
	output reg [31:0] RhValue,
	output reg [31:0] RoValue,
	output reg [31:0] RdValue,
	output reg [31:0] LinkValue,
	
	// Test
	output reg [31:0] r4_value,
	output reg [31:0] r31_value
);

	reg [31:0] regBank [31:0]; // Register bank
	reg [31:0] LinkRegister;
	

	always@(posedge clock) begin
		// If should write
		if ( store_reg_signal ) begin
			regBank[RdAddress] <= WriteData; // Write
		end
					
		if ( store_link_signal ) begin
			LinkRegister <= new_LinkValue;
		end
	end
	
	
	always @ (posedge fast_clock) begin
		
		r31_value <= regBank[31];
		r4_value <= regBank[4];
		
		RhValue <= regBank[RhAddress];
		RoValue <= regBank[RoAddress];
		RdValue <= regBank[RdAddress];
		
		LinkValue <= LinkRegister;
		
	end
	
endmodule