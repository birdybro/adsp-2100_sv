create_clock -name virtual_direct_dm_decode_clock -period 20.000
set_input_delay -clock virtual_direct_dm_decode_clock 0.000 [all_inputs]
set_output_delay -clock virtual_direct_dm_decode_clock 0.000 [all_outputs]
