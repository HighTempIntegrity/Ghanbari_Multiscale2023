from time import time
import subprocess
import pandas as pd

def runAbaqus(job, input, system):
	platform = system['platform']
	cpus = system['cpus']
	
	if platform == 'win':
		cmd_frt = 'ifortvars intel64\r\n'
		cmd_job = 'abaqus job=%s input=%s cpus=%i interactive ask_delete=OFF\r\n'%(job, input, cpus)
		cmd = cmd_frt + ';' + cmd_job
		process = subprocess.Popen('cmd.exe', stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=None, shell=False)
		out = process.communicate(cmd.encode('utf-8', 'ignore'))[0]
		print(out.decode('utf-8', 'ignore'))
		
	elif platform == 'lnx':
		args = ['abaqus', 'job='+job, 'input='+input, 'cpus='+str(cpus)]
		process = subprocess.Popen(args)
		process.communicate()

def runLocal(job, input, subroutine, globalmodel, system):
	platform = system['platform']
	cpus = system['cpus']

	if platform == 'win':
		cmd_frt = 'ifortvars intel64\r\n'
		cmd_job = 'abaqus job=%s input=%s user=%s globalmodel=%s cpus=%i interactive ask_delete=OFF\r\n'%(job, input, subroutine, globalmodel, cpus)
		cmd = cmd_frt + ';' + cmd_job
		process = subprocess.Popen('cmd.exe', stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=None, shell=False)
		out = process.communicate(cmd.encode('utf-8', 'ignore'))[0]
		print(out.decode('utf-8', 'ignore'))
		
	elif platform == 'lnx':
		args = ['abaqus', 'job='+job, 'input='+input,'user='+subroutine,'globalmodel='+globalmodel,'cpus='+str(cpus)]
		process = subprocess.Popen(args)
		process.communicate()

def contGlobal(job, input, oldjob, system):
	platform = system['platform']
	cpus = system['cpus']

	if platform == 'win':
		cmd_frt = 'ifortvars intel64\r\n'
		cmd_job = 'abaqus job=%s input=%s oldjob=%s cpus=%i interactive ask_delete=OFF\r\n'%(job, input, oldjob, cpus)
		cmd = cmd_frt + ';' + cmd_job
		process = subprocess.Popen('cmd.exe', stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=None, shell=False)
		out = process.communicate(cmd.encode('utf-8', 'ignore'))[0]
		print(out.decode('utf-8', 'ignore'))
		
	elif platform == 'lnx':
		args = ['abaqus', 'job='+job, 'input='+input, 'oldjob='+oldjob, 'cpus='+str(cpus)]
		process = subprocess.Popen(args)
		process.communicate()

def timeStamp(ref_time):
	m,s = divmod(time()-ref_time,60)
	h,m = divmod(m,60)
	return('{:.0f}:{:02.0f}:{:06.3f}'.format(h, m, s))

class TimeLog:
	def __init__(self, time_file_dir, indent_string):
		self.time_file = time_file_dir	# Relative path of the time file
		self.time_df = pd.DataFrame(columns=['seconds','duration','message'])	# For writing a clean log
		self.in_s = indent_string	# String used to indent messages
		self.init_time = time()	# Timestamp for the beginning of the script
		self.start_time = time()	# Timestamp for the beginning of a code block
		self.first_log = True	# To track creation of log file

	def start(self):
		self.start_time = time()
		
	def append(self, message, in_i):
		new_row = {'seconds':time()-self.start_time, 'duration':timeStamp(self.start_time), 'message':message}
		self.time_df = self.time_df.append(new_row, ignore_index=True)
		log_line = '%s%s - %s'%(self.in_s*in_i, message, timeStamp(self.start_time))
		print(log_line)
		
		if self.first_log:
			with open(self.time_file+'.log', 'w') as file:
				file.write(log_line+'\n')
			self.first_log = False
		else:
			with open(self.time_file+'.log', 'a') as file:
				file.write(log_line+'\n')
	
	def closure(self):
		log_line = '%s %s'%('\nScript executed in', timeStamp(self.init_time))
		print(log_line)
		with open(self.time_file+'.log', 'a') as file:
			file.write(log_line+'\n')
		self.time_df.to_csv(self.time_file+'.csv', index=False)
