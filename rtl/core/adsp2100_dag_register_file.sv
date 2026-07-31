`default_nettype none

module adsp2100_dag_register_file (
    input  logic        clk_i,
    input  logic        reset_i,

    input  logic [2:0]  i_l_read_address_i,
    input  logic [2:0]  m_read_address_i,
    output logic [13:0] i_read_data_o,
    output logic        i_read_valid_o,
    output logic [13:0] m_read_data_o,
    output logic        m_read_valid_o,
    output logic [13:0] l_read_data_o,
    output logic        l_read_valid_o,

    input  logic [2:0]  probe_address_i,
    output logic [13:0] probe_i_data_o,
    output logic        probe_i_valid_o,
    output logic [13:0] probe_m_data_o,
    output logic        probe_m_valid_o,
    output logic [13:0] probe_l_data_o,
    output logic        probe_l_valid_o,

    input  logic        setup_write_i,
    input  logic [1:0]  setup_kind_i,
    input  logic [2:0]  setup_address_i,
    input  logic [13:0] setup_data_i,

    input  logic        i_write_enable_i,
    input  logic [2:0]  i_write_address_i,
    input  logic [13:0] i_write_data_i,
    input  logic        i_write_result_valid_i,

    output logic        invalid_setup_kind_o,
    output logic        write_conflict_o
);
    localparam logic [1:0] KIND_I = 2'b00;
    localparam logic [1:0] KIND_M = 2'b01;
    localparam logic [1:0] KIND_L = 2'b10;

    logic [13:0] i_q [0:7];
    logic [13:0] m_q [0:7];
    logic [13:0] l_q [0:7];
    logic [7:0]  i_valid_q;
    logic [7:0]  m_valid_q;
    logic [7:0]  l_valid_q;

    always_comb begin
        i_read_data_o = i_q[i_l_read_address_i];
        i_read_valid_o = i_valid_q[i_l_read_address_i];
        m_read_data_o = m_q[m_read_address_i];
        m_read_valid_o = m_valid_q[m_read_address_i];
        l_read_data_o = l_q[i_l_read_address_i];
        l_read_valid_o = l_valid_q[i_l_read_address_i];

        probe_i_data_o = i_q[probe_address_i];
        probe_i_valid_o = i_valid_q[probe_address_i];
        probe_m_data_o = m_q[probe_address_i];
        probe_m_valid_o = m_valid_q[probe_address_i];
        probe_l_data_o = l_q[probe_address_i];
        probe_l_valid_o = l_valid_q[probe_address_i];

        invalid_setup_kind_o = (
            !reset_i
            && setup_write_i
            && (setup_kind_i == 2'b11)
        );
        write_conflict_o = (
            !reset_i
            && setup_write_i
            && (setup_kind_i == KIND_I)
            && i_write_enable_i
            && (setup_address_i == i_write_address_i)
        );
    end

    // Original I/M/L contents are not documented after reset. Validity is
    // cleared without assigning invented data values. A valid Type 21 result
    // writes only its selected I register at the cycle-ending edge.
    always_ff @(posedge clk_i) begin
        if (reset_i) begin
            i_valid_q <= 8'h00;
            m_valid_q <= 8'h00;
            l_valid_q <= 8'h00;
        end else if (!write_conflict_o) begin
            if (setup_write_i && !invalid_setup_kind_o) begin
                case (setup_kind_i)
                    KIND_I: begin
                        i_q[setup_address_i] <= setup_data_i;
                        i_valid_q[setup_address_i] <= 1'b1;
                    end
                    KIND_M: begin
                        m_q[setup_address_i] <= setup_data_i;
                        m_valid_q[setup_address_i] <= 1'b1;
                    end
                    KIND_L: begin
                        l_q[setup_address_i] <= setup_data_i;
                        l_valid_q[setup_address_i] <= 1'b1;
                    end
                    default: begin
                    end
                endcase
            end

            if (i_write_enable_i) begin
                if (i_write_result_valid_i) begin
                    i_q[i_write_address_i] <= i_write_data_i;
                end
                i_valid_q[i_write_address_i]
                    <= i_write_result_valid_i;
            end
        end
    end
endmodule

`default_nettype wire
