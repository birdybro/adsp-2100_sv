`default_nettype none

package adsp2100_pkg;
  localparam int unsigned PROGRAM_WORD_WIDTH = 24;
  localparam int unsigned DATA_WORD_WIDTH    = 16;
  localparam int unsigned ADDRESS_WIDTH      = 14;
  localparam int unsigned MAC_RESULT_WIDTH   = 40;
  localparam int unsigned ASTAT_WIDTH        = 8;
  localparam int unsigned MSTAT_WIDTH        = 4;
  localparam int unsigned IMASK_WIDTH        = 4;
  localparam int unsigned ICNTL_WIDTH        = 5;

  typedef logic [PROGRAM_WORD_WIDTH-1:0] program_word_t;
  typedef logic [DATA_WORD_WIDTH-1:0]    data_word_t;
  typedef logic [ADDRESS_WIDTH-1:0]      address_t;
  typedef logic [MAC_RESULT_WIDTH-1:0]   mac_result_t;
  typedef logic [ASTAT_WIDTH-1:0]        astat_t;
  typedef logic [MSTAT_WIDTH-1:0]        mstat_t;
  typedef logic [IMASK_WIDTH-1:0]        imask_t;
  typedef logic [ICNTL_WIDTH-1:0]        icntl_t;

  // Names reflect the manual's externally observable states 1 through 8.
  // Encoding state 1 as zero keeps the type at the minimum three bits.
  typedef enum logic [2:0] {
    PHASE_STATE_1 = 3'd0,
    PHASE_STATE_2 = 3'd1,
    PHASE_STATE_3 = 3'd2,
    PHASE_STATE_4 = 3'd3,
    PHASE_STATE_5 = 3'd4,
    PHASE_STATE_6 = 3'd5,
    PHASE_STATE_7 = 3'd6,
    PHASE_STATE_8 = 3'd7
  } phase_state_t;

  typedef enum logic {
    MEMORY_SPACE_PM = 1'b0,
    MEMORY_SPACE_DM = 1'b1
  } memory_space_t;

  typedef enum logic [1:0] {
    TRANSACTION_FETCH = 2'b00,
    TRANSACTION_READ  = 2'b01,
    TRANSACTION_WRITE = 2'b10
  } transaction_kind_t;
endpackage

`default_nettype wire
