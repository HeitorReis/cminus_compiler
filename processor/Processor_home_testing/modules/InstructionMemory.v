// Quartus Prime Verilog Template
// Single Port ROM

module InstructionMemory
#(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 10
)
(
    input  [(ADDR_WIDTH - 1):0] addr,
    input                     clock,
    input                     fast_clock,
    output reg [(DATA_WIDTH - 1):0] instruction
);

    // Caminho relativo à pasta processor/Processor/
    (* ram_init_file = "modules/program.mif" *)
    reg [DATA_WIDTH - 1:0] rom [0:(2**ADDR_WIDTH) - 1];

    always @(posedge fast_clock) begin
        instruction <= rom[addr];
    end

endmodule