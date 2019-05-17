"""
	File name: rpi_sense.py
	Author: Yerbol Aussat
	Date created: 7/25/2018
	Python Version: 2.7
	
	Process that sets target illuminance values on Philips Hue bulbs
"""
import sys
from ceiling_actuation import CeilingActuation

# d_opt = [int(val) for val in sys.argv[1].split()]

d_opt = [1]*8

phue_bridge_ip_address = '192.168.0.2'
actuators = CeilingActuation(phue_bridge_ip_address)
actuators.set_dimming(d_opt)
