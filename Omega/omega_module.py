"""
File name: omega_module.py
Author: Yerbol Aussat
Python Version: 2.7

Stationary "Per-desk" sensing module.

In the current implementation, all "per-desk" sensing modules should be started before running the main controller.

This process sends (light reading , occupancy reading) to the control module (RPi), whenever RPi requests it.

TODO: Send (light reading , occupancy reading, user lux preference) to the control module. This way target illuminance
on the sensor could be inferred at the control module based on the provided user lux preference and occupancy.
User lux preference could be inputted by a user (like in omega_portable_module.py).
"""

import time
import socket
import threading
from onionGpio import OnionGpio
from tsl2561 import TSL2561

# Constants
MOTION_HISTORY_SIZE = 500
MOTION_HISTORY_UPDATE_FREQUENCY = 0.15
DISCOUNT_FACTOR = 0.995  # discount factor for calculating the occupancy score


# Initialize light and PIR sensors.
def initialize_sensors():
	tsl = TSL2561()
	print "[*] Light sensor is initialized"
	pin = 1
	pir = OnionGpio(pin)
	pir_status = pir.setInputDirection()
	print "[*] PIR sensor is initialized: ", pir_status
	return tsl, pir


# Thread that keeps updating motion history queue. The updating frequency is specified in
# the MOTION_HISTORY_UPDATE_FREQUENCY constant.
def update_motion_history():
	global motion_history
	while True:
		# Read from PIR sensor
		try:
			occupancy_reading = int(pir.getValue())
			# Update motion history:
			with lock:
				if len(motion_history) >= MOTION_HISTORY_SIZE:
					motion_history.pop()
				motion_history.insert(0, occupancy_reading)
		except Exception, e:
			print "Error Message:\n", str(e)
			continue
		time.sleep(MOTION_HISTORY_UPDATE_FREQUENCY)


# Get occupancy score from the motion history queue.
# Occupancy score is a discounted sum of motion values (which are 1 or 0).
def get_occup_score(motion_values):
	score = 0
	alpha = DISCOUNT_FACTOR
	for i, motion in enumerate(motion_values):
		score += motion * alpha**i
	return score	


# Get occupancy status:
#   1 - occupied
#   0 - not occupied
def get_occupancy_status():		
	global motion_history
	with lock:		
		occup_score = get_occup_score(motion_history)
		print "MOTION HISTORY: {}".format(motion_history)
		print "\nOCCUPANCY SCORE: {}\n".format(occup_score)

		if len(motion_history) >= MOTION_HISTORY_SIZE and occup_score >= 0.8:
			return 1
		elif len(motion_history) < MOTION_HISTORY_SIZE and occup_score >= 0.8:
			return 1
		else:
			return 0


# Start socket server to communicate with the control module (RPi).
def start_responder():
	# Create a TCP socket object
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPV-4 address, TCP$
	server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allows to reuse the address (ip and port)
	machine_name = socket.gethostname()  # name of host computer
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	ip = s.getsockname()[0]
	s.close()
	print "IP address of the Onion machine {}: {}".format(machine_name, ip)
	port = 1234
	address = (ip, port)
	server.bind(address)
	
	# Receive an incoming connection from a client
	server.listen(1)
	print "[*] Started listening on", ip, ":", port
	client, addr = server.accept()
	print "[*] Got a connection from", addr[0], ":", addr[1]

	# Responder's logic:
	while True:
		# Receive data from client
		data = client.recv(1024)
		
		print "\n[*] Received '", data, "' from the client"
		if data == "Check connection":
			client.send(str(machine_name) + " is Initialized")
			print "    Processing done.\n[*] Reply sent"
		elif data in ["disconnect", ""]:
			client.send("Goodbye")
			print "[*] Client disconnected"
			client.close()
			server.close()
			print "[*] Restarting the server"
			start_responder()
			break
		elif data == "Read":
			visible_light_reading = tsl.read_value(TSL2561.Light.Visible)
			occupancy_reading = get_occupancy_status()
			combined_string = '{} {}'.format(str(visible_light_reading), str(occupancy_reading))
			client.send(combined_string)
			print "    Light:", visible_light_reading
			print "    Occupancy:", occupancy_reading
			print "[*] Sensor readings sent to the client"


if __name__ == '__main__':
	tsl, pir = initialize_sensors()
	motion_history = []
	lock = threading.Lock()

	thread = threading.Thread(target=update_motion_history)
	thread.daemon = True
	thread.start()
	start_responder()
