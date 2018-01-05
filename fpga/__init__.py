#!/usr/bin/env python

__author__ = 'michiel'

import myhdl.conversion._toVHDL as conv2vhdl

from . import utils
from . import basics

from .utils import *
from .basics import *


class CustomVHDL(conv2vhdl._ToVHDLConvertor):

    def __init__(self):
        super(CustomVHDL, self).__init__()
        self.library = "work"
        self.architecture = "ScryverDesign"
        self.numeric_ports = False
        self.std_logic_ports = True

conv2vhdl.toVHDL = CustomVHDL()

__all__ = utils.__all__ + basics.__all__
