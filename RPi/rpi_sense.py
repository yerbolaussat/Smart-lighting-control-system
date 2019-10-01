"""
File name: rpi_sense.py
Author: Yerbol Aussat
Python Version: 2.7

Monitors changes in occupancy and illuminance in the office, and updates corresponding files every 0.1 seconds.
Restarts optimization process whenever office occupancy changes.
"""

import time
import os
import numpy as np
from datetime import datetime as dt
import subprocess
from threading import Thread
import socket
from multiprocessing.connection import Client
import traceback
from office_sensing import OfficeSensing
import rpi_calibrate as calibrator
from portable_sensing_module import PortableSensingModule


# Constants
OPTIMIZE_COMMAND = "Optimize"
PAUSE_OPTIMIZATION_COMMAND = "Pause"
CLOSE_CONNECTION_COMMAND = "Close"
ILLUMINANCE_FILE_NAME = "cur_illum.txt"
OCCUPANCY_FILE_NAME = "cur_occup.txt"
SENS_MODULE_CONFIG_FILE_NAME = 'sensing_module_list.txt'
ILLUM_GAIN_MTX_FILE_NAME = 'illum_gain.npy'
ENV_GAIN_FILE_NAME = 'env_gain.npy'


# Get sensor values and trigger optimization process
def sense_and_optimize(office_sensing):
	# Start optimizer process and connect to it
	subprocess.call('python2 rpi_optimize.py &', shell=True)
	address_optimizer = ('localhost', 6000)
	conn = Client(address_optimizer, authkey='secret password')
	print "[*] Sensing process connected to optimizer"

	t1 = time.time()	
	try: 
		while True:

			if len(portable_sensing_modules) > 0:
				conn.send(PAUSE_OPTIMIZATION_COMMAND)
				while portable_sensing_modules:
					module, calibr_const = portable_sensing_modules.pop()
					office_sensing.add_portable_module(module, calibr_const)
				print "[*] New sensing module detected. Starting recalibration."
				calibrator.calibrate(office_sensing_modules, step=0.1, B=0.65, wait_time=0.9)

			# Get sensor readings
			illuminance, occupancy = office_sensing.get_sensor_readings()
			cur_illum_str = " ".join([str(illum_val) for illum_val in illuminance])
			cur_occup_str = " ".join([str(occup_val) for occup_val in occupancy])

			# Print illuminance and occupancy values every 3 seconds
			t2 = time.time()
			if t2-t1 > 3:
				print "\n\n", "*" * 50
				print dt.now().strftime("%H:%M:%S.%f")
				print_illuminance(illuminance, occupancy)
				print_occupancy(occupancy)
				t1 = t2
				
			# Update illuminance file:
			with open(ILLUMINANCE_FILE_NAME, 'w+') as f_illum:
				f_illum.write(cur_illum_str)

			# Update occupancy file
			if os.path.isfile('./{}'.format(OCCUPANCY_FILE_NAME)):
				# If occupancy file already exists, compare current occupancy with the previous one
				with open(OCCUPANCY_FILE_NAME, 'r') as f_occup:
					prev_occup_str = f_occup.read()
				if prev_occup_str != cur_occup_str:
					with open(OCCUPANCY_FILE_NAME, 'w+') as f_occup:
						f_occup.write(cur_occup_str)

					cur_occup = cur_occup_str.split(" ")
					prev_occup = prev_occup_str.split(" ")

					# Check if a portable module should be disconnected
					i = 4
					while i < len(cur_occup):
						if cur_occup[i] == '-1':
							break
						i += 1

					if i < len(cur_occup):
						print "\n\n", "*" * 50
						print "[*] Disconnecting portable module {} ...".format(i)
						conn.send(PAUSE_OPTIMIZATION_COMMAND)
						office_sensing.detach_portable_module(i)
						A = np.load(ILLUM_GAIN_MTX_FILE_NAME)
						A = np.delete(A, i, 0)
						np.save(ILLUM_GAIN_MTX_FILE_NAME, A)
						E = np.load(ENV_GAIN_FILE_NAME)
						E = np.delete(E, i)
						np.save(ENV_GAIN_FILE_NAME, E)
						continue

					if len(cur_occup) == len(prev_occup):
						if cur_occup[:4] == prev_occup[:4]:
							print "\n", "#" * 50, "\n", "#" * 50
							print "\nTARGET ILLUMINANCE ON PORTABLE SENSING MODULES CHANGED.\n\n{} ==> {}\n\n" \
							      "RESTART OPTIMIZER.\n".format(prev_occup[4:], cur_occup[4:])
							print dt.now().strftime("%H:%M:%S.%f"), "\n"
							print "#" * 50, "\n", "#" * 50, "\n"
						else:
							print "\n", "#" * 50, "\n", "#" * 50
							print "\nOCCUPANCY CHANGES: RESTART OPTIMIZER\n"
							print dt.now().strftime("%H:%M:%S.%f"), "\n"
							print_occupancy(occupancy)
							print "#" * 50, "\n", "#" * 50, "\n"
					conn.send(OPTIMIZE_COMMAND)  # Restart the optimizer
				else:
					time.sleep(0.1)
			else:
				# If occupancy file does not exist, create it, and start optimization process
				print "CREATE {} file".format(OCCUPANCY_FILE_NAME)
				with open(OCCUPANCY_FILE_NAME, 'w+') as f_occup:
					f_occup.write(cur_occup_str)
				conn.send(OPTIMIZE_COMMAND)

	except KeyboardInterrupt:
		print "\nScript Interrupted"
		office_sensing.stop_sens_modules()
		conn.send(CLOSE_CONNECTION_COMMAND)  # Close connection with optimizer
		conn.close()
		subprocess.call('rm {}'.format(OCCUPANCY_FILE_NAME), shell=True)

	except Exception, e:  # Stop sensing modules if there is an exception
		office_sensing.stop_sens_modules()
		print "Exception:\n", str(e)
		traceback.print_exc()
		conn.send(CLOSE_CONNECTION_COMMAND)  # Close connection with optimizer
		conn.close()
		subprocess.call('rm {}'.format(OCCUPANCY_FILE_NAME), shell=True)


# Print illuminance values on each sensor
def print_illuminance(illuminance, occupancy):
	print "\nIlluminance readings from light sensors:"
	print " ", "-"*13
	print "  |   LIGHT   |"
	print " ", "-"*13
	print "  | {:<3} | {:<3} |".format(int(round(illuminance[1])), int(round(illuminance[3])))
	print " ", "-"*13
	print "  | {:<3} | {:<3} |".format(int(round(illuminance[0])), int(round(illuminance[2])))
	print " ", "-"*13

	if len(illuminance) > 4:
		print "\nIlluminance readings on portable sensing modules:"
		for i in range(4, len(illuminance)):
			print "     -------"
			print "     | {:<3} | -> Target {}".format(int(round(illuminance[i])), occupancy[i])
			print "     -------"


# Print occupancy values on each sensor
def print_occupancy(occupancy):
	print "\nOccupancy matrix:"
	print "  ", "_"*11
	print "  ", "| {:<1}  |  {:<1} |".format(occupancy[1], occupancy[3])
	print "  ", "_"*11
	print "  ", "| {:<1}  |  {:<1} |".format(occupancy[0], occupancy[2])
	print "  ", "_"*11
	print "\n"


# Get configs for sensing modules
def get_sens_module_config():
	address_list = []
	light_calibration = []
	with open(SENS_MODULE_CONFIG_FILE_NAME) as f:
		line = f.readline()
		while line:
			ip, port, calibr_const = line.split(',')
			address_list.append((ip, int(port)))
			light_calibration.append(float(calibr_const))
			line = f.readline()
	return address_list, light_calibration


def listen_for_connection(portable_modules):
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	ip = s.getsockname()[0]
	s.close()
	port = 1234

	address = (ip, port)
	server.bind(address)
	server.listen(5)
	print "Listening for connection requests at {}".format(address)
	while True:
		client, addr = server.accept()
		print "\n\n", "*" * 50
		print "[*] Got connection request from", addr[0], ":", addr[1]
		module = PortableSensingModule(client)
		calibr_const = float(client.recv(1024))
		portable_modules.append((module, calibr_const))


if __name__ == '__main__':
	addresses, light_calibration_const = get_sens_module_config()
	office_sensing_modules = OfficeSensing(addresses, light_calibration_const)
	calibrator.calibrate(office_sensing_modules, initial_calibration=True)
	portable_sensing_modules = []

	thread = Thread(target=listen_for_connection, args=(portable_sensing_modules, ))
	thread.daemon = True
	thread.start()

	sense_and_optimize(office_sensing_modules)
