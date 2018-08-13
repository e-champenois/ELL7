import serial
from time import sleep as time_sleep
from numpy import int32

class ELL7(object):
	""" Thorlabs ELL7 (https://www.thorlabs.com/thorproduct.cfm?partnumber=ELL7) motion
		controller.

		:param address: Serial address for the motor. Defaults to '/dev/ttyUSB2'.
		:param timeout: Communication timeout time. Defaults to 1 s.
		:param sleep: Default sleep time used to wait for a read request. Defaults to 10 ms.

		:method home: Homes the motor.
		:method get_abs: Returns the absolute position of the motor (in motor units).
		:method move_abs: Moves the motor to an absolute position (in motor units).
		:method move_rel: Moves the motor by a relative amount (in motor units).
	"""

	def __init__(self, address='/dev/ttyUSB2', timeout=1, sleep=0.01):
		self.ser = serial.Serial(address, timeout=timeout)
		self.term = '\r\n'
		self.sleep_duration = sleep
		self.sleep()
		self.home()

	def sleep(self, sleep_duration=None):
		time_sleep(self.sleep_duration if sleep_duration is None else sleep_duration)

	def write(self, cmd):
		self.ser.write(bytes(cmd + self.term, 'utf-8'))

	def read(self):
		msg = self.ser.read(max(1,self.ser.in_waiting)).decode('utf-8')
		if len(msg)==0:
			return ''
		elif len(msg) >= 2 and msg[-2:]==self.term:
			return msg[:-2]
		else:
			self.sleep()
			return msg + self.read()


	def home(self):
		self.write('0ho0')
		self.sleep()
		homing = 1
		while homing:
			msg = self.read()
			if msg[1:3]=='PO':
				homing = 0
				pos = pos_from_msg(msg)
				print('Homed to:', pos)

	def get_abs(self, verbose=True):
		self.write('0gp')
		pos = pos_from_msg(self.read())
		if verbose: print('Position:', pos)
		return pos

	def move_abs(self, pos, verbose=True):
		pos = int2hex(pos)[2:]
		self.write('0ma' + '0' * (8 - len(pos)) + pos)
		pos = pos_from_msg(self.read())
		if verbose: print('Position:', pos)

	def move_rel(self, pos, verbose=True):
		pos = int2hex(pos)[2:]
		self.write('0mr' + '0' * (8 - len(pos)) + pos)
		pos = pos_from_msg(self.read())
		if verbose: print('Position:', pos)


def pos_from_msg(msg):
	assert msg[1:3]=='PO'
	return hex2int(msg[3:])

def int2hex(pos):
	return "{0:0{1}X}".format(pos & ((1<<32) - 1), 32//4)

def hex2int(bits):
	pos = int(bits, 16)
	if pos >= 1<<31:
		pos -= 1<<32
	return pos