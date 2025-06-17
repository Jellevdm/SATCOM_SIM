
import csv
import os
import pandas as pd
import numpy as np

'''
1. Merge pico files into one CSV file. - merge_pico
2. Find start and end of jitter segment.
3. Trim the data to only include the jitter segment and shift time scale and make csv file with only the jitter segment.
4. Find BER.

'''

def merge_pico(folderpath, filename, number_of_files=None, output_file_path=None, sampling_frequency=100000):

    def read_csv(file_path, delimiter=';'):
        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=delimiter)
            data = [row for row in reader]
        return data

    if output_file_path is None:
        print("Error: no output file path specified.")
        return

    # If number_of_files is not specified, count all pico files in the folder
    if number_of_files is None:
        print("No number of files specified. Merging all pico files in the folder.")
        number_of_files = len([f for f in os.listdir(folderpath) if f.startswith(f'{filename}_') and f.endswith('.csv')])

    output_data = [] #[["Time", "Channel B", "Channel D"]]  # Initialize with header

    for i in range(number_of_files):  # 0-tot
        csv_file_path = f'{folderpath}/{filename}_{i + 1:03}.csv'  # Format i+1 as a zero-padded 3-digit number
        csv_data = read_csv(csv_file_path)
        print(f"Saving {csv_file_path}")

        for row in csv_data[3::int(10000000/sampling_frequency)]:  # Start from the 4th row and take every xth row, depending on the sampling frequency
            row = [value.replace(',', '.') if isinstance(value, str) else value for value in row]  # Replace commas with dots
            row[0] = float(i) + float(row[0]) + 5  # Add i to the first value in each row
            row[0] = str(float(row[0]) / 1000)  # Divide the first column by 1000
            output_data.append(row)


    # Writing rows to a new CSV file
    with open(output_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(output_data)


    print(f"Data written to {output_file_path}")





def find_transition_points(picodata, noise_tolerance):

    data = pd.read_csv(picodata, header=None)

    t_values = pd.to_numeric(data.iloc[:, 0], errors='coerce').fillna(0)  # time values - ensure numeric
    V_values = pd.to_numeric(data.iloc[:, 2], errors='coerce').fillna(0)  # received voltage values - ensure numeric

    V_above_tolerance = V_values > noise_tolerance

    start_index = None
    for i in range(len(V_above_tolerance) - 9):
        if all(V_above_tolerance[i:i + 10]):
            start_index = i
            break
    
    #print(f"Start time: {t_values[start_index]}")

    end_index = None
    constant_value = V_values[V_values > noise_tolerance].iloc[-1] 
    for i in range(len(V_values) - 1, start_index, -1):
        if V_values[i] > noise_tolerance and not(np.isclose(V_values[i], constant_value, atol=noise_tolerance)):
            end_index = i
            break

    #print(f"End time: {t_values[end_index]}")

    return start_index, end_index

def trim_data(picodata, start_index, end_index, output_file_path):
    
    data = pd.read_csv(picodata, header=None)

    trimmed_data = data.iloc[start_index:end_index + 1].copy()

    # Shift the time scale so that it starts from 0
    #trimmed_data.iloc[:, 0] = pd.to_numeric(trimmed_data.iloc[:, 0], errors='coerce') - pd.to_numeric(trimmed_data.iloc[0, 0], errors='coerce')

    # Save the trimmed data to the specified output file
    trimmed_data.to_csv(output_file_path, index=False, header=False)
    
def find_BER(picodata, bit_length):
    data = pd.read_csv(picodata, header=None)

    # Ensure numeric values
    col_B = pd.to_numeric(data.iloc[:, 1], errors='coerce').fillna(0)
    col_D = pd.to_numeric(data.iloc[:, 2], errors='coerce').fillna(0)

    # Calculate averages for each bit_length segment
    bits = []
    voltages = []
    count = 0
    for i in range(0, len(data), bit_length):
        avg_B = col_B[i:i + bit_length].mean()
        avg_D = col_D[i:i + bit_length].mean()
        voltages.append([avg_B, avg_D])
        sent = 1 if avg_B > noise_tolerance else 0
        received = 1 if avg_D > noise_tolerance else 0
        bits.append([sent, received])
        if count < 100:
            print([sent, received])
            count += 1

    # Print the last 100 sent bits
    #print("Last 100 sent bits:", [sent for sent, _ in bits[-100:]])

    BER = sum(1 for sent, received in bits if sent != received) / len(bits)
    print(f"BER: {BER}")

def find_BER2(picodata, bit_length):
    data = pd.read_csv(picodata, header=None)

    





""" Usage example """

# 1. Merge pico files into one CSV file

folderpath = 'trial_1305' # Path to the folder contatining pico files
filename = 'trial_1305'  # Base name of the pico files - excluding '_0001.csv' etc.
number_of_files = None  # Number of pico files to read within folder. If None, all files are read.
output_file_path = 'testprbs.csv'  # Path to save the merged CSV file
sampling_frequency = 100000  # Desired sampling frequency of pico data - in Hz (100 Hz to 10 MHz)



merge = True

if merge:
    merge_pico(folderpath, filename, number_of_files, output_file_path, sampling_frequency)



# 2. Find start and end of jitter segment.

noise_tolerance = 0.5  # Noise range (in volts) - calculated from noise.py
    
start, end = find_transition_points('testprbs.csv', noise_tolerance)
print(f"Start index: {start}, End index: {end}")


# 3. Trim the data to only include the jitter segment and shift time scale.

output_file_path = 'trimmed_test_prbs.csv'

trim_data('testprbs.csv', start, end, output_file_path)

# 4. Find BER.

bit_length = 20 # How many datapoints for each bit of sent information

find_BER('trimmed_test_prbs.csv', bit_length)
