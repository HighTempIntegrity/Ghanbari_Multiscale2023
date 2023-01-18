# BSUB -J fine
# BSUB -n 12
# BSUB -W 120:00
# BSUB -R 'rusage[mem=5158,scratch=10000]'
# BSUB -R 'select[model=XeonGold_6150]'
python _pycode_globals.py