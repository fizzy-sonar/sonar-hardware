# Batch synthesis/implementation gate. This intentionally fails before spending
# host time when T-011's audited PACKAGE_PIN constraints are unavailable.
set script_dir [file dirname [file normalize [info script]]]
set gateware_dir [file normalize [file join $script_dir ..]]
set real_xdc [file join $gateware_dir constraints sonar_cmod_a7.xdc]

if {![file exists $real_xdc]} {
    error "T-011 gate: constraints/sonar_cmod_a7.xdc is missing; no pins may be guessed"
}

source [file join $script_dir create_project.tcl]
set report_dir [file join $gateware_dir build reports]
file mkdir $report_dir

launch_runs synth_1 -jobs 4
wait_on_run synth_1
open_run synth_1
report_utilization -file [file join $report_dir post_synth_utilization.rpt]
report_timing_summary -file [file join $report_dir post_synth_timing.rpt]

launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1
open_run impl_1
report_utilization -file [file join $report_dir post_route_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained \
    -file [file join $report_dir post_route_timing.rpt]
report_cdc -file [file join $report_dir post_route_cdc.rpt]

set timing_paths [get_timing_paths -quiet -slack_lesser_than 0]
if {[llength $timing_paths] != 0} {
    error "Timing is not closed; see build/reports/post_route_timing.rpt"
}
puts "Bitstream and reports completed"
