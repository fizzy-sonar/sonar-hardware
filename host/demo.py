import numpy as np
from sonar_host.dsp import chirp, matched_filter

fs = 128000
c = chirp(fs, 1024)
x = np.zeros(4096)
x[1500:2524] = c
y = matched_filter(x, c)
print("peak sample", np.argmax(y), "range_m", np.argmax(y) / fs * 343 / 2)
