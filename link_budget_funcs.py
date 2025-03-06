import numpy as np
import matplotlib.pyplot as plt
import tomllib as tom

class OpticalLinkBudget:
    def __init__(self,config, input_name, losses_name):
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
