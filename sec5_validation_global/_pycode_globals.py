# Use modern python to run this. Notepadd++ F5 command:
# cmd /k cd /d $(CURRENT_DIRECTORY) && python $(FULL_CURRENT_PATH)

import _pylib.tools as tl

STG = {	# Settings
	'sim_tag':'glb_coarse',	# String used inside job names
	'id_len':3,				# Number of characters to fill with leading zeros
	'time_file':'9_time_global.log'	# File name for saving all script duration values
}
SYS = {
	# 'command':'abaqus',
	# 'cpus':12,			# Number of logical processors to run the simulations
}
time_log = tl.TimeLog(STG['time_file'])

time_log.in_right()
old_job = None
for track_id in range(30):
	time_log.start()
	if track_id == 0:
		abaqus_tags = {
			'job':'run_%s_track%s'%(STG['sim_tag'], str(track_id+1).zfill(STG['id_len'])),
			'input':'3_input_track%s'%(str(track_id+1).zfill(STG['id_len'])),
		}
		tl.runAbaqus(system=SYS,**abaqus_tags)
		old_job = abaqus_tags['job']
	else:
		abaqus_tags = {
			'job':'run_%s_track%s'%(STG['sim_tag'], str(track_id+1).zfill(STG['id_len'])),
			'input':'3_input_track%s'%(str(track_id+1).zfill(STG['id_len'])),
			'oldjob':old_job,
		}
		tl.runAbaqus(system=SYS,**abaqus_tags)
		old_job = abaqus_tags['job']
	time_log.append('Finished running the global simulation for track %i'%(track_id+1))
time_log.in_left()

time_log.closure()