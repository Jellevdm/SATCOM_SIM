# Import needed packages
import numpy as np
import matplotlib.pyplot as plt
import tomllib as tom
import scipy.signal as signal

class OpticalLinkBudget:
    def __init__(self, config, input_name, losses_name):
        self.config = config
        # Read loss settings
        self.losses = self.config[losses_name]

        # Read input parameters
        inputs = self.config[input_name]
        self.Tx_power = inputs["Tx_power"]
        self.theta_div = inputs["theta_div"]
        self.sigma_pj = inputs["sigma_pj"]
        self.optics_array = inputs["optics_array"]
        self.Dr = inputs["Dr"]
        self.wave = inputs["wave"]
        self.V = inputs["V"]
        self.L = inputs["L"]
        self.temp = inputs["temp"]
        self.r = inputs["r"]
        self.p_out = inputs["p_out"]
        self.sigma_i = inputs["sigma_i"]
        self.r0 = inputs["r0"]
        self.D_spot = self.L * self.theta_div
        self.eta_rx = inputs["eta_rx"]
        self.Rx_treshold = inputs["Rx_treshold"]
        self.n_nom = inputs["n_nom"]
        self.attenuator = inputs["attenuator"]
        self.link = inputs["link"]

    @property
    def tx_gain(self):
        """Transmitter Gain"""
        G_tx = 8 / (self.theta_div ** 2)
        return 10 * np.log10(G_tx)

    @property
    def rx_gain(self):
        """Receiver Gain"""
        R_tx = self.eta_rx*((np.pi * self.Dr) / self.wave) ** 2
        return 10 * np.log10(R_tx)

    @property
    def free_space_loss(self):
        """Free space loss using the correct Friis equation"""
        L_fs = (4 * np.pi * self.L / self.wave) ** -2
        return -np.abs(10 * np.log10(L_fs))

    @property
    def total_optics_loss(self):
        """Optical Loss"""
        optics_loss = np.prod(self.optics_array)
        return -np.abs(10 * np.log10(optics_loss))

    @property 
    #TODO: combine static and dynamic errors
    def static_pointing_loss(self):
        """Static Pointing Loss"""
        theta_pe = self.r / self.L
        T_pe = np.exp((-2 * theta_pe ** 2) / self.theta_div**2) 
        T_pe = max(T_pe, 1e-6) # it was throwing inf errors without this
        return -np.abs(10 * np.log10(T_pe))

    @property
    def jitter_loss(self):
        """Jitter Loss"""
        return -np.abs(10 * np.log10(self.theta_div**2 / (self.theta_div**2 + 4 * self.sigma_pj**2) * self.p_out ** ((4 * self.sigma_pj ** 2)/(self.theta_div ** 2))))
    # --------------------------------------

    @property
    def beam_spread_loss(self):
        """Beam Spread Loss"""
        return -np.abs(10 * np.log10((1 + (self.D_spot / self.r0) ** (5/3)) ** (-5/6)) * self.n_nom)

    @property
    def wavefront_loss(self):
        """Wavefront Loss"""
        return -np.abs(10 * np.log10((1 + (self.D_spot / self.r0) ** (5/3)) ** (-5/6)) * self.n_nom)

    @property
    def scintillation_loss(self):
        """Scintillation Loss"""
        p_out = max(self.p_out, 1e-6)  # Prevent log(0) errors
        return -np.abs((3.3 - 5.77 * np.sqrt(-np.log(p_out))) * self.sigma_i ** (4/5))
    
    @property
    def atmos_loss(self):
        """Atmospheric Loss"""
        sigma = 3.91/self.V * ((self.wave)/(550e-9)) ** -1.6
        T_atmos = np.exp(-sigma * (self.L/1000))
        return -np.abs(10 * np.log10(T_atmos))

    def compute_link_budget(self):
        """Computes the full optical link budget"""
        Gtx = self.tx_gain
        Grx = self.rx_gain

        losses = {
        "Optical loss [dB]": self.total_optics_loss if self.losses["optics_loss"] else 0,
        "Free space loss [dB]": self.free_space_loss if self.losses["free_space_loss"] else 0,
        "Atmospheric loss [dB]": self.atmos_loss if self.losses["atmospheric_loss"] else 0,
        "Static pointing loss [dB]": self.static_pointing_loss if self.losses["static_pointing_loss"] else 0,
        "Jitter loss [dB]": self.jitter_loss if self.losses["jitter_loss"] else 0,
        "Scintillation loss [dB]": self.scintillation_loss if self.losses["scintillation_loss"] else 0,
        "Beam spread loss [dB]": self.beam_spread_loss if self.losses["beam_spread_loss"] and self.link == "up" else 0,
        "Wavefront error loss [dB]": self.wavefront_loss if self.losses["wavefront_error_loss"] and self.link == "down" else 0,
        "Attenuator loss [dB]": self.attenuator if self.losses["attenuator_loss"] else 0,
        }

        # Sum all included losses
        total_losses = sum(losses.values()) + Gtx + Grx

        P_tx_db = 10 * np.log10(self.Tx_power * 1000)
        Rx_treshold_db = 10 * np.log10(self.Rx_treshold * 1000)
        link_margin = total_losses + P_tx_db - Rx_treshold_db

        P_rx_db = P_tx_db + total_losses
        P_rx = (10 ** (P_rx_db / 10)) / 1000

        # sigma2_thermal = 1.38e-23 * (273.15 + self.temp) / 50  # Thermal noise
        # I_d = P_rx / (1.6e-19 * 0.99)  # Assume quantum efficiency of 0.99
        # sigma2_shot = 2 * 1.6e-19 * I_d  # Shot noise
        # sigma2 = sigma2_thermal + sigma2_shot  # Total noise power
        # snr = P_rx /sigma2
        # snr_db = 10 * np.log10(snr)

        return {
            "Transmit laser power [dBm]": P_tx_db,
            "Tx Antenna gain [dB]": Gtx,
            "Tx/Rx transmission loss [dB]": losses["Optical loss [dB]"],

            "Free space loss [dB]": losses["Free space loss [dB]"],
            "Atmospheric loss [dB]": losses["Atmospheric loss [dB]"],
            
            "Systematic pointing loss [dB]": losses["Static pointing loss [dB]"],
            "Pointing jitter loss [dB]": losses["Jitter loss [dB]"],
            "Scintillation loss [dB]": losses["Scintillation loss [dB]"],
            "Beam Spread loss [dB]": losses["Beam spread loss [dB]"],
            "Wavefront error loss [dB]": losses["Wavefront error loss [dB]"],
            "Rx Antenna gain [dB]": Grx,

            "Total losses [dB]": total_losses,
            "Link margin [dB]": link_margin,
            "Rx treshold [dBm]": Rx_treshold_db,
            # "SNR (dB)": snr_db,
        }

# Simulating optical signal
class Signal_simulation:
    def __init__(self, config, inputs_link, inputs_signal, L_c, snr):
        self.config = config
        link = self.config[inputs_link]
        signal = self.config[inputs_signal]

        # Read link input parameters
        self.P_l = link["Tx_power"]
        self.sigma_pj = link["sigma_pj"]
        self.z = link["L"]
        self.lam = link["wave"]
        self.theta_div = link["theta_div"]
        self.L_c = L_c
        self.snr = snr 

        # Read signal input parameters
        self.random = signal["random"]
        self.R_f = signal["R_f"]
        self.bitrate = signal["bitrate"]
        self.t_end = signal["t_end"]
        self.fs = signal["fs"]
        self.fc = signal["fc"]
        self.n = signal["n"]

    # Convert dB to linear scale
    def db_2_lin(self, val):
        lin_val = 10 ** (val / 10)
        return lin_val

    # Generate PRBS signal
    def gen_prbs(self, n_bits):
        seed_size = 5
        taps = [5, 2]  # Feedback taps positions (e.g., [5, 2] for x^5 + x^2 + 1)
        seed = np.random.choice([0, 1], size=(seed_size))

        state = np.array(seed, dtype=int)
        taps = np.array(taps) - 1  # Convert to zero-based indexing
        signal = []

        for _ in range(n_bits):
            new_bit = np.bitwise_xor.reduce(state[taps])  # XOR the tapped bits
            signal.append(state[-1])  # Output the last bit
            state = np.roll(state, -1)  # Shift left
            state[-1] = new_bit  # Insert new bit
        return signal

    # Calculate time-variant loss: jitter-induced scintillation
    def sample_xy(self, std, la, len):
        theta_x = np.random.normal(0, std, len)
        theta_y = np.random.normal(0, std, len)
        x = np.tan(theta_x) * la
        y = np.tan(theta_y) * la
        return x, y

    def butt_filt(self, fs, fc, x, y):
        # FILTER #
        # Normalize frequency
        Wn = fc / (fs / 2)  # Normalize by Nyquist frequency

        # Design a second-order Butterworth filter
        b, a = signal.butter(N=2, Wn=Wn, btype='low', analog=False, output='ba')

        # Apply filter
        x_f = signal.lfilter(b, a, x)
        y_f = signal.lfilter(b, a, y)
        return x_f, y_f

    def intensity_function(self, x_f, y_f, lam, theta_div, n, z):
        # Substitute in intensity function
        r = np.sqrt(x_f ** 2 + y_f ** 2)
        w_0 = lam / (theta_div * np.pi * n)
        z_R = np.pi * w_0 ** 2 * n / lam
        w = w_0 * np.sqrt(1 + (z / z_R) ** 2)
        L_pj = (w_0 / w) ** 2 * np.exp(-2 * r ** 2 / w ** 2)
        return L_pj

    # Generate AWGN noise for given SNR
    def gen_awgn(self, signal, snr_db):
        signal_power = np.mean(signal ** 2)  # Compute signal power
        snr_linear = self.db_2_lin(snr_db)  # Convert SNR from dB to linear scale
        noise_power = signal_power / snr_linear  # Compute noise power
        noise = np.random.normal(0, np.sqrt(noise_power), signal.shape)  # Generate Gaussian noise
        return noise
    
    def generate_time_sig(self):
        if self.random == False:
            np.random.seed(0)

        # Generate PRBS transmitter signal
        n_bits = self.bitrate * self.t_end
        tx_bits = self.gen_prbs(n_bits)  # PRBS generator
        tx_signal = np.multiply(np.repeat(tx_bits, self.R_f), self.P_l)  # Transmitted signal
        t = np.linspace(0, self.t_end, len(tx_signal))  # Time steps

        # Attenuate signal: include losses
        # Pointing jitter loss [dB]
        # Losses

        array = self.sample_xy(self.sigma_pj, self.z, len(t))
        print(array)
        array_f = self.butt_filt(self.fs, self.fc, array[0], array[1])
        print(array_f)
        L_pj = self.intensity_function(array_f[0], array_f[1], self.lam, self.theta_div, self.n, self.z)
        L_tot = self.db_2_lin(self.L_c) * L_pj  # Total loss [-]
        tx_signal_loss = L_tot * tx_signal

        # Add Gaussian noise (AWGN)
        awgn = self.gen_awgn(tx_signal_loss, self.snr)
        rx_signal = (tx_signal_loss + awgn)

        # Apply on-off keying
        threshold = np.mean(rx_signal[::self.R_f])
        rx_bits = (rx_signal[::self.R_f] > threshold).astype(int)
        bit_errors = np.sum(tx_bits != rx_bits)
        BER = bit_errors / n_bits
        print("BER: " + str(BER))

        #####=- Plotter -=#####
        # Create figure for plots
        plt.figure(figsize=(12, 9))

        # Plot 1: Received signals
        plt.subplot(3, 1, 1)
        plt.step(t, tx_signal_loss, where='post', label="Attenuated signal", linewidth=2, alpha=0.7)
        plt.step(t, rx_signal, where='post', label="Noisy signal: SNR = "+str(self.snr)+" dB", linewidth=1, alpha=0.7)
        #plt.plot(t, rx_signal, label="Noisy signal", linewidth=1, alpha=0.7)
        plt.scatter(t[::self.R_f], rx_signal[::self.R_f], label="Receiver sampling", s=15)
        plt.step(t, np.repeat(rx_signal[::self.R_f], self.R_f), where='post', label="Received signal", linewidth=2, alpha=0.7)
        plt.axhline(threshold, color='r', linestyle='dashed', label="Decision Threshold = "+str(round(threshold,4)))
        plt.xlabel("Time [s]")
        plt.ylabel("Power [W]")
        plt.title("Attenuated, noisy and received signals")
        plt.grid(True)
        plt.legend()

        # Plot 2: Transmitted and received binary signals
        plt.subplot(3, 1, 2)
        plt.step(t, np.repeat(tx_bits, self.R_f), where='post', label="Transmitted binary signal", linewidth=3, alpha=0.7)
        plt.step(t, np.repeat(rx_bits, self.R_f), where='post', label="Received binary signal", linewidth=3, alpha=0.7)
        plt.xlabel("Time [s]")
        plt.ylabel("Voltage [V]")
        plt.title("Transmitted and received binary signals: bitrate = "+str(self.bitrate)+str(" bps")+", BER = "+str(BER))
        plt.grid(True)
        plt.legend()

        # Plot 3: Histogram of received signal
        plt.subplot(3, 1, 3)
        plt.hist(rx_signal[::self.R_f], bins=10, density=True, alpha=0.6, color='b', edgecolor='black')
        plt.axvline(threshold, color='r', linestyle='dashed', label="Decision Threshold = "+str(round(threshold,4)))
        plt.xlabel("Power [W]")
        plt.ylabel("Probability density [-]")
        plt.title("Histogram of received power")
        plt.legend()
        plt.grid(True)

        # Show all plots
        plt.tight_layout()
        plt.show()
        return