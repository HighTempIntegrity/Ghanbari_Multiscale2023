from time import time
import subprocess
import pandas as pd
import sys

STG = { # Settings
	'indent_string':'   ',	# Used for indenting the output info in command line
}

# def runAbaqus(job, input, system):
def runAbaqus(system, **kwargs):
	# Get the necessary input variables
	arg_list = [system['command']]
	for key in kwargs:
		arg_list.append('%s=%s'%(key,kwargs[key]))
	
	if  sys.platform == 'win32':
		command_frt = 'ifortvars intel64\r\n'
		command_job = '%s cpus=%i ask_delete=OFF\r\n'%(' '.join(arg_list), system['cpus'])
		command = command_frt + ';' + command_job
		process = subprocess.Popen('cmd.exe', stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=None, shell=False)
		out = process.communicate(command.encode('utf-8', 'ignore'))[0]
		print(out.decode('utf-8', 'ignore'))
		
	elif sys.platform == 'linux':
		arg_list.append('cpus=%i'%(system['cpus']))
		process = subprocess.Popen(arg_list)
		process.communicate()

class TimeLog:
	def __init__(self, time_file_dir):
		self.time_file = time_file_dir	# Relative path of the time file
		self.time_df = pd.DataFrame(columns=['seconds','duration','message'])	# For writing a clean log
		self.in_s = STG['indent_string']	# String used to indent messages
		self.in_i = 0	# Level of indentation
		self.init_time = time()	# Timestamp for the beginning of the script
		self.start_times = [time()]	# List of timestamps at the beginning of code blocks
		self.first_log = True	# To track creation of log file

	def start(self):
		self.start_times.append(time())
		
	def in_left(self):
		self.in_i-=1
		
	def in_right(self):
		self.in_i+=1
		
	def in_str(self):
		return self.in_i*self.in_s
		
	def append(self, message):
		cur_time = self.start_times.pop(-1)
		cur_stamp = timeStamp(cur_time)
		df_new_row = pd.DataFrame.from_dict({'seconds':[time()-cur_time], 'duration':[cur_stamp], 'message':[message]})
		self.time_df = pd.concat([self.time_df, df_new_row])
		log_line = '%s%s - %s'%(self.in_s*self.in_i, message, cur_stamp)
		print(log_line)
		
		if self.first_log:
			with open(self.time_file, 'w') as file:
				file.write(log_line+'\n')
			self.first_log = False
		else:
			with open(self.time_file, 'a') as file:
				file.write(log_line+'\n')
	
	def closure(self):
		log_line = '%s %s'%('\nScript executed in', timeStamp(self.init_time))
		print(log_line)
		with open(self.time_file, 'a') as file:
			file.write(log_line+'\n')
		file_name_csv = '.'.join(self.time_file.split('.')[:-1])+'.csv'
		self.time_df.to_csv(file_name_csv, index=False)

def timeStamp(ref_time):
	m,s = divmod(time()-ref_time,60)
	h,m = divmod(m,60)
	return('{:.0f}:{:02.0f}:{:06.3f}'.format(h, m, s))
