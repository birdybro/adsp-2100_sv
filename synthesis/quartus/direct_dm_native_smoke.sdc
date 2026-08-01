# Bounded Type 3/native-DM attachment, not whole-core or analog pin timing.
create_clock -name direct_dm_native_clock -period 25.000 [get_ports {clk_i}]
set_input_delay -clock direct_dm_native_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock direct_dm_native_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock direct_dm_native_clock 0.000 [all_outputs]
