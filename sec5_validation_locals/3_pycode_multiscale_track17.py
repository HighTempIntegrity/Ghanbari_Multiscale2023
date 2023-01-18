# Use modern python to run this. Notepadd++ F5 command:
# cmd /k cd /d $(CURRENT_DIRECTORY) && python $(FULL_CURRENT_PATH)

import _input.multiscale as inpr
import _plib.laser as lsr
import _plib.tools as tl

STG = {	# Settings
	'local_tag':'L',		# A string for naming local models
	'id_len':3,				# Number of characters to fill with leading zeros
	'time_file':'5_time_locals_track17.log'
}
SYS = {
	'command':'abaqus',
	'cpus':4,			# Number of logical processors to run the simulations
}
MS_LCL = {
	'xlim':(0,10),			# Limits on x axis where the laser enters and exits the probe region
	'mid_points':13,			# Number of points in the local time range to save data (w/o start and finish)
	'laser':'2_AM_laser.inp',	# Laser file
	'local_length':1,		# The length that laser moves inside the local model (millimeters)
}
MS_GLB = {
	'type':'track',	# single|layer|track ; how global ODBs are saved
	'name':'run_glb_coarse',	# The name of global model to import initial conditions
	'nodes':'1_run_glb_coarse-node-coords.csv',
}
PRC = {	# Precision values for rounding numbers where needed
	'time':8,	# number of digits for rounding time
	'space':7,	# number of digits for rounding space
}
TPL = {	# Templates
	'subroutine':'1_subroutine',
	'input':'2_input',
	'mesh':'2_mesh_3track',
	'step':'2_step'
}

time_log = tl.TimeLog(STG['time_file'])

# read the laser file
time_log.start()
laser_events = lsr.LaserEvents(MS_LCL['laser'])
local_events = lsr.LocalEvents(laser_events, MS_LCL, MS_GLB['type'], PRC)
time_log.append('Prepared local info based on laser event series')

time_log.in_right()
for lcl_id in range(160,170):
	local = local_events.locals[lcl_id]
	
	time_log.start()
	
	# if lcl_id > 2:
		# break
	
	# finding the correct name for referencing the global model
	if MS_GLB['type'] == 'track':
		# name of corresponding track in global model
		track_name = '%s%s'%(MS_GLB['type'], str(local['track_id']+1).zfill(STG['id_len']))
		# name of the corresponding global ODB
		cor_global = '%s_%s'%(MS_GLB['name'], track_name)
	else:
		cor_global = MS_GLB['name']
		
	# Laser file processing
	coords_shift  = local['shift']
	coords_rotate = local['angle']
	local_events.write_file(STG['local_tag'],lcl_id,STG['id_len'])
	
	# Abaqus input file processing
	local_input = inpr.InputFile(TPL['input'],STG['local_tag'],STG['id_len'])
	local_input.set_mesh(lcl_id)
	local_input.set_laser(lcl_id)
	local_input.set_initial_conditions(lcl_id, local['track_step'], cor_global,
		local_events.check_trackchange(lcl_id))
	local_input.set_step(lcl_id)
	local_input.write_file(lcl_id)
		
	# Mesh file processing
	local_mesh = inpr.MeshFile(TPL['mesh'],STG['local_tag'],STG['id_len'])
	local_mesh.tranform_nodes(coords_shift,coords_rotate)
	local_mesh.activate(MS_GLB['nodes'],lcl_id,PRC['space'])
	local_mesh.write_file(lcl_id)
	
	# Step file processing
	local_step = inpr.StepFile(TPL['step'],STG['local_tag'],STG['id_len'])
	local_step.set_submodel_step(local['whole_step'])
	local_step.write_file(lcl_id)
	
	time_log.append('Local %i | Prepared all files'%(lcl_id))
	
	## Run local simulation
	time_log.start()
	# name of local job run
	abaqus_tags = {
		'job':'run_%s%s'%(STG['local_tag'], str(lcl_id).zfill(STG['id_len'])),
		'input':local_input.filename,
		'user':TPL['subroutine'],
		'globalmodel':cor_global,
	}
	# Run the local model
	# tl.runLocal(job_name, local_input.filename, TPL['subroutine'], cor_global, SYS)
	tl.runAbaqus(system=SYS,**abaqus_tags)
	time_log.append('Finished running the simulation for Local %i'%(lcl_id))
time_log.in_left()

time_log.closure()