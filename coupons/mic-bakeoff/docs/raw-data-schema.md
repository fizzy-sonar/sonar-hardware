# pdm-bakeoff-dataset/1 — raw dataset schema

Consumed by `analysis/pdm_bakeoff.py --dataset`. One JSON file per bake-off run.
All dB quantities are dB SPL (noise) or dB re calibrated reference (SNR/response).
`null` marks a missing member (makes its (q,u,r) block incomplete by rule).

```json
{
  "schema": "pdm-bakeoff-dataset/1",
  "fixture": {
    "u_fixture_k2_db": {
      "noise_bin": [12 floats], "noise_band": float,
      "snr_bin":  [12 floats], "loss_bin": [12 floats], "loss_band": float
    },
    "reference_drift": {"magnitude_db": float, "phase_deg": float},
    "calibration_provenance": "string: reference mic cal artifact id + date + decimator rev"
  },
  "candidates": {
    "SPH0641LU4H-1": {
      "clock_hz": 3072000,
      "installed_units": 12, "assembly_failures": 0, "sourceable": true,
      "valid_units": [{"coupon": 1, "site": 1, "serial": "..."}],
      "records": [ {
        "coupon": 1, "site": 1, "reseat": 1,
        "snr_bin_db": [12 floats], "snr_band_db": float,
        "noise_bin_db_spl": [12 floats], "noise_band_db_spl": float,
        "resp_mag_db": [12 floats], "resp_phase_deg": [12 floats],
        "gain_norm_db": float, "raw_files": ["sha256:..."],
        "temperature_c": float, "humidity_pct": float, "fixture_pose": "..."
      } ]
    },
    "ICS-41352": { "clock_hz": 4800000 }
  },
  "electrical": {
    "SPH0641LU4H-1": {
      "all_units_started": true, "both_select_polarities": true,
      "startup_cycles": 10, "startup_cycles_clean": true, "data_pulls_present": false,
      "measurements": {"duty_pct": {"value": 50.1, "uncertainty": 0.2},
                       "rise_ns": {...}, "fall_ns": {...}, "tdd_ns": {...},
                       "tdz_ns": {...}, "skew_ns": {...}}
    },
    "ICS-41352": {
      "datasheet_limits": {"enable_ns": [null, 50.0], "disable_ns": [5.0, 40.0],
                           "skew_ns": [null, 0.5]},
      "measurements": {"enable_ns": {...}, "disable_ns": {...}, "skew_ns": {...}}
    }
  },
  "power": {
    "SPH0641LU4H-1": {"extrapolated_24mic_steady_ma": float, "observed_peak_ma": float},
    "ICS-41352": {"extrapolated_24mic_steady_ma": float, "observed_peak_ma": float}
  },
  "ports": {
    "SPH0641LU4H-1": {"holes_inspected": 12, "holes_pass": 12, "max_offset_mm": float},
    "ICS-41352": {"holes_inspected": 12, "holes_pass": 12, "max_offset_mm": float}
  },
  "overload": {
    "SPH0641LU4H-1": {"fixture_max_spl_db": float, "thd10_db_spl": float,
                      "recovery_s": float},
    "ICS-41352": {"fixture_max_spl_db": float, "thd10_db_spl": float,
                  "recovery_s": float}
  }
}
```

Notes:
- Decision bins are the 12 non-overlapping 1 kHz bins from 20–32 kHz
  (bin b = [20+b, 21+b) kHz). Band metrics are integrated in linear power first.
- SPH electrical limits are fixed by the ticket (48–52% duty, <=3 ns edges,
  tDD <=40 ns, tDZ >=3 ns, skew <=0.500 ns) and hard-coded in the analyzer;
  ICS limits are entered from the DS-000048 revision used at the bench.
- SPH-at-4.8 MHz diagnostic records travel as separate files, not in this
  dataset (the comparison is intended-mode only).
