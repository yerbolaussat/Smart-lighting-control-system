"""
File name: office_sensing.py
Author: Yerbol Aussat
Python Version: 2.7

CeilingActuatuion class abstacts away actuation of LED bulbs
"""

import time
from phue import Bridge
from pandas import DataFrame
from datetime import datetime as dt
from threading import Thread
from threading import Lock


class CeilingActuation:
	# Constants
	BULB_DICT = {0: (0, 0), 1: (0, 2), 2: (2, 0), 3: (2, 2), 4: (0, 1), 5: (2, 1), 6: (1, 2), 7: (1, 0)}
	DIM_LEVEL_FILE_NAME = 'cur_dim_level.txt'

	# Dimming level -> control value conversion constants
	A_DIM = 1.74069750372e-05
	M_DIM = 1.97866862723
	B_DIM = 0.00279331968066

	def __init__(self, phue_bridge_ip_address):
		bridge = Bridge(phue_bridge_ip_address)
		bridge.connect()
		self.lights = bridge.lights
		print "Successfully connected to Philips Hue Bridge"
		self.lock = Lock()

	# Convert dimming level to control value
	def __dim_to_contr(self, d):
		if d == -1:
			return -1
		elif d <= self.B_DIM:
			return 0
		elif d > 1:
			return 255
		control_val = ((d-self.B_DIM) / self.A_DIM) ** (1.0 / self.M_DIM)
		return control_val
	
	# Set dimming level dim_val on a bulb i
	def set_bulb(self, i, dim_val, dim_levels):
		try:
			if dim_val <= 0.01:
				with self.lock:
					dim_levels[i] = 0.0
				self.lights[i].on = False
			elif dim_val > 1:
				with self.lock:
					dim_levels[i] = 1.0
				self.lights[i].on = True
				self.lights[i].brightness = int(round(self.__dim_to_contr(1)))
			else:
				with self.lock:
					dim_levels[i] = dim_val
				self.lights[i].on = True
				self.lights[i].brightness = int(round(self.__dim_to_contr(dim_val)))
		except Exception, e:
			print "\n ERROR: Bulb {}".format(i)
			print str(e), '\n'

	# Set dimming levels on all bulbs cuncurrently (using multithreading)
	def set_dimming(self, desired_dimming, wait_time=0.0):
		if len(desired_dimming) != 8:
			raise ValueError('Error: Length of dimming vector should be 8!')

		print "{:<35} {:<25}".format("Setting dimming values...", dt.now().strftime("%H:%M:%S.%f"))

		dim_levels = [None for _ in range(len(desired_dimming))]
		thread_list = []
		for i, dim_val in enumerate(desired_dimming):
			thread = Thread(target=self.set_bulb, args=(i, dim_val, dim_levels))
			thread_list.append(thread)
			thread.start()
		for thread in thread_list:
			thread.join()

		print "{:<35} {:<25}".format("New dimming values set.", dt.now().strftime("%H:%M:%S.%f"))
		# Update dimming levels file
		dim_levels_str = ' '.join([str(val) for val in dim_levels])
		with open(self.DIM_LEVEL_FILE_NAME, 'w+') as f_dim:
			f_dim.write(dim_levels_str)
		time.sleep(wait_time)
				
	# Change dimming on a bulb
	# @param bulb_id: id of bulb whose dimming needs to be changed
	# @param delta_dim: value in [-1.0, 1.0] that corresponds to change in dimming
	# @param wait_time is the amount of time the system waits for bulbs to be dimmed
	def change_dim_on_bulb(self, bulb_id, delta_dim, wait_time=0):
		try:		
			# If cur_dim_level file already exists, read current dimming levels on bulbs
			with open(self.DIM_LEVEL_FILE_NAME, 'r') as f_dim:
				dim_levels_str = f_dim.read()
			dim_levels = [float(val) for val in dim_levels_str.split()]
			cur_dim = dim_levels[bulb_id]
			target_dim = cur_dim + delta_dim
			print " * Target dimming on bulb {} is set to {}.".format(bulb_id, target_dim)
			if target_dim <= 0.01:
				target_dim = 0.0
				self.lights[bulb_id].on = False
			elif target_dim > 1:
				print "Target dimming on bulb {} is out of range.".format(bulb_id)
				self.lights[bulb_id].on = True
				self.lights[bulb_id].brightness = int(round(self.__dim_to_contr(1)))
				target_dim = 1.0
			else:
				self.lights[bulb_id].on = True
				self.lights[bulb_id].brightness = int(round(self.__dim_to_contr(target_dim)))
	
			# Write updated dimming level values to a file
			dim_levels[bulb_id] = target_dim
			dim_levels_str = ' '.join([str(val) for val in dim_levels])
			with open(self.DIM_LEVEL_FILE_NAME, 'w+') as f_dim:
				f_dim.write(dim_levels_str)
			time.sleep(wait_time)
		except IOError:
			print "Dimming levels file is not found"

	# Print dimming level vector
	def print_dim_levels(self, name="Bulb dimming level map"):
		try:
			with open(self.DIM_LEVEL_FILE_NAME, 'r') as f_dim:
				dim_levels_str = f_dim.read()
			dim_levels = [float(val) for val in dim_levels_str.split()]
		
			out_map = [['x' for _ in range(3)] for _ in range(3)]

			for bulb_i, dim in enumerate(dim_levels):
				x, y = self.BULB_DICT[bulb_i]
				out_map[x][y] = dim
			print "-"*40
			print name+":\n",  DataFrame(out_map), '\n'
			print "-"*40
		except IOError:
			print "Dimming levels file is not found"

	# Get current dimming levels on bulbs	
	def get_dim_levels(self):
		try:
			with open(self.DIM_LEVEL_FILE_NAME, 'r') as f_dim:
				dim_levels_str = f_dim.read()
			dim_levels = [float(val) for val in dim_levels_str.split()]
			return dim_levels
		except IOError:
			print "Dimming levels file is not found"
