# Import needed packages
import numpy as np
import matplotlib.pyplot as plt
import tomllib as tom
import scipy.signal as signal
from scipy.special import iv 
from scipy.special import erfc
from scipy.integrate import simpson
import pandas as pd

def pj_loss(self, x_f, y_f, lam, theta_div, n, res=100):
    w_0 = lam / (theta_div * np.pi * n)
    
    def gauss_beam(x, y):
        r = np.sqrt(x ** 2 + y ** 2)
        return (w_0 / self.w_beam) ** 2 * np.exp(-2 * r ** 2 / self.w_beam ** 2)

    R_det = self.Dr / 2
    dx = dy = None

    losses = []

    for x_f_i, y_f_i in zip(np.ravel(x_f), np.ravel(y_f)):
        x_grid = np.linspace(x_f_i - R_det, x_f_i + R_det, res)
        y_grid = np.linspace(y_f_i - R_det, y_f_i + R_det, res)
        X, Y = np.meshgrid(x_grid, y_grid)

        if dx is None:
            dx = x_grid[1] - x_grid[0]
            dy = y_grid[1] - y_grid[0]

        mask = (X - x_f_i) ** 2 + (Y - y_f_i) ** 2 <= R_det ** 2
        intensity = gauss_beam(X, Y)
        captured_power = np.sum(intensity[mask]) * dx * dy
        total_power = (np.pi * w_0**2) / 2
        L_pj = captured_power / total_power

        losses.append(L_pj)

    return np.array(losses).reshape(np.shape(x_f))
