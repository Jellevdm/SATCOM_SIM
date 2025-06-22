import os
import numpy as np
import matplotlib.pyplot as plt
import tomllib as tom
from functions_classes import *
from tqdm import tqdm

# Constants
R = 50  # Ohm, for converting V to W
threshold_voltages = np.arange(0.05, 0.85, 0.05)  # V
threshold_powers = threshold_voltages**2 / R      # W

# Input parameters
sigmas = [0.1, 0.2, 0.3, 0.4, 0.5]
means = [0, 0.1, 0.2, 0.3, 0.4]
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
            signal_sim = Signal_simulation(config, file_name, "inputs_design", "inputs_signal", L_c=1)
            
            ber_list_th = []
            ber = signal_sim.generate_time_sig_square()  # Assumes it takes threshold power
            ber_results.append(((sigma, mean), ber))
            pbar.update(1)

# Plotting
plt.figure(figsize=(12, 6))
colors = plt.cm.coolwarm(np.linspace(0, 1, len(threshold_voltages)))

x_labels = []
for (sigma, mean), bers in ber_results:
    label = f"$\\sigma$={sigma:.2f}, $\\mu$={mean:.2f}"
    x_labels.append(label)

for i, (thresh_v, color) in enumerate(zip(threshold_voltages, colors)):
    plt.plot(range(len(ber_results)),
             [ber_list[i] for (_, ber_list) in ber_results],
             label=f"Threshold = {thresh_v:.2f} V",
             color=color)

plt.xticks(range(len(ber_results)), x_labels, rotation=45, ha='right')
plt.ylabel("BER [-]")
plt.title("BER vs Thresholds for Varying σ and μ")
plt.grid(True)
plt.legend(loc="center left", bbox_to_anchor=(1, 0.5), ncol=1)
plt.tight_layout()
plt.show()