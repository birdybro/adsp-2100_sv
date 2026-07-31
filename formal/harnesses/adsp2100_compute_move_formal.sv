`default_nettype none

module adsp2100_compute_move_formal (
    input logic        clk,
    input logic        reset,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        astat_setup,
    input logic [7:0]  astat_setup_data,
    input logic        mstat_setup,
    input logic [3:0]  mstat_setup_data,
    input logic        dreg_setup,
    input logic [3:0]  dreg_setup_code,
    input logic [15:0] dreg_setup_data,
    input logic        af_setup,
    input logic [15:0] af_setup_data,
    input logic        mf_setup,
    input logic [15:0] mf_setup_data
);
    logic        class_valid;
    logic        action_valid;
    logic        unsupported_subencoding;
    logic        unverified_amf_zero;
    logic        destination_collision;
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        internal_conflict;
    logic        is_mac;
    logic        destination_feedback;
    logic [4:0]  amf;
    logic [1:0]  yop;
    logic [2:0]  xop;
    logic [3:0]  x_source_dreg;
    logic [3:0]  y_source_dreg;
    logic [3:0]  move_destination_dreg;
    logic [3:0]  move_source_dreg;
    logic [15:0] x_source_data;
    logic [15:0] y_source_data;
    logic [15:0] move_source_data;
    logic [15:0] alu_result;
    logic [39:0] mac_result;
    logic        move_write;
    logic        alu_write;
    logic        mac_write;
    logic        alu_status_write;
    logic        mac_status_write;
    logic [15:0] probe_data;
    logic [15:0] af;
    logic [15:0] mf;
    logic [39:0] mr;
    logic [7:0]  astat;
    logic [3:0]  mstat;
    logic        alternate_bank;
    logic        pm_data_access;
    logic        dm_access;
    logic        expected_class;
    logic        expected_amf_zero;
    logic        expected_collision;
    logic        expected_action;
    logic        expected_is_mac;
    logic [3:0]  expected_x_source;
    logic [3:0]  expected_y_source;
    logic [3:0]  setup_count;
    logic        expected_conflict;
    logic        past_valid;

    assign expected_class = ((opcode & 24'hf80000) == 24'h280000);
    assign expected_amf_zero = expected_class && opcode[17:13] == 5'h00;
    assign expected_is_mac = (
        expected_class && !opcode[17] && !expected_amf_zero
    );
    assign expected_collision = (
        expected_class
        && !expected_amf_zero
        && !opcode[18]
        && (
            (opcode[17] && opcode[7:4] == 4'ha)
            || (
                !opcode[17]
                && opcode[7:4] >= 4'hb
                && opcode[7:4] <= 4'hd
            )
        )
    );
    assign expected_action = (
        expected_class && !expected_amf_zero && !expected_collision
    );
    assign setup_count = (
        {3'h0, astat_setup}
        + {3'h0, mstat_setup}
        + {3'h0, dreg_setup}
        + {3'h0, af_setup}
        + {3'h0, mf_setup}
    );
    assign expected_conflict = (
        !reset
        && ((execute && setup_count != 4'h0) || setup_count > 4'h1)
    );

    always_comb begin
        expected_x_source = 4'h0;
        expected_y_source = 4'h0;
        if (expected_action) begin
            if (opcode[10:8] <= 3'd1) begin
                expected_x_source = {2'b00, expected_is_mac, opcode[8]};
            end else begin
                expected_x_source = {1'b1, opcode[10:8]};
            end
            if (opcode[12:11] <= 2'd1) begin
                expected_y_source = {
                    2'b01, expected_is_mac, opcode[11]
                };
            end
        end
    end

    adsp2100_compute_move_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .astat_setup_write_i(astat_setup),
        .astat_setup_data_i(astat_setup_data),
        .mstat_setup_write_i(mstat_setup),
        .mstat_setup_data_i(mstat_setup_data),
        .dreg_setup_write_i(dreg_setup),
        .dreg_setup_code_i(dreg_setup_code),
        .dreg_setup_data_i(dreg_setup_data),
        .af_setup_write_i(af_setup),
        .af_setup_data_i(af_setup_data),
        .mf_setup_write_i(mf_setup),
        .mf_setup_data_i(mf_setup_data),
        .inspect_probe_i(1'b0),
        .probe_code_i(4'h0),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported_subencoding),
        .unverified_amf_zero_o(unverified_amf_zero),
        .destination_collision_o(destination_collision),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .is_mac_o(is_mac),
        .destination_feedback_o(destination_feedback),
        .amf_o(amf),
        .yop_o(yop),
        .xop_o(xop),
        .x_source_dreg_o(x_source_dreg),
        .y_source_dreg_o(y_source_dreg),
        .move_destination_dreg_o(move_destination_dreg),
        .move_source_dreg_o(move_source_dreg),
        .x_source_data_o(x_source_data),
        .y_source_data_o(y_source_data),
        .move_source_data_o(move_source_data),
        .alu_result_o(alu_result),
        .mac_result_o(mac_result),
        .move_write_o(move_write),
        .alu_write_o(alu_write),
        .mac_write_o(mac_write),
        .alu_status_write_o(alu_status_write),
        .mac_status_write_o(mac_status_write),
        .probe_data_o(probe_data),
        .af_o(af),
        .mf_o(mf),
        .mr_o(mr),
        .astat_o(astat),
        .mstat_o(mstat),
        .alternate_bank_o(alternate_bank),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (class_valid == expected_class);
        assert (action_valid == expected_action);
        assert (unverified_amf_zero == expected_amf_zero);
        assert (destination_collision == expected_collision);
        assert (unsupported_subencoding == (expected_class && !expected_action));
        assert (is_mac == expected_is_mac);
        assert (destination_feedback == (expected_class ? opcode[18] : 1'b0));
        assert (amf == (expected_class ? opcode[17:13] : 5'h00));
        assert (yop == (expected_class ? opcode[12:11] : 2'b00));
        assert (xop == (expected_class ? opcode[10:8] : 3'b000));
        assert (x_source_dreg == expected_x_source);
        assert (y_source_dreg == expected_y_source);
        assert (
            move_destination_dreg == (expected_class ? opcode[7:4] : 4'h0)
        );
        assert (move_source_dreg == (expected_class ? opcode[3:0] : 4'h0));
        assert (
            boundary_valid
            == (!reset && execute && expected_action && setup_count == 4'h0)
        );
        assert (invalid_opcode == (!reset && execute && !expected_action));
        assert (integration_conflict == expected_conflict);
        assert (!internal_conflict);
        assert (move_write == boundary_valid);
        assert (alu_write == (boundary_valid && !expected_is_mac));
        assert (mac_write == (boundary_valid && expected_is_mac));
        assert (alu_status_write == alu_write);
        assert (mac_status_write == mac_write);
        assert (!(alu_write && mac_write));
        assert (!pm_data_access && !dm_access);
        assert (alternate_bank == mstat[0]);
        assert (probe_data == move_source_data);
        if (action_valid && yop == 2'd3) begin
            assert (y_source_data == 16'h0000);
        end
        if (action_valid && x_source_dreg == move_source_dreg) begin
            assert (x_source_data == move_source_data);
        end
        if (action_valid && yop <= 2'd1
            && y_source_dreg == move_source_dreg) begin
            assert (y_source_data == move_source_data);
        end
        if (boundary_valid && !destination_feedback && !expected_is_mac) begin
            assert (move_destination_dreg != 4'ha);
        end
        if (boundary_valid && !destination_feedback && expected_is_mac) begin
            assert (
                move_destination_dreg < 4'hb
                || move_destination_dreg > 4'hd
            );
        end
        cover (boundary_valid && !is_mac && !destination_feedback);
        cover (boundary_valid && !is_mac && destination_feedback);
        cover (boundary_valid && is_mac && !destination_feedback);
        cover (boundary_valid && is_mac && destination_feedback);
        cover (unverified_amf_zero);
        cover (destination_collision);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (mstat == 4'h0);
        end else if ($past(invalid_opcode || integration_conflict)) begin
            assert (af == $past(af));
            assert (mf == $past(mf));
            assert (mr == $past(mr));
            assert (astat == $past(astat));
            assert (mstat == $past(mstat));
        end else if ($past(boundary_valid)) begin
            assert (mstat == $past(mstat));
            if ($past(is_mac && destination_feedback)) begin
                assert (mf == $past(mac_result[31:16]));
            end else if ($past(is_mac)) begin
                assert (mr == $past(mac_result));
            end else if ($past(destination_feedback)) begin
                assert (af == $past(alu_result));
            end
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
