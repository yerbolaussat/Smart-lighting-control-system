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
from phue import Bridge

PHUE_IP_ADDRESS = '192.168.0.2'

# Get sensor values and trigger optimization process
def find_curve(office_sensing, lights, bulb_id):	
	brighness_vals = [-1] + range(0, 255, 25) + [255]
	sensor_readings = []
	
	try:
		for brightness in brighness_vals:
			set_brightness(bulb_id, brightness)
			time.sleep(2)
			light_sensor_reading, occupancy = office_sensing.get_sensor_readings()
			light_sensor_reading = light_sensor_reading[0]
			sensor_readings.append(light_sensor_reading)
			print "Brightness: {}, Light sensor: {}".format(brightness, light_sensor_reading)
	except KeyboardInterrupt:
		print "\nScript Interrupted"
		office_sensing.stop_sens_modules()
	print "Bulb {}".format(bulb_id)
	print brighness_vals
	print sensor_readings

# Turn the bulb on, and set brightness to a specified value
def set_brightness(bulb_id, bright_value):
	l = lights[bulb_id]
	if bright_value == -1:
		l.on = False
	else:
		l.on = True
		l.brightness = bright_value

if __name__ == '__main__':
	addresses = [("192.168.50.171", 1234)]  # Omega-B02D
	
	# Set up hue bridge
	b = Bridge(PHUE_IP_ADDRESS)
	b.connect()
	lights = b.lights
	for l in lights:
		l.on = False
	
	office_sensing_modules = OfficeSensing(addresses, [1.0])
	
	bulb_id = 1
	find_curve(office_sensing_modules, lights, bulb_id)
	office_sensing_modules.stop_sens_modules()
	for light in lights:
		light.on = True

	# lights[bulb_id].on = True
	# lights[bulb_id].brightness = 100
