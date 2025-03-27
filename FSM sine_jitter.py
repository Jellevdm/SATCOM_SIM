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
combined_data_queue = queue.Queue()  # Queue to store combined (X, Y) data

import csv

# Open files for logging data
x_log_file = open("sine_x_data.csv", "w", newline="")
y_log_file = open("sine_y_data.csv", "w", newline="")

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
    [sg.Text('X Frequency (Hz):'), sg.InputText('1', key='freq_x', size=(5,1)), sg.Text('Amplitude:'), sg.InputText('1', key='amp_x', size=(5,1)), sg.Button('Start X Sine'), sg.Button('Stop X Sine')],
    [sg.Text('Y Frequency (Hz):'), sg.InputText('1', key='freq_y', size=(5,1)), sg.Text('Amplitude:'), sg.InputText('1', key='amp_y', size=(5,1)), sg.Button('Start Y Sine'), sg.Button('Stop Y Sine')],
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

# Helper functions for jitter generation
def generate_jitter_amp(mean, std):
    return np.random.normal(mean, std)

def generate_jitter_freq(low, high):
    return np.random.uniform(low, high)

# Track time for x and y independently
global_time_x = 0
global_time_y = 0

# Function to generate sine wave with jitter and send data
def sine_wave_with_jitter(base_freq, base_amp, running_flag, queue, channel):
    global global_time_x, global_time_y

    # Define DAC limits
    min_x1, min_x2 = 0x740D, 0x923D  # X limits (29709 - 37437)
    min_y1, min_y2 = 0x70E4, 0x927C  # Y limits (28900 - 37500)

    # Compute center and amplitude limits
    offset_x = 0x84D0
    max_amplitude_x = min((0x923D-0x84D0),(0x84D0-0x740D))  # Half-range amplitude for X

    offset_y = 0x7FBC
    max_amplitude_y = min((0x927C-0x7FBC),(0x7FBC-0x70E4))  # Half-range amplitude for Y

    jitter_interval = 3  # Jitter every ... seconds
    prev_freq = base_freq

    # Start with exact base values (no jitter at first)
    first_cycle = True  

    while running_flag():
        if channel == 0:  # X Channel
            if first_cycle:  # First sine wave cycle uses exact base values
                jittered_freq = base_freq
                jittered_amp = base_amp
                first_cycle = False  # Next cycle can use jitter
            elif (global_time_x % jitter_interval) < 0.01:  # Apply jitter later
                jittered_freq = generate_jitter_freq(prev_freq * 0.8, prev_freq * 1.2)
                jitter_scale = generate_jitter_amp(0.95, 1.05)  # Random factor
                jittered_amp = max(0.1, min(base_amp * jitter_scale, 1.0))  
                prev_freq = jittered_freq  
            amplitude_x = int(max_amplitude_x * jittered_amp)
            sine_value = int(offset_x + amplitude_x * np.sin(2 * np.pi * jittered_freq * global_time_x))
            global_time_x += 0.01
            sendDAC(sine_value, 0, 1)
            queue.put((global_time_x, sine_value))
            x_writer.writerow([global_time_x, sine_value])  
        elif channel == 1:  # Y Channel
            if first_cycle:  
                jittered_freq = base_freq
                jittered_amp = base_amp
                first_cycle = False  
            elif (global_time_y % jitter_interval) < 0.01:  
                jittered_freq = generate_jitter_freq(prev_freq * 0.8, prev_freq * 1.2)
                jitter_scale = generate_jitter_amp(0.95, 1.05)  
                jittered_amp = max(0.1, min(base_amp * jitter_scale, 1.0))  
                prev_freq = jittered_freq  
            amplitude_y = int(max_amplitude_y * jittered_amp)
            sine_value = int(offset_y + amplitude_y * np.sin(2 * np.pi * jittered_freq * global_time_y))
            global_time_y += 0.01
            sendDAC(sine_value, 1, 1)
            queue.put((global_time_y, sine_value))
            y_writer.writerow([global_time_y, sine_value])  
        time.sleep(0.01)  

# Functions to start and stop sine waves for X and Y axes
def start_sine_x():
    global running_x
    if not running_x:
        running_x = True
        base_freq_x = float(values['freq_x'])  # Get frequency from GUI
        base_amp_x = float(values['amp_x'])    # Get amplitude from GUI
        threading.Thread(target=sine_wave_with_jitter, args=(base_freq_x, base_amp_x, lambda: running_x, data_queue_x, 0), daemon=True).start()

def stop_sine_x():
    global running_x, x_log_file
    running_x = False
    x_log_file.close()  # Close file

def start_sine_y():
    global running_y
    if not running_y:
        running_y = True
        base_freq_y = float(values['freq_y'])  # Get frequency from GUI
        base_amp_y = float(values['amp_y'])    # Get amplitude from GUI
        threading.Thread(target=sine_wave_with_jitter, args=(base_freq_y, base_amp_y, lambda: running_y, data_queue_y, 1), daemon=True).start()

def stop_sine_y():
    global running_y, y_log_file
    running_y = False
    y_log_file.close()  # Close file

# Matplotlib real-time plot setup
time_data_x = deque(maxlen=plot_length)
sine_data_x = deque(maxlen=plot_length)
time_data_y = deque(maxlen=plot_length)
sine_data_y = deque(maxlen=plot_length)

# Function to update the plot (use global_time for continuous time tracking)
def update_plot():
    while not data_queue_x.empty():
        current_time, sine_value = data_queue_x.get()
        time_data_x.append(current_time)
        sine_data_x.append(sine_value)

    while not data_queue_y.empty():
        current_time, sine_value = data_queue_y.get()
        time_data_y.append(current_time)
        sine_data_y.append(sine_value)

    # Update individual X and Y sine wave plots
    ax[0].clear()
    ax[0].plot(time_data_x, sine_data_x, 'r-', label="X Sine Wave")
    ax[0].set_title("X Sine Wave")
    ax[0].set_xlabel(f'Running time')
    ax[0].set_ylabel(f'DAC value')
    ax[0].set_ylim(0x740D, 0x923D)
    ax[0].legend()

    ax[1].clear()
    ax[1].plot(time_data_y, sine_data_y, 'b-', label="Y Sine Wave")
    ax[1].set_title("Y Sine Wave")
    ax[1].set_xlabel(f'Running time')
    ax[1].set_ylabel(f'DAC value')
    ax[1].set_ylim(0x70E4, 0x927C)
    ax[1].legend()

    # Redraw the figure
    canvas.draw()

# Function to draw the matplotlib figure on the PySimpleGUI Canvas
def draw_figure(canvas_elem, fig):
    figure_canvas_agg = FigureCanvasTkAgg(fig, canvas_elem.TKCanvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

# Create the Matplotlib figure with subplots
fig, ax = plt.subplots(2, 1, figsize=(8, 12))  # Three subplots: X, Y, and Y vs X

# Draw the Matplotlib figure in the Canvas element
canvas = draw_figure(window['-CANVAS-'], fig)

# Main event loop
while True:
    event, values = window.read(timeout=10)

    # Update plot
    update_plot()

    if event == sg.WIN_CLOSED:
        break
    if event == 'Start X Sine':
        start_sine_x()
    if event == 'Stop X Sine':
        stop_sine_x()
    if event == 'Start Y Sine':
        start_sine_y()
    if event == 'Stop Y Sine':
        stop_sine_y()
    if event == 'Start Both':
        start_sine_x()
        start_sine_y()
    if event == 'Stop Both':
        stop_sine_x()
        stop_sine_y()
# Cleanup
window.close()
if fsmPort:
    fsmPort.close()
