# Import needed packages
import os
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
import tomllib as tom

from functions_classes import *

std = 0.5
mean = 0.0

base_path = "FSM inputs/04-30-inputs/"
os.chdir('Simulation files')
file_name = f"{base_path}04_30-fsm-std({std})-mean({mean}).csv"

# Configure toml file and initialise link budget
#-----------------------------------------------
config_path = "config.toml"

with open(config_path, 'rb') as f:          # 'rb' mode is required for tomllib
    config = tom.load(f)                    # Use tomllib to load the file

optical_link_design = OpticalLinkBudget(config, "inputs_design", "losses_design")   # Initialise optical link budget class for our design                   
link_budget_des = optical_link_design.compute_link_budget()

# # Results of time simulation
# #-----------------------------------------------
L_c = 10 ** (link_budget_des["Total losses const [db]"] / 10)
signal_sim = Signal_simulation(config, file_name, "inputs_design", "inputs_signal", L_c)     # Initialse time signal simulation class    
result_sim1 = signal_sim.generate_time_sig_square(std, mean)
x = signal_sim.pdf2ber_plot(0.1, 0.5)


