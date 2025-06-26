        
        #####=- Plotter -=#####
        # Create figure for plots
        plt.figure(figsize=(16, 9))

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
        plt.ylabel("Power [W]")
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
        plt.tight_layout(pad=2.0, h_pad=2.5, w_pad=2.0)
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
        plt.ylabel("Power [W]")
        plt.title("Transmitted and received binary signals: bitrate = "+str(self.bitrate)+str(" bps")+", BER = "+str(BER))
        plt.xlim([t[0], t[samples_to_plot]])
        plt.grid(True)
        plt.legend()

        # Show all plots
        plt.tight_layout(pad=3.0, h_pad=2.5, w_pad=2.0)
        plt.show()