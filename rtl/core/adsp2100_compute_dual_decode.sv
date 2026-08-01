`default_nettype none

module adsp2100_compute_dual_decode (
    input  logic [23:0] opcode_i,
    output logic        class_valid_o,
    output logic        action_valid_o,
    output logic        unsupported_subencoding_o,
    output logic        computation_enable_o,
    output logic        is_mac_o,
    output logic        destination_feedback_o,
    output logic [4:0]  amf_o,
    output logic [1:0]  yop_o,
    output logic [2:0]  xop_o,
    output logic [3:0]  x_source_dreg_o,
    output logic [3:0]  y_source_dreg_o,
    output logic        compute_destination_ar_o,
    output logic        compute_destination_mr_o,
    output logic [3:0]  pm_destination_dreg_o,
    output logic [3:0]  dm_destination_dreg_o,
    output logic [2:0]  pm_i_address_o,
    output logic [2:0]  pm_m_address_o,
    output logic [2:0]  dm_i_address_o,
    output logic [2:0]  dm_m_address_o
);
    assign class_valid_o = (
        (opcode_i & 24'hc00000) == 24'hc00000
    );
    assign action_valid_o = class_valid_o;
    assign unsupported_subencoding_o = 1'b0;
    assign amf_o = class_valid_o ? opcode_i[17:13] : 5'h00;
    assign yop_o = class_valid_o ? opcode_i[12:11] : 2'b00;
    assign xop_o = class_valid_o ? opcode_i[10:8] : 3'b000;
    assign computation_enable_o = class_valid_o && (amf_o != 5'h00);
    assign is_mac_o = computation_enable_o && !amf_o[4];
    assign destination_feedback_o = 1'b0;
    assign compute_destination_ar_o = computation_enable_o && !is_mac_o;
    assign compute_destination_mr_o = computation_enable_o && is_mac_o;
    assign pm_destination_dreg_o = (
        class_valid_o ? {2'b01, opcode_i[21:20]} : 4'h0
    );
    assign dm_destination_dreg_o = (
        class_valid_o ? {2'b00, opcode_i[19:18]} : 4'h0
    );
    assign pm_i_address_o = (
        class_valid_o ? {1'b1, opcode_i[7:6]} : 3'h0
    );
    assign pm_m_address_o = (
        class_valid_o ? {1'b1, opcode_i[5:4]} : 3'h0
    );
    assign dm_i_address_o = (
        class_valid_o ? {1'b0, opcode_i[3:2]} : 3'h0
    );
    assign dm_m_address_o = (
        class_valid_o ? {1'b0, opcode_i[1:0]} : 3'h0
    );

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
