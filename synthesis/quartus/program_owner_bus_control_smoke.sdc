create_clock -name program_owner_bus_control_clock -period 20.000 [get_ports {clk_i}]
set_input_delay -clock program_owner_bus_control_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock program_owner_bus_control_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock program_owner_bus_control_clock 0.000 [all_outputs]
