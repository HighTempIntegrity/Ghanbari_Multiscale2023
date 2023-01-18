# Use modern python to run this. Notepadd++ F5 command:
# cmd /k cd /d $(CURRENT_DIRECTORY) && python $(FULL_CURRENT_PATH)

import _pylib_inpyt_multiscale as inpr
import _pylib_laser as lsr
import _pylib_tools as tl

STG = {	# Settings
	'local_tag':'L',		# A string for naming local models
	'id_len':3,				# Number of characters to fill with leading zeros
	'indent_string':' > ',	# Used for indenting the output info in command line
	'time_file':'3_time_locals_track8'
}
SYS = {
	'platform':'lnx',	# win | lnx - The OS where the script is running.
	'cpus':12,			# Number of logical processors to run the simulations
}
MS_LCL = {
	'xlim':(0,10),			# Limits on x axis where the laser enters and exits the probe region
	'mid_points':4,			# Number of points in the local time range to save data (w/o start anf finish)
	'laser':'2_AM_laser',	# Laser file
	'local_length':0.1,		# The length that laser moves inside the local model (millimeters)
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
	'mesh':'2_mesh_finefront',
	'step':'2_step'
}

time_log = tl.TimeLog(STG['time_file'],STG['indent_string'])
in_i = 0 # For controlling the level of indentation

# read the laser file
time_log.start()
laser_data = lsr.LaserEvents(MS_LCL['laser'], MS_LCL['local_length'])
laser_data.find_locals(MS_LCL['xlim'],MS_LCL['mid_points'],PRC['time'],PRC['space'])
time_log.append('Prepared local info based on laser event series', in_i)

in_i+=1
for lcl_id in range(700,800):
	local = laser_data.locals[lcl_id]
	
	time_log.start()
	
	# if lcl_id > 2:
		# break
	
	# finding the correct name for referencing the global model
	if MS_GLB['type'] == 'track':
		# name of corresponding track in global model
		track_name = '%s%s'%(MS_GLB['type'], str(local['track_id']).zfill(STG['id_len']))
		# name of the corresponding global ODB
		cor_global = '%s_%s'%(MS_GLB['name'], track_name)
	else:
		cor_global = MS_GLB['name']
		
	# Laser file processing
	coords_shift  = local['shift'].ar
	coords_rotate = local['angle']
	laser_data.write_file(STG['local_tag'],lcl_id,STG['id_len'])
	
	# Abaqus input file processing
	local_input = inpr.InputFile(TPL['input'],STG['local_tag'],STG['id_len'])
	local_input.set_mesh(lcl_id)
	local_input.set_laser(lcl_id)
	local_input.set_initial_conditions(lcl_id, local['track_step'], cor_global,
		laser_data.check_trackchange(lcl_id))
	local_input.set_step(lcl_id)
	local_input.write_file(lcl_id)
		
	# Mesh file processing
	local_mesh = inpr.MeshFile(TPL['mesh'],STG['local_tag'],STG['id_len'])
	local_mesh.tranform_nodes(coords_shift,coords_rotate)
	local_mesh.activate(MS_GLB['nodes'],lcl_id,PRC['space'])
	local_mesh.write_file(lcl_id)
	
	# Step file processing
	local_step = inpr.StepFile(TPL['step'],STG['local_tag'],STG['id_len'])
	local_step.set_submodel_step(local['ref_step'])
	local_step.write_file(lcl_id)
	
	time_log.append('Local %i | Prepared all files'%(lcl_id), in_i)
	
	## Run local simulation
	time_log.start()
	# name of local job run
	job_name = 'run_%s%s'%(STG['local_tag'], str(lcl_id).zfill(STG['id_len']))
	# Run the local model
	tl.runLocal(job_name, local_input.filename, TPL['subroutine'], cor_global, SYS)
	time_log.append('Finished running the simulation for Local %i'%(lcl_id), in_i)
in_i-=1

time_log.closure()