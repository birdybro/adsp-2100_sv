`default_nettype none

module adsp2100_load_non_dreg_immediate_formal (
    input logic        clk,
    input logic        reset,
    input logic        execute,
    input logic [23:0] opcode,
    input logic        setup_write,
    input logic [5:0]  setup_code,
    input logic [15:0] setup_data,
    input logic [5:0]  probe_code
);
    logic class_valid;
    logic action_valid;
    logic invalid_subencoding;
    logic boundary_valid;
    logic invalid_opcode;
    logic invalid_setup;
    logic integration_conflict;
    logic internal_conflict;
    logic [1:0] register_group;
    logic [3:0] register_index;
    logic [5:0] register_code;
    logic [13:0] immediate_data;
    logic data_register_destination;
    logic reserved_destination;
    logic read_only_destination;
    logic [15:0] probe_data;
    logic [7:0] astat;
    logic [3:0] mstat;
    logic [4:0] icntl;
    logic [3:0] imask;
    logic [13:0] cntr;
    logic cntr_valid;
    logic [7:0] px;
    logic [7:0] sstat;
    logic count_stack_push;
    logic [13:0] count_stack_push_data;
    logic [2:0] count_stack_depth;
    logic count_stack_overflow;
    logic pm_data_access;
    logic dm_access;
    logic expected_class;
    logic expected_present;
    logic expected_writable;
    logic expected_setup_present;
    logic expected_setup_writable;
    logic past_valid;

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

    assign expected_class = opcode[23:20] == 4'h3;
    assign expected_present = selector_present(opcode[19:18], opcode[3:0]);
    assign expected_writable = (
        expected_present
        && opcode[19:18] != 2'b00
        && !(opcode[19:18] == 2'b11 && opcode[3:0] == 4'd2)
    );
    assign expected_setup_present = selector_present(
        setup_code[5:4], setup_code[3:0]
    );
    assign expected_setup_writable = (
        expected_setup_present && setup_code != 6'h32
    );

    adsp2100_load_non_dreg_immediate_slice dut (
        .clk_i(clk),
        .reset_i(reset),
        .execute_i(execute),
        .opcode_i(opcode),
        .setup_write_i(setup_write),
        .setup_code_i(setup_code),
        .setup_data_i(setup_data),
        .probe_code_i(probe_code),
        .class_valid_o(class_valid),
        .action_valid_o(action_valid),
        .invalid_subencoding_o(invalid_subencoding),
        .boundary_valid_o(boundary_valid),
        .invalid_opcode_o(invalid_opcode),
        .invalid_setup_o(invalid_setup),
        .integration_conflict_o(integration_conflict),
        .internal_conflict_o(internal_conflict),
        .register_group_o(register_group),
        .register_index_o(register_index),
        .register_code_o(register_code),
        .immediate_data_o(immediate_data),
        .data_register_destination_o(data_register_destination),
        .reserved_destination_o(reserved_destination),
        .read_only_destination_o(read_only_destination),
        .probe_data_o(probe_data),
        .astat_o(astat),
        .mstat_o(mstat),
        .icntl_o(icntl),
        .imask_o(imask),
        .cntr_o(cntr),
        .cntr_valid_o(cntr_valid),
        .px_o(px),
        .sstat_o(sstat),
        .count_stack_push_o(count_stack_push),
        .count_stack_push_data_o(count_stack_push_data),
        .count_stack_depth_o(count_stack_depth),
        .count_stack_overflow_o(count_stack_overflow),
        .pm_data_access_o(pm_data_access),
        .dm_access_o(dm_access)
    );

    initial past_valid = 1'b0;

    always_comb begin
        assert (class_valid == expected_class);
        assert (action_valid == (expected_class && expected_writable));
        assert (
            invalid_subencoding
            == (!reset && execute && expected_class && !expected_writable)
        );
        assert (
            boundary_valid
            == (!reset && execute && expected_class
                && expected_writable && !setup_write)
        );
        assert (invalid_opcode == (!reset && execute && !expected_class));
        assert (integration_conflict == (!reset && execute && setup_write));
        assert (
            invalid_setup
            == (!reset && !execute && setup_write && !expected_setup_writable)
        );
        assert (!internal_conflict);
        assert (!pm_data_access && !dm_access);
        if (expected_class) begin
            assert (register_group == opcode[19:18]);
            assert (register_index == opcode[3:0]);
            assert (register_code == {opcode[19:18], opcode[3:0]});
            assert (immediate_data == opcode[17:4]);
            assert (data_register_destination == (opcode[19:18] == 2'b00));
            assert (reserved_destination == !expected_present);
            assert (
                read_only_destination
                == (opcode[19:18] == 2'b11 && opcode[3:0] == 4'd2)
            );
        end else begin
            assert (register_group == 2'b00);
            assert (register_index == 4'h0);
            assert (register_code == 6'h00);
            assert (immediate_data == 14'h0000);
        end
        if (count_stack_push) begin
            assert (boundary_valid || (!execute && setup_write));
            assert ((boundary_valid && register_code == 6'h35)
                || (!execute && setup_code == 6'h35));
            assert (count_stack_push_data == cntr);
        end
        cover (boundary_valid && register_code == 6'h10);
        cover (boundary_valid && register_code == 6'h31);
        cover (boundary_valid && register_code == 6'h35 && count_stack_push);
        cover (invalid_subencoding && data_register_destination);
        cover (invalid_subencoding && read_only_destination);
    end

    always_ff @(posedge clk) begin
        if (!past_valid) begin
            assume (reset);
        end else if ($past(reset)) begin
            assert (mstat == 4'h0);
            assert (imask == 4'h0);
            assert (!cntr_valid);
            assert (count_stack_depth == 3'd0);
            assert (!count_stack_overflow);
            assert (sstat == 8'h55);
        end else if (
            $past(invalid_opcode || invalid_subencoding
                || integration_conflict || invalid_setup)
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
