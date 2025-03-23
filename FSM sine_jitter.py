import FreeSimpleGUI as sg
import serial.tools.list_ports
import threading
import numpy as np
import time

# Decrease this to make the FSM movement smoother
update_time = 0.0005

ports = serial.tools.list_ports.comports()
portList = [port.name for port in ports]

fsmPort = None

#TODO:implement data logging
logging = False


def sendDAC(d, channel, mode):
    """Function to send the data packets"""
    global fsmPort
    if fsmPort:
        packet = bytearray(3)
        packet[2] = (d & 0xFF) | 0b10000000
        packet[1] = ((d >> 7) & 0xFF) | 0b10000000
        packet[0] = (d >> 14) & 0x03
        packet[0] |= (channel << 4)
        packet[0] |= (mode << 2)
        fsmPort.write(packet)

sg.theme('DarkAmber')

# What is displayed in the GUI
windowLayout = [
    [sg.Text('X Frequency (Hz):'), sg.InputText('1', key='freq_x', size=(5,1)), sg.Text('Amplitude:'), sg.InputText('1', key='amp_x', size=(5,1)), sg.Button('Start X Sine'), sg.Button('Stop X Sine')],
    [sg.Text('Y Frequency (Hz):'), sg.InputText('1', key='freq_y', size=(5,1)), sg.Text('Amplitude:'), sg.InputText('1', key='amp_y', size=(5,1)), sg.Button('Start Y Sine'), sg.Button('Stop Y Sine')],
]

window = sg.Window('FSM DIM - GUI', windowLayout, finalize=True)


# Reading the ports. In my pc the usb port is listed as the last one hence portList[-1]. However this can be changed
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

mean = 0
std = 1e-4

def generate_jitter_amp(mean, std):
    """Generate a new value within a jitter range."""
    return np.random.normal(mean, std)

def generate_jitter_freq(low, high):
    """Generate a new value within a jitter range."""
    return np.random.uniform(low, high)

# Function to run sine wave with jitter
def sine_wave_with_jitter(channel, base_freq, base_amp, running_flag):
    """Generates a sine wave with jitter that updates frequency, amplitude, and phase over time."""
    global running_x, running_y
    t = 0
    offset = 0x7FFF
    jitter_interval = 2  # Time in seconds before changing jitter
    prev_freq = base_freq  # Start with the input base frequency

    while running_flag():
        # Generate jittered frequency and amplitude within a small variation range
        jittered_freq = generate_jitter_freq(prev_freq * 0.8, prev_freq * 1.2)  # 20% variation
        jittered_amp = base_amp * generate_jitter_amp(0.8, 1.2)  # 20% amplitude variation
        jittered_phase = np.random.uniform(0, 2 * np.pi)  # Random phase shift

        amplitude = int(0x3FFF + (0x3FFF * jittered_amp))  # Ensure realistic amplitude scaling
        prev_freq = jittered_freq  # Store for the next update

        start_time = time.time()
        while time.time() - start_time < jitter_interval and running_flag():
            sine_value = int(offset + amplitude * np.sin(2 * np.pi * jittered_freq * t + jittered_phase))
            sine_value = max(0, min(0xFFFF, sine_value))  # Ensure within DAC range
            sendDAC(sine_value, channel, 1)

            time.sleep(0.01)  # 10 ms update rate
            t += 0.01
def start_sine_x():
    global running_x
    if not running_x:
        running_x = True
        base_freq_x = float(values['freq_x'])  # Get base frequency from GUI
        base_amp_x = float(values['amp_x'])    # Get base amplitude from GUI
        threading.Thread(target=sine_wave_with_jitter, args=(0, base_freq_x, base_amp_x, lambda: running_x), daemon=True).start()

def stop_sine_x():
    global running_x
    running_x = False

def start_sine_y():
    global running_y
    if not running_y:
        running_y = True
        base_freq_y = float(values['freq_y'])  # Get base frequency from GUI
        base_amp_y = float(values['amp_y'])    # Get base amplitude from GUI
        threading.Thread(target=sine_wave_with_jitter, args=(1, base_freq_y, base_amp_y, lambda: running_y), daemon=True).start()

def stop_sine_y():
    global running_y
    running_y = False

# This is the main loop
while True:
    event, values = window.read(timeout=10)
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
    if event == 'coarse':
        valueCoarse = int(values['coarse'])
        sendDAC(valueCoarse, 0, 1)

window.close()
if fsmPort:
    fsmPort.close()
