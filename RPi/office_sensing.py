"""
File name: office_sensing.py
Author: Yerbol Aussat
Python Version: 2.7

OfficeSensing class abstacts away communication with all sensing modules in the smart lighting system.
"""

from sensing_module import SensingModule


class OfficeSensing:
	def __init__(self, addresses, light_calibration_const):
		try:
			self.sens_modules = []
			self.light_calibration_const = light_calibration_const
			for ip, port in addresses:
				module = SensingModule(ip, port)
				print "[*]", module.send_msg("Check connection")
				self.sens_modules.append(module)
			print "[*] Successfully connected to sensing modules"
		except:
			print "* Initialization error!"
			self.stop_sens_modules()
	
	# Interrupt connection with all sensing modules
	def stop_sens_modules(self):
		print "\nConnection with sensing modules is interrupted"
		for module in self.sens_modules:
			module.disconnect()

	# Add sensing module to the system
	def add_portable_module(self, module, calibr_const):
		self.sens_modules.append(module)
		self.light_calibration_const.append(calibr_const)

	# Add sensing module to the system
	def detach_portable_module(self, i):
		self.sens_modules[i].disconnect()
		del self.sens_modules[i]
		del self.light_calibration_const[i]

	# Get light and occupancy readings from sensing modules
	def get_sensor_readings(self):
		light_readings = []
		occupancy_readings = []
		for i, sens_module in enumerate(self.sens_modules):
			received_message = sens_module.send_msg("Read")
			light_readings.append(int(received_message.split()[0])*self.light_calibration_const[i])
			occupancy_readings.append(int(received_message.split()[1]))
		return light_readings, occupancy_readings
