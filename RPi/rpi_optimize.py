"""
	File name: rpi_optimize.py
	Author: Yerbol Aussat
	Date created: 7/25/2018
	Python Version: 2.7
	
	Process that calculates optimal dimming levels of Phue bulbs, given occupancy and lighting values
"""

from datetime import datetime as dt
t = dt.now()
print "Optimization process started.  ", t.hour, ":", t.minute, ":", t.second, ":", t.microsecond	

import time
t = dt.now()
print "Time imported.  ", t.hour, ":", t.minute, ":", t.second, ":", t.microsecond	

import numpy as np
t = dt.now()
print "Numpy imported.  ", t.hour, ":", t.minute, ":", t.second, ":", t.microsecond	

import traceback
t = dt.now()
print "Traceback imported.  ", t.hour, ":", t.minute, ":", t.second, ":", t.microsecond	

from scipy.optimize import linprog
t = dt.now()
print "Scipy imported.  ", t.hour, ":", t.minute, ":", t.second, ":", t.microsecond		

from ceiling_actuation import CeilingActuation
t = dt.now()
print "Ceiling Actuation module imported.  ", t.hour, ":", t.minute, ":", t.second, ":", t.microsecond	

from multiprocessing.connection import Listener
import multiprocessing

# Get target illuminance based on occupancy
def get_target_illum():	
	try:
		f_occup = open('cur_occup.txt', 'r')
		occupancy_vals_str = f_occup.read()
		f_occup.close()
		occupancy_vals = [int(val) for val in occupancy_vals_str.split()]
		return np.array([200 if occupancy_vals[i] == 1 else 0 for i in range(len(occupancy_vals))])
	except IOError:
		print "Occupancy file is not found"

# Set optimal dimming value that would satisfy target illuminance
# Updates cur_dim_level file via actuators
def set_optimal_dimming(actuators, target_illum, wait_time = 1):
	# Take negative of values so we can represent constraints as required by scipy.optimize.linprog
	A = np.load('illum_gain.npy')
	A = np.negative(A) 
	E = np.load('env_gain.npy')
	t = dt.now()
	print "\nI/O operations finished.  ", t.hour, ":", t.minute, ":", t.second, ":", t.microsecond	
	
	# Coefficients of "power vs dimming" best fit line
	a_pow = 3.86706205178
	b_pow = 1.04678541344
	
	# Power consumed by bulb i: Power_i = a_pow * dim_i + b_pow
	# Coefficients of variable that is being optimized
	c = [a_pow] * 8
	
	# Target for each sensor
	# Offsetting target by environmental contribution (Again, to get the form required by scipy.optimize.linprog)
	target_no_env = [target_illum[i] - E[i] for i in range(len(E))]
	target_no_env = np.negative(target_no_env)

	bound = (0.0, 1.0) # When the bulb is on
	bnds = [bound for _ in range(8)]
	
# 	start_time = time.time()
	res = linprog(c, A_ub=A, b_ub=target_no_env, bounds=bnds, method = 'simplex', options={"disp": False})
# 	print "Optimization time is {} sec.".format(time.time()-start_time)
	t = dt.now()
	print "Optimization finished.  ", t.hour, ":", t.minute, ":", t.second, ":", t.microsecond	
	
	
	if res.success: 
# 		print "OPTIMIZATION SUCCESSFUL!!!"
		d_opt = res.x
		d_opt = d_opt.tolist()
		actuators.set_dimming(d_opt, wait_time)
		bulbs_on = 0
		for dim_val in d_opt:
			if dim_val > 0.0001:
				bulbs_on+=1
		power = res.fun + bulbs_on * b_pow
	else:
# 		print "OPTIMIZATION CONSTRAINTS CANNOT BE SATISFIED!!!"
		d_opt = np.ones((8,1))
		d_opt = d_opt.tolist()
		actuators.set_dimming(d_opt, wait_time)
		power = 8 * (3.86706205178+1.04678541344)
		
# 	print "Optimal power consumption:", "%.3f"%power, "W"


def optimizer(actuators):
	target_illum = get_target_illum()
	R_prev = np.array([0 for i in range(4)]) # Initialize R_prev
	while True:
		try:
			set_optimal_dimming(actuators, target_illum, 1.5)
			R = R_prev # Predefine R
			try:
				f_illum = open('cur_illum.txt', 'r')
				cur_illum_str = f_illum.read()
				f_illum.close()
				if len(cur_illum_str)!=0:
					R = [float(val) for val in cur_illum_str.split()]
					R = np.array(R)
			except IOError:
				print "Illuminance file is not found"
				break
			except Exception, e:
				print "\Illuminance file reading error\n"
				print "Error Message:\n", str(e)
				traceback.print_exc()
				break
			A = np.load('illum_gain.npy')
			d = actuators.get_dim_levels()
			E = R - A.dot(d)
			np.save('env_gain.npy', E)
			R_prev = R # Update R_prev
		
		except Exception, e: # Stop optimizer if there is an error
			print "\nOPTIMIZER FAILURE\n"
			print "Error Message:\n", str(e)
			traceback.print_exc()
			break

# Main optimization code:
t = dt.now()
print "Main script started.  ", t.hour, ":", t.minute, ":", t.second, ":", t.microsecond

phue_bridge_ip_address = '192.168.0.3'
actuators = CeilingActuation(phue_bridge_ip_address)
t = dt.now()
print "Setup finished.  ", t.hour, ":", t.minute, ":", t.second, ":", t.microsecond	

# Initialize Listener, to listen to commands from sensing process
sensing_address = ('localhost', 6000) 
listener = Listener(sensing_address, authkey='secret password')
conn = listener.accept()
print "[*] Optimizer accepted connection from sensing process"

optimizer_process = None
while True:
    msg = conn.recv()
    if msg == 'Optimize':
        if optimizer_process:
        	optimizer_process.terminate()
        optimizer_process = multiprocessing.Process(target = optimizer, args = (actuators, ))
        optimizer_process.daemon = True
        optimizer_process.start()
    elif msg == 'Close':
        conn.close()
        break