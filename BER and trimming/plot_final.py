import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the data
df = pd.read_csv("BER and trimming/results.csv", skiprows=1, names=["std", "mean", "threshold", "BER"])

# Sort and format
df.sort_values(by=["std", "mean", "threshold"], inplace=True)
df["mean_str"] = df["mean"].map(lambda x: f"{x:.2f}")
df["x_label"] = df.apply(lambda row: f"μ={row['mean_str']}, σ={row['std']:.2f}", axis=1)

# Unique groupings
thresholds = sorted(df["threshold"].unique())
stds = sorted(df["std"].unique())

# Use a blue-to-red colormap
cmap = plt.cm.coolwarm  # or plt.cm.bwr
colors = cmap(np.linspace(0, 1, len(thresholds)))  # gradient from blue to red

# Set up plot
plt.figure(figsize=(14, 6))

x_labels = []
x_ticks = []
x_pos = 0

# For each std group
for std in stds:
    df_std = df[df["std"] == std]
    means = sorted(df_std["mean"].unique())
    
    for thresh_i, thresh in enumerate(thresholds):
        df_group = df_std[df_std["threshold"] == thresh]
        df_group = df_group.set_index("mean").reindex(means).reset_index()
        y = df_group["BER"].values
        x = list(range(x_pos, x_pos + len(means)))
        plt.plot(x, y, marker=None, label=f"Threshold = {thresh:.2f} V" if std == stds[0] else "", color=colors[thresh_i])
    
    # Store x-axis labels and ticks
    x_labels.extend([f"σ={std:.2f} - μ={m:.2f}" for m in means])
    x_ticks.extend(range(x_pos, x_pos + len(means)))
    x_pos += len(means) + 1  # spacing between groups

# Final formatting
plt.xticks(ticks=x_ticks, labels=x_labels, rotation=75, ha='right')
# plt.xlabel("Mean (μ), Grouped by Std (σ)")
plt.ylabel("BER (-)")
# plt.title("BER vs Mean, Grouped by Std – One Curve per Threshold (Blue to Red)")
plt.grid(True)
plt.legend(ncol=2)
plt.tight_layout()
plt.show()
