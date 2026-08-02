# Three-client shared-cache/native-PM/BR-BG composition; not whole-core closure.
create_clock -name program_clients_owner_control_clock -period 20.000 \
    [get_ports {clk_i}]
set_input_delay -clock program_clients_owner_control_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock program_clients_owner_control_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock program_clients_owner_control_clock 0.000 [all_outputs]

# integration_conflict_o is a verification-only aggregation of every bounded
# client's fail-closed diagnostics.  It neither feeds architectural state nor
# represents an original ADSP-2100 pin.  Permit an external checker to sample
# that observation on the second edge; all architectural, PM, BR/BG, HALT, and
# client event outputs retain the one-cycle 50 MHz requirement above.
set_multicycle_path -setup 2 -to [get_ports {integration_conflict_o}]
set_multicycle_path -hold 1 -to [get_ports {integration_conflict_o}]
