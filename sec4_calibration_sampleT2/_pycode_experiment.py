# Use modern python to run this. Notepadd++ F5 command:
# cmd /k cd /d $(CURRENT_DIRECTORY) && python $(FULL_CURRENT_PATH)

import pandas as pd
import _pylib.tools as tl

class TextFile:
	def __init__(self, template_name, exp_name):
		self.exp_name = exp_name
		self.format = template_name.split('.')[-1]
		self.function = '_'+'_'.join(template_name.split('_')[1:])
		
		with open(template_name, 'r') as file:
			self.contents = file.readlines()
	
	def swap_line(self, old_line, new_line):
		search_id = self.contents.index(old_line+'\n')
		self.contents[search_id] = new_line+'\n'
	
	def write_file(self):
		self.filename = self.exp_name + self.function
		with open(self.filename,'w+') as file:
			for line in self.contents:
				file.write(line)

STG = {	# Settings
	'model_tag':'Exp',			# This will be used in the beginning of all input files for local models
	'zeros':3,
	'time_file':'9_time.log',
}
TPL = {	# Templates
	'experiment':'2_exp.csv',
	'tableCollection':'2_AM_tableCollections.inp',
	'step':'2_step.inp',
	'subroutine':'2_subroutine.f',
	'input':'2_input.inp',
}
SYS = { # For running abaqus
	# 'command':'abaqus',
	# 'cpus':12,			# Number of logical processors to run the simulations
}
time_log = tl.TimeLog(STG['time_file'])

# Read the experimental design vectors
exp_df = pd.read_csv(TPL['experiment'])

time_log.in_right()
for exp_id, exp_info  in exp_df.iterrows():
	# exp_id:	index of experiments starting from 0
	# exp_info:	contatining individual setting of current experiment
	time_log.start()
	
	exp_id = int(exp_info['id'])
	exp_name = '%s%s'%(STG['model_tag'],str(exp_id).zfill(STG['zeros']))

	# Create new table collection file
	tabcol = TextFile(TPL['tableCollection'], exp_name)
	tabcol.swap_line(
		old_line='0.65',
		new_line='%s'%(str(exp_info['absorption'])))
	tabcol.write_file()
	
	# Create new step file
	exp_info['convection']
	step = TextFile(TPL['step'], exp_name)
	step.swap_line(
		old_line='AM_Model_AllBuildParts , FFS , 25 , 30e-6',
		new_line='AM_Model_AllBuildParts , FFS , 25 , %s'%(str(exp_info['convection']*1e-6)))
	step.write_file()
	
	# Create new subroutine file
	sub = TextFile(TPL['subroutine'], exp_name)
	sub.swap_line(
		old_line='      CHARACTER(*), PARAMETER :: COUTPUT = \'run_2track.csta\'',
		new_line='      CHARACTER(*), PARAMETER :: COUTPUT = \'run_%s.csta\''%(exp_name))
	sub.write_file()
	
	# Create new input file
	input = TextFile(TPL['input'], exp_name)
	input.swap_line('*Include,input=2_AM_tableCollections.inp',
		'*Include,input=%s'%(tabcol.filename))
	input.swap_line('*Include,input=2_step.inp',
		'*Include,input=%s'%(step.filename))
	input.write_file()
	

	time_log.append('Prepared input files for experiment %i'%(exp_id))
	
	# Run simulation
	time_log.start()
	abaqus_tags = {
		'job':'run_%s'%(exp_name),
		'input':input.filename,
		'user':sub.filename,
	}
	tl.runAbaqus(system=SYS,**abaqus_tags)
	time_log.append('Simulation %i finished'%(exp_id))
time_log.in_left()

time_log.closure()
