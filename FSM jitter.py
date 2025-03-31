import FreeSimpleGUI as sg
import serial.tools.list_ports
import threading
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import queue
import csv

# Decrease this to make the FSM movement smoother
update_time = 0.0005

ports = serial.tools.list_ports.comports()
portList = [port.name for port in ports]

fsmPort = None

# Initialize the queue for real-time plotting
plot_length = 500  # Number of points to display in the plot (adjust as needed)
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

# Function to send data to DAC
def sendDAC(d, channel, mode):
    global fsmPort
    if fsmPort:
        packet = bytearray(3)
        packet[2] = (d & 0xFF) | 0b10000000
        packet[1] = ((d >> 7) & 0xFF) | 0b10000000
        packet[0] = (d >> 14) & 0x03
        packet[0] |= (channel << 4)
        packet[0] |= (mode << 2)
        fsmPort.write(packet)

# GUI Layout
sg.theme('DarkAmber')
windowLayout = [
    [sg.Text('Noise std:'), sg.InputText('1', key='noise_std', size=(5,1)), 
     sg.Text('Noise mean:'), sg.InputText('0', key='noise_mean', size=(5,1))],
    [sg.Button('Start Both')], [sg.Button('Stop Both')],
    [sg.Canvas(key='-CANVAS-', size=(800, 600))]
]

window = sg.Window('FSM DIM - GUI', windowLayout, finalize=True)

# Reading the ports
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

running_x = False
running_y = False

# Track time for x and y independently
global_time_x = 0
global_time_y = 0

def white_noise_signal(mean, std, running_flag, queue, channel):
    global global_time_x, global_time_y

    # Define DAC limits
    min_x1, min_x2 = 0x740D, 0x923D  # X limits (29709 - 37437)
    min_y1, min_y2 = 0x70E4, 0x927C  # Y limits (28900 - 37500)

    # Detector center
    offset_x = 0x84D0                # () Offset Gregoire and I have determined early on
    offset_y = 0x7FBC                # () Offset Gregoire and I have determined early on

    # Maximum Amplitude Ranges
    max_amp_x = min((min_x2-offset_x), (offset_x-min_x1))       # Due to slight misalignment we choose which maximum amplitude we can use
    max_amp_y = min((min_y2-offset_y), (offset_y-min_y1))       # Due to slight misalignment we need to ensure amplitudes stay within range

    while running_flag():
        noise_value = np.random.normal(mean, std)  # Generate white noise value
        #TODO: From noise statistic value to DAC value for FSM, right now still scaling values
        if channel == 0:  # X Channel
            noise_value = max(min((offset_x + max_amp_x * noise_value), min_x2), min_x1)            # Cap it at max amplitude
            global_time_x += 0.01
            sendDAC(noise_value, 0, 1)
            queue.put((global_time_x, noise_value))
            x_writer.writerow([global_time_x, noise_value])  # Log X data
        
        elif channel == 1:  # Y Channel
            noise_value = max(min((offset_y + max_amp_y * noise_value), min_y2), min_y1)            # Cap it at max amplitude
            global_time_y += 0.01
            sendDAC(noise_value, 1, 1)
            queue.put((global_time_y, noise_value))
            y_writer.writerow([global_time_y, noise_value])  # Log Y data
        
        time.sleep(0.01)  # Update rate: 10 ms

# Functions to start and stop noise for X and Y axes
def start_x_noise():
    global running_x
    if not running_x:
        running_x = True
        noise_std = float(values['noise_std'])      # Get std from gui
        noise_mean = float(values['noise_mean'])    # Get mean from gui
        threading.Thread(target=white_noise_signal, args=(noise_mean, noise_std, lambda: running_x, data_queue_x, 0), daemon=True).start()

def stop_x_noise():
    global running_x, x_log_file
    running_x = False
    x_log_file.close()  # Close file

def start_y_noise():
    global running_y
    if not running_y:
        running_y = True
        noise_std = float(values['noise_std'])      # Get std from gui
        noise_mean = float(values['noise_mean'])    # Get mean from gui
        threading.Thread(target=white_noise_signal, args=(noise_mean, noise_std, lambda: running_y, data_queue_y, 1), daemon=True).start()

def stop_y_noise():
    global running_y, y_log_file
    running_y = False
    y_log_file.close()  # Close file

# Matplotlib real-time plot setup
time_data_x = deque(maxlen=plot_length)
noise_data_x = deque(maxlen=plot_length)
time_data_y = deque(maxlen=plot_length)
noise_data_y = deque(maxlen=plot_length)

def update_plot():
    while not data_queue_x.empty():
        current_time, sine_value = data_queue_x.get()
        time_data_x.append(current_time)
        noise_data_x.append(sine_value)

    while not data_queue_y.empty():
        current_time, sine_value = data_queue_y.get()
        time_data_y.append(current_time)
        noise_data_y.append(sine_value)

    # Update individual X and Y noise plots
    ax[0,0].clear()
    ax[0,0].plot(time_data_x, noise_data_x, 'r-', label="X Signal")
    ax[0,0].set_title("X Noise signal")
    ax[0,0].set_xlabel(f'Running time')
    ax[0,0].set_ylabel(f'DAC value')
    ax[0,0].set_ylim(0x740D, 0x923D)
    ax[0,0].legend()

    ax[1,0].clear()
    ax[1,0].plot(time_data_y, noise_data_y, 'b-', label="Y Signal")
    ax[1,0].set_title("Y Noise Signal")
    ax[1,0].set_xlabel(f'Running time')
    ax[1,0].set_ylabel(f'DAC value')
    ax[1,0].set_ylim(0x70E4, 0x927C)
    ax[1,0].legend()

    if np.shape(noise_data_x) == np.shape(noise_data_y):
        ax[0,1].clear()
        ax[0,1].scatter(noise_data_x, noise_data_y, label='Offset due to noise')
        ax[0,1].scatter(0x84D0, 0x7FBC, label='Mirror centre', color='red')
        ax[0,1].set_title("FSM Pattern")
        ax[0,1].set_xlabel(f'X DAC Value')
        ax[0,1].set_xlim(0x740D, 0x923D)
        ax[0,1].set_ylabel(f'Y DAC Value')
        ax[0,1].set_ylim(0x70E4, 0x927C)

    # Redraw the figure
    canvas.draw()

# Function to draw the matplotlib figure on the PySimpleGUI Canvas
def draw_figure(canvas_elem, fig):
    figure_canvas_agg = FigureCanvasTkAgg(fig, canvas_elem.TKCanvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

# Create the Matplotlib figure with subplots
fig, ax = plt.subplots(2, 2, figsize=(8, 12))

# Draw the Matplotlib figure in the Canvas element
canvas = draw_figure(window['-CANVAS-'], fig)

# Main event loop
while True:
    event, values = window.read(timeout=10)

    # Update plot
    update_plot()

    if event == sg.WIN_CLOSED:
        break
    if event == 'Start Both':
        start_x_noise()
        start_y_noise()
    if event == 'Stop Both':
        stop_x_noise()
        stop_y_noise()

# Cleanup
window.close()
if fsmPort:
    fsmPort.close()

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