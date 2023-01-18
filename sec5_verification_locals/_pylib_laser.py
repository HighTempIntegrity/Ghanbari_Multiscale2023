import numpy as np
import math
import os

class LaserEvents:
	def __init__(self, template_name, LOCAL_LEN):
		self.local_length = LOCAL_LEN
		
		# Reading the template file into 'contents'
		f = open(template_name+'.inp', "r")
		contents = f.readlines()
		f.close()
		
		hatchCount  = int(len(contents)/2)	# Number of hatches that laser is active
		layer_counter = 0
		self.vectors = [] # List of dictionaries with laser hatch information
		for hatch_id in range(hatchCount):	# Processing each hatch separately
			start_line_segments = contents[hatch_id*2].split(',')   # Activation line
			end_line_segments = contents[hatch_id*2+1].split(',') # Deactivation line
			
			hatch_p1 = coord3D(\
				float(start_line_segments[1]),\
				float(start_line_segments[2]),\
				float(start_line_segments[3]))
			hatch_p2 = coord3D(\
				float(end_line_segments[1]),\
				float(end_line_segments[2]),\
				float(end_line_segments[3]))
			hatch_vector = coord3D(hatch_p2.ar - hatch_p1.ar)
			
			fresh_layer = False
			## Checking for layer change
			if self.vectors:	# If the vector list is not empty/not first hatch
				prev_height = self.vectors[-1]['start'].ar[2]
				cur_height = hatch_p1.ar[2]
				if cur_height>prev_height: # If the new hatch is at a higher z than last one
					layer_counter+=1
					fresh_layer = True
			else:
				fresh_layer = True
			
			# vectors: laser hatch with direction
			# 'norm': normal vector in direction of hatch
			# 'start': coordinates of hatch start
			# 'length': length of hatch
			# 'on': the time when the hatch startswith
			# 'duration': how long the hatch takes
			# 'power': laser power for the current vector
			# 'hatch_id': index of hatches in total
			# 'layer_id': index of layers in total
			# 'fresh_layer': true if it's the first track of current layer
			self.vectors.append({})
			self.vectors[-1]['norm'] = hatch_vector.normal()
			self.vectors[-1]['start'] = hatch_p1
			self.vectors[-1]['length'] = hatch_vector.length()
			self.vectors[-1]['on'] = float(start_line_segments[0])
			self.vectors[-1]['duration'] = float(end_line_segments[0]) - self.vectors[-1]['on']
			self.vectors[-1]['power'] = float(start_line_segments[4][:-1])
			self.vectors[-1]['hatch_id'] = hatch_id
			self.vectors[-1]['layer_id'] = layer_counter
			self.vectors[-1]['fresh_layer'] = fresh_layer
				
	
	def find_locals(self, LIMITS, MIDNO, TIMEPREC, SPREC):
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
		# 'ref_step': step number in the global model
		# 'track_step': step number in the current track
		
		self.locals = []	
		
		x_min = LIMITS[0]
		x_max = LIMITS[1]
		local_ID = 0
		
		layer_start_time = self.vectors[0]['on']
		for vector in self.vectors:
			ratios = []	# List of length ratios that the vectors passes the x limits
			ratios.append((x_min - vector['start'].xx)/(vector['norm'].xx*vector['length']))
			ratios.append((x_max - vector['start'].xx)/(vector['norm'].xx*vector['length']))
			ratio_min = min(ratios)	# the least ratio that corresponds to entry into probe region
			
			# time_vector: total time of where locals start in current vector
			# local_duration: duration of local model for current vector
			# x_length: length of track in probe region
			# local_number: number of local models in current track
			time_vector = ratio_min*vector['duration']+vector['on']
			local_duration = (self.local_length/vector['length'])*vector['duration']
			x_length = abs(x_max-x_min)
			local_number = int(x_length/self.local_length)
			
			for segment_id in range(local_number):
				self.locals.append({}) # add empty dictionary
				start = coord3D(\
					vector['start'].ar+\
					vector['norm'].ar*vector['length']*ratio_min+\
					vector['norm'].ar*x_length*segment_id/local_number)
				end = coord3D(start.ar+\
					vector['norm'].ar*self.local_length)
				time1 = round(time_vector+segment_id*local_duration-layer_start_time,TIMEPREC)
				time2 = round(time_vector+segment_id*local_duration,TIMEPREC)
				tps0 = np.linspace(0,local_duration,MIDNO+2).tolist()
				tps1 = np.linspace(time1,time1+local_duration,MIDNO+2).tolist()
				tps2 = np.linspace(time2,time2+local_duration,MIDNO+2).tolist()
				format1 = {'t':0.0,'x':start.xx,'y':start.yy,'z':start.zz,'pow':vector['power'],'sp':SPREC,'ts':TIMEPREC}
				format2 = {'t':local_duration,'x':end.xx,'y':end.yy,'z':end.zz,'pow':0.0,'sp':SPREC,'ts':TIMEPREC}
				self.locals[-1]['line1'] = "{t:12.{ts}},{x:6.{sp}},{y:6.{sp}},{z:6.{sp}},{pow}\n".format(**format1)
				self.locals[-1]['line2'] = "{t:12.{ts}},{x:6.{sp}},{y:6.{sp}},{z:6.{sp}},{pow}\n".format(**format2)
				self.locals[-1]['start'] = start
				self.locals[-1]['end'] = end
				self.locals[-1]['shift'] = start.minus(self.vectors[0]['start'])
				self.locals[-1]['angle'] = math.degrees(math.acos(np.dot(vector['norm'].ar,self.vectors[0]['norm'].ar)))
				self.locals[-1]['time1'] = time1
				self.locals[-1]['time2'] = time2
				self.locals[-1]['duration'] = round(local_duration,TIMEPREC)
				self.locals[-1]['timepoints0'] = [round(x,TIMEPREC) for x in tps0]
				self.locals[-1]['timepoints1'] = [round(x,TIMEPREC) for x in tps1]
				self.locals[-1]['timepoints2'] = [round(x,TIMEPREC) for x in tps2]
				self.locals[-1]['id'] = local_ID
				self.locals[-1]['track_id'] = vector['hatch_id']
				self.locals[-1]['layer_id'] = vector['layer_id']
				self.locals[-1]['ref_step'] = (vector['layer_id']+1)+(local_ID+1)
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
		
		# If the local is not in the list then it's for a new hatch
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


class coord3D:
	# A small custom class for processing 3D coordinates
	def __init__(self, *args):
		PRC = 9
		if isinstance(args[0],float):
			self.xx = round(args[0],PRC)
			self.yy = round(args[1],PRC)
			self.zz = round(args[2],PRC)
			self.ar = np.array([self.xx,self.yy,self.zz])
		elif isinstance(args[0],np.ndarray):
			self.xx = round(args[0][0],PRC)
			self.yy = round(args[0][1],PRC)
			self.zz = round(args[0][2],PRC)
			self.ar = np.array([self.xx,self.yy,self.zz])

	def __str__(self):
		return 'Point(%s,%s,%s)'%(self.xx, self.yy, self.zz)
	
	def distance(self, other):
		delta_x = self.xx - other.xx
		delta_y = self.yy - other.yy
		delta_z = self.zz - other.zz
		return (delta_x**2+delta_y**2+delta_z)**0.5
	
	def length(self):
		return (self.xx**2+self.yy**2+self.zz)**0.5
	
	def minus(self,other):
		return(coord3D(self.xx-other.xx, self.yy-other.yy, self.zz-other.zz))
		
	def plus(self,other):
		return(coord3D(self.xx+other.xx, self.yy+other.yy, self.zz+other.zz))
	
	def multiply(self,factor):
		return(coord3D(self.xx*factor, self.yy*factor, self.zz*factor))
	
	def normal(self):
		length = (self.xx**2+self.yy**2+self.zz)**0.5
		norm_x = self.xx/length
		norm_y = self.yy/length
		norm_z = self.zz/length
		return(coord3D(norm_x,norm_y,norm_z))
