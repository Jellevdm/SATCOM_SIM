import os
import numpy as np
import matplotlib.pyplot as plt
import tomllib as tom
from functions_classes import *
from tqdm import tqdm

# Constants
thresholds_pw = (np.arange(0.05, 0.85, 0.05)/3.8)*10e-3

# Input parameters
sigmas = [0.1, 0.2, 0.3, 0.4, 0.5]
means = [0.0, 0.1, 0.2, 0.3, 0.4]
base_path = "FSM inputs/04-30-inputs/"
os.chdir('Simulation files')
config_path = "config.toml"

# Load config
with open(config_path, 'rb') as f:
    config = tom.load(f)

ber_results = []

# Calculate total iterations for tqdm
total_iterations = len(sigmas) * len(means)

# Iterate with progress bar
with tqdm(total=total_iterations, desc="Running BER simulations") as pbar:
    for sigma in sigmas:
        for mean in means:
            file_name = f"{base_path}04_30-fsm-std({sigma})-mean({mean}).csv"

            optical_link_design = OpticalLinkBudget(config, "inputs_design", "losses_design")   # Initialise optical link budget class for our design                   
            link_budget_des = optical_link_design.compute_link_budget()
            L_c = 10 ** (link_budget_des["Total losses const [db]"] / 10)
            signal_sim = Signal_simulation(config, file_name, "inputs_design", "inputs_signal", L_c)

            ber_list_th = []
            ber = signal_sim.generate_time_sig_square(sigma, mean)
            ber_results.append(((sigma, mean), ber))
            pbar.update(1)

# Plotting
# Setup
threshold_voltages = np.arange(0.05, 0.85, 0.05)  # V
colors = plt.cm.coolwarm(np.linspace(0, 1, len(threshold_voltages)))

# Group data
sigmas = [0.1, 0.2, 0.3, 0.4, 0.5]
means = [0.0, 0.1, 0.2, 0.3, 0.4]

# Reorganize BER data
ber_matrix = [[] for _ in threshold_voltages]
x_labels = []
tick_positions = []

index = 0
for sigma in sigmas:
    for mean in means:
        label = f"σ={sigma:.2f} - μ={mean:.2f}"
        x_labels.append(label)
        tick_positions.append(index)

        # Pull out the BERs for each threshold at this (σ, μ)
        (_, ber_list) = ber_results.pop(0)
        for i in range(len(threshold_voltages)):
            ber_matrix[i].append(ber_list[i])
        index += 1

    # Add spacing after each σ group
    x_labels.append("")  # empty tick label
    tick_positions.append(index)
    for row in ber_matrix:
        row.append(np.nan)
    index += 1

# Plotting
plt.figure(figsize=(14, 6))
for i, (thresh_v, color) in enumerate(zip(threshold_voltages, colors)):
    plt.plot(range(len(x_labels)), ber_matrix[i], label=f"Threshold = {thresh_v:.2f} V", color=color)

plt.xticks(tick_positions, x_labels, rotation=75, ha='right')
plt.ylabel("BER [-]")
plt.title("BER vs Thresholds for Varying σ and μ")
plt.grid(True)
plt.legend(loc="center left", bbox_to_anchor=(1, 0.5), ncol=1)
plt.tight_layout()
plt.show()