# Recreate the Vivado project from source; no GUI project state is authoritative.
set script_dir [file dirname [file normalize [info script]]]
set gateware_dir [file normalize [file join $script_dir ..]]
set project_dir [file join $gateware_dir build vivado]

create_project -force sonar_gateware $project_dir -part xc7a35tcpg236-1
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]
set_property verilog_define XILINX [current_fileset]

set rtl_files [glob -nocomplain [file join $gateware_dir rtl *.sv]]
add_files -norecurse $rtl_files
set_property top sonar_top [current_fileset]

set real_xdc [file join $gateware_dir constraints sonar_cmod_a7.xdc]
set placeholder_xdc [file join $gateware_dir constraints sonar_cmod_a7_placeholder.xdc]
if {[file exists $real_xdc]} {
    add_files -fileset constrs_1 -norecurse $real_xdc
    puts "Using T-011 pin constraints: $real_xdc"
} else {
    add_files -fileset constrs_1 -norecurse $placeholder_xdc
    puts "WARNING: T-011 pin map missing; project is timing-inspection only."
    puts "WARNING: build_bitstream.tcl will refuse an unpinned build."
}

update_compile_order -fileset sources_1
puts "Created sonar_gateware for xc7a35tcpg236-1 at $project_dir"
