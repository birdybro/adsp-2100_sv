`default_nettype none

module adsp2100_conditional_shift_formal (
    input logic        clk,
    input logic        reset,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        not_counter_expired,
    input logic        astat_setup,
    input logic [7:0]  astat_setup_data,
    input logic        mstat_setup,
    input logic [3:0]  mstat_setup_data,
    input logic        dreg_setup,
    input logic [3:0]  dreg_setup_code,
    input logic [15:0] dreg_setup_data,
    input logic        sb_setup,
    input logic [4:0]  sb_setup_data,
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
    logic [3:0]  condition;
    logic [3:0]  source_dreg;
    logic        condition_true;
    logic [15:0] source_data;
    logic [31:0] sr_result;
    logic [7:0]  se_result;
    logic [4:0]  sb_result;
    logic        ss_result;
    logic        sr_write;
    logic        se_write;
    logic        sb_write;
    logic        ss_write;
    logic [15:0] probe_data;
    logic [31:0] sr;
    logic [7:0]  se;
    logic [4:0]  sb;
    logic [7:0]  astat;
    logic [3:0]  mstat;
    logic        alternate_bank;
    logic        pm_data_access;
    logic        dm_access;
    logic        expected_class;
    logic        expected_action;
    logic        expected_conflict;
    logic [3:0]  setup_count;
    logic [3:0]  expected_source;
    logic        past_valid;

    assign expected_class = ((opcode & 24'hff80f0) == 24'h0e0000);
    assign expected_action = (
        expected_class
        && opcode[10:8] != 3'b001
    );
    assign setup_count = (
        {3'h0, astat_setup}
        + {3'h0, mstat_setup}
        + {3'h0, dreg_setup}
        + {3'h0, sb_setup}
    );
    assign expected_conflict = (
        !reset
        && (
            (execute && (setup_count != 4'h0))
            || (setup_count > 4'h1)
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

    adsp2100_conditional_shift_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .not_counter_expired_i(not_counter_expired),
        .astat_setup_write_i(astat_setup),
        .astat_setup_data_i(astat_setup_data),
        .mstat_setup_write_i(mstat_setup),
        .mstat_setup_data_i(mstat_setup_data),
        .dreg_setup_write_i(dreg_setup),
        .dreg_setup_code_i(dreg_setup_code),
        .dreg_setup_data_i(dreg_setup_data),
        .sb_setup_write_i(sb_setup),
        .sb_setup_data_i(sb_setup_data),
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
        .condition_o(condition),
        .source_dreg_o(source_dreg),
        .condition_true_o(condition_true),
        .source_data_o(source_data),
        .sr_result_o(sr_result),
        .se_result_o(se_result),
        .sb_result_o(sb_result),
        .ss_result_o(ss_result),
        .sr_write_o(sr_write),
        .se_write_o(se_write),
        .sb_write_o(sb_write),
        .ss_write_o(ss_write),
        .probe_data_o(probe_data),
        .sr_o(sr),
        .se_o(se),
        .sb_o(sb),
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
                && (setup_count == 4'h0)
            )
        );
        assert (invalid_opcode == (!reset && execute && !expected_action));
        assert (integration_conflict == expected_conflict);
        assert (!internal_conflict);
        assert (sf == (expected_class ? opcode[14:11] : 4'h0));
        assert (xop == (expected_class ? opcode[10:8] : 3'h0));
        assert (condition == (expected_class ? opcode[3:0] : 4'h0));
        assert (source_dreg == (expected_action ? expected_source : 4'h0));
        assert (!pm_data_access);
        assert (!dm_access);
        assert (alternate_bank == mstat[0]);
        assert (!(sr_write && (se_write || sb_write)));
        assert (!(se_write && sb_write));
        assert (!(ss_write && !(se_write && (sf == 4'hc || sf == 4'hd))));
        if (boundary_valid && !condition_true) begin
            assert (!(sr_write || se_write || sb_write || ss_write));
        end
        if (boundary_valid && condition_true && sf <= 4'hb) begin
            assert (sr_write);
            assert (!(se_write || sb_write || ss_write));
        end
        if (boundary_valid && condition_true
            && (sf == 4'hc || sf == 4'hd)) begin
            assert (se_write && ss_write);
            assert (!(sr_write || sb_write));
        end
        if (probe_code == source_dreg) begin
            assert (probe_data == source_data);
        end
        cover (boundary_valid && !condition_true);
        cover (sr_write && sf == 4'h8);
        cover (se_write && ss_write && sf == 4'hd);
        cover (se_write && !ss_write && sf == 4'he);
        cover (sb_write && sf == 4'hf);
        cover (unsupported_subencoding);
        cover (invalid_opcode);
        cover (integration_conflict);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (mstat == 4'h0);
        end else if ($past(boundary_valid && !condition_true)) begin
            assert (sr == $past(sr));
            assert (se == $past(se));
            assert (sb == $past(sb));
            assert (astat == $past(astat));
            assert (mstat == $past(mstat));
        end else if ($past(sr_write)) begin
            assert (sr == $past(sr_result));
            assert (se == $past(se));
            assert (sb == $past(sb));
            assert (astat == $past(astat));
            assert (mstat == $past(mstat));
        end else if ($past(se_write)) begin
            assert (se == $past(se_result));
            assert (sr == $past(sr));
            assert (sb == $past(sb));
            assert (mstat == $past(mstat));
            if ($past(ss_write)) begin
                assert (astat[7] == $past(ss_result));
                assert (astat[6:0] == $past(astat[6:0]));
            end else begin
                assert (astat == $past(astat));
            end
        end else if ($past(sb_write)) begin
            assert (sb == $past(sb_result));
            assert (sr == $past(sr));
            assert (se == $past(se));
            assert (astat == $past(astat));
            assert (mstat == $past(mstat));
        end else if ($past(invalid_opcode || integration_conflict)) begin
            assert (sr == $past(sr));
            assert (se == $past(se));
            assert (sb == $past(sb));
            assert (astat == $past(astat));
            assert (mstat == $past(mstat));
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
