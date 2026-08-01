`default_nettype none

module adsp2100_shifter_pm_decode (
    input  logic [23:0] opcode_i,
    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic        unavailable_xop_o,
    output logic        destination_collision_o,
    output logic        write_o,
    output logic [3:0]  sf_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  shifter_source_dreg_o,
    output logic [3:0]  memory_dreg_o,
    output logic [2:0]  i_address_o,
    output logic [2:0]  m_address_o
);
    logic raw_destination_collision;

    assign class_valid_o = (
        (opcode_i & 24'hff0000) == 24'h110000
    );
    assign write_o = class_valid_o ? opcode_i[15] : 1'b0;
    assign sf_o = class_valid_o ? opcode_i[14:11] : 4'h0;
    assign xop_o = class_valid_o ? opcode_i[10:8] : 3'h0;
    assign memory_dreg_o = class_valid_o ? opcode_i[7:4] : 4'h0;
    assign i_address_o = (
        class_valid_o ? {1'b1, opcode_i[3:2]} : 3'h0
    );
    assign m_address_o = (
        class_valid_o ? {1'b1, opcode_i[1:0]} : 3'h0
    );
    assign unavailable_xop_o = (
        class_valid_o && opcode_i[10:8] == 3'b001
    );
    assign raw_destination_collision = (
        (
            opcode_i[14:11] <= 4'hb
            && (opcode_i[7:4] == 4'he || opcode_i[7:4] == 4'hf)
        )
        || (
            opcode_i[14:11] >= 4'hc
            && opcode_i[14:11] <= 4'he
            && opcode_i[7:4] == 4'h9
        )
    );
    assign destination_collision_o = (
        class_valid_o
        && !opcode_i[15]
        && opcode_i[10:8] != 3'b001
        && raw_destination_collision
    );
    assign action_valid_o = (
        class_valid_o
        && opcode_i[10:8] != 3'b001
        && (opcode_i[15] || !raw_destination_collision)
    );
    assign unsupported_subencoding_o = class_valid_o && !action_valid_o;

    always_comb begin
        shifter_source_dreg_o = 4'h0;
        if (action_valid_o) begin
            unique case (xop_o)
                3'b000: shifter_source_dreg_o = 4'h8; // SI
                3'b010: shifter_source_dreg_o = 4'ha; // AR
                3'b011: shifter_source_dreg_o = 4'hb; // MR0
                3'b100: shifter_source_dreg_o = 4'hc; // MR1
                3'b101: shifter_source_dreg_o = 4'hd; // MR2
                3'b110: shifter_source_dreg_o = 4'he; // SR0
                3'b111: shifter_source_dreg_o = 4'hf; // SR1
                default: shifter_source_dreg_o = 4'h0;
            endcase
        end
    end
endmodule

`default_nettype wire
