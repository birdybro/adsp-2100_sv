create_clock -name mode_slice_clock -period 20.000 [get_ports {clk_i}]
# These virtual ports model same-clock, register-launched core controls rather
# than asynchronous package pins. Five nanoseconds includes the launch clock
# tree and source register clock-to-Q in this isolated top-level fit.
set_input_delay -clock mode_slice_clock -max 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_input_delay -clock mode_slice_clock -min 5.000 \
    [remove_from_collection [all_inputs] [get_ports {clk_i}]]
set_output_delay -clock mode_slice_clock 0.000 [all_outputs]
