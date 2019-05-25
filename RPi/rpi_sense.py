"""
File name: rpi_sense.py
Author: Yerbol Aussat
Python Version: 2.7

Monitors changes in occupancy and illuminance in the office, and updates corresponding files every 0.1 seconds.
Restarts optimization process whenever office occupancy changes.
"""

import time
import os
from datetime import datetime as dt
import subprocess
from multiprocessing.connection import Client
import traceback
from office_sensing import OfficeSensing

# Constants
OPTIMIZE_COMMAND = "Optimize"
CLOSE_CONNECTION_COMMAND = "Close"
ILLUMINANCE_FILE_NAME = "cur_illum.txt"
OCCUPANCY_FILE_NAME = "cur_occup.txt"


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
			# Get sensor readings
			illuminance, occupancy = office_sensing.get_sensor_readings()
			cur_illum_str = " ".join([str(illum_val) for illum_val in illuminance])
			cur_occup_str = " ".join([str(occup_val) for occup_val in occupancy])

			# Print illuminance and occupancy values every 3 seconds
			t2 = time.time()
			if t2-t1 > 3:
				print "\n\n", "*" * 50
				print dt.now().strftime("%H:%M:%S.%f")

				print_illuminance(illuminance)
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
					conn.send(OPTIMIZE_COMMAND)  # Restart the optimizer
					print "\n", "#" * 50, "\n", "#" * 50
					print "\nOCCUPANCY CHANGES: START NEW OPTIMIZATION\n"
					print dt.now().strftime("%H:%M:%S.%f"), "\n"
					print_occupancy(occupancy)
					print "#" * 50, "\n", "#" * 50, "\n"
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
def print_illuminance(illuminance):
	print "\nIlluminance readings from light sensors:"
	print " ", "-"*13
	print "  |   LIGHT   |"
	print " ", "-"*13
	print "  | {:<3} | {:<3} |".format(int(round(illuminance[1])), int(round(illuminance[3])))
	print " ", "-"*13
	print "  | {:<3} | {:<3} |".format(int(round(illuminance[0])), int(round(illuminance[2])))
	print " ", "-"*13


# Print occupancy values on each sensor
def print_occupancy(occupancy):
	print "\n Occupancy matrix:"
	print "  ", "_"*11
	print "  ", "| {:<1}  |  {:<1} |".format(occupancy[1], occupancy[3])
	print "  ", "_"*11
	print "  ", "| {:<1}  |  {:<1} |".format(occupancy[0], occupancy[2])
	print "  ", "_"*11
	print "\n"


if __name__ == '__main__':
	addresses = [("192.168.50.188", 1234),  # Omega-F13D
	             ("192.168.50.179", 1234),  # Omega-F075
	             ("192.168.50.158", 1234),  # Omega-F11F
	             ("192.168.50.168", 1234)]  # Omega-F129
	light_calibration_const = [0.478023824068, 0.472723094776, 0.472723094776, 0.513906092956]
	office_sensing_modules = OfficeSensing(addresses, light_calibration_const)
	sense_and_optimize(office_sensing_modules)
