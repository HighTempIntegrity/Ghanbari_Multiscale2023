# Use modern python to run this. Notepadd++ F5 command:
# cmd /k cd /d $(CURRENT_DIRECTORY) && python $(FULL_CURRENT_PATH)

import _pylib_inpyt_multiscale as inpr
import _pylib_laser as lsr

STG = {	# Settings
}
MS_LCL = {
	'xlim':(0,10),			# Limits on x axis where the laser enters and exits the probe region
	'mid_points':4,			# Number of points in the local time range to save data (w/o start anf finish)
	'laser':'2_AM_laser',	# Laser file
	'local_length':0.1,		# The length that laser moves inside the local model (millimeters)
}
PRC = {	# Precision values for rounding numbers where needed
	'time':8,	# number of digits for rounding time
	'space':7,	# number of digits for rounding space
}
TPL = {	# Templates
	'script':'_pycode_locals.py',
}

# read the laser file
laser_data = lsr.LaserEvents(MS_LCL['laser'], MS_LCL['local_length'])
laser_data.find_locals(MS_LCL['xlim'],MS_LCL['mid_points'],PRC['time'],PRC['space'])
laser_data.find_tracks()

for track in laser_data.tracks:
	pycode = inpr.ParallelTracks(TPL['script'])
	pycode.set_localrange(track['local_first_id'], track['local_last_id'], track['id'])
	pycode.write_file(track['id'])

