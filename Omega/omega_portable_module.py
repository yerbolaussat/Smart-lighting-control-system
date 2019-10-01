"""
File name: omega_portable_module.py
Author: Yerbol Aussat
Python Version: 2.7

Portable sensing modules can connect to the smart lighting system when the main controller is running. They only have
light sensors (it is assumed that when they are connected to the system, the area is occupied).

This process sends (light sensor reading, user lux preference) to the control module (RPi), whenever RPi requests it.

A user can input user lux preference on the portable sensing module's light sensor.

Note:
 - IP address (and port number) of the control module should be specified in the CONTROL_MODULE_ADDRESS.
 - Each light sensor has its own calibration constant, which should be specified in CALIBRATION_CONST.

TODO: Send (light reading , occupancy reading, user lux preference) to the control module. This way target illuminance
on the sensor could be inferred at the control module based on the provided user lux preference and occupancy.
For portable sensing modules, occupancy reading would always be 1.
"""

import socket
from tsl2561 import TSL2561
from threading import Thread
from threading import Lock

# Constants
CALIBRATION_CONST = 0.449729180772
# CONTROL_MODULE_ADDRESS = ('192.168.50.151', 1234)  # Macbook
CONTROL_MODULE_ADDRESS = ('192.168.0.2', 1234)  # RPi
DEFAULT_USER_LUX_PREFERENCE = 200


# Start a socket server to communicate with the control module (RPi).
def start_responder():
	global user_lux_preference
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.connect(CONTROL_MODULE_ADDRESS)

	# When connection is established, send light calibration constant to the control module:
	client.send(str(CALIBRATION_CONST))
	while True:
		data = client.recv(1024)
		if data in ["disconnect", ""]:
			client.send("Goodbye")
			print "\n[*] Portable module disconnected"
			client.close()
			break
		elif data == "Read":
			visible_light_reading = tsl.read_value(TSL2561.Light.Visible)
			with lock:
				combined_string = '{} {}'.format(str(visible_light_reading), str(user_lux_preference))
			client.send(combined_string)


if __name__ == '__main__':
	tsl = TSL2561()
	lock = Lock()
	user_lux_preference = DEFAULT_USER_LUX_PREFERENCE

	ip = raw_input('\nEnter IP address of the lighting system. \n(Press "Enter" to use default address)')
	if ip:
		CONTROL_MODULE_ADDRESS = (ip, 1234)

	thread = None
	while True:
		if not thread or not thread.is_alive():
			raw_input('\nPress "Enter" to connect to the smart lighting system.')
			print "* Recalibrating the system to integrate this module... "
			thread = Thread(target=start_responder)
			thread.daemon = True
			thread.start()
		print "\n\n" + "-" * 30
		user_input = raw_input('Enter desired illuminance (lux) or "-1" to disconnect: ')
		if user_input.isdigit() or (user_input.startswith('-') and user_input[1:].isdigit()):
			with lock:
				user_lux_preference = int(user_input)
		if user_lux_preference == -1:
			" * Disconnecting ..."
			thread.join()
			user_lux_preference = DEFAULT_USER_LUX_PREFERENCE
