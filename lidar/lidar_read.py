import time
import serial
import math
import os
import threading

# for little endian
def hex_to_dec(x1, x2):
	return x1 + x2 * 256
	

def check_sum(data):
	try:
		og_cs = hex_to_dec(data[6], data[7])
		cs = 0x55AA
		n = data[1]
		for i in range(0, 6, 2):
			cs ^= hex_to_dec(data[i], data[i + 1])
		for i in range(0, n * 2, 2):
			cs ^= hex_to_dec(data[i + 8], data[i + 9])
		if cs == og_cs:
			return True
		else:
			return False
	except Exception as e:
		#print('check_sum', e)
		return False
		
		
def valid_data(data_chunk):
	try:
		# check for packet type
		
		if not check_sum(data_chunk):
			return False
	except Exception as e:
		#print('valid_data',e)
		return False
	return True
	
	
def cal_angles(temp_dist, angles, sample_size, data_chunk):
	fsa = (hex_to_dec(data_chunk[2], data_chunk[3]) >> 1) / 64.0
	lsa = (hex_to_dec(data_chunk[4], data_chunk[5]) >> 1) / 64.0

	for i in range(sample_size):
		diff = 0
		if fsa > lsa:
			diff = 360 + lsa - fsa
		else:
			diff = lsa - fsa
		try:
			angles.append(diff * (i + 1) / float(sample_size - 1) + fsa)
		except Exception as e:
			#print('angle diff', e)
			angles.append(fsa)
		if temp_dist[i]:
			angles[i] += math.atan(21.8 * (155.3 - temp_dist[i]) / (155.3 * temp_dist[i]) * (180 / math.pi))
			if angles[i] >= 360:
				angles[i] -= 360
			elif angles[i] < 0:
				angles[i] += 360
		else:
			angles[i] = 0
		
	
def cal_dist(data_chunk, dist):
	sample_size = data_chunk[1]

	temp_dist = []
	for i in range(0, sample_size * 2, 2):
		temp_dist.append(hex_to_dec(data_chunk[i + 8], data_chunk[i + 9]) / 4)
		
	angles = []
	cal_angles(temp_dist, angles, sample_size, data_chunk)
	
	for i in range(sample_size):
		dist[math.floor(angles[i])] = temp_dist[i]

def scan(dist):
	while True:
		readings_list = ser.read(3000).split(b'\xaa\x55')
		for data_chunk in readings_list:
			if not valid_data(data_chunk):
				continue
			cal_dist(data_chunk, dist)



# driver code
ser = serial.Serial('/dev/ttyUSB0', 115200)
ser.reset_input_buffer()
ser.write(b'\xA5\x5A')
time.sleep(0.5)
ser.read(7)

dist = []
for i in range(360):
	dist.append(0)
	
t = threading.Thread(target = scan, args = (dist,))
t.daemon = True
t.start()

while True:
	# 0 direction
	print('0:', round((sum(dist[0:8]) + sum(dist[352:])) / 16.0, 2), '  ', end='')
	
	# 90 direction
	print('90:', round(sum(dist[82:98]) / 16.0, 2), '  ', end='')
	
	# 180 direction
	print('180:', round(sum(dist[172:188]) / 16.0, 2), '  ', end='')
	
	# 270 direction
	print('270:', round(sum(dist[262:278]) / 16.0, 2), '\t', end='\r')
	

	
ser.close()


	
	
	
	
	
	
	
