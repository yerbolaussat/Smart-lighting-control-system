"""
File name: phue_bulbs_control.py
Author: Yerbol Aussat
Python Version: 2.7

Script for testing Philips Hue bulbs
"""

from phue import Bridge

# Constants
PHUE_IP_ADDRESS = '192.168.0.3'


# Turn the bulb on, and set brightness to max
def on(bulb_id):
	l = lights[bulb_id]
	l.brightness = 255
	l.on = True


# Turn the bulb off
def off(bulb_id):
	l = lights[bulb_id]
	l.on = False    


# Turn the bulb on, and set brightness to a specified value
def set_brightness(bulb_id, bright_value):
	l = lights[bulb_id]
	l.on = True
	l.brightness = bright_value


# Get phue control value for dimming level d
def get_contr(d): 
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


def test_binary():
	while True:
		bulb_id_status = raw_input(
			"\nInsert bulb number and on/off (1/0) separated by space."
			"\n    (For selecting a different operation insert \"next\".)\n")
		if bulb_id_status == "next":
			break

		bulb_id = int(bulb_id_status.split()[0])
		on_status = int(bulb_id_status.split()[1])

		if on_status == 1:
			on(bulb_id)
		elif on_status == 0:
			off(bulb_id)
		print "Bulb {} is on: {}".format(bulb_id, on_status)


def test_control_value():
	bulb_id = raw_input("\nInsert bulb id (or several id's separated by space):\n")
	bulbs = bulb_id.split()
	while True:
		control_value = raw_input(
			"\nInsert control value on bulbs (-1 for turning off a bulb)."
			"\n     (For selecting a different operation insert \"next\".)\n")
		if control_value == "next":
			break
		for b in bulbs:
			bulb_id = int(b)
			control_value = int(control_value)
			if control_value == -1:
				off(bulb_id)
			else:
				set_brightness(bulb_id, control_value)


def test_dimming():
	bulb_id = raw_input("\nInsert bulb id (or several id's separated by space):\n")
	bulbs = bulb_id.split()
	while True:
		dim_lev = raw_input(
			"\nInsert dimming level (from 0.0 to 1.0) on bulbs (-1 for turning off a bulb)."
			"\n    (For selecting a different operation insert \"next\".)\n")
		if dim_lev == "next":
			break
		dim_lev = float(dim_lev)
		control_value = get_contr(dim_lev)
		for b in bulbs:
			bulb_id = int(b)
			control_value = int(round(control_value))
			if control_value == -1:
				off(bulb_id)
			else:
				set_brightness(bulb_id, control_value)


if __name__ == '__main__':
	# Set up hue bridge
	b = Bridge(PHUE_IP_ADDRESS)
	b.connect()
	lights = b.lights

	# Turn all bulbs off
	for l in lights:
		l.on = False

	# Test bulbs
	while True:
		print "Layout of bulbs:\n"
		print "    {}  {}  {}\n    {}  {}  {}\n    {}  {}  {}".format(0, 4, 1, 7, "x", 6, 2, 6, 3)
		text = raw_input("\n * For binary control of bulbs insert \"binary\"."
		                 "\n * For adjusting control value insert \"control\"."
		                 "\n * For adjusting dimming insert \"dimming\".\n")
		if text == "control":
			test_control_value()
		elif text == "dimming":
			test_dimming()
		elif text == "binary":
			test_binary()
