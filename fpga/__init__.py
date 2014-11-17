#!/usr/bin/env python

__author__ = 'michiel'

from myhdl.conversion._toVHDL import _ToVHDLConvertor

class CustomVHDL(_ToVHDLConvertor):

    def __init__(self):
        super(CustomVHDL, self).__init__()
        self.library = "work"
        self.architecture = "ScryverDesign"
        self.numeric_ports = False

toVHDL = CustomVHDL()