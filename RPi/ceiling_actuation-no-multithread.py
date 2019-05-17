"""
	File name: office_sensing.py
	Author: Yerbol Aussat
	Date created: 7/25/2018
	Python Version: 2.7
	
	This file contains CeilingActuatuion class that abstacts away actuation of LED bulbs
"""

import time
import traceback
from phue import Bridge
from pandas import DataFrame
from datetime import datetime as dt


class CeilingActuation:
	
	def __init__(self, phue_bridge_ip_address):
		bridge = Bridge(phue_bridge_ip_address)
		bridge.connect()
		self.lights = bridge.lights
		self.bulbs_dict = {0:(0,0), 1:(0, 2), 2:(2,0), 3:(2,2), 4:(0,1), 5:(2,1), 6:(1,2), 7:(1,0)}
		print "Successfully connected to Philips Hue Bridge"

	# Convert dimming level to control value
	def __dim_to_contr__(self, d): 
		'''
		@param d: dimming level
		@returns: corresponding control value
		'''
		a_dim = 1.74069750372e-05
		m_dim = 1.97866862723
		b_dim = 0.00279331968066
		if d == -1:
			return -1
		elif d <= b_dim:
			return 0
		elif d > 1:
			return 255
		contr = ((d-b_dim) / a_dim) ** (1.0/m_dim)
		return contr
		
	# Set dimming levels on all bulbs
	def set_dimming(self, desired_dimming, wait_time = 0):
		'''
		@param desired_dimming is a vector of length 8 containing desired dimming levels that the system needs to set on bulbs
		@param wait_time is the amount of time the system waits for bulbs to be dimmed
		'''
		if len(desired_dimming) != 8:
			raise ValueError('Length of dimming vector is {}, but should be 8!'.format(len(self.dim_levels)))
		
		t = dt.now()
		print "Right before setting dimming values.  ", t.hour, ":", t.minute, ":", t.second, ":", t.microsecond
		
		dim_levels = [None for _ in range(len(desired_dimming))]
		for i, dim in enumerate(desired_dimming):
			try:
				if dim <= 0.01:
					dim_levels[i] = 0.0
					self.lights[i].on = False
				elif dim > 1:
					dim_levels[i] = 1.0
					self.lights[i].on = True
					self.lights[i].brightness = int(round(self.__dim_to_contr__(1)))
				else:
					dim_levels[i] = dim
					self.lights[i].on = True
					self.lights[i].brightness = int(round(self.__dim_to_contr__(dim)))
			
			except Exception, e:
				print "\n ERROR: Bulb {}".format(i)
				print str(e), '\n'

		t = dt.now()
		print "New dimming values set.  ", t.hour, ":", t.minute, ":", t.second, ":", t.microsecond
		 
		# Update dimming levels file
		dim_levels_str = ' '.join([str(val) for val in dim_levels])
		f_dim = open('cur_dim_level.txt', 'w+')
		f_dim.write(dim_levels_str)	
		f_dim.close()		
		time.sleep(wait_time)

				
	# Change dimming on a bulb
	def change_dim_on_bulb(self, bulb_id, delta_dim, wait_time = 0):
		'''
		@param bulb_id: id of bulb whose dimming needs to be changed
		@param delta_dim: value in [-1.0, 1.0] that corresponds to change in dimming
		@param wait_time is the amount of time the system waits for bulbs to be dimmed
		'''
		
		try:		
			# If cur_dim_level file already exists, read current dimming levels on bulbs
			f_dim = open('cur_dim_level.txt', 'r')
			dim_levels_str = f_dim.read()
			f_dim.close()
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
				self.lights[bulb_id].brightness = int(round(self.__dim_to_contr__(1)))
				target_dim = 1.0
			else:
				self.lights[bulb_id].on = True
				self.lights[bulb_id].brightness = int(round(self.__dim_to_contr__(target_dim)))
	
			# Write updated dimming level values to a file
			dim_levels[bulb_id] = target_dim
			dim_levels_str = ' '.join([str(val) for val in dim_levels])
			f_dim = open('cur_dim_level.txt', 'w+')
			f_dim.write(dim_levels_str)	
			f_dim.close()		
			time.sleep(wait_time)
		except IOError:
			print "Dimming levels file is not found"
			
		
	# Print dimming level vector	
	def print_dim_levels(self, name =  "Bulb dimming level map"):
		try:
			f_dim = open('cur_dim_level.txt', 'r')
			dim_levels_str = f_dim.read()
			f_dim.close()
			dim_levels = [float(val) for val in dim_levels_str.split()]
		
			out_map = [['x' for _ in range(3)] for _ in range(3)]

			for bulb_i, dim in enumerate(dim_levels):
				x, y = self.bulbs_dict[bulb_i]
				out_map[x][y] = dim
			print "-"*40
			print name+":\n",  DataFrame(out_map), '\n'
			print "-"*40
		except IOError:
			print "Dimming levels file is not found"

	# Get current dimming levels on bulbs	
	def get_dim_levels(self):
		try:
			f_dim = open('cur_dim_level.txt', 'r')
			dim_levels_str = f_dim.read()
			f_dim.close()
			dim_levels = [float(val) for val in dim_levels_str.split()]
			return dim_levels
		except IOError:
			print "Dimming levels file is not found"