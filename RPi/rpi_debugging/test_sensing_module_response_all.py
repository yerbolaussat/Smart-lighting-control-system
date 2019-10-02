"""
File name: test_sensing_module_response_all.py
Author: Yerbol Aussat
Python Version: 2.7

Script to test response of sensing modules. When printing the values, this script assumes that there are
four sensing modules.
"""

import time
import sys
import os
import inspect
from datetime import datetime as dt
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from office_sensing import OfficeSensing


# Get sensor values and trigger optimization process
def test_sensing_module_response(office_sensing):
	try:
		while True:
			# Get sensor readings
			illuminance, occupancy = office_sensing.get_sensor_readings()
			print "\n", "*"*25
			print dt.now()
			print_illuminance(illuminance)
			print_occupancy(occupancy)
			time.sleep(0.01)
	except KeyboardInterrupt:
		print "\nScript Interrupted"
		office_sensing.stop_sens_modules()


# Print illuminance values on each sensor
def print_illuminance(illuminance):
	print "\nIlluminance readings from light sensors:"
	print " ", "-"*13
	print "  |   LIGHT   |"
	print " ", "-"*13
	print "  | {:<3} | {:<3} |".format(int(round(illuminance[1])), int(round(illuminance[3])))
	print " ", "-"*13
	print "  | {:<3} | {:<3} |".format(int(round(illuminance[0])), int(round(illuminance[2])))
	print " ", "-"*13


# Print occupancy values on each sensor
def print_occupancy(occupancy):
	print "\n Occupancy matrix:"
	print "  ", "_"*11
	print "  ", "| {:<1}  |  {:<1} |".format(occupancy[1], occupancy[3])
	print "  ", "_"*11
	print "  ", "| {:<1}  |  {:<1} |".format(occupancy[0], occupancy[2])
	print "  ", "_"*11
	print "\n"


if __name__ == '__main__':
	addresses = [("192.168.50.188", 1234),  # Omega-F13D
	             ("192.168.50.179", 1234),  # Omega-F075
	             ("192.168.50.158", 1234),  # Omega-F11F
	             ("192.168.50.168", 1234)]  # Omega-F129
	light_calibration_const = [0.478023824068, 0.472723094776, 0.472723094776, 0.513906092956]
	office_sensing_modules = OfficeSensing(addresses, light_calibration_const)
	test_sensing_module_response(office_sensing_modules)
