"""
File name: test_sensing_module_response.py
Author: Yerbol Aussat
Python Version: 2.7

Script to test response of sensing modules
"""

import time
import picamera
import sys
import os
import inspect
from datetime import datetime as dt
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from office_sensing import OfficeSensing
from phue import Bridge

PHUE_IP = "192.168.0.2"

# Get sensor values and trigger optimization process
def test_sensing_module_response(office_sensing, bulb):
	try:
		while True:
			
			for brightness in [-1] + range(0, 255, 25) + [255]:
				if brightness == -1:
					bulb.on = False
				else:
					bulb.on = True
					bulb.brightness = brightness		 

				t = int(time.time())
				with picamera.PiCamera() as camera:
					camera.resolution = (160, 120)
					camera.vflip = True
					camera.hflip = True
					time.sleep(2)
					camera.capture("images/{}.jpg".format(str(t)))
				illuminance, _ = office_sensing.get_sensor_readings()			
				string_to_write = "{},{}\n".format(t, illuminance[0])
				print string_to_write
				with open("experiment_data.txt", "a+") as file:
					file.write(string_to_write)				
			time.sleep(10)

	except KeyboardInterrupt:
		print "\nScript Interrupted"
		office_sensing.stop_sens_modules()


if __name__ == '__main__':
	addresses = [
	             ("192.168.50.162", 1234)  # Omega-AF65
	]
	
	light_calibration_const = [0.478023824068, 0.472723094776, 0.472723094776, 0.513906092956]
	office_sensing_modules = OfficeSensing(addresses, light_calibration_const)
	b = Bridge(PHUE_IP)
	b.connect()
	lights = b.lights
	bulb = lights[3]
	test_sensing_module_response(office_sensing_modules, bulb)
