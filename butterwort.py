import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal

# Sampling frequency and cutoff frequency
fs = 1e7  # Hz
fc = 1e5   # Hz (Cutoff frequency)

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
t = np.linspace(0, t_end, 1000)  

#noise
array = sample_xy(sigma_pj, la, len(t), 0)
x = array[0]
y = array[1]
print(x)
print(y)

#filtered noise
array_f = butt_filt(fs, fc, x, y)
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
plt.title("Frequency Response of Butterworth Filter")
plt.legend()
plt.grid()

plt.tight_layout()
plt.show()

# Subplot 1: Time Domain Signal
plt.subplot(2, 1, 1)
plt.plot(t, x, label='Original Signal')
plt.plot(t, x_f, label='Filtered Signal', linewidth=2)
plt.legend()
plt.xlabel("Time [seconds]")
plt.ylabel("Amplitude - x")
plt.title("Time Domain: Original vs. Filtered Signal")
plt.grid()

# Subplot 2: Frequency Response
plt.subplot(2, 1, 2)
plt.plot(t, y, label='Original Signal')
plt.plot(t, y_f, label='Filtered Signal', linewidth=2)
plt.legend()
plt.xlabel("Time [seconds]")
plt.ylabel("Amplitude - y")
plt.title("Time Domain: Original vs. Filtered Signal")
plt.grid()
plt.show()












# # Normalize frequency
# Wn = fc / (fs / 2)  # Normalize by Nyquist frequency

# # Design a second-order Butterworth filter
# b, a = signal.butter(N=2, Wn=Wn, btype='low', analog=False, output='ba')

# # # Create a test signal (10 Hz sine wave + 100 Hz noise)
# # t = np.linspace(0, 1, fs, endpoint=False)                           # Time vector
# # x = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 120 * t)  # Signal with noise

# # # Apply the filter
# # y = signal.lfilter(b, a, x)

# # Compute Frequency Response
# w, h = signal.freqz(b, a, worN=1024)  # Compute frequency response
# frequencies = w * fs / (2 * np.pi)  # Convert to Hz

# # # # Plot both time-domain and frequency response
# # # plt.figure(figsize=(12, 6))

# # # Subplot 1: Time Domain Signal
# # plt.subplot(2, 1, 1)
# # plt.plot(t, x, label='Original Signal')
# # plt.plot(t, y, label='Filtered Signal', linewidth=2)
# # plt.legend()
# # plt.xlabel("Time [seconds]")
# # plt.ylabel("Amplitude")
# # plt.title("Time Domain: Original vs. Filtered Signal")
# # plt.grid(