`default_nettype none

// Type 17 compatibility/action wrapper around the one shared architectural
// state owner. The decoder determines one cycle-start read and one cycle-end
// general-register write; storage does not live in this instruction wrapper.
module adsp2100_internal_move_slice (
    input  logic        clk_i,
    input  logic        reset_i,
    input  logic        execute_i,
    input  logic [23:0] opcode_i,

    input  logic        setup_write_i,
    input  logic        setup_data_valid_i,
    input  logic [5:0]  setup_code_i,
    input  logic [15:0] setup_data_i,

    input  logic [5:0]  probe_code_i,
    output logic [15:0] probe_data_o,

    output logic        class_valid_o,
    output logic        boundary_valid_o,
    output logic        invalid_opcode_o,
    output logic        invalid_subencoding_o,
    output logic        invalid_setup_o,
    output logic        integration_conflict_o,
    output logic        internal_conflict_o,
    output logic [5:0]  source_code_o,
    output logic [5:0]  destination_code_o,
    output logic [15:0] source_data_o,
    output logic        source_extension_provisional_o,
    output logic        count_stack_push_o,
    output logic [13:0] count_stack_push_data_o,
    output logic [2:0]  count_stack_depth_o,
    output logic        count_stack_overflow_o,
    output logic [7:0]  astat_o,
    output logic [3:0]  mstat_o,
    output logic [4:0]  icntl_o,
    output logic [3:0]  imask_o,
    output logic [13:0] cntr_o,
    output logic        cntr_valid_o,
    output logic [7:0]  px_o,
    output logic [7:0]  sstat_o,
    output logic        pm_data_access_o,
    output logic        dm_access_o
);
    logic       decoded_move_valid;
    logic       decoded_invalid_subencoding;
    logic [1:0] unused_destination_group;
    logic [1:0] source_group;
    logic [3:0] unused_destination_index;
    logic [3:0] source_index;
    logic       unused_destination_present;
    logic       unused_destination_writable;
    logic       unused_source_selector_valid;

    logic       setup_present;
    logic       setup_writable;
    logic       setup_valid;
    logic       state_write;
    logic [5:0] state_write_code;
    logic [15:0] state_write_data;
    logic       state_write_data_valid;
    logic       state_invalid_move_write;
    logic       alternate_bank_unused;
    logic       unused_observation;

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

    adsp2100_internal_move_decode decode (
        .opcode_i(opcode_i),
        .class_valid_o(class_valid_o),
        .move_valid_o(decoded_move_valid),
        .invalid_subencoding_o(decoded_invalid_subencoding),
        .destination_group_o(unused_destination_group),
        .source_group_o(source_group),
        .destination_index_o(unused_destination_index),
        .source_index_o(source_index),
        .destination_code_o(destination_code_o),
        .source_code_o(source_code_o),
        .destination_present_o(unused_destination_present),
        .destination_writable_o(unused_destination_writable),
        .source_valid_o(unused_source_selector_valid)
    );

    assign setup_present = selector_present(
        setup_code_i[5:4], setup_code_i[3:0]
    );
    assign setup_writable = setup_present && (setup_code_i != 6'h32);
    assign setup_valid = setup_write_i && setup_writable;
    assign invalid_setup_o = !reset_i && setup_write_i && !setup_writable;
    assign integration_conflict_o = !reset_i && execute_i && setup_write_i;
    assign invalid_opcode_o = !reset_i && execute_i && !class_valid_o;
    assign invalid_subencoding_o = (
        !reset_i && execute_i && class_valid_o
        && decoded_invalid_subencoding
    );
    assign boundary_valid_o = (
        !reset_i && execute_i && decoded_move_valid && !setup_write_i
    );
    assign state_write = boundary_valid_o || (
        !reset_i && !execute_i && setup_valid
    );
    assign state_write_code = boundary_valid_o
        ? destination_code_o : setup_code_i;
    assign state_write_data = boundary_valid_o
        ? source_data_o : setup_data_i;
    assign state_write_data_valid = boundary_valid_o || setup_data_valid_i;
    assign source_extension_provisional_o = (
        boundary_valid_o && (source_group == 2'b11)
        && (source_index <= 4'd4)
    );
    assign pm_data_access_o = 1'b0;
    assign dm_access_o = 1'b0;

    adsp2100_architectural_state state (
        .clk_i(clk_i),
        .reset_i(reset_i),
        .move_write_i(state_write),
        .move_data_valid_i(state_write_data_valid),
        .move_code_i(state_write_code),
        .move_data_i(state_write_data),
        .read_code_i(source_code_o),
        .read_data_o(source_data_o),
        .probe_code_i(probe_code_i),
        .probe_data_o(probe_data_o),
        .invalid_move_write_o(state_invalid_move_write),
        .internal_conflict_o(internal_conflict_o),
        .count_stack_push_o(count_stack_push_o),
        .count_stack_push_data_o(count_stack_push_data_o),
        .count_stack_depth_o(count_stack_depth_o),
        .count_stack_overflow_o(count_stack_overflow_o),
        .astat_o(astat_o),
        .mstat_o(mstat_o),
        .icntl_o(icntl_o),
        .imask_o(imask_o),
        .cntr_o(cntr_o),
        .cntr_valid_o(cntr_valid_o),
        .px_o(px_o),
        .sstat_o(sstat_o),
        .alternate_bank_o(alternate_bank_unused)
    );

    assign unused_observation = ^{
        unused_destination_group, unused_destination_index,
        unused_destination_present, unused_destination_writable,
        unused_source_selector_valid, state_invalid_move_write,
        alternate_bank_unused
    };

`ifndef SYNTHESIS
    always_comb begin
        assert (unused_observation == unused_observation);
        assert (!(boundary_valid_o && integration_conflict_o));
        assert (!(state_write && state_invalid_move_write));
        assert (!pm_data_access_o && !dm_access_o);
    end
`endif
endmodule

`default_nettype wire
