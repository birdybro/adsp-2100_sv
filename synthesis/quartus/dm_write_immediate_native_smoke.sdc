create_clock -name dm_write_native_clock -period 20.000 [get_ports {clk_i}]
# Virtual controls model same-clock, register-launched phase and request inputs.
set_input_delay -clock dm_write_native_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock dm_write_native_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock dm_write_native_clock 0.000 [all_outputs]
