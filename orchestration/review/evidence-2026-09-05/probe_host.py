"""T-019 diagnostic reproductions; run with PYTHONPATH=host python3 this_file.

These assert the reviewed defects, not desired production behavior.
"""
import numpy as np
from sonar_host.packet import SNR1_HEADER, SNR1_FLAGS, SNR1_MAGIC, SNR1_VERSION
from sonar_host.transport import BufferedTransportReader, MockTransport
from sonar_host.errors import StreamIncompleteError
from sonar_host.dsp import decimate_pdm_cic_fir

header = SNR1_HEADER.pack(SNR1_MAGIC, SNR1_VERSION, 32, SNR1_FLAGS,
                         1, 0, 3072000, 24, 12, 0)
reader = BufferedTransportReader(MockTransport([header, b'', b'\x01\x02\x03']))
try:
    reader.open_stream().capture_exact_frames(1)
except StreamIncompleteError as exc:
    print('REPRODUCED: transient empty read discards subsequent valid data:', exc)
else:
    raise AssertionError('empty-read behavior changed; reassess review')

# Calling the exposed block decimator on adjacent transport chunks cannot
# preserve integrator/comb/FIR state. Compare identical deterministic input.
rng = np.random.default_rng(19)
bits = rng.integers(0, 2, (24 * 1024, 4), dtype=np.uint8)
whole = decimate_pdm_cic_fir(bits)
split = np.vstack([decimate_pdm_cic_fir(b) for b in np.split(bits, 4)])
error = np.max(np.abs(whole - split))
assert error > 1e-3
print(f'REPRODUCED: chunked vs whole decimator max difference={error:.6f}')
