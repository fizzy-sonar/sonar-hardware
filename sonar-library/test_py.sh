#!/bin/bash
export TEST_VAR="hello"
python3 - <<'PY'
import os
print("Test:", os.environ["TEST_VAR"])
PY
