# Bounded Type 3 architectural/logical-DM slice, not whole-core timing.
create_clock -name direct_dm_slice_clock -period 25.000 [get_ports {clk_i}]
set_input_delay -clock direct_dm_slice_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock direct_dm_slice_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock direct_dm_slice_clock 0.000 [all_outputs]
