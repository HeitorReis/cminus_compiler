module output_module(

	input [31:0]number,
	
	output [6:0]HEX0,
	output [6:0]HEX1,
	output [6:0]HEX2,
	output [6:0]HEX3

);

	wire [3:0] number0;
	wire [3:0] number1;
	wire [3:0] number2;
	wire [3:0] number3;
	
	assign number3 = number/1000;
	assign number2 = number/100 - (number3*10);
	assign number1 = number/10 - ((number3*100) + (number2*10));
	assign number0 = number - ((number3*1000) + (number2*100) + (number1*10)) ;
	
	to_display hex0(
		.number(number0),
		.display(HEX0)
	);
	
	to_display hex1(
		.number(number1),
		.display(HEX1)
	);
	
	to_display hex2(
		.number(number2),
		.display(HEX2)
	);
	
	to_display hex3(
		.number(number3),
		.display(HEX3)
	);
	
endmodule

module to_display(

	input [3:0] number,
	
	output reg [6:0] display
	
);
		always@* begin
			
				case(number)
					4'd0:		display = 7'b1000000;
					4'd1:		display = 7'b1111001;
					4'd2:		display = 7'b0100100;
					4'd3:		display = 7'b0110000;
					4'd4:		display = 7'b0011001;
					4'd5:		display = 7'b0010010;
					4'd6:		display = 7'b0000010;
					4'd7:		display = 7'b1111000;
					4'd8:		display = 7'b0000000;
					4'd9:		display = 7'b0011000;
					4'd10:	display = 7'b1000000;
					4'd11:	display = 7'b1111001;
					4'd12:	display = 7'b0100100;
					4'd13:	display = 7'b0110000;
					4'd14:	display = 7'b0011001;
					4'd15:	display = 7'b0010010;
					
					default: display = 7'b1111110;
				endcase		
		end
	
endmodule