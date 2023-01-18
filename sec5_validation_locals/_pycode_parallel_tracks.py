# Use modern python to run this. Notepadd++ F5 command:
# cmd /k cd /d $(CURRENT_DIRECTORY) && python $(FULL_CURRENT_PATH)

import _input.multiscale as inpr
import _plib.laser as lsr

STG = {	# Settings
}
MS_LCL = {
	'xlim':(0,10),			# Limits on x axis where the laser enters and exits the probe region
	'mid_points':13,			# Number of points in the local time range to save data (w/o start and finish)
	'laser':'2_AM_laser.inp',	# Laser file
	'local_length':1,		# The length that laser moves inside the local model (millimeters)
}
MS_GLB = {
	'type':'track',	# single|layer|track ; how global ODBs are saved
}
PRC = {	# Precision values for rounding numbers where needed
	'time':8,	# number of digits for rounding time
	'space':7,	# number of digits for rounding space
}
TPL = {	# Templates
	'script':'_pycode_locals.py',
}

# read the laser file
laser_events = lsr.LaserEvents(MS_LCL['laser'])
local_events = lsr.LocalEvents(laser_events, MS_LCL, MS_GLB['type'], PRC)
local_events.find_tracks()
# OLD
# laser_data = lsr.LaserEvents(MS_LCL['laser'], MS_LCL['local_length'])
# laser_data.find_locals(MS_LCL['xlim'],MS_LCL['mid_points'],PRC['time'],PRC['space'])

for track in local_events.tracks:
	pycode = inpr.ParallelTracks(TPL['script'])
	pycode.set_localrange(track['local_first_id'], track['local_last_id'], track['id'])
	pycode.write_file(track['id'])

print('Done!')