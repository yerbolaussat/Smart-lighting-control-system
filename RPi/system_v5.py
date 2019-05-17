import socket
import time
from pandas import DataFrame
from datetime import datetime as dt
from phue import Bridge

class PyClient:

	def __init__(self, ip, port):
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPV-4 address, TCP-oriented socket 
		self.ip = ip
		self.port = port
		self.client.connect((ip, port))
		
	# Send a message msg from client to the server
	def send_msg(self, msg):
		self.client.send(msg)
		return self.client.recv(1024)
	
	# Disconnect from the server	
	def disconnect(self):
		self.send_msg("disconnect")
				
	
# Class for interacting with the lighting system
class LightingSystem:

	# Initialization of lighting system
	def __init__(self):
		try:
			# IP addresses of sensing modules
			addresses = [("192.168.50.188", 1234), # Omega-F13D
						("192.168.50.193", 1234),  # Omega-F10F    
						("192.168.50.158", 1234),  # Omega-F11F
						("192.168.50.168", 1234)]  # Omega-F129
		
			# Calibration constants for light sensors:
			self.callibration_const = [0.478023824068, 0.472723094776, 0.472723094776, 0.513906092956]
		
			# Initialize clients that communicate with sensing module servers
			self.sens_modules = []
			for ip, port in addresses:
				module = PyClient(ip, port)
				print "   [*]", module.send_msg("Check connection")
				sens_modules.append(module)
			print "Readers Initialized"		
		
			# Initialize Philips Hue:
			bridge = Bridge('192.168.0.2')
			bridge.connect()
			self.lights = bridge.lights
			for l in self.lights:
				l.on = True
				l.brightness = 0
			print "Philips Hue Initialized"
			
			# Mapping from bulb order to bulb id: 
			self.bulbs_dict = {0:(0,0), 1:(0, 2), 2:(2,0), 3:(2,2), 4:(0,1), 5:(2,1), 6:(1,2), 7:(1,0)}
			
			# Current brightness values
			self.dim_levels = [0]*8
			
			# Illuminance contribution matrix (4x8 matrix)
			self.A = [[None for _ in range(8)] for _ in range(4)] 
			
			# Environmental contribution matrix
			self.E = [None in range(4)]

		except:
			print "* Initialization error!"
			self.stop_sens_modules()
			
	# Stop connection with sensing modules
	def stop_sens_modules(self):
		print "\nConnection with sensing modules is interrupted"
		for module in self.sens_modules:
			module.disconnect()

	# Get light and occupancy readings from sensing modules
	def get_sensor_readings(self):
		light_readings = []
		motion_readings = []
		for i, module in enumerate(self.sens_modules):
			received_message = module.send_msg("Read")
			light_readings.append(int(received_message.split()[0])*self.callibration_const[i]) # Note: light values are stored as float
			motion_readings.append(int(received_message.split()[1]))
		return light_readings, motion_readings

	# Visualize illuminance on each sensor
	def print_illuminance(self):
		
		light, _ = self.get_sensor_readings()
		print "\nIlluminance readings from light sensors:"
		print " ", "-"*15
		print "  |     LIGHT   |"
		print " ", "-"*15
		print "  | ", int(round(light[1])), " | ", int(round(light[3])), " |"
		print " ", "-"*15
		print "  | ", int(round(light[0])), " | ", int(round(light[2])), " |"
		print " ", "-"*15
	
	# Convert dimming level to control value
	def dim_to_contr(self, d): 
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
	def set_dimming(self, desired_dimming, wait_time = 2):
		'''
		@param desired_dimming is a vector of length 8 containing desired dimming levels that the system needs to set on bulbs
		@param wait_time is the amount of time the system waits for bulbs to be dimmed
		'''
	
		if len(desired_dimming) != 8:
			raise ValueError('Length of dimming vector is {}, but should be 8!'.format(len(self.dim_levels)))
		
		for i, dim in enumerate(desired_dimming):
			if dim <= 0.01:
				self.lights[i].on = False
			else:
				self.lights[i].on = True
				self.lights[i].brightness = int(round(self.dim_to_contr(dim)))
		
		self.dim_levels = desired_dimming
		time.sleep(wait_time)
	

	# Change dimming on a bulb
	def change_dim_on_bulb(self, bulb_id, delta_dim, wait_time = 2):
		'''
		@param bulb_id: id of bulb whose dimming needs to be changed
		@param delta_dim: value in [-1.0, 1.0] that corresponds to change in dimming
		@param wait_time is the amount of time the system waits for bulbs to be dimmed
		'''
		
		cur_dim = self.dim_levels[bulb_id]
		target_dim = cur_dim + delta_dim
		print " * Target dimming on bulb {} is set to {}.".format(bulb_id, target_dim)
		
		if target_dim > 1:
			print "Target dimming on bulb {} is out of range.".format(bulb_id)
			target_dim = 1
		elif target_dim < 0:
			print "Target dimming on bulb {} is out of range.".format(bulb_id)
			target_dim = 0
		self.dim_levels[bulb_id] = target_dim
		self.lights[bulb_id].brightness = int(round(self.dim_to_contr(target_dim)))
		
		time.sleep(wait_time)

	
	# Print layout of bulbs
	def print_layouts(self):
		print "\nLayout of sensors:"
		print "    {}  {}\n    {}  {}".format(1, 3, 0, 2) 
		print "\nLayout of bulbs:\n"
		print "    {}  {}  {}\n    {}  {}  {}\n    {}  {}  {}".format(0, 4, 1, 7, "x", 6, 2, 5, 3) 
		
	# Print gain matrix A
	def print_contrib_matrix(self):
		print '-'*38
		print "Illuminance Contributon Matrix:"
		print DataFrame(self.A)
	
	# Print dimming level vector	
	def print_dim_levels(self, name =  "Bulb dimming level map"):
		out_map = [['x' for _ in range(3)] for _ in range(3)]
		for bulb_i, dim in enumerate(self.dim_levels):
			x, y = self.bulbs_dict[bulb_i]
			out_map[x][y] = dim
		print "-"*40
		print name+":\n",  DataFrame(out_map), '\n'
		print "-"*40


	# Get occupancy matrix based on motion
	def get_occupancy(self, verb = True):	
		_, motion = self.get_sensor_readings()
		occupancy = []
		for i in range(len(self.sens_modules)):
			occup_i = 0
			if len(self.motion_history[i]) >= 10:
				self.motion_history[i].pop()
				self.motion_history[i].insert(0, motion[i])
			
				occup_score = self.get_occup_score(self.motion_history[i])
				if occup_score >= 0.8:
					occup_i = 1
			else:
				self.motion_history[i].insert(0, motion[i])
				occup_score = self.get_occup_score(self.motion_history[i])
				if occup_score >= 1:
					occup_i = 1
			occupancy.append(occup_i)
				
		if verb:
			print "\n  Motioin matrix:"
			print "   ", "_"*11
			print "   ", "| {}  |  {} |".format(motion[1], motion[3])
			print "   ", "_"*11
			print "   ", "| {}  |  {} |".format(motion[0], motion[2])
			print "   ", "_"*11	
					
			print "\n  Occupancy matrix:"
			print "   ", "_"*11
			print "   ", "| {}  |  {} |".format(occupancy[1], occupancy[3])
			print "   ", "_"*11
			print "   ", "| {}  |  {} |".format(occupancy[0], occupancy[2])
			print "   ", "_"*11
		return occupancy
	
	# Occupancy score: discounted sum of occupancy values (which are 1 or 0)
	def get_occup_score(self, motions):
		score = 0
		alpha = 0.9
		for i in range(len(motions)):	
			score += motions[i] * alpha**i
		return score	
	