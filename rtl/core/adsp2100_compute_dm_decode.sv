`default_nettype none

module adsp2100_compute_dm_decode (
    input  logic [23:0] opcode_i,
    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic        destination_collision_o,
    output logic        computation_enable_o,
    output logic        is_mac_o,
    output logic        destination_feedback_o,
    output logic        dag_select_o,
    output logic        write_o,
    output logic [4:0]  amf_o,
    output logic [1:0]  yop_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  x_source_dreg_o,
    output logic [3:0]  y_source_dreg_o,
    output logic [3:0]  memory_dreg_o,
    output logic [2:0]  i_address_o,
    output logic [2:0]  m_address_o
);
    logic raw_destination_collision;

    assign class_valid_o = (
        (opcode_i & 24'he00000) == 24'h600000
    );
    assign dag_select_o = class_valid_o ? opcode_i[20] : 1'b0;
    assign write_o = class_valid_o ? opcode_i[19] : 1'b0;
    assign destination_feedback_o = class_valid_o ? opcode_i[18] : 1'b0;
    assign amf_o = class_valid_o ? opcode_i[17:13] : 5'h00;
    assign yop_o = class_valid_o ? opcode_i[12:11] : 2'b00;
    assign xop_o = class_valid_o ? opcode_i[10:8] : 3'b000;
    assign memory_dreg_o = class_valid_o ? opcode_i[7:4] : 4'h0;
    assign i_address_o = (
        class_valid_o ? {opcode_i[20], opcode_i[3:2]} : 3'h0
    );
    assign m_address_o = (
        class_valid_o ? {opcode_i[20], opcode_i[1:0]} : 3'h0
    );
    assign computation_enable_o = class_valid_o && (amf_o != 5'h00);
    assign is_mac_o = computation_enable_o && !amf_o[4];
    assign raw_destination_collision = (
        !write_o && !destination_feedback_o && computation_enable_o
        && (
            (amf_o[4] && memory_dreg_o == 4'ha)
            || (
                !amf_o[4]
                && memory_dreg_o >= 4'hb
                && memory_dreg_o <= 4'hd
            )
        )
    );
    assign destination_collision_o = (
        class_valid_o && raw_destination_collision
    );
    assign action_valid_o = class_valid_o && !raw_destination_collision;
    assign unsupported_subencoding_o = class_valid_o && !action_valid_o;

    always_comb begin
        x_source_dreg_o = 4'h0;
        y_source_dreg_o = 4'h0;
        if (action_valid_o && computation_enable_o) begin
            if (xop_o <= 3'd1) begin
                x_source_dreg_o = {
                    2'b00,
                    is_mac_o,
                    xop_o[0]
                };
            end else begin
                x_source_dreg_o = {1'b1, xop_o};
            end
            if (yop_o <= 2'd1) begin
                y_source_dreg_o = {
                    1'b0,
                    1'b1,
                    is_mac_o,
                    yop_o[0]
                };
            end
        end
    end
endmodule

`default_nettype wire
