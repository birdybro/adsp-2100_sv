# Bounded linear-fetch/BR-BG composition, not whole-core timing.
create_clock -name linear_bus_control_clock -period 25.000 [get_ports {clk_i}]
set_input_delay -clock linear_bus_control_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock linear_bus_control_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock linear_bus_control_clock 0.000 [all_outputs]
