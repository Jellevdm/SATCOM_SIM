import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal
import pandas as pd
import os

os.chdir('Simulation files')       
file_name = "FSM inputs/04-03-inputs/04_03-testing-std(0.1)-mean(0).csv"

df = pd.read_csv(file_name)
time = df["Time"].to_numpy()
x_values = df["X Value"].to_numpy()
y_values = df["Y Value"].to_numpy()
plt.plot(time, x_values, label='x input to fsm')
plt.plot(time, y_values, label='yinput to fsm')
plt.xlabel(f'Approximate Time [s]')
plt.ylabel(f'FSM DAC value')
plt.legend()
plt.grid()
plt.show()

# Sampling frequency and cutoff frequency
fs = 1000  # Hz
fc = 100   # Hz (Cutoff frequency)

def sample_xy(std, la, len, seed):
        np.random.seed(seed)
        theta_x = np.random.normal(0, std, len)
        theta_y = np.random.normal(0, std, len)
        x = np.tan(theta_x) * la
        y = np.tan(theta_y) * la
        return x, y

def butt_filt(fs, fc, x, y):
    # FILTER #
    # Normalize frequency
    Wn = fc / (fs / 2)  # Normalize by Nyquist frequency
    # Design a second-order Butterworth filter
    b, a = signal.butter(N=2, Wn=Wn, btype='low', analog=False, output='ba')
    # Apply filter
    x_f = signal.lfilter(b, a, x)
    y_f = signal.lfilter(b, a, y)
    w, h = signal.freqz(b, a, worN=1024)  # Compute frequency response
    frequencies = w * fs / (2 * np.pi)  # Convert to Hz
    return x_f, y_f, frequencies, h

def intensity_function(x_f, y_f, lam, theta_div, n, z):
    # Substitute in intensity function
    r = np.sqrt(x_f ** 2 + y_f ** 2)
    w_0 = lam / (theta_div * np.pi * n)
    z_R = np.pi * w_0 ** 2 * n / lam
    w = w_0 * np.sqrt(1 + (z / z_R) ** 2)
    L_pj = (w_0 / w) ** 2 * np.exp(-2 * r ** 2 / w ** 2)
    return L_pj

#input
sigma_pj = 2e-3 #pointing jitter
la = 50      # link length
t_end = 10  #time to simulate
t = np.linspace(0, t_end, 10000)  

#noise
array = sample_xy(sigma_pj, la, len(t), 0)
x = array[0]
y = array[1]
# print(x)
# print(y)

#filtered noise
array_f = butt_filt(fs, fc, x_values, y_values)
frequencies = array_f[2]
x_f = array_f[0]
y_f =array_f[1]

# Plot both time-domain and frequency response
plt.figure(figsize=(12, 6))

# Subplot 2: Frequency Response
plt.plot(frequencies, 20 * np.log10(abs(array_f[3])), 'b')  # Convert magnitude to dB
plt.axvline(fc, color='r', linestyle='--', label=f'Cutoff Frequency ({fc} Hz)')
plt.xlabel("Frequency [Hz]")
plt.ylabel("Magnitude [dB]")
plt.xscale('log')
plt.title("Frequency Response of Butterworth Filter")
plt.legend()
plt.grid()

plt.tight_layout()
plt.show()

# Subplot 1: Time Domain Signal x
plt.subplot(2, 1, 1)
plt.plot(time, x_values, label='Original Signal')
plt.plot(time, x_f, label='Filtered Signal', linewidth=2)
plt.legend()
plt.xlabel("Time [seconds]")
plt.ylabel("Amplitude - x")
plt.title("Time Domain: Original vs. Filtered Signal")
plt.grid()

# Subplot 2: Time domain signal y
plt.subplot(2, 1, 2)
plt.plot(time, y_values, label='Original Signal')
plt.plot(time, y_f, label='Filtered Signal', linewidth=2)
plt.legend()
plt.xlabel("Time [seconds]")
plt.ylabel("Amplitude - y")
plt.title("Time Domain: Original vs. Filtered Signal")
plt.grid()
plt.show()

plt.figure(figsize=(8, 6))

# Plot original and filtered trajectories
plt.plot(x_values, y_values, label="Original Path", alpha=0.6)
plt.plot(x_f, y_f, label="Filtered Path", linestyle="--", linewidth=2)

# Mark start and end points
plt.scatter(x[0], y[0], color='g', label="Start", marker='o', s=100)
plt.scatter(x[-1], y[-1], color='r', label="End", marker='x', s=100)

plt.xlabel("X Position")
plt.ylabel("Y Position")
plt.title("Trajectory of x-y Coordinates Over Time")
plt.legend()
plt.grid()
plt.axis("equal")  # Ensures equal scaling of x and y axes
plt.show()

# # Normalize frequency
# Wn = fc / (fs / 2)  # Normalize by Nyquist frequency

# # Design a second-order Butterworth filter
# b, a = signal.butter(N=2, Wn=Wn, btype='low', analog=False, output='ba')

# Create a test signal (10 Hz sine wave + 100 Hz noise)
t = np.linspace(0, 1, fs, endpoint=False)                           # Time vector
x = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 120 * t)  # Signal with noise

# # # Apply the filter
# # y = signal.lfilter(b, a, x)

# # Compute Frequency Response
# w, h = signal.freqz(b, a, worN=1024)  # Compute frequency response
# frequencies = w * fs / (2 * np.pi)  # Convert to Hz

# Plot both time-domain and frequency response
plt.figure(figsize=(12, 6))

# Subplot 1: Time Domain Signal
plt.subplot(2, 1, 1)
plt.plot(t, x, label='Original Signal')
plt.plot(t, y, label='Filtered Signal', linewidth=2)
plt.legend()
plt.xlabel("Time [seconds]")
plt.ylabel("Amplitude")
plt.title("Time Domain: Original vs. Filtered Signal")
plt.grid()
plt.show()