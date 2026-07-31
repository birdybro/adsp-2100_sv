`default_nettype none

module adsp2100_immediate_shift_formal (
    input logic        clk,
    input logic        reset,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        mstat_setup,
    input logic [3:0]  mstat_setup_data,
    input logic        dreg_setup,
    input logic [3:0]  dreg_setup_code,
    input logic [15:0] dreg_setup_data,
    input logic [3:0]  probe_code
);
    logic        class_valid;
    logic        action_valid;
    logic        unsupported_subencoding;
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        integration_conflict;
    logic        internal_conflict;
    logic [3:0]  sf;
    logic [2:0]  xop;
    logic [7:0]  exponent;
    logic [3:0]  source_dreg;
    logic [15:0] source_data;
    logic [31:0] sr_result;
    logic        sr_write;
    logic [15:0] probe_data;
    logic [31:0] sr;
    logic [7:0]  se;
    logic [3:0]  mstat;
    logic        alternate_bank;
    logic        pm_data_access;
    logic        dm_access;
    logic        expected_class;
    logic        expected_action;
    logic        expected_conflict;
    logic [3:0]  expected_source;
    logic        past_valid;

    assign expected_class = ((opcode & 24'hff8000) == 24'h0f0000);
    assign expected_action = (
        expected_class
        && !opcode[14]
        && opcode[10:8] != 3'b001
    );
    assign expected_conflict = (
        !reset
        && (
            (execute && (mstat_setup || dreg_setup))
            || (mstat_setup && dreg_setup)
        )
    );

    always_comb begin
        case (opcode[10:8])
            3'd0: expected_source = 4'h8;
            3'd2: expected_source = 4'ha;
            3'd3: expected_source = 4'hb;
            3'd4: expected_source = 4'hc;
            3'd5: expected_source = 4'hd;
            3'd6: expected_source = 4'he;
            3'd7: expected_source = 4'hf;
            default: expected_source = 4'h0;
        endcase
    end

    adsp2100_immediate_shift_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .mstat_setup_write_i(mstat_setup),
        .mstat_setup_data_i(mstat_setup_data),
        .dreg_setup_write_i(dreg_setup),
        .dreg_setup_code_i(dreg_setup_code),
        .dreg_setup_data_i(dreg_setup_data),
        .probe_code_i(probe_code),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .unsupported_subencoding_o(unsupported_subencoding),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .sf_o(sf),
        .xop_o(xop),
        .exponent_o(exponent),
        .source_dreg_o(source_dreg),
        .source_data_o(source_data),
        .sr_result_o(sr_result),
        .sr_write_o(sr_write),
        .probe_data_o(probe_data),
        .sr_o(sr),
        .se_o(se),
        .mstat_o(mstat),
        .alternate_bank_o(alternate_bank),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (class_valid == expected_class);
        assert (action_valid == expected_action);
        assert (
            unsupported_subencoding
            == (expected_class && !expected_action)
        );
        assert (
            boundary_valid
            == (
                !reset
                && execute
                && expected_action
                && !mstat_setup
                && !dreg_setup
            )
        );
        assert (invalid_opcode == (!reset && execute && !expected_action));
        assert (integration_conflict == expected_conflict);
        assert (!internal_conflict);
        assert (sf == (expected_class ? opcode[14:11] : 4'h0));
        assert (xop == (expected_class ? opcode[10:8] : 3'h0));
        assert (exponent == (expected_class ? opcode[7:0] : 8'h00));
        assert (
            source_dreg
            == (expected_action ? expected_source : 4'h0)
        );
        assert (sr_write == boundary_valid);
        assert (!pm_data_access);
        assert (!dm_access);
        assert (alternate_bank == mstat[0]);
        if (probe_code == source_dreg) begin
            assert (probe_data == source_data);
        end
        cover (boundary_valid && sf == 4'd0 && exponent == 8'hfb);
        cover (boundary_valid && sf == 4'd7 && xop == 3'd7);
        cover (unsupported_subencoding && xop == 3'd1);
        cover (unsupported_subencoding && sf == 4'd8);
        cover (invalid_opcode);
        cover (integration_conflict);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (mstat == 4'h0);
            if (!$past(mstat[0])) begin
                assert (sr == $past(sr));
                assert (se == $past(se));
            end
        end else if ($past(boundary_valid)) begin
            assert (sr == $past(sr_result));
            assert (se == $past(se));
            assert (mstat == $past(mstat));
        end else if ($past(invalid_opcode || integration_conflict)) begin
            assert (sr == $past(sr));
            assert (se == $past(se));
            assert (mstat == $past(mstat));
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
