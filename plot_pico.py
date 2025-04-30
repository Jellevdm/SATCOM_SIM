import pandas as pd

import matplotlib.pyplot as plt

# Load the CSV file
file_path = 'pico_total_trimmed.csv'  # Replace with your CSV file path
data = pd.read_csv(file_path)

# Ensure the CSV has at least 3 columns
if data.shape[1] < 3:
    raise ValueError("The CSV file must have at least 3 columns.")

# Extract columns
x = data.iloc[:, 0]
y1 = data.iloc[:, 1]
y2 = data.iloc[:, 2]

# Plot the data
plt.figure(figsize=(10, 6))
#plt.plot(x, y1, label='Curve 1', marker='o')
plt.plot(x, y2, label='Curve 2', marker='x')

# Add labels, title, and legend
plt.xlabel('X-axis')
plt.ylabel('Y-axis')
plt.title('Plot from CSV Data')
plt.legend()
plt.grid()

# Show the plot
plt.show()