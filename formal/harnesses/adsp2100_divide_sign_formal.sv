`default_nettype none

module adsp2100_divide_sign_formal (
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
    input logic [15:0] af_setup_data
);
    logic class_valid;
    logic action_valid;
    logic unsupported_yop;
    logic [1:0] yop;
    logic [2:0] xop;
    logic [3:0] x_source;
    logic [3:0] upper_source;
    logic upper_feedback;
    logic boundary_valid;
    logic invalid_opcode;
    logic integration_conflict;
    logic internal_conflict;
    logic source_known;
    logic result_known;
    logic quotient_sign;
    logic [15:0] divisor_before;
    logic [15:0] upper_before;
    logic [15:0] ay0_before;
    logic [15:0] af_result;
    logic [15:0] ay0_result;
    logic af_write;
    logic ay0_write;
    logic aq_write;
    logic [15:0] af;
    logic af_valid;
    logic [15:0] ay0;
    logic ay0_valid;
    logic [7:0] astat;
    logic [7:0] astat_valid_mask;
    logic [3:0] mstat;
    logic alternate_bank;
    logic pm_data_access;
    logic dm_access;
    logic [2:0] setup_count;
    logic expected_class;
    logic expected_action;
    logic past_valid;

    assign setup_count = (
        {2'b00, astat_setup}
        + {2'b00, mstat_setup}
        + {2'b00, dreg_setup}
        + {2'b00, af_setup}
    );
    assign expected_class = (opcode & 24'hffe0ff) == 24'h060000;
    assign expected_action = expected_class
        && (opcode[12:11] == 2'd1 || opcode[12:11] == 2'd2);

    adsp2100_divide_sign_slice dut (
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
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_yop_o(unsupported_yop),
        .yop_o(yop),
        .xop_o(xop),
        .x_source_dreg_o(x_source),
        .upper_source_dreg_o(upper_source),
        .upper_source_feedback_o(upper_feedback),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .source_known_o(source_known),
        .result_known_o(result_known),
        .quotient_sign_o(quotient_sign),
        .divisor_before_o(divisor_before),
        .upper_before_o(upper_before),
        .ay0_before_o(ay0_before),
        .af_result_o(af_result),
        .ay0_result_o(ay0_result),
        .af_write_o(af_write),
        .ay0_write_o(ay0_write),
        .aq_write_o(aq_write),
        .af_o(af),
        .af_valid_o(af_valid),
        .ay0_o(ay0),
        .ay0_valid_o(ay0_valid),
        .astat_o(astat),
        .astat_valid_mask_o(astat_valid_mask),
        .mstat_o(mstat),
        .alternate_bank_o(alternate_bank),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    always_comb begin
        assert (class_valid == expected_class);
        assert (action_valid == expected_action);
        assert (unsupported_yop == (expected_class && !expected_action));
        assert (yop == (expected_class ? opcode[12:11] : 2'd0));
        assert (xop == (expected_class ? opcode[10:8] : 3'd0));
        assert (
            boundary_valid
            == (!reset && execute && expected_action && setup_count == 3'd0)
        );
        assert (invalid_opcode == (!reset && execute && !expected_action));
        assert (
            integration_conflict
            == (!reset && ((execute && setup_count != 0) || setup_count > 1))
        );
        assert (!internal_conflict);
        assert (result_known == source_known);
        assert (!source_known || boundary_valid);
        assert (af_write == boundary_valid);
        assert (ay0_write == boundary_valid);
        assert (aq_write == boundary_valid);
        assert (alternate_bank == mstat[0]);
        assert (!pm_data_access && !dm_access);
        unique case (xop)
            3'd0: assert (x_source == 4'h0);
            3'd1: assert (x_source == 4'h1);
            3'd2: assert (x_source == 4'ha);
            3'd3: assert (x_source == 4'hb);
            3'd4: assert (x_source == 4'hc);
            3'd5: assert (x_source == 4'hd);
            3'd6: assert (x_source == 4'he);
            default: assert (x_source == 4'hf);
        endcase
        if (source_known) begin
            assert (quotient_sign == (divisor_before[15] ^ upper_before[15]));
            assert (af_result == {upper_before[14:0], ay0_before[15]});
            assert (ay0_result == {ay0_before[14:0], quotient_sign});
        end
        if (action_valid && yop == 2'd1) begin
            assert (upper_source == 4'h5 && !upper_feedback);
        end
        if (action_valid && yop == 2'd2) begin
            assert (upper_source == 4'h0 && upper_feedback);
        end

        cover (boundary_valid && source_known && quotient_sign);
        cover (boundary_valid && source_known && !quotient_sign);
        cover (boundary_valid && source_known && divisor_before == 16'ha55a);
        cover (boundary_valid && !source_known);
        cover (unsupported_yop);
        cover (integration_conflict);
        cover (invalid_opcode && !class_valid);
        cover (boundary_valid && alternate_bank);
    end

    initial past_valid = 1'b0;

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (mstat == 4'h0);
            assert (astat_valid_mask == 8'h00);
            assert (!af_valid && !ay0_valid);
        end else if ($past(boundary_valid)) begin
            assert (mstat == $past(mstat));
            assert ((astat & 8'hdf) == ($past(astat) & 8'hdf));
            assert ((astat_valid_mask & 8'hdf)
                    == ($past(astat_valid_mask) & 8'hdf));
            if ($past(source_known)) begin
                assert (af_valid && ay0_valid && astat_valid_mask[5]);
                assert (af == $past(af_result));
                assert (ay0 == $past(ay0_result));
                assert (astat[5] == $past(quotient_sign));
            end else begin
                assert (!af_valid && !ay0_valid && !astat_valid_mask[5]);
            end
        end else if (
            $past(integration_conflict) || $past(invalid_opcode)
        ) begin
            assert (mstat == $past(mstat));
            assert (astat == $past(astat));
            assert (astat_valid_mask == $past(astat_valid_mask));
            assert (af_valid == $past(af_valid));
            assert (ay0_valid == $past(ay0_valid));
            if (af_valid) assert (af == $past(af));
            if (ay0_valid) assert (ay0 == $past(ay0));
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
