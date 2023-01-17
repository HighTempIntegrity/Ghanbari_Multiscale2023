# Ghanbari_Multiscale2023

This repository contains the input files and python scripts used to conduct the simulations presented in the following study: https://doi.org/tobedetermined
If you benefit from this work please include a reference to above study.

## 4. Finite element thermal modelling of LPBF
The files under `sec4_calibration_sampleT2` were used to run different probe simulations for calibration of two modelling parameters alpha and h_p. The python script `_pycode_experiment.py` creats and runs different simulations based on variables provided in `2_exp.csv`.

`sec4_validateT3` contains the input files for running a similar model for sample T3 using the result of above calibration. Here, only `1_input.inp` and `1_subroutine.f` are required to run the Abaqus job. An example of the submission command is provided in `0_run_abq.sh`.

## 5. Multiscale approach
The simulations files for verification of the multiscale approach are listed under the following directories.
- `sec5_verification_reference` a highly refined static mesh used for verifying the results. Use `_pycode_globals.py` to run the simulation.
- `sec5_verification_global` the global model using coarse discretization. Use `_pycode_globals.py` to run the simulation.
- `sec5_verification_locals` sequence of local models which use the output of the global model to recalculate the temperature profiles around the moving laser. Make sure the ODB files from the global model are placed in this directory before starting the calculations. The simulations for 9 tracks can be conducted in parallel using `0_run_batch.sh`.

The simulation files for the multiscale model used to compare with the probe simulation in the previous section are presented under
- `sec5_validation_global` coarse global model. The python script `_pycode_globals.py` is used to run the simulation.
- `sec5_validation_locals` refinement using local models. The global ODBs need to be placed in this directory before starting the simulations with `0_run_batch_t*.sh`


