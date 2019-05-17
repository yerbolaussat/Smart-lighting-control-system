"""
	File name: office_sensing.py
	Author: Yerbol Aussat
	Date created: 7/25/2018
	Python Version: 2.7
	
	This file contains OfficeSensing class that abstacts away communication with sensing modules
"""

from sensing_module import SensingModule

class OfficeSensing:
	def __init__(self, addresses, light_calibration_const):
		try:
			self.sens_modules = []
			self.light_calibration_const = light_calibration_const
			for ip, port in addresses:
				module = SensingModule(ip, port)
				print "   [*]", module.send_msg("Check connection")
				self.sens_modules.append(module)
			print "   [*] Successfully connected to sensing modules"
		except:
			print "* Initialization error!"
			self.stop_sens_modules()	
	
	# Terminate connection with sensing modules
	def stop_sens_modules(self):
		print "\nConnection with sensing modules is interrupted"
		for module in self.sens_modules:
			module.disconnect()
			
	# Get light and occupancy readings from sensing modules
	def get_sensor_readings(self):
		light_readings = []
		occupancy_readings = []
		for i, module in enumerate(self.sens_modules):
			received_message = module.send_msg("Read")			
			light_readings.append(int(received_message.split()[0])*self.light_calibration_const[i]) # Note: light values are stored as float
			occupancy_readings.append(int(received_message.split()[1]))
		return light_readings, occupancy_readings
	

	# Visualize illuminance on each sensor
	def print_illuminance(self):
		light, _ = self.get_sensor_readings()
		print "\nIlluminance readings from light sensors:"
		print " ", "-"*15
		print "  |     LIGHT   |"
		print " ", "-"*15
		print "  | ", int(round(light[1])), " | ", int(round(light[3])), " |"
		print " ", "-"*15
		print "  | ", int(round(light[0])), " | ", int(round(light[2])), " |"
		print " ", "-"*15

