import numpy as np


def cic_fir(bits, R=24):
    x = bits * 2 - 1
    y = x[: len(x) // R * R].reshape(-1, R, x.shape[1]).mean(1)
    return np.convolve(y[:, 0], [0.25, 0.5, 0.25], "same")[:, None] if x.shape[1] == 1 else y


def chirp(fs, n, f0=20000, f1=32000):
    t = np.arange(n) / fs
    return np.sin(2 * np.pi * (f0 * t + (f1 - f0) * t * t / (2 * t[-1])))


def matched_filter(x, c):
    return np.convolve(x, c[::-1], "same")


def beamform(channels):
    return channels.mean(1)
