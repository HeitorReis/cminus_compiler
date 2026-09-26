module home_display(

	input clock,
	input reset_n,
	input [31:0] number,

	output reg [3:0] digit_select,
	output reg [7:0] segments

);

	wire [6:0] digit0_segments;
	wire [6:0] digit1_segments;
	wire [6:0] digit2_segments;
	wire [6:0] digit3_segments;

	output_module decimal_digits(
		.number(number),
		.HEX0(digit0_segments),
		.HEX1(digit1_segments),
		.HEX2(digit2_segments),
		.HEX3(digit3_segments)
	);

	// At 50 MHz, the two most significant bits refresh each digit at about
	// 190 Hz. Both digit selects and segment outputs are active-low.
	reg [15:0] refresh_counter;

	always @(posedge clock or negedge reset_n) begin
		if (!reset_n)
			refresh_counter <= 16'd0;
		else
			refresh_counter <= refresh_counter + 16'd1;
	end

	always @* begin
		case (refresh_counter[15:14])
			2'd0: begin
				digit_select = 4'b1110;
				segments = {1'b1, digit0_segments};
			end
			2'd1: begin
				digit_select = 4'b1101;
				segments = {1'b1, digit1_segments};
			end
			2'd2: begin
				digit_select = 4'b1011;
				segments = {1'b1, digit2_segments};
			end
			default: begin
				digit_select = 4'b0111;
				segments = {1'b1, digit3_segments};
			end
		endcase
	end

endmodule
