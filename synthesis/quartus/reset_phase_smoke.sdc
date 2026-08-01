# Original RESET/logical-phase owner, not reset-PM or whole-core timing.
create_clock -name reset_phase_clock -period 20.000 [get_ports {clk_i}]
set_input_delay -clock reset_phase_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock reset_phase_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock reset_phase_clock 0.000 [all_outputs]
