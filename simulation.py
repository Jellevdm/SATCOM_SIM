# Import needed packages
from os import link
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
import tomllib as tom

from functions_classes import *

file_name = "FSM inputs/04-03-inputs/04_03-testing-std(0.3)-mean(0).csv"                   # Change this to read different inputs

# Configure toml file and initialise link budget
#-----------------------------------------------
config_path = "config.toml"
with open(config_path, 'rb') as f:          # 'rb' mode is required for tomllib
    config = tom.load(f)                    # Use tomllib to load the file

# Load a specific input file
#------
# optical_link_lect = OpticalLinkBudget(config, "inputs_lec", "losses_lec")           # Initialise optical link budget class for lecture example
optical_link_design = OpticalLinkBudget(config, "inputs_design", "losses_design")   # Initialise optical link budget class for our design                   
#-----------------------------------------------

# Results of link budget
#-----------------------------------------------
print(f'Design example:')
link_budget_des = optical_link_design.compute_link_budget()
for key in link_budget_des.keys():
    print(f"{key}: {link_budget_des[key]:.4f}")
#-----------------------------------------------

# Results of time simulation
#-----------------------------------------------
L_c = 10 ** ((link_budget_des["Total losses [dB]"] - link_budget_des["Pointing jitter loss [dB]"]) / 10)  # Constant loss: all link budget losses except for (jitter-induced) scintillation [dB]

signal_sim = Signal_simulation(config, file_name, "inputs_design", "inputs_signal", L_c)     # Initialse time signal simulation class    
result_sim = signal_sim.generate_time_sig()                                            # Run the function for generating time signal at Tx and Rx
result_pdf2ber = signal_sim.pdf2ber_plot()

# TODO: Fix the connection with link budget (Same input values)
# TODO: Fix the SNR calculation
# TODO: Fix correction noise addition




