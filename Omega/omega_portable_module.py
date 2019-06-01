"""
File name: omega_portable_module.py
Author: Yerbol Aussat
Python Version: 2.7

Logic for portable sensing modules.
"""

import socket
from tsl2561 import TSL2561
from threading import Thread
from threading import Lock

# Constants
MOTION_HISTORY_SIZE = 500
MOTION_HISTORY_UPDATE_FREQUENCY = 0.15
CALIBRATION_CONST = 0.449729180772
CONTROL_MODULE_ADDRESS = ('192.168.50.151', 1234)
DEFAULT_TARGET_ILLUMINANCE = 200


# Start server to communicate with the control module (RPi).
def start_responder():
	global target_illuminance
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.connect(CONTROL_MODULE_ADDRESS)

	# When connection is established, send light calibration constant to the control module:
	client.send(str(CALIBRATION_CONST))
	while True:
		data = client.recv(1024)
		if data == "disconnect":
			client.send("Goodbye")
			print "\n[*] Portable module disconnected"
			client.close()
			break
		elif data == "Read":
			visible_light_reading = tsl.read_value(TSL2561.Light.Visible)
			with lock:
				combined_string = '{} {}'.format(str(visible_light_reading), str(target_illuminance))
			client.send(combined_string)


if __name__ == '__main__':
	tsl = TSL2561()
	lock = Lock()
	target_illuminance = DEFAULT_TARGET_ILLUMINANCE

	thread = None
	while True:
		if not thread or not thread.is_alive():
			raw_input('\nPress "Enter" to connect to the smart lighting system.')
			print "* Recalibrating the system ... "
			thread = Thread(target=start_responder)
			thread.daemon = True
			thread.start()
		print "\n\n" + "-" * 30
		user_input = raw_input('Enter desired illuminance (lux) or "-1" to disconnect: ')
		if user_input.isdigit() or (user_input.startswith('-') and user_input[1:].isdigit()):
			with lock:
				target_illuminance = int(user_input)
		if target_illuminance == -1:
			" * Disconnecting ..."
			thread.join()
			target_illuminance = DEFAULT_TARGET_ILLUMINANCE
