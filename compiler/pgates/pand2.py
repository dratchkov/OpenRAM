import debug
import design
from tech import drc
from math import log
from vector import vector
from globals import OPTS
from pnand2 import pnand2
from pinv import pinv

class pand2(design.design):
    """
    This is a simple buffer used for driving loads. 
    """
    from importlib import reload
    c = reload(__import__(OPTS.bitcell))
    bitcell = getattr(c, OPTS.bitcell)

    unique_id = 1

    def __init__(self, size=1, height=bitcell.height, name=""):

        self.size = size
        self.height = height
        
        if name=="":
            name = "pand2_{0}_{1}".format(size, pand2.unique_id)
            pand2.unique_id += 1

        design.design.__init__(self, name)
        debug.info(1, "Creating {}".format(self.name))

        
        self.create_netlist()
        if not OPTS.netlist_only:        
            self.create_layout()


    def create_netlist(self):
        self.add_pins()
        self.create_modules()
        self.create_insts()

    def create_modules(self):
        # Shield the cap, but have at least a stage effort of 4
        self.nand = pnand2(height=self.height) 
        self.add_mod(self.nand)
        
        self.inv = pinv(size=self.size, height=self.height)
        self.add_mod(self.inv)

    def create_layout(self):
        self.width = self.nand.width + self.inv.width
        self.place_insts()
        self.add_wires()
        self.add_layout_pins()
        
    def add_pins(self):
        self.add_pin("A")
        self.add_pin("B")
        self.add_pin("Z")
        self.add_pin("vdd")
        self.add_pin("gnd")

    def create_insts(self):
        self.nand_inst=self.add_inst(name="pand2_nand",
                                     mod=self.nand)
        self.connect_inst(["A", "B", "zb_int",  "vdd", "gnd"])
        
        self.inv_inst=self.add_inst(name="pand2_inv",
                                    mod=self.inv)
        self.connect_inst(["zb_int", "Z",  "vdd", "gnd"])

    def place_insts(self):
        # Add NAND to the right 
        self.nand_inst.place(offset=vector(0,0))

        # Add INV to the right
        self.inv_inst.place(offset=vector(self.nand_inst.rx(),0))
        
    def add_wires(self):
        # nand Z to inv A
        z1_pin = self.nand_inst.get_pin("Z")
        a2_pin = self.inv_inst.get_pin("A")
        mid1_point = vector(0.5*(z1_pin.cx()+a2_pin.cx()), z1_pin.cy())
        mid2_point = vector(mid1_point, a2_pin.cy())
        self.add_path("metal1", [z1_pin.center(), mid1_point, mid2_point, a2_pin.center()])
        
        
    def add_layout_pins(self):
        # Continous vdd rail along with label.
        vdd_pin=self.inv_inst.get_pin("vdd")
        self.add_layout_pin(text="vdd",
                            layer="metal1",
                            offset=vdd_pin.ll().scale(0,1),
                            width=self.width,
                            height=vdd_pin.height())
        
        # Continous gnd rail along with label.
        gnd_pin=self.inv_inst.get_pin("gnd")
        self.add_layout_pin(text="gnd",
                            layer="metal1",
                            offset=gnd_pin.ll().scale(0,1),
                            width=self.width,
                            height=vdd_pin.height())
            
        z_pin = self.inv_inst.get_pin("Z")
        self.add_via_center(layers=("metal1","via1","metal2"),
                            offset=z_pin.center(),
                            rotate=90)
        self.add_layout_pin_rect_center(text="Z",
                                        layer="metal2",
                                        offset=z_pin.center())

        for pin_name in ["A","B"]:
            pin = self.nand_inst.get_pin(pin_name)
            self.add_layout_pin_rect_center(text=pin_name,
                                            layer="metal2",
                                            offset=pin.center())
            self.add_via_center(layers=("metal1","via1","metal2"),
                                offset=pin.center(),
                                rotate=90)
        
        

    def analytical_delay(self, slew, load=0.0):
        """ Calculate the analytical delay of DFF-> INV -> INV """
        nand_delay = selfnand.analytical_delay(slew=slew, load=self.inv.input_load()) 
        inv_delay = self.inv.analytical_delay(slew=nand_delay.slew, load=load)
        return nand_delay + inv_delay
    
    
