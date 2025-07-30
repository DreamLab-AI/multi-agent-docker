#!/usr/bin/env python3
"""Simple test runner that imports properly."""

import subprocess
import sys

# Run as module to avoid import issues
subprocess.run([sys.executable, "-m", "src.test_pipeline"], cwd=".")