import numpy as np
from sonar_host.dsp import *
from sonar_host.packet import *


def test_packet_order_crc():
    p = bytes([1, 0, 128]) * 24
    d = decode_snp1(encode_snp1(p))
    b = unpack_payload(d["payload"])
    assert b.shape == (24, 24) and b[0, 0] and b[0, 23]


def test_dsp_known_range():
    fs = 128000
    c = chirp(fs, 1024)
    x = np.zeros(4096)
    x[1500:2524] = c
    y = matched_filter(x, c)
    assert abs(np.argmax(y) - 2012) < 3
