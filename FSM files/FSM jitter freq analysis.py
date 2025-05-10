import FreeSimpleGUI as sg
import serial.tools.list_ports
import threading
import numpy as np
import queue
import csv
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ===========================
# Configuration and Setup
# ===========================

update_time = 0.0005  # Smaller value = smoother movement
max_data_points = 500  # Max number of points to show at a time (increase this to show more points)

ports = serial.tools.list_ports.comports()
portList = [port.name for port in ports]

fsmPort = None

# Initialize queues for real-time plotting
data_queue_x = queue.Queue()
data_queue_y = queue.Queue()

# Open files for logging data
x_log_file = open("noise_x_data.csv", "w", newline="")
y_log_file = open("noise_y_data.csv", "w", newline="")

x_writer = csv.writer(x_log_file)
y_writer = csv.writer(y_log_file)

# Write headers
x_writer.writerow(["Time", "Value"])
y_writer.writerow(["Time", "Value"])

# ===========================
# DAC Communication Function
# ===========================

def sendDAC(d, channel, mode):
    """Send data to DAC via serial communication."""
    global fsmPort
    if fsmPort:
        packet = bytearray(3)
        packet[2] = (d & 0xFF) | 0b10000000
        packet[1] = ((d >> 7) & 0xFF) | 0b10000000
        packet[0] = (d >> 14) & 0x03
        packet[0] |= (channel << 4)
        packet[0] |= (mode << 2)
        fsmPort.write(packet)

# ===========================
# GUI Layout
# ===========================

sg.theme('DarkAmber')

# Matplotlib Figure for real-time plotting
fig, ax = plt.subplots()
ax.set_title("Real-time DAC Output")
ax.set_xlabel("Time (s)")
ax.set_ylabel("DAC Value")
(line_x,) = ax.plot([], [], label='X Data')
(line_y,) = ax.plot([], [], label='Y Data')
ax.legend()

canvas_elem = sg.Canvas(key='-CANVAS-', size=(800, 600))
layout = [
    [sg.Button('Start Both'), sg.Button('Stop Both')],
    [canvas_elem]
]

window = sg.Window('FSM DIM - GUI', layout, finalize=True)
canvas = FigureCanvasTkAgg(fig, window['-CANVAS-'].Widget)
canvas.get_tk_widget().pack()

# ===========================
# Serial Port Initialization
# ===========================

try:
    if portList:
        fsmPort = serial.Serial(portList[-1], 460800, timeout=0)
        sendDAC(0x7FFF, 0, 1)
    else:
        sg.popup("No available FSM port detected!")
        fsmPort = None
except IndexError:
    sg.popup("No available FSM port detected!")
    fsmPort = None

# ===========================
# Signal Generation Function (Adjusted for Real-Time Sync)
# ===========================

global_time = 0

def signal(running_flag, data_queue, channel):
    global global_time
    scale = 1
    fs = 400 # Hz (200 samples per second, which means 1 sample every 5ms)
    tend = 100  # Duration of the signal (in seconds)
    t = np.linspace(0, tend, fs * tend, endpoint=False)  # Create time vector
    data = (np.sin(2 * np.pi * 1 * t))  # Simulate signal with multiple frequencies
    
    # Normalize the data to fit in DAC range
    data_min, data_max = np.min(data), np.max(data)
    data_normalized = (data - data_min) / (data_max - data_min)

    while running_flag():
        if channel == 0:
            offset = 0x84D0
            max_amp = min((0x923D-0x84D0), (0x84D0-0x740D))
        elif channel == 1:
            offset = 0x7FBC
            max_amp = min((0x927C-0x7FBC), (0x7FBC-0x70E4))
        
        data_scaled = offset + scale * max_amp * (2 * data_normalized - 1) 

        for i in range(len(data_scaled)):
            if not running_flag():
                break
            else: 
                sendDAC(int(data_scaled[i]), channel, 1)
                data_queue.put((t[i], int(data_scaled[i]))) 
                global_time += 0.01
                time.sleep(0.001) 
            if channel == 0:
                x_writer.writerow([t[i], int(data_scaled[i])])
            else:
                y_writer.writerow([t[i], int(data_scaled[i])])
            
            

# ===========================
# Update Plot Function
# ===========================

x_data, y_data = [], []

def update_plot():
    global x_data, y_data
    
    # Fetch new data points from the queue
    while not data_queue_x.empty():
        new_x = data_queue_x.get()
        x_data.append(new_x)
        if len(x_data) > max_data_points:  # Keep the list size bounded
            x_data.pop(0)  # Remove the oldest data point
    
    while not data_queue_y.empty():
        new_y = data_queue_y.get()
        y_data.append(new_y)
        if len(y_data) > max_data_points:  # Keep the list size bounded
            y_data.pop(0)  # Remove the oldest data point
    
    # Update the plot with new data
    if x_data:
        line_x.set_data(*zip(*x_data))
    if y_data:
        line_y.set_data(*zip(*y_data))
    
    ax.relim()  # Recalculate limits for new data
    ax.autoscale_view()  # Automatically scale the view
    canvas.draw()

# ===========================
# Main Loop for Running the Signal and Plotting
# ===========================

running_x = False
running_y = False

def start_x_noise():
    global running_x
    if not running_x:
        running_x = True
        threading.Thread(target=signal, args=(lambda: running_x, data_queue_x, 0), daemon=True).start()

def stop_x_noise():
    global running_x
    running_x = False

def start_y_noise():
    global running_y
    if not running_y:
        running_y = True
        threading.Thread(target=signal, args=(lambda: running_y, data_queue_y, 1), daemon=True).start()

def stop_y_noise():
    global running_y
    running_y = False

# ===========================
# Main Event Loop
# ===========================

while True:
    event, _ = window.read(timeout=10)
    if event == sg.WIN_CLOSED:
        break
    if event == 'Start Both':
        start_x_noise()
        start_y_noise()
    if event == 'Stop Both':
        stop_x_noise()
        stop_y_noise()
    update_plot()

window.close()
if fsmPort:
    fsmPort.close()


# Close CSV files
x_log_file.close()
y_log_file.close()

def combine_csv_files(x_file, y_file, combined_file):
    """
    Combines two CSV files (X and Y data) into a single CSV file.
    Assumes both X and Y files have the same time order and same length.
    Writes a combined CSV with columns: Time, X Value, Y Value.
    """
    # Open the X and Y CSV files
    with open(x_file, 'r') as x_data, open(y_file, 'r') as y_data, open(combined_file, 'w', newline='') as combined_data:
        x_reader = csv.reader(x_data)
        y_reader = csv.reader(y_data)
        combined_writer = csv.writer(combined_data)
        
        # Skip headers
        next(x_reader)
        next(y_reader)
        
        # Write the header for the combined file
        combined_writer.writerow(["Time", "X Value", "Y Value"])
        
        # Read both files line by line and write to the combined CSV
        for x_row, y_row in zip(x_reader, y_reader):
            # Assuming both files have the same time format and order
            time = x_row[0]  # Time column from X CSV (we assume same time in both files)
            x_value = x_row[1]  # X value from X CSV
            y_value = y_row[1]  # Y value from Y CSV
            
            # Write the combined row
            combined_writer.writerow([time, x_value, y_value])

# Function call after stopping the noise generation
combine_csv_files('noise_x_data.csv', 'noise_y_data.csv', 'combined_noise_data_after.csv')

print("CSV files have been successfully combined into 'combined_noise_data_after.csv'.")
