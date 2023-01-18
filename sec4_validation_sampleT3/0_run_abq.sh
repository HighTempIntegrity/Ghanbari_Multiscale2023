#BSUB -J valT3
#BSUB -n 12
#BSUB -W 72:00
#BSUB -N
#BSUB -R 'rusage[mem=2048,scratch=2000]'
#BSUB -R 'select[model=XeonGold_5118]'

abaqus job=run_Exp000 input=1_input user=1_subroutine cpus=12 scratch=$TMPDIR
