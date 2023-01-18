# Use modern python to run this. Notepadd++ F5 command:
# cmd /k cd /d $(CURRENT_DIRECTORY) && python $(FULL_CURRENT_PATH)

import _pylib_tools as tl

STG = {	# Settings
	'track_tag':'track',	# String for naming models
	'sim_tag':'glb_coarse',	# String used inside job names
	'id_len':3,				# Number of characters to fill with leading zeros
	'indent_string':' > ',	# Used for indenting the output info in command line
	'time_file':'3_time_global'	# File name for saving all script duration values
}
SYS = {
	'platform':'linux',	# windows | linux - The OS where the script is running.
	'cpus':12,			# Number of logical processors to run the simulations
}
time_log = tl.TimeLog(STG['time_file'],STG['indent_string'])
in_i = 0 # For controlling the level of indentation

in_i += 1
old_job = None
for track_id in range(9):
	time_log.start()
	track_name = '%s%s'%(STG['track_tag'], str(track_id).zfill(STG['id_len']))
	
	if track_id == 0:
		cur_job = 'run_%s_%s'%(STG['sim_tag'], track_name)
		tl.runAbaqus(cur_job, '1_input_%s'%(track_name), SYS)
		old_job = cur_job
	else:
		cur_job = 'run_%s_track%i'%(STG['sim_tag'], str(track_id).zfill(STG['id_len']))
		tl.contGlobal(cur_job, '1_input_%s'%(track_name), old_job, SYS)
		old_job = cur_job
	time_log.append('Finished running the global simulation for track %i'%(track_id), in_i)
in_i -= 1

time_log.closure()