import numpy as np
import math
import os

class LaserEvents:
	def __init__(self, laser_file):
		# Reading the laser file into 'contents'
		f = open(laser_file, 'r')
		contents = f.readlines()
		f.close()
		
		tracks_NO  = int(len(contents)/2)	# Number of trackes that laser is active
		layer_counter = 0
		self.vectors = []	# List of dictionaries with laser track information
		self.layers = []	# List of dictionaries with layer information
		for track_id in range(tracks_NO):	# Processing each track separately
			start_line_segments = contents[track_id*2].split(',')   # Activation line
			end_line_segments = contents[track_id*2+1].split(',') # Deactivation line
			
			track_p1 = coord3D(\
				float(start_line_segments[1]),\
				float(start_line_segments[2]),\
				float(start_line_segments[3]))
			track_p2 = coord3D(\
				float(end_line_segments[1]),\
				float(end_line_segments[2]),\
				float(end_line_segments[3]))
			track_vector = coord3D(track_p2.ar - track_p1.ar)
			
			# Checking for layer change
			fresh_layer = False # Set to True if the track belongs to a new lauer
			if self.vectors:	# If the vector list is not empty i.e. not first track
				prev_height = self.vectors[-1]['start'][2]
				cur_height = track_p1.ar[2]
				if cur_height > prev_height: # If the new track is at a higher z than last one
					layer_counter+=1
					self.layers.append({})
					fresh_layer = True
			else:	# If first track then it's new layer
				self.layers.append({})
				fresh_layer = True
			
			# vectors: 		laser track with direction
			# 'dir':	normal vector in direction of track
			# 'length':		length of track
			# 'start': 		spatial coordinates of track start
			# 'end': 		spatial coordinates of track end
			# 'on': 		total time that the track starts
			# 'off': 		total time that the track ends
			# 'duration':	how long the track takes
			# 'power':		laser power for the current vector
			# 'track_id':	index of trackes in total
			# 'layer_id':	index of layers in total
			# 'fresh_layer': True if it's the first track of current layer
			self.vectors.append({})
			self.vectors[-1]['dir'] = track_vector.normal()
			self.vectors[-1]['length'] = track_vector.length()
			self.vectors[-1]['start'] = track_p1.ar
			self.vectors[-1]['end'] = track_p2.ar
			self.vectors[-1]['on'] = float(start_line_segments[0])
			self.vectors[-1]['duration'] = float(end_line_segments[0]) - self.vectors[-1]['on']
			self.vectors[-1]['off'] = self.vectors[-1]['on']+self.vectors[-1]['duration']
			self.vectors[-1]['power'] = float(start_line_segments[4][:-1])
			self.vectors[-1]['track_id'] = track_id
			self.vectors[-1]['layer_id'] = layer_counter
			self.vectors[-1]['fresh_layer'] = fresh_layer
			if fresh_layer:
				self.layers[-1]['layer_id'] = layer_counter
				self.layers[-1]['on'] = self.vectors[-1]['on']
				
	def laser_status(self, cur_time):
		# Returns the current position and state of laser
		# If the laser is off, it is stationary at the last track
		last_position = self.vectors[0]['start']
		last_track_time = self.vectors[0]['on']
		last_track_id = 0
		# Find which track we are at
		for vector in self.vectors:
			if cur_time<=vector['on']:
				break
			if cur_time<=vector['off']:
				# Find the time fraction
				track_time = cur_time-vector['on']
				cur_fraction = track_time/vector['duration']
				# Calculate the position
				cur_position = vector['start']+vector['dir']*cur_fraction*vector['length']
				# Return position and on/off state
				return cur_position,True,vector['track_id']
			else:
				last_position = vector['end']
				last_track_time = vector['off']
				last_track_id = vector['track_id']
		# If the time is outside of the laser event series
		# OR in the off state
		return last_position,False,last_track_id
		

class LocalEvents:
	def __init__(self, LEO, MS_LCL, GLOBAL_TYPE, ROUND_DIGITS):
		# Dicts containing local model info
		# 'line1': line 1 of laser input file
		# 'line2': line 2 of laser input file
		# 'start': coordinates of where laser starts in local model
		# 'end': coordinates of where laser ends in local model
		# 'shift': translation vector for mesh coordinates
		# 'angle': angle of rotation wrt global coordinate system
		# 'time1': start time of local model wrt current layer
		# 'time2': total start time of local model 
		# 'duration': the run time of the local model 
		# 'timepoints0': timepoints for saving data in local model
		# 'timepoints1': timepoints consistent with the heating step of global model
		# 'timepoints2': timepoints wrt total time
		# 'id': index of local model
		# 'track_id': index of corresponding laser track
		# 'layer_id': index of corresponding layer
		# 'whole_step': step number in the global model
		# 'track_step': step number in the current track
		
		self.locals = []	
		
		local_length = MS_LCL['local_length']
		x_min = MS_LCL['xlim'][0]
		x_max = MS_LCL['xlim'][1]
		mid_points = MS_LCL['mid_points']
		time_precision  = ROUND_DIGITS['time']
		space_precision = ROUND_DIGITS['space']
		
		local_ID = 0
		
		layer_start_time = LEO.vectors[0]['on']
		for vector in LEO.vectors:
			ratios = []	# List of length ratios that the vectors passes the x limits
			ratios.append((x_min - vector['start'][0])/(vector['dir'][0]*vector['length']))
			ratios.append((x_max - vector['start'][0])/(vector['dir'][0]*vector['length']))
			ratio_min = min(ratios)	# the least ratio that corresponds to entry into probe region
			
			# time_vector: total time of where locals start in current vector
			# local_duration: duration of local model for current vector
			# x_length: length of track in probe region
			# local_number: number of local models in current track
			time_vector = ratio_min*vector['duration']+vector['on']
			local_duration = (local_length/vector['length'])*vector['duration']
			x_length = abs(x_max-x_min)
			local_number = int(x_length/local_length)
			
			for segment_id in range(local_number):
				self.locals.append({}) # add empty dictionary
				start = vector['start']+vector['dir']*vector['length']*ratio_min+\
					vector['dir']*x_length*segment_id/local_number
				end = start+vector['dir']*local_length
				time1 = round(time_vector+segment_id*local_duration-layer_start_time,time_precision)
				time2 = round(time_vector+segment_id*local_duration,time_precision)
				tps0 = np.linspace(0,local_duration,mid_points+2).tolist()
				tps1 = np.linspace(time1,time1+local_duration,mid_points+2).tolist()
				tps2 = np.linspace(time2,time2+local_duration,mid_points+2).tolist()
				format1 = {'t':0.0,'x':start[0],'y':start[1],'z':start[2],'pow':vector['power'],'sp':space_precision,'ts':time_precision}
				format2 = {'t':local_duration,'x':end[0],'y':end[1],'z':end[2],'pow':0.0,'sp':space_precision,'ts':time_precision}
				self.locals[-1]['line1'] = "{t:12.{ts}},{x:6.{sp}},{y:6.{sp}},{z:6.{sp}},{pow}\n".format(**format1)
				self.locals[-1]['line2'] = "{t:12.{ts}},{x:6.{sp}},{y:6.{sp}},{z:6.{sp}},{pow}\n".format(**format2)
				self.locals[-1]['start'] = start
				self.locals[-1]['end'] = end
				self.locals[-1]['shift'] = start - LEO.vectors[0]['start']
				self.locals[-1]['angle'] = math.degrees(math.acos(np.dot(vector['dir'],LEO.vectors[0]['dir'])))
				self.locals[-1]['time1'] = time1
				self.locals[-1]['time2'] = time2
				self.locals[-1]['duration'] = round(local_duration,time_precision)
				self.locals[-1]['timepoints0'] = [round(x,time_precision) for x in tps0]
				self.locals[-1]['timepoints1'] = [round(x,time_precision) for x in tps1]
				self.locals[-1]['timepoints2'] = [round(x,time_precision) for x in tps2]
				self.locals[-1]['id'] = local_ID
				self.locals[-1]['track_id'] = vector['track_id']
				self.locals[-1]['layer_id'] = vector['layer_id']
				if GLOBAL_TYPE == 'probe':
					self.locals[-1]['whole_step'] = (local_ID+1)+(vector['layer_id']*2+1)+(vector['track_id']+1)
				else:
					self.locals[-1]['whole_step'] = (vector['layer_id']+1)+(local_ID+1)
				if vector['fresh_layer']:
					self.locals[-1]['track_step'] = segment_id+2
				else:
					self.locals[-1]['track_step'] = segment_id+1
				local_ID+=1
	
	def find_tracks(self):
		self.tracks = []
		# Dicts containing local model info
		# 'id': index of laser track
		# 'local_first_id': index of first local model in track
		# 'local_last_id': index of last local model in track
		
		
		track_ID = 0
		for local in self.locals:
			if self.check_trackchange(local['id']):
				self.tracks.append({}) # add empty dictionary
				self.tracks[-1]['id'] = track_ID
				self.tracks[-1]['local_first_id'] = local['id']
				track_ID+=1
			if self.check_trackchange(local['id']+1):
				self.tracks[-1]['local_last_id'] = local['id']	
			
	def get_shift(self,local_id):
		return self.locals[local_id]['start'].ar-self.locals[0]['start'].ar
		
	def get_rotation(self,local_id):
		return self.locals[local_id]['angle']
	
	def check_trackchange(self,local_id):
		## Function to determine if laser has moved to a new track to handle exceptions
		
		# If the local is not in the list then it's for a new track
		try: self.locals[local_id]
		except IndexError:
			return True
			
		if local_id == 0:
			return True	# The track is new at the very beginning
		elif self.locals[local_id]['track_id'] == self.locals[local_id-1]['track_id']:
			return False
		else:
			return True

	def check_layerchange(self,local_id):
		## Function to determine if laser has moved to a new layer
		
		# If the local is not in the list then it's for a new layer
		try: self.locals[local_id]
		except IndexError:
			return True
			
		if local_id == 0:
			return True	# The layer is new at the very beginning
		elif self.locals[local_id]['layer_id'] == self.locals[local_id-1]['layer_id']:
			return False
		else:
			return True

	def get_timepoints1(self):
		tps = []
		for local in self.locals:
			tps.extend(local['timepoints1'])
		tps = list(set(tps))
		tps.sort()
		self.timepoints1 = tps
		
	def get_tps2(self, lcl_ids = []):
		tps = []

		for local in self.locals:
			if lcl_ids: # List is not empty
				if local['id'] in lcl_ids:
					tps.extend(local['timepoints2'])
			else: # List is empty
				tps.extend(local['timepoints2'])
				
		tps = list(set(tps))
		tps.sort()
		return tps
		
	def get_starts(self):
		tps = []
		for local in self.locals:
			tps.append(local['time1'])
		tps = list(set(tps))
		tps.sort()
		self.startpoints = tps
		
	def write_timepoints_global(self, FILE_NAME):
		with open(FILE_NAME,'w+') as file:
			file.write('*Time Points, name=TimePoints\n')
			ii = 0
			for point in self.timepoints:
				file.write(str(point)+', ')
				if ii % 8 == 7: # Maximum 8 data points per line
					file.write('\n')
				ii+=1
				
	def write_timepoints_local(self, FILE_NAME):
		with open(FILE_NAME,'w+') as file:
			file.write('*Time Points, name=TimePoints-local\n')
			ii = 0
			for point in self.locals[0]['timepoints0']:
				file.write(str(point)+', ')
				if ii % 8 == 7: # Maximum 8 data points per line
					file.write('\n')
				ii+=1

	def write_file(self, TAG, LOCAL_ID, ZF):
		filename = TAG + str(LOCAL_ID).zfill(ZF) + '_AM_laser.inp'
		with open(filename,'w+') as file:
			file.write(self.locals[LOCAL_ID]['line1'])
			file.write(self.locals[LOCAL_ID]['line2'])
	
	def exportLocals(self,FILE_NAME):
		with open(FILE_NAME,'w+') as file:
			export_keys = ['id','timepoints2']
			separator = '\t,\t'
			
			header = separator.join(export_keys)
			file.write(header+'\n')
			for local in self.locals:
				line = separator.join([str(local[x]) for x in export_keys])
				file.write(line+'\n')
	
	def time_wrt_global(self, local, relative_df):
		index_glb = relative_df.index + local['time2']
		relative_df.index = index_glb
		return relative_df
	
	
class coord3D:
	# A small custom class for processing 3D coordinates
	def __init__(self, *args):
		PRC = 9
		if isinstance(args[0],float):
			self.xx = round(args[0],PRC)
			self.yy = round(args[1],PRC)
			self.zz = round(args[2],PRC)
			self.ar = np.array([self.xx,self.yy,self.zz])
		elif isinstance(args[0],np.ndarray) or isinstance(args,tuple):
			self.xx = round(args[0][0],PRC)
			self.yy = round(args[0][1],PRC)
			self.zz = round(args[0][2],PRC)
			self.ar = np.array([self.xx,self.yy,self.zz])

	def __str__(self):
		return '(%s,%s,%s)'%(self.xx, self.yy, self.zz)
	
	def distance(self, other):
		delta_x = self.xx - other.xx
		delta_y = self.yy - other.yy
		delta_z = self.zz - other.zz
		return (delta_x**2+delta_y**2+delta_z)**0.5
	
	def length(self):
		return (self.xx**2+self.yy**2+self.zz)**0.5
		
	def normal(self):
		length = (self.xx**2+self.yy**2+self.zz)**0.5
		norm_x = self.xx/length
		norm_y = self.yy/length
		norm_z = self.zz/length
		return(coord3D(norm_x,norm_y,norm_z).ar)
