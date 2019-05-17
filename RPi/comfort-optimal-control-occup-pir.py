import time
import traceback
from datetime import datetime as dt
from system_v4_occup_pir import LightingSystem
import numpy as np
from scipy.optimize import linprog


# Initial calibration of the system (getting A and E matrices)
# NOTE: This is a hardcoded calibration for initial dimming = 0.8 for all bulbs
# and S = 0.35 for all bulbs	
def calibration(system, step=0.35, B=0.65, wait_time = 2, type = "Calibration."):
	
	print "*" * 40, "\n", type
	
	if type == "Initial Calibration":
		# Start with setting all bulbs to dimming level of 0.8
		dim_calibr = [0.8]*8
		system.set_dimming(dim_calibr, wait_time)
	 
	# Initialize A as 8x4 matrix
	A = [[None for _ in range(4)] for _ in range(8)] 

	# Initial light sensor readings (for all bulbs at dimming of 0.8)
	R, _ = system.get_sensor_readings()
	print "\nR:", R
	
	# Next apply calibration algorithm to each bulb j one by one
	for j in range(8):
		print "\n", "-"*20, "\nBULB:", j
		
		S = step
		if system.dim_levels[j] < B: # compare with pivot point
			S = -S
		
		system.change_dim_on_bulb(j, -S, wait_time)		
		R_prime, _ = system.get_sensor_readings()
		print "R_prime:", R_prime
		A[j] = [abs(R_prime[i] - R[i]) / step for i in range(4)]
		system.change_dim_on_bulb(j, S, wait_time)
	
	# Update matrices A and E
	system.A = map(list,zip(*A))
	system.print_contrib_matrix()
	
	A = np.matrix(system.A)
	d = np.array(system.dim_levels)
	R = np.array(R)
	
	E = R - A.dot(d)
	system.E = E.tolist()[0]
	print "\nVector E (Environment contribution):\n", system.E
	print "Calibration is completed\n", "*" * 40
	
	
def get_target_illum(motion):
	return np.array([150 if motion[i] == 1 else 0 for i in range(len(motion))])

#############################################################################
# Linear comfort optimization:

# Set optimal dimming value that would satisfy target illuminance
def set_optimal_dimming(system, target_illum):
	start_time = time.time()

	# Take negative of values so we can represent constraints as required by scipy.optimize.linprog
	A = np.negative(system.A) 
	E = np.array(system.E)
	
	# Coefficients of "power vs dimming" best fit line
	a_pow = 3.86706205178
	b_pow = 1.04678541344
	
	# Power consumed by bulb i:
	# Power_i = a_pow * dim_i + b_pow
	
	# Coefficients of variable that is being optimized
	c = [a_pow] * 8
	
	# Target for each sensor
	# Offsetting target by environmental contribution (Again, to get the form required by scipy.optimize.linprog)
	target_no_env = [target_illum[i] - E[i] for i in range(len(E))]
	target_no_env = np.negative(target_no_env)

	bound = (0.0, 1.0) # When the bulb is on
	bnds = [bound for _ in range(8)]
	res = linprog(c, A_ub=A, b_ub=target_no_env, bounds=bnds, method = 'simplex', options={"disp": False})
	
	if res.success: 
		d_opt = res.x
		d_opt = d_opt.tolist()
		system.set_dimming(d_opt)
		
		bulbs_on = 0
		for dim_val in d_opt:
			if dim_val > 0.0001:
				bulbs_on+=1
		power = res.fun + bulbs_on * b_pow
		
		print "Optimization info:"
		print "		Optimal power consumption:", "%.3f"%power, "W"
		system.print_dim_levels("Optimal dimming is set:")
	else:
		print "OPTIMIZATION CONSTRAINTS CANNOT BE SATISFIED!!!"
		d_opt = np.ones((8,1))
		d_opt = d_opt.tolist()
		system.set_dimming(d_opt)
		power = 8 * (3.86706205178+1.04678541344)
		
	time_elapsed = time.time() - start_time
	print "Optimization time is {} sec.".format(time_elapsed)
	
# Main code
try:
	lsys = LightingSystem()
	lsys.print_layouts()
	calibration(lsys, type = "Initial Calibration")	
		
	while True:
		print "*" * 40
		
		occup = lsys.get_occupancy() 
		target_illum = get_target_illum(occup) # target illuminances based on occupancy
				
		t = dt.now()
		print t.hour, ":", t.minute, ":", t.second, "\n"
		
		set_optimal_dimming(lsys, target_illum)
		lsys.print_illuminance()
		time.sleep(1)
		
		# Update environmental contribution + error term E
		A = np.matrix(lsys.A)
		d = np.array(lsys.dim_levels)
		R, _ = lsys.get_sensor_readings()
		R = np.array(R)
		E = R - A.dot(d)
		lsys.E = E.tolist()[0]
	
	lsys.stop_sens_modules()

except Exception, e: # Stop sensing modules if there is an error
	lsys.stop_sens_modules()
	print "Error Message:\n", str(e)
	traceback.print_exc()

except KeyboardInterrupt:
	print "\nScript Interrupted"
	lsys.stop_sens_modules()