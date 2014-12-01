#!/usr/env/python

from __future__ import print_function
# from distutils.core import setup
from setuptools import setup

__author__ = 'michiel'

setup(name='fpga',
      version='0.1.0',
      description='FPGA modules for conversion to VHDL',
      author='Michiel',
      install_requires=['myhdl'],
      packages=['fpga', 'fpga.basics', 'fpga.encoders', 'fpga.generators', 'fpga.interfaces', 'fpga.tests'])