create_clock -name virtual_mac_clock -period 20.000
set_input_delay -clock virtual_mac_clock 0.000 [all_inputs]
set_output_delay -clock virtual_mac_clock 0.000 [all_outputs]
