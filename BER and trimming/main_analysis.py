import pandas as pd
import numpy as np

def find_transition_points(file_path, threshold=1):
    # Read the CSV file
    data = pd.read_csv(file_path, header=None)
    
    # Extract the x values (first column) and curve values (third column)
    x_values = pd.to_numeric(data.iloc[:, 0], errors='coerce').fillna(0)  # Convert to numeric, replace invalid values with 0
    curve = pd.to_numeric(data.iloc[:, 2], errors='coerce').fillna(0)  # Convert to numeric, replace invalid values with 0
    
    # Calculate the difference between consecutive points
    diff = np.abs(np.diff(curve))
    
    # Find indices where the difference exceeds the threshold
    transition_indices = np.where(diff > threshold)[0]
    
    if len(transition_indices) == 0:
        print("No significant transitions found.")
        return None, None, data
    
    # Find the start and end of the non-constant region
    start_index = transition_indices[0]
    end_index = transition_indices[-1]
    
    # Get the corresponding x values
    start_x = x_values.iloc[start_index]
    end_x = x_values.iloc[end_index + 1]  # +1 because diff reduces the length by 1
    
    # Slice the data and shift the first column to start at 0
    trimmed_data = data.iloc[start_index:end_index + 2].copy()
    trimmed_data.iloc[:, 0] = pd.to_numeric(trimmed_data.iloc[:, 0], errors='coerce').fillna(0)  # Ensure numeric values
    trimmed_data.iloc[:, 0] -= start_x  # Shift the first column
    
    return start_x, end_x, trimmed_data

# Example usage
file_path = "pico_total.csv"  # Replace with the path to your CSV file
start, end, trimmed_data = find_transition_points(file_path, threshold=1)
if start is not None and end is not None:
    print(f"The curve starts to change at x = {start} and becomes constant again at x = {end}.")
    # Save the trimmed data to a new CSV file
    trimmed_data.to_csv("pico_total_trimmed.csv", index=False, header=False)
    print("Trimmed data saved to 'pico_total_trimmed.csv'.")
else:
    print("No significant transitions found.")



def scale_time_series(file_path, start, end):
    # Read the CSV file, ensuring the header is skipped and not treated as data
    data = pd.read_csv(file_path, skiprows=1)
    
    # Extract the time values (first column)
    time_values = pd.to_numeric(data.iloc[:, 0], errors='coerce').fillna(0)
    
    # Scale the time values such that the total time equals end - start
    total_time = end - start
    min_time = time_values.min()
    max_time = time_values.max()
    scaled_time = (time_values - min_time) / (max_time - min_time) * total_time
    
    # Replace the first column with the scaled time values
    data.iloc[:, 0] = scaled_time
    
    # Read the header from the original file
    with open(file_path, 'r') as f:
        header = f.readline().strip()
    
    # Save the scaled data to a new CSV file with the same header
    scaled_file_path = file_path.replace(".csv", "_scaled.csv")
    header_columns = header.split(",")  # Split the header string into a list of column names
    data.to_csv(scaled_file_path, index=False, header=header_columns)
    print(f"Scaled time series saved to '{scaled_file_path}'.")
    
# Example usage
if start is not None and end is not None:
    scale_time_series("fsm.csv", start, end)

