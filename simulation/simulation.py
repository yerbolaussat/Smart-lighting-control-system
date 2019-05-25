"""
File name: simulation.py
Author: Yerbol Aussat
Python Version: 2.7

Simulation
"""

from datetime import datetime as dt
import os
import numpy as np
import traceback
from scipy.optimize import linprog
from ceiling_actuation import CeilingActuation
from multiprocessing.connection import Listener
from multiprocessing import Process
from multiprocessing import Lock
from rpi_sense import OCCUPANCY_FILE_NAME
from rpi_sense import ILLUMINANCE_FILE_NAME

print "{:<35} {:<25}".format("Finished importing libraries.", dt.now().strftime("%H:%M:%S.%f"))

# Constants
# Coefficients of "power vs dimming" best fit line:
BEST_FIT_COEF_1 = 3.86706205178
BEST_FIT_COEF_2 = 1.04678541344

ILLUM_GAIN_MTX_FILE_NAME = 'illum_gain.npy'
ENV_GAIN_FILE_NAME = 'env_gain.npy'
PHUE_IP_ADDRESS = '192.168.0.3'
lock = Lock()


# Get target illuminance based on occupancy
def get_target_illum():	
	with open(OCCUPANCY_FILE_NAME, 'r') as f_occup:
		occupancy_vals_str = f_occup.read()
	occupancy_vals = [int(val) for val in occupancy_vals_str.split()]
	return np.array([200 if occupancy_vals[i] == 1 else 0 for i in range(len(occupancy_vals))])


# Set optimal dimming value that satisfies target illuminance.
# cur_dim_level file gets updated in actuators.set_dimming method.
def set_optimal_dimming(actuators, target_illum, wait_time=1.0):
	# Take negative of values so we can represent constraints as required by scipy.optimize.linprog
	if not os.path.isfile('./{}'.format(ILLUM_GAIN_MTX_FILE_NAME)) or \
			not os.path.isfile('./{}'.format(ENV_GAIN_FILE_NAME)):
		return
	A = np.load(ILLUM_GAIN_MTX_FILE_NAME)
	A = np.negative(A)
	try:
		E = np.load(ENV_GAIN_FILE_NAME)
	except IOError, e:
		log_error(str(e))
		return
	print "\n{:<35} {:<25}".format("I/O operations finished.", dt.now().strftime("%H:%M:%S.%f"))
	# Power consumed by bulb i: Power_i = a_pow * dim_i + b_pow
	# Coefficients of variable that is being optimized
	a_pow = BEST_FIT_COEF_1
	b_pow = BEST_FIT_COEF_2
	c = [a_pow] * 8
	
	# Target for each sensor
	# Offsetting target by environmental contribution (Again, to get the form required by scipy.optimize.linprog)
	target_no_env = [target_illum[i] - E[i] for i in range(len(E))]
	target_no_env = np.negative(target_no_env)

	# Solve optimization program
	bounds = [(0.0, 1.0) for _ in range(8)]
	res = linprog(c, A_ub=A, b_ub=target_no_env, bounds=bounds, method = 'simplex', options={"disp": False})
	print "{:<35} {:<25}".format("Optimization finished.", dt.now().strftime("%H:%M:%S.%f"))

	if res.success: 
		d_opt = res.x
		d_opt = d_opt.tolist()
		actuators.set_dimming(d_opt, wait_time)
		bulbs_on = 0
		for dim_val in d_opt:
			if dim_val > 0.0001:
				bulbs_on += 1
		power = res.fun + bulbs_on * b_pow
	else:
		d_opt = np.ones((8, 1))
		d_opt = d_opt.tolist()
		actuators.set_dimming(d_opt, wait_time)
		power = 8 * (a_pow+b_pow)
# 	print "Optimal power consumption:", "%.3f"%power, "W"


# Optimizer thread that sets optimal dimming levels based on current illuminance values.
def optimizer(actuators):
	target_illum = get_target_illum()
	A = np.load(ILLUM_GAIN_MTX_FILE_NAME)
	R = np.zeros(4)
	while True:
		try:
			set_optimal_dimming(actuators, target_illum, 1.5)
			if not os.path.isfile('./{}'.format(ILLUMINANCE_FILE_NAME)):
				print "Illuminance file is not found"
				break
			with open(ILLUMINANCE_FILE_NAME, 'r') as f_illum:
				cur_illum_str = f_illum.read()
			if len(cur_illum_str) != 0:
				R = np.array([float(val) for val in cur_illum_str.split()])
			d = actuators.get_dim_levels()
			E = R - A.dot(d)
			with lock:
				np.save(ENV_GAIN_FILE_NAME, E)
		except Exception, e:  # Stop optimizer if there is an error
			print "\nOPTIMIZER FAILURE\n"
			error_msg = str(e)
			print "Error Message: {}\n".format(error_msg)
			log_error(error_msg)
			traceback.print_exc()
			break


# Log an error
def log_error(error_msg):
	with open("errors.log", "a") as log_fle:
		log_fle.write("{}  :  {}\n".format(dt.now(), error_msg))


if __name__ == '__main__':
	print "{:<35} {:<25}".format("Main script started.", dt.now().strftime("%H:%M:%S.%f"))
	ceiling_actuation = CeilingActuation(PHUE_IP_ADDRESS)

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
			optimizer_process = Process(target=optimizer, args=(ceiling_actuation, ))
			optimizer_process.daemon = True
			optimizer_process.start()
		elif msg == 'Close':
			if optimizer_process:
				optimizer_process.terminate()
			conn.close()
			break