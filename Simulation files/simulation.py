# Import needed packages
import os
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
import tomllib as tom

from functions_classes import *

file_name = "FSM inputs/04-30-inputs/04_30-fsm-std(0.5)-mean(0.2).csv"                     # Change this to read different inputs
os.chdir('Simulation files')                                                               # Change working directory to the folder where the script is located

# Configure toml file and initialise link budget
#-----------------------------------------------
config_path = "config.toml"

with open(config_path, 'rb') as f:          # 'rb' mode is required for tomllib
    config = tom.load(f)                    # Use tomllib to load the file

# # Results of time simulation
# #-----------------------------------------------
# L_c = 10 ** (link_budget_des["Total losses const [db]"] / 10)  # Constant loss
L_c = 1         #Due to incorrect link budget constant losses set to zero
signal_sim = Signal_simulation(config, file_name, "inputs_design", "inputs_signal", L_c)     # Initialse time signal simulation class    
result_sim1 = signal_sim.generate_time_sig_square()



