`default_nettype none

module adsp2100_internal_move_slice_formal (
    input logic        clk,
    input logic        reset,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        setup_write,
    input logic [5:0]  setup_code,
    input logic [15:0] setup_data,
    input logic [5:0]  probe_code
);
    logic [15:0] probe_data;
    logic        class_valid;
    logic        boundary_valid;
    logic        invalid_opcode;
    logic        invalid_subencoding;
    logic        invalid_setup;
    logic        integration_conflict;
    logic        internal_conflict;
    logic [5:0]  source_code;
    logic [5:0]  destination_code;
    logic [15:0] source_data;
    logic        source_extension_provisional;
    logic        count_stack_push;
    logic [13:0] count_stack_push_data;
    logic [2:0]  count_stack_depth;
    logic        count_stack_overflow;
    logic [7:0]  astat;
    logic [3:0]  mstat;
    logic [4:0]  icntl;
    logic [3:0]  imask;
    logic [13:0] cntr;
    logic        cntr_valid;
    logic [7:0]  px;
    logic [7:0]  sstat;
    logic        pm_data_access;
    logic        dm_access;
    logic        expected_class;
    logic        expected_source_present;
    logic        expected_destination_present;
    logic        expected_destination_writable;
    logic        expected_move;
    logic        expected_setup_present;
    logic        expected_setup_writable;
    logic        past_valid;

    function automatic logic selector_present (
        input logic [1:0] group,
        input logic [3:0] index
    );
        case (group)
            2'b00: selector_present = 1'b1;
            2'b01,
            2'b10: selector_present = index < 4'd12;
            2'b11: selector_present = index < 4'd8;
            default: selector_present = 1'b0;
        endcase
    endfunction

    assign expected_class = (
        (opcode & 24'hfff000) == 24'h0d0000
    );
    assign expected_source_present = selector_present(
        opcode[9:8],
        opcode[3:0]
    );
    assign expected_destination_present = selector_present(
        opcode[11:10],
        opcode[7:4]
    );
    assign expected_destination_writable = (
        expected_destination_present
        && !(
            opcode[11:10] == 2'b11
            && opcode[7:4] == 4'd2
        )
    );
    assign expected_move = (
        expected_class
        && expected_source_present
        && expected_destination_writable
    );
    assign expected_setup_present = selector_present(
        setup_code[5:4],
        setup_code[3:0]
    );
    assign expected_setup_writable = (
        expected_setup_present
        && setup_code != 6'h32
    );

    adsp2100_internal_move_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .setup_write_i(setup_write),
        .setup_code_i(setup_code),
        .setup_data_i(setup_data),
        .probe_code_i(probe_code),
        .probe_data_o(probe_data),
        .class_valid_o(class_valid),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .invalid_subencoding_o(invalid_subencoding),
        .invalid_setup_o(invalid_setup),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .source_code_o(source_code),
        .destination_code_o(destination_code),
        .source_data_o(source_data),
        .source_extension_provisional_o(source_extension_provisional),
        .count_stack_push_o(count_stack_push),
        .count_stack_push_data_o(count_stack_push_data),
        .count_stack_depth_o(count_stack_depth),
        .count_stack_overflow_o(count_stack_overflow),
        .astat_o(astat),
        .mstat_o(mstat),
        .icntl_o(icntl),
        .imask_o(imask),
        .cntr_o(cntr),
        .cntr_valid_o(cntr_valid),
        .px_o(px),
        .sstat_o(sstat),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (class_valid == expected_class);
        assert (
            boundary_valid
            == (!reset && execute && expected_move && !setup_write)
        );
        assert (invalid_opcode == (!reset && execute && !expected_class));
        assert (
            invalid_subencoding
            == (!reset && execute && expected_class && !expected_move)
        );
        assert (
            invalid_setup
            == (!reset && setup_write && !expected_setup_writable)
        );
        assert (
            integration_conflict
            == (!reset && execute && setup_write)
        );
        assert (!pm_data_access);
        assert (!dm_access);
        assert (count_stack_depth <= 3'd4);
        assert (
            source_extension_provisional
            == (
                boundary_valid
                && opcode[9:8] == 2'b11
                && opcode[3:0] <= 4'd4
            )
        );
        if (expected_class) begin
            assert (source_code == {opcode[9:8], opcode[3:0]});
            assert (destination_code == {opcode[11:10], opcode[7:4]});
        end else begin
            assert (source_code == 6'h00);
            assert (destination_code == 6'h00);
        end
        if (!count_stack_push) begin
            assert (count_stack_push_data == 14'h0000);
        end
        if (boundary_valid && opcode[9:8] == 2'b11) begin
            unique case (opcode[3:0])
                4'd0: assert (source_data == {8'h00, astat});
                4'd1: assert (source_data == {12'h000, mstat});
                4'd2: assert (source_data == {8'h00, sstat});
                4'd3: assert (source_data == {12'h000, imask});
                4'd4: assert (source_data == {11'h000, icntl});
                4'd5: assert (source_data == {2'b00, cntr});
                4'd7: assert (source_data == {8'h00, px});
                default: begin
                end
            endcase
        end
        assert (!internal_conflict);
        cover (boundary_valid);
        cover (invalid_subencoding);
        cover (source_extension_provisional);
        cover (count_stack_push);
        cover (count_stack_overflow);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (mstat == 4'h0);
            assert (imask == 4'h0);
            assert (!cntr_valid);
            assert (sstat == 8'h55);
            assert (count_stack_depth == 3'd0);
            assert (!count_stack_overflow);
        end else if (
            $past(
                invalid_opcode
                || invalid_subencoding
                || invalid_setup
                || integration_conflict
            )
        ) begin
            assume (probe_code == $past(probe_code));
            assert (probe_data == $past(probe_data));
            assert (astat == $past(astat));
            assert (mstat == $past(mstat));
            assert (icntl == $past(icntl));
            assert (imask == $past(imask));
            assert (cntr == $past(cntr));
            assert (cntr_valid == $past(cntr_valid));
            assert (px == $past(px));
            assert (sstat == $past(sstat));
            assert (count_stack_depth == $past(count_stack_depth));
            assert (count_stack_overflow == $past(count_stack_overflow));
        end
        past_valid <= 1'b1;
    end
endmodule

`default_nettype wire
