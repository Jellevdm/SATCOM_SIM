# Import needed packages
import numpy as np
import matplotlib.pyplot as plt
import tomllib as tom
import scipy.signal as signal
from scipy.special import iv 
from scipy.special import erfc
from scipy.integrate import simpson
import pandas as pd
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
    #TODO: Some of the following losses are not used in the link budget
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
        total_const = sum(losses.values()) 
        total_losses = sum(losses.values()) + Gtx + Grx

        P_tx_db = 10 * np.log10(self.Tx_power * 1000)
        Rx_treshold_db = 10 * np.log10(self.Rx_treshold * 1000)
        link_margin = total_losses + P_tx_db - Rx_treshold_db

        P_rx_db = P_tx_db + total_losses

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

            "Attenuator loss [dB]": losses["Attenuator loss [dB]"],

            "Total losses [dB]": total_losses, #With gains
            "Total losses const [db]": total_const,     #just the constant losses
            "Link margin [dB]": link_margin,
            "Rx treshold [dBm]": Rx_treshold_db,
        }

# Simulating optical signal
class Signal_simulation:
    def __init__(self, config, csv_file, inputs_link, inputs_signal, L_c):
        self.config = config
        self.csv_file = csv_file
        link = self.config[inputs_link]
        signal = self.config[inputs_signal]

        # Read link input parameters
        self.P_l = link["Tx_power"]
        self.sigma_pj = link["sigma_pj"]
        self.z = link["L"]
        self.lam = link["wave"]
        self.theta_div = link["theta_div"]
        self.L_c = L_c
        self.Dr = link["Dr"]
        self.w_beam = link['w_beam']

        # Read signal input parameters
        self.random = signal["random"]
        self.R_f = signal["R_f"]
        self.bitrate = signal["bitrate"]
        self.fs = signal["fs"]
        self.fc = signal["fc"]
        self.n = signal["n"]
        self.mu = signal["mu"]
        self.snr = signal["snr"] 

    def read_FSM(self, csv_file):
        df = pd.read_csv(csv_file, header=None).dropna().iloc[1:].astype(float)
        t, x_dac, y_dac = np.array(df[0].tolist()), np.array(df[1].tolist()), np.array(df[2].tolist())
        return t, x_dac, y_dac

    def bits_2_pos(self, bits, bounds):
        pos = bits.copy()
        idx_low = np.where(pos < bounds[1])
        idx_mid = np.where(pos == bounds[1])
        idx_high = np.where(pos > bounds[1])
        pos[idx_low] = -1 * ((bounds[1] - bounds[0]) - (pos[idx_low] - bounds[0])) / (bounds[1] - bounds[0]) 
        pos[idx_mid] = 0.0
        pos[idx_high] = ((bounds[2] - bounds[1]) - (bounds[2] - pos[idx_high])) / (bounds[2] - bounds[1])  
        pos *= (self.Dr + self.w_beam) / 2
        return pos

    # Convert dB to linear scale
    def db_2_lin(self, val):
        lin_val = 10 ** (val / 10)
        return lin_val

    def gen_square(self, n_bits):
        signal = []
        for i in range(n_bits):
            if i % 2 == 0:
                signal.append(1)
            else:
                signal.append(0)
        return signal
    
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

    def pj_loss(self, x_f, y_f, lam, theta_div, n, res=100):
        # Calculate the beam waist (w0) at the focus of the last lens (assuming beam is focused by lens to its waist). Detector 
        # is positioned at the focal point of the last lens.
        w_0 = lam / (theta_div * np.pi * n)  # [m]

        # Define a 2D Gaussian beam intensity profile centered at (0,0)
        def gauss_beam(x, y):
            r = np.sqrt(x ** 2 + y ** 2)  # radial distance from beam center
            return np.exp(-2 * r ** 2 / w_0 ** 2)  # normalized Gaussian intensity

        R_det = self.Dr / 2  # Radius of circular detector [m]
        dx = dy = None  # Spatial resolution elements for integration

        losses = []  # Store loss values for each FSM position

        # Loop over all FSM x/y positions
        for x_f_i, y_f_i in zip(np.ravel(x_f), np.ravel(y_f)):
            # Define grid over area of detector centered at FSM position
            x_grid = np.linspace(x_f_i - R_det, x_f_i + R_det, res)
            y_grid = np.linspace(y_f_i - R_det, y_f_i + R_det, res)
            X, Y = np.meshgrid(x_grid, y_grid)  # Create 2D meshgrid

            # Compute dx, dy (only once, assuming uniform grid)
            if dx is None:
                dx = x_grid[1] - x_grid[0]
                dy = y_grid[1] - y_grid[0]

            # Shift coordinates so that the Gaussian beam is centered at (x_f_i, y_f_i)
            intensity = gauss_beam(X - x_f_i, Y - y_f_i)

            # Apply circular mask for detector aperture (still centered at original detector center)
            mask = X**2 + Y**2 <= R_det ** 2

            # Integrate beam intensity over the detector aperture (captured power)
            captured_power = np.sum(intensity[mask]) * dx * dy

            # Total power of a 2D Gaussian beam (analytical)
            total_power = (np.pi * w_0**2) / 2

            # Compute fraction of power captured = "pointing loss" or link efficiency
            L_pj = captured_power / total_power
            losses.append(L_pj)

        # Return loss array reshaped to match input shape
        return np.array(losses).reshape(np.shape(x_f))
    
    def gen_awgn(self, signal):
        mean = -0.5297e-3
        std = 1.3598e-3
        num_samples = len(signal)
        noise = (np.random.normal(mean, std, num_samples)/3.8)
        return noise
    
    def generate_time_sig_square(self, sigma, mean):
        t_fsm, x_dac, y_dac = self.read_FSM(self.csv_file)

        n_bits = self.bitrate * int(t_fsm[-1])
        tx_bits = self.gen_square(n_bits)  # Square wave generator
        tx_signal = np.multiply(np.repeat(tx_bits, self.R_f), self.P_l)  # Transmitted signal
        t = np.linspace(0, t_fsm[-1], len(tx_signal))  # Time steps

        # Interpolate FSM positions over the higher-resolution time vector
        t_fsm_interp = np.linspace(0, t_fsm[-1], len(tx_signal))  # match full signal length
        x_raw = self.bits_2_pos(x_dac, bounds=[22850, 36400, 45750])
        y_raw = self.bits_2_pos(y_dac, bounds=[22100, 33200, 44000])
        x = np.interp(t_fsm_interp, t_fsm, x_raw)
        y = np.interp(t_fsm_interp, t_fsm, y_raw)

        L_pj = self.pj_loss(x, y, self.lam, self.theta_div, self.n)

        L_tot = self.L_c * L_pj  # Total loss [-]
        tx_signal_loss = L_tot * tx_signal
   
        # Add Gaussian noise (AWGN)
        awgn = self.gen_awgn(tx_signal_loss)
        rx_signal = (tx_signal_loss + awgn)

        thresholds_pw = (np.arange(0.05, 0.85, 0.05)/3.8)*self.P_l
        ber_list = []

        for th in range(len(thresholds_pw)):
            rx_bits = (rx_signal[::self.R_f] > thresholds_pw[th]).astype(int)
            bit_errors = np.sum(tx_bits != rx_bits)
            ber_temp = bit_errors / n_bits
            ber_list.append(ber_temp)

            n_bits_to_plot = 100
            samples_to_plot = n_bits_to_plot * self.R_f

            #####=- Plotter -=#####
            # Create figure for plots
            plt.figure(figsize=(12, 9))

            # Plot 1: Received signals
            plt.subplot(3, 1, 1)
            plt.step(t, tx_signal_loss, where='post', label="Tx: Attenuated transmitted signal", linewidth=2, alpha=0.7)
            plt.step(t, np.repeat(rx_signal[::self.R_f], self.R_f), where='post', label="Rx: Received signal + detector noise", linewidth=2, alpha=0.7)
            plt.axhline(thresholds_pw[th], color='r', linestyle='dashed', label=f"Decision Threshold = {round((thresholds_pw[th]/self.P_l)*3.8,3)} Voltage [V]")
            plt.xlabel("Time [s]")
            plt.ylabel("Power [W]")
            plt.xlim([t[0], t[samples_to_plot]])
            plt.title(f"Simulated Square Wave signal: σ={sigma}, μ={mean}, th={round((thresholds_pw[th]/self.P_l)*3.8,3), 'Voltage [V]'}")
            plt.grid(True)
            plt.legend()

            # Plot 2: Transmitted and received binary signals
            plt.subplot(3, 1, 2)
            plt.step(t, np.repeat(tx_bits, self.R_f), where='post', label="Transmitted binary signal", linewidth=3, alpha=0.7)
            plt.step(t, np.repeat(rx_bits, self.R_f), where='post', label="Received binary signal", linewidth=3, alpha=0.7)
            plt.xlabel("Time [s]")
            plt.ylabel("[-]")
            plt.xlim([t[0], t[samples_to_plot]])
            plt.title("Transmitted and received binary signals: bitrate = "+str(self.bitrate)+str(" bps")+", BER = "+str(round(ber_temp, 4)))
            plt.grid(True)
            plt.legend()

            # Plot 3: Histogram of received signal
            plt.subplot(3, 1, 3)
            plt.hist(rx_signal, bins=1000, density=True, alpha=0.6, color='b', edgecolor='black')
            plt.axvline(thresholds_pw[th], color='r', linestyle='dashed', label=f"Decision Threshold = {round((thresholds_pw[th]/self.P_l)*3.8,3)} Voltage [V]")
            plt.xlabel("Power [W]")
            plt.ylabel("Probability density [-]")
            plt.title("Histogram of received power")
            plt.legend()
            plt.grid(True)
            plt.tight_layout(pad=3.0, h_pad=2.5, w_pad=2.0)

            plt.savefig(f"Sim_analysis_output/signal_sigma_{sigma}_mean_{mean}_thresh_{round((thresholds_pw[th]/self.P_l)*3.8,3)}.png")  # or any naming scheme
            print(f"Plot saved for σ={sigma}, μ={mean}, th={round((thresholds_pw[th]/self.P_l)*3.8,3)}")
            plt.close()
        return ber_list

    def generate_time_sig_prbs(self):
        if self.random == False:
            np.random.seed(0)

        t_fsm, x_dac, y_dac = self.read_FSM(self.csv_file)

        # Generate PRBS transmitter signal
        n_bits = self.bitrate * int(t_fsm[-1])
        tx_bits = self.gen_prbs(n_bits)  # PRBS generator
        tx_signal = np.multiply(np.repeat(tx_bits, self.R_f), self.P_l)  # Transmitted signal
        t = np.linspace(0, t_fsm[-1], len(tx_signal))  # Time steps

        # Interpolate FSM positions over the higher-resolution time vector
        t_fsm_interp = np.linspace(0, t_fsm[-1], len(tx_signal))  # match full signal length
        x_raw = self.bits_2_pos(x_dac, bounds=[22850, 36400, 45750])
        y_raw = self.bits_2_pos(y_dac, bounds=[22100, 33200, 44000])
        x = np.interp(t_fsm_interp, t_fsm, x_raw)
        y = np.interp(t_fsm_interp, t_fsm, y_raw)

        L_pj = self.pj_loss(x, y, self.lam, self.theta_div, self.n)
        L_tot = self.L_c * L_pj  # Total loss [-]
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
        plt.show()

        # Number of bits you want to visualize clearly
        n_bits_to_plot = 50
        samples_to_plot = n_bits_to_plot * self.R_f

        # Zoom in on a portion of the signal for visibility
        # Plot 1: Received signals
        plt.figure(figsize=(12, 9))
        plt.subplot(3, 1, 1)
        plt.step(t, tx_signal_loss, where='post', label="Attenuated signal", linewidth=2, alpha=0.7)
        plt.step(t, rx_signal, where='post', label="Noisy signal: SNR = "+str(self.snr)+" dB", linewidth=1, alpha=0.7)
        #plt.plot(t, rx_signal, label="Noisy signal", linewidth=1, alpha=0.7)
        plt.scatter(t[::self.R_f], rx_signal[::self.R_f], label="Receiver sampling", s=15)
        plt.step(t, np.repeat(rx_signal[::self.R_f], self.R_f), where='post', label="Received signal", linewidth=2, alpha=0.7)
        plt.axhline(threshold, color='r', linestyle='dashed', label="Decision Threshold = "+str(round(threshold,4)))
        plt.xlabel("Time [s]")
        plt.ylabel("Power [W]")
        plt.xlim([t[0], t[samples_to_plot]])
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
        plt.xlim([t[0], t[samples_to_plot]])
        plt.grid(True)
        plt.legend()

        # Show all plots
        plt.tight_layout()
        plt.show()
        return 
    
    def pdfIGauss(self, lam, theta_div, sigmaPJ, mu, n):
        """
        Computes the probability density function (PDF) of the irradiance fluctuations 
        for free-space optical communications with nonzero boresight pointing errors.

        Parameters:
        w0      : Beam waist (spot size at the receiver)
        sigmaPJ : Pointing jitter standard deviation
        mu      : Mean offset of the pointing error

        Returns:
        pdf : The probability density function values
        hp  : The corresponding intensity fluctuation values (range from 0 to 1)
        """
        w_0 = lam / (theta_div * np.pi * n)
   
        gamma = w_0 / (2 * sigmaPJ)  # Compute gamma
        hp = np.linspace(0.1, 1, 1001)  # Define hp values from 0 to 1

        # Compute the argument for the modified Bessel function
        Z = (mu / sigmaPJ**2) * np.sqrt(-w_0**2 * np.log(hp) / 2)

        # Compute the integral term using the modified Bessel function of the first kind (I0)
        I = np.exp(-mu**2 / (2 * sigmaPJ**2)) * iv(0, Z)

        # Compute the final PDF
        pdf = gamma**2 * hp**(gamma**2 - 1) * I
        pdf /= simpson(pdf)     # Normalize the PDF
        return pdf, hp

    def pdf2ber(self, pdf, u):
        pdf = np.asarray(pdf).flatten()
        u = np.asarray(u).flatten()

        du = np.mean(np.diff(u))
        SNR = np.linspace(0, 100, 1000)

        integr = pdf * erfc(SNR[:, None] * u / (2 * np.sqrt(2)))
        BER = 0.5 * np.sum(integr, axis=1) * du

        return BER, SNR
    
    def pdf2ber_plot(self, a, b):
        pdf, hp = self.pdfIGauss(self.lam, self.theta_div, self.sigma_pj, self.mu, self.n)
        BER, SNR = self.pdf2ber(pdf, hp)
        
        if a < hp[0] or b > hp[-1] or a>=b:
            raise ValueError("Invalid range for hp. Ensure that a < b and a, b are within the range of hp.")
        mask = (hp >= a) & (hp <= b)
        probability = simpson(pdf[mask])
        print(f"Probability that h' is in [{a},{b}]: {probability:.4f}")

        # Plot PDF
        plt.plot(hp, pdf, label='Simulation')  # Log scale for BER
        plt.xlabel("Normalized Irradiance (h')")
        plt.ylabel("PDF")
        plt.legend()
        plt.title("PDF of Irradiance Fluctuations")
        plt.grid()
        plt.show()

        # Plot the BER curve
        plt.semilogy(SNR, BER, label='Simulation')  # Log scale for BER
        plt.xlabel("SNR (dB)")
        plt.ylabel("BER")
        plt.legend()
        plt.title("Bit Error Rate vs. SNR")
        plt.grid()
        plt.show()
        return
