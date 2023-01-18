#BSUB -J track[1-9]
#BSUB -n 12
#BSUB -W 4:00
#BSUB -R 'rusage[mem=2048,scratch=2000]'
#BSUB -R 'select[model=XeonGold_6150]'
python 3_pycode_multiscale_track$LSB_JOBINDEX.py
