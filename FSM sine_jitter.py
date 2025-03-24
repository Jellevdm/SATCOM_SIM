import FreeSimpleGUI as sg
import serial.tools.list_ports
import threading
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import queue

# Decrease this to make the FSM movement smoother
update_time = 0.0005

ports = serial.tools.list_ports.comports()
portList = [port.name for port in ports]

fsmPort = None

# Initialize the queue for real-time plotting
plot_length = 500  # Number of points to display in the plot (adjust as needed)
data_queue_x = queue.Queue()
data_queue_y = queue.Queue()

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

# Track global time (in seconds)
global_time = 0

# Function to generate sine wave with jitter and send data
def sine_wave_with_jitter(channel, base_freq, base_amp, running_flag, queue):
    global global_time  # Use the global time for continuous tracking
    offset = 0x7FFF
    jitter_interval = 2  # Jitter every 2 seconds
    prev_freq = base_freq

    # Initial jitter parameters
    jittered_freq = base_freq
    jittered_amp = base_amp
    jittered_phase = np.random.uniform(0, 2 * np.pi)

    while running_flag():
        # Apply jitter every 'jitter_interval' seconds
        if (global_time % jitter_interval) < 0.01:  # Update jitter parameters roughly every jitter_interval seconds
            jittered_freq = generate_jitter_freq(prev_freq * 0.8, prev_freq * 1.2)
            jittered_amp = base_amp * generate_jitter_amp(0.8, 1.2)
            jittered_phase = np.random.uniform(0, 2 * np.pi)
            prev_freq = jittered_freq  # Update the previous frequency

        amplitude = int(0x3FFF + (0x3FFF * jittered_amp))

        # Calculate the sine wave value based on continuous time
        sine_value = int(offset + amplitude * np.sin(2 * np.pi * jittered_freq * global_time + jittered_phase))
        sine_value = max(0, min(0xFFFF, sine_value))  # Ensure sine_value is within DAC range

        # Send data to DAC
        sendDAC(sine_value, channel, 1)

        # Store data for plotting
        queue.put((global_time, sine_value))  # Use global_time for continuous time tracking

        # Increment global time continuously
        global_time += 0.01  # You can adjust this increment based on your update rate

        time.sleep(0.01)  # Update rate: 10 ms

# Functions to start and stop sine waves for X and Y axes
def start_sine_x():
    global running_x
    if not running_x:
        running_x = True
        base_freq_x = float(values['freq_x'])  # Get frequency from GUI
        base_amp_x = float(values['amp_x'])    # Get amplitude from GUI
        threading.Thread(target=sine_wave_with_jitter, args=(0, base_freq_x, base_amp_x, lambda: running_x, data_queue_x), daemon=True).start()

def stop_sine_x():
    global running_x
    running_x = False

def start_sine_y():
    global running_y
    if not running_y:
        running_y = True
        base_freq_y = float(values['freq_y'])  # Get frequency from GUI
        base_amp_y = float(values['amp_y'])    # Get amplitude from GUI
        threading.Thread(target=sine_wave_with_jitter, args=(1, base_freq_y, base_amp_y, lambda: running_y, data_queue_y), daemon=True).start()

def stop_sine_y():
    global running_y
    running_y = False

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
    ax[0].set_ylim(0, 0xFFFF)
    ax[0].legend()

    ax[1].clear()
    ax[1].plot(time_data_y, sine_data_y, 'b-', label="Y Sine Wave")
    ax[1].set_title("Y Sine Wave")
    ax[1].set_ylim(0, 0xFFFF)
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
fig, ax = plt.subplots(2, 1, figsize=(8, 10))  # Only two subplots: one for X and one for Y

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

# Cleanup
window.close()
if fsmPort:
    fsmPort.close()
