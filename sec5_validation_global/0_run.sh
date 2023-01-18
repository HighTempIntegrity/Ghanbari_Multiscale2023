# BSUB -J Glb
# BSUB -n 12
# BSUB -W 120:00
# BSUB -N
# BSUB -R 'rusage[mem=1024,scratch=2000]'
# BSUB -R 'select[model=XeonGold_5118]'
python _pycode_globals.py
