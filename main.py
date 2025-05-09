# Set console output encoding
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("Miniconda environment test successful!")
print("Python version information:")
import sys
print(f"Python version: {sys.version}")
import platform
print(f"System platform: {platform.platform()}")

# Try to import common libraries
try:
    import numpy as np
    print(f"NumPy version: {np.__version__}")
except ImportError:
    print("NumPy is not installed")

try:
    import pandas as pd
    print(f"Pandas version: {pd.__version__}")
except ImportError:
    print("Pandas is not installed") 