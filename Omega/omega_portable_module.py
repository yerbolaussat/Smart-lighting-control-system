"""
File name: omega_responder.py
Author: Yerbol Aussat
Python Version: 2.7

Process that sends sensor readings (light and occupancy) to the control module (RPi),
whenever it requests them.
"""

import socket
from tsl2561 import TSL2561

# from threading import Thread
# from threading import Lock

from multiprocessing import Process
from multiprocessing import Lock
from multiprocessing import Value

# Constants
MOTION_HISTORY_SIZE = 500
MOTION_HISTORY_UPDATE_FREQUENCY = 0.15
CALIBRATION_CONST = 0.449729180772
CONTROL_MODULE_ADDRESS = ('192.168.50.151', 1234)


# Initialize light and PIR sensors
def initialize_sensors():
	tsl = TSL2561()
	print "[*] Light sensor is initialized"
	return tsl


# Start server to communicate with the control module (RPi).
def start_responder():
	raw_input('\nPress "Enter" to connect to the smart lighting system.')
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.connect(CONTROL_MODULE_ADDRESS)
	# When connection is established, send light calibration constant
	# to the control module:
	client.send(str(CALIBRATION_CONST))

	# Responder's logic:
	global target_illuminance
	while True:
		# Receive data from client
		data = client.recv(1024)

		if data == "disconnect":
			client.send("Goodbye")
			print "[*] Portable module disconnected"
			client.close()
			start_responder()
			break
		elif data == "Read":
			visible_light_reading = tsl.read_value(TSL2561.Light.Visible)
			with lock:
				combined_string = '{} {}'.format(str(visible_light_reading), str(target_illuminance))
			client.send(combined_string)
			# print "    Calibrated Light Value:", visible_light_reading * CALIBRATION_CONST
			# print "    Target illuminance:", target_illuminance
			# print "[*] Sensor readings sent to the client"


def set_target_illuminance():
	global target_illuminance
	while True:
		print "-" * 30
		user_input = raw_input('\n * Enter desired illuminance.'
		                  '\n * Enter "-1" to disconnect.'
		                  '\n * Enter "-2" to recalibrate.\n')
		with lock:
			if user_input.isdigit() or \
					(user_input.startswith('-') and user_input[1:].isdigit()):
				target_illuminance = int(user_input)

if __name__ == '__main__':
	tsl = initialize_sensors()
	lock = Lock()
	target_illuminance = 200
	thread = Process(target=set_target_illuminance)
	thread.daemon = True
	thread.start()
	while True:
		start_responder()

	# while True:
	# 	input_text = raw_input("\nEnter desired illuminance: ")
	# 	with lock:
	# 		target_illuminance = int(input_text)
