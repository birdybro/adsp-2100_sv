# The Type 4/native-DM slice qualifies one bounded client attachment. It is
# not a whole-core timing constraint or a claim about asynchronous pin timing.
create_clock -name compute_dm_native_clock -period 25.000 [get_ports {clk_i}]
set_input_delay -clock compute_dm_native_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock compute_dm_native_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock compute_dm_native_clock 0.000 [all_outputs]
