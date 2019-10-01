"""
File name: test_sensing_module_response.py
Author: Yerbol Aussat
Python Version: 2.7

Script to test response of sensing modules
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
			time.sleep(0.5)
	except KeyboardInterrupt:
		print "\nScript Interrupted"
		office_sensing.stop_sens_modules()


# Print illuminance values on each sensor
def print_illuminance(illuminance):
	print "\nIlluminance readings from light sensors:"
	for i in range(len(illuminance)):
		print "{}".format(illuminance[i])
	print " ", "-"*13


# Print occupancy values on each sensor
def print_occupancy(occupancy):
	print "\n Occupancy matrix:"
	for i in range(len(occupancy)):
		print "{}".format(occupancy[i])
	print " ", "-"*13


if __name__ == '__main__':
	addresses = [
	             # ("192.168.50.188", 1234),  # Omega-F13D
	             # ("192.168.50.179", 1234),  # Omega-F075
	             # ("192.168.50.158", 1234),  # Omega-F11F
	             ("192.168.50.168", 1234),  # Omega-F129
	             # ("192.168.50.171", 1234)  # Omega-B02D

	]
	light_calibration_const = [0.478023824068, 0.472723094776, 0.472723094776, 0.513906092956]
	office_sensing_modules = OfficeSensing(addresses, light_calibration_const)
	test_sensing_module_response(office_sensing_modules)
