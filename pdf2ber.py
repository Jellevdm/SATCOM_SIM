import numpy as np
from scipy.special import erfc
import matplotlib.pyplot as plt
from scipy.special import iv        # iv is the modified Bessel function of the first kind, # can be used to check against the simulation to determine correctness of the simulation.
                      

w0 = 0.0009688
sigma_pj = 2e-3
mu = 0.1e-3

def pdfIGauss(w0, sigmaPJ, mu):
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
    gamma = w0 / (2 * sigmaPJ)  # Compute gamma
    hp = np.linspace(0.1, 1, 1001)  # Define hp values from 0 to 1

    # Compute the argument for the modified Bessel function
    Z = (mu / sigmaPJ**2) * np.sqrt(-w0**2 * np.log(hp) / 2)

    # Compute the integral term using the modified Bessel function of the first kind (I0)
    I = np.exp(-mu**2 / (2 * sigmaPJ**2)) * iv(0, Z)

    # Compute the final PDF
    pdf = gamma**2 * hp**(gamma**2 - 1) * I

    return pdf, hp

def pdf2ber(pdf, u):
    pdf = np.asarray(pdf).flatten()
    u = np.asarray(u).flatten()
    
    du = np.mean(np.diff(u))
    SNR = np.linspace(0, 100, 1000)
    
    integr = pdf * erfc(SNR[:, None] * u / (2 * np.sqrt(2)))
    BER = 0.5 * np.sum(integr, axis=1) * du
    
    return BER, SNR

pdf, u = pdfIGauss(w0, sigma_pj, mu)
BER, SNR = pdf2ber(pdf, u)

# Plot the PDF
plt.plot(u, pdf)
plt.xlabel("Normalized Irradiance (h')")
plt.ylabel("PDF")
plt.title(f'PDF of Irradiance Fluctuations - static pointing error: {mu} [m]')
plt.grid(True)
plt.show()

# Plot the BER curve
plt.semilogy(SNR, BER)  # Log scale for BER
plt.xlabel("SNR (dB)")
plt.ylabel("BER")
plt.title("Bit Error Rate vs. SNR")
plt.grid()
plt.show()