# Bounded steady-state NOP/Type 6/Type 7 owner, not whole-core timing.
create_clock -name linear_core_clock -period 25.000 [get_ports {clk_i}]
set_input_delay -clock linear_core_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock linear_core_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock linear_core_clock 0.000 [all_outputs]
