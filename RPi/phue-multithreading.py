"""
	File name: office_sensing.py
	Author: Yerbol Aussat
	Date created: 7/25/2018
	Python Version: 2.7
	
	This file contains CeilingActuatuion class that abstacts away actuation of LED bulbs
"""

import time
import traceback
from datetime import datetime as dt
from phue import Bridge
import threading

phue_bridge_ip_address = '192.168.0.3'
bridge = Bridge(phue_bridge_ip_address)
bridge.connect()
lights = bridge.lights
print "Successfully connected to Philips Hue Bridge"

# Convert dimming level to control value
def __dim_to_contr__(d): 
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

def set_bulb(i, dim):
	try:
		if dim <= 0.01:
			lights[i].on = False
		elif dim > 1:
			lights[i].on = True
			lights[i].brightness = int(round(__dim_to_contr__(1)))
		else:
			lights[i].on = True
			lights[i].brightness = int(round(__dim_to_contr__(dim)))
	except Exception, e:
		print "\n ERROR: Bulb {}".format(i)
		print str(e), '\n'
	
	

desired_dimming = [0.9] * 8
print "\n\nPARALLEL CODE TEST:"

thread_list = []
st_t = dt.now()
print "BEFORE: ", st_t.hour, ":", st_t.minute, ":", st_t.second, ":", st_t.microsecond

for i, dim in enumerate(desired_dimming):
	thread = threading.Thread(target = set_bulb, args =(i, dim))
	thread_list.append(thread)
	thread.start()

for thread in thread_list:
	thread.join()

t = dt.now()
print "AFTER: ", t.hour, ":", t.minute, ":", t.second, ":", t.microsecond
print t.second - st_t.second, t.microsecond - st_t.microsecond

	

	
desired_dimming = [0.5] * 8
print "LINEAR CODE TEST:"
st_t = dt.now()
print "BEFORE: ", st_t.hour, ":", st_t.minute, ":", st_t.second, ":", st_t.microsecond
for i, dim in enumerate(desired_dimming):
	try:
		if dim <= 0.01:
			lights[i].on = False
		elif dim > 1:
			lights[i].on = True
			lights[i].brightness = int(round(__dim_to_contr__(1)))
		else:
			lights[i].on = True
			lights[i].brightness = int(round(__dim_to_contr__(dim)))
	except Exception, e:
		print "\n ERROR: Bulb {}".format(i)
		print str(e), '\n'
t = dt.now()
print "AFTER: ", t.hour, ":", t.minute, ":", t.second, ":", t.microsecond
print t.second - st_t.second, t.microsecond - st_t.microsecond