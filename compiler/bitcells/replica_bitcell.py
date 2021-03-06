# See LICENSE for licensing information.
#
# Copyright (c) 2016-2019 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import design
import debug
import utils
from tech import GDS,layer,drc,parameter,cell_properties
from tech import cell_properties as props

from globals import OPTS

class replica_bitcell(design.design):
    """
    A single bit cell (6T, 8T, etc.)
    This module implements the single memory cell used in the design. It
    is a hand-made cell, so the layout and netlist should be available in
    the technology library. """

    if cell_properties.bitcell.split_wl:
        pin_names = ["bl", "br", "wl0", "wl1", "vdd", "gnd"]
        type_list = ["OUTPUT", "OUTPUT", "INPUT", "INPUT" , "POWER", "GROUND"] 
    else:
        pin_names = [props.bitcell.cell_6t.pin.bl,
                     props.bitcell.cell_6t.pin.br,
                     props.bitcell.cell_6t.pin.wl,
                     props.bitcell.cell_6t.pin.vdd,
                     props.bitcell.cell_6t.pin.gnd]

        type_list = ["OUTPUT", "OUTPUT", "INPUT", "POWER", "GROUND"] 
    
    if not OPTS.netlist_only:
        (width,height) = utils.get_libcell_size("replica_cell_6t", GDS["unit"], layer["boundary"])
        pin_map = utils.get_libcell_pins(pin_names, "replica_cell_6t", GDS["unit"])
    else:
        (width,height) = (0,0)
        pin_map = []

    def __init__(self, name=""):
        # Ignore the name argument
        design.design.__init__(self, "replica_cell_6t")
        debug.info(2, "Create replica bitcell object")

        self.width = replica_bitcell.width
        self.height = replica_bitcell.height
        self.pin_map = replica_bitcell.pin_map
        self.add_pin_types(self.type_list)
        
    def get_stage_effort(self, load):
        parasitic_delay = 1
        size = 0.5 #This accounts for bitline being drained thought the access TX and internal node
        cin = 3 #Assumes always a minimum sizes inverter. Could be specified in the tech.py file.
        read_port_load = 0.5 #min size NMOS gate load
        return logical_effort.logical_effort('bitline', size, cin, load+read_port_load, parasitic_delay, False)
        
    def input_load(self):
        """Return the relative capacitance of the access transistor gates"""
        
        # FIXME: This applies to bitline capacitances as well.
        access_tx_cin = parameter["6T_access_size"]/drc["minwidth_tx"]
        return 2*access_tx_cin    
    
    def analytical_power(self, corner, load):
        """Bitcell power in nW. Only characterizes leakage."""
        from tech import spice
        leakage = spice["bitcell_leakage"]
        dynamic = 0 #temporary
        total_power = self.return_power(dynamic, leakage)
        return total_power

    def build_graph(self, graph, inst_name, port_nets):        
        """Adds edges based on inputs/outputs. Overrides base class function."""
        self.add_graph_edges(graph, port_nets)
