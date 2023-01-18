import numpy as np
import pandas as pd

class InputFile:
	def __init__(self,template_name,model_tag,zero_fill):
		self.tag = model_tag
		self.zf = zero_fill
		
		f=open(template_name + '.inp', "r")
		self.contents = f.readlines()
		f.close()
	
	def set_mesh(self, local_id):
		id_mesh = self.contents.index('**>>>>>FLAG.MESH<<<<<\n')
		line_mesh = '*INCLUDE,input=' + self.tag + str(local_id).zfill(self.zf) + '_mesh.inp\n'
		self.contents[id_mesh] = line_mesh

	def set_laser(self, local_id):
		id_laser = self.contents.index('**>>>>>FLAG.LASER<<<<<\n')
		line_laser = '	INPUT = "' + self.tag + str(local_id).zfill(self.zf) + '_AM_laser.inp"\n'
		self.contents[id_laser] = line_laser
		
	def set_initial_conditions(self, local_id, ref_step, globalname, trackchange):
	# Function to set the initial conditions for the input file
	# if else statements are for handling exceptions
	
		id_init = self.contents.index('**>>>>>FLAG.INITIAL_CONDITIONS<<<<<\n')
		if local_id == 0 or trackchange: # First local or when there is track change
			line_new = '*Initial Conditions, type=TEMPERATURE, '+\
				'file='+globalname+'.odb, '+\
				'step='+str(ref_step)+', inc=0, '+\
				'interpolate\n'
			lines_init = line_new
		else: # Normal conditions
			line_new = '*Initial Conditions, type=TEMPERATURE, '+\
				'file='+globalname+'.odb, '+\
				'step='+str(ref_step)+', inc=0, '+\
				'interpolate\n'
			line_overlap = '*Initial Conditions, type=TEMPERATURE, '+\
				'file=run_'+self.tag+str(local_id-1).zfill(self.zf)+'.odb, '+\
				'interpolate, driving elsets\n'+\
				'Set-all-elemenets,Set-overlap-nodes\n'
			lines_init = line_new+line_overlap
			
		self.contents[id_init] = lines_init
	
	def set_step(self, local_id):
		line_id = self.contents.index('**>>>>>FLAG.STEP<<<<<\n')
		line_new = '*INCLUDE,input=' + self.tag + str(local_id).zfill(self.zf) + '_step.inp\n'
		self.contents[line_id] = line_new
	
	def write_file(self, local_id):
		self.filename = self.tag + str(local_id).zfill(self.zf) + '_input.inp'
		with open(self.filename,'w+') as file:
			for line in self.contents:
				file.write(line)


class MeshFile:
	def __init__(self,template_name,model_tag,zero_fill):
		self.tag = model_tag
		self.zf = zero_fill
		
		f=open(template_name + '.inp', "r")
		self.contents = f.readlines()
		f.close()
		
	def tranform_nodes(self, model_shift, model_rotation):
		self.delta_r = model_shift
		self.theta = model_rotation
	
		id_transform = self.contents.index('**>>>>>FLAG.TRANSFORM<<<<<\n')
		translation = '%s,%s,%s'%(self.delta_r[0], self.delta_r[1], self.delta_r[2])
		rotation_0 = translation
		rotation_1 = '%s,%s,%s'%(self.delta_r[0], self.delta_r[1], self.delta_r[2]+1)
		line_transform = translation+'\n'+\
			rotation_0+','+rotation_1+','+str(self.theta)+'\n'
		self.contents[id_transform] = line_transform
	
	def activate(self, glb_nd_csv, local_id, PRC_SPACE):
		coords_glb = pd.read_csv(glb_nd_csv,index_col='label')

		outline_glb = {
			'x':(coords_glb['x'].min(),coords_glb['x'].max()),
			'y':(coords_glb['y'].min(),coords_glb['y'].max()),
			'z':(coords_glb['z'].min(),coords_glb['z'].max()),
		}
		
		id_node = self.contents.index('*Node\n')
		id_element = self.contents.index('*Element, type=DC3D8\n')
		id_end = self.contents.index('*Nset, nset=Set-all, generate\n')
		
		nodes_lcl_lines = self.contents[id_node+1:id_element]
		elements_lcl_lines = self.contents[id_element+1:id_end]
	
		# Activation status of the elements, assming all are inactive at the beginning
		element_activation = [0]*len(elements_lcl_lines)
		set_on_el = []
		set_off_el = []

		for el_con in elements_lcl_lines:
			nodes = el_con.split(',')	# Splitting each string line to its nodes
			nodes[-1] = nodes[-1][:-1]	# Removing newline character from the last node
			el_label = int(nodes.pop(0))
			nodes = [int(x) for x in nodes]	# Transforming the nodes into integers

			center = {'x':0,'y':0,'z':0}
			
			for nd_label in nodes:
				coords = nodes_lcl_lines[nd_label-1].split(',')
				coords[-1] = coords[-1][:-1]
				coords = [round(float(x),PRC_SPACE) for x in coords[1:]]
				ct = np.cos(np.radians(self.theta))
				st = np.sin(np.radians(self.theta))
				center['x'] += self.delta_r[0] + ct*coords[0] - st*coords[1]
				center['y'] += self.delta_r[1] + st*coords[0] + ct*coords[1]
				center['z'] += self.delta_r[2] + coords[2]
			
			center['x'] = center['x']/len(nodes)
			center['y'] = center['y']/len(nodes)
			center['z'] = center['z']/len(nodes)
			
			
			if ( center['x'] > outline_glb['x'][0] and center['x'] < outline_glb['x'][1] and
				 center['y'] > outline_glb['y'][0] and center['y'] < outline_glb['y'][1] and
				 center['z'] > outline_glb['z'][0] and center['z'] < outline_glb['z'][1]):
				element_activation[el_label-1]=1

		label_counter = 1
		for eactive in element_activation:
			if eactive == 1:
				set_on_el.append(label_counter)
			elif eactive == 0:
				set_off_el.append(label_counter)
			label_counter+=1
		
		file_eactive = self.tag + str(local_id).zfill(self.zf) + '_elsets.inp'
		with open(file_eactive ,'w+') as file:
			file.write('*Elset, elset=Set-active-elements, instance=Part-local-ins\n')
			ii = 0
			for label in set_on_el:
				file.write(str(label)+', ')
				if ii % 16 == 15: # Maximum 16 data points per line
					file.write('\n')
				ii+=1
			file.write('\n*Elset, elset=Set-inactive-elements, instance=Part-local-ins\n')
			ii = 0
			for label in set_off_el:
				file.write(str(label)+', ')
				if ii % 16 == 15: # Maximum 16 data points per line
					file.write('\n')
				ii+=1
				
		id_activate = self.contents.index('**>>>>>FLAG.ACTIVATE<<<<<\n')
		line_activation = '*Include,input="%s%s_elsets.inp"\n'%(self.tag, str(local_id).zfill(self.zf))
		self.contents[id_activate] = line_activation
		
	def write_file(self, local_id):
		self.filename = self.tag + str(local_id).zfill(self.zf) + '_mesh.inp'
		with open(self.filename,'w+') as file:
			for line in self.contents:
				file.write(line)


class StepFile:
	def __init__(self,template_name,model_tag,zero_fill):
		self.tag = model_tag
		self.zf = zero_fill
		
		f=open(template_name + '.inp', "r")
		self.contents = f.readlines()
		f.close()
		
	def set_submodel_step(self, ref_step):
		id_line = self.contents.index('**>>>>>FLAG.SUBMODEL<<<<<\n')
		line_new = '*Boundary, submodel, step='+str(ref_step)+'\n'
		self.contents[id_line] = line_new
	
	def write_file(self, local_id):
		self.filename = self.tag + str(local_id).zfill(self.zf) + '_step.inp'
		with open(self.filename,'w+') as file:
			for line in self.contents:
				file.write(line)


class SubroutineFile:
	def __init__(self,template_name,model_tag,zero_fill):
		self.tag = model_tag
		self.zf = zero_fill
		
		f=open(template_name + '.f', "r")
		self.contents = f.readlines()
		f.close()
	
	def set_name(self, local_id):
		line_name = self.contents.index('      CHARACTER(*), PARAMETER :: RUNNAME = >>>>>FLAG.MODELNAME<<<<<'+'\n')
		self.contents[line_name] =	    '      CHARACTER(*), PARAMETER :: RUNNAME = \''+self.tag+str(local_id).zfill(self.zf)+'\''+'\n'

	def write_file(self, local_id):
		self.filename = self.tag + str(local_id).zfill(self.zf) + '_subroutine.f'
		with open(self.filename,'w+') as file:
			for line in self.contents:
				file.write(line)


class ParallelTracks:
	def __init__(self, template_name):
		f=open(template_name, "r")
		self.contents = f.readlines()
		f.close()
		
	def set_localrange(self, first_id, last_id, track_id):
		line_for = 'for lcl_id in range(%i,%i):\n'%(first_id,last_id+1)
		line_localid = '	local = local_events.locals[lcl_id]\n'
		line_time = '	\'time_file\':\'5_time_locals_track%i.log\'\n'%(track_id+1)
		
		range_id = self.contents.index('for local in local_events.locals:\n')
		time_id = self.contents.index('	\'time_file\':\'5_time_locals.log\',	# File name for saving all script duration values\n')
		self.contents[range_id] = line_for
		self.contents[range_id+1] = line_localid
		self.contents[time_id] = line_time
		
	def write_file(self, track_id):
		filename = '3_pycode_multiscale_track%s.py'%(str(track_id+1))
		with open(filename,'w+') as file:
			for line in self.contents:
				file.write(line)