#BSUB -J track[19-30]
#BSUB -n 3
#BSUB -W 24:00
#BSUB -N
#BSUB -R 'rusage[mem=2048,scratch=2000]'
#BSUB -R 'select[model=XeonGold_5118]'
python 3_pycode_multiscale_track$LSB_JOBINDEX.py
