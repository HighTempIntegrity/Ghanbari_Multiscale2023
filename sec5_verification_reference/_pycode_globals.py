# Use modern python to run this. Notepadd++ F5 command:
# cmd /k cd /d $(CURRENT_DIRECTORY) && python $(FULL_CURRENT_PATH)

import _pylib_tools as tl

STG = {	# Settings
	'track_tag':'track',	# String for naming models
	'sim_tag':'glb_fine',	# String used inside job names
	'id_len':3,				# Number of characters to fill with leading zeros
	'indent_string':' > ',	# Used for indenting the output info in command line
	'time_file':'3_time_global'	# File name for saving all script duration values
}
SYS = {
	'platform':'lnx',	# win | lnx - The OS where the script is running.
	'cpus':12,			# Number of logical processors to run the simulations
}
time_log = tl.TimeLog(STG['time_file'],STG['indent_string'])
in_i = 0 # For controlling the level of indentation

in_i += 1
# name of old_job for restarting the tracks
old_job = None
# index of tracks that have been already processed
processed_tracks = []
for track_id in range(9):
	time_log.start()
	track_name = '%s%s'%(STG['track_tag'], str(track_id).zfill(STG['id_len']))
	cur_job = 'run_%s_%s'%(STG['sim_tag'], track_name)
	
	if track_id not in processed_tracks:
		if track_id == 0:	# First track has no old job
			tl.runAbaqus(cur_job, '1_input_%s'%(track_name), SYS)
		else:	# Tracks 1,2,... are a restart of 0
			tl.contGlobal(cur_job, '1_input_%s'%(track_name), old_job, SYS)
		time_log.append('Finished running the global simulation for track %i'%(track_id), in_i)
	else:
		time_log.append('Track %i already finished.'%(track_id), in_i)
		
	
	old_job = cur_job
in_i -= 1

time_log.closure()