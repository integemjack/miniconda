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

try:
    import matplotlib
    print(f"Matplotlib version: {matplotlib.__version__}")
    
    # Create a simple plot
    import matplotlib.pyplot as plt
    plt.figure(figsize=(6, 4))
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    plt.plot(x, y)
    plt.title("Simple Sine Wave")
    plt.xlabel("X")
    plt.ylabel("sin(x)")
    plt.savefig("test_plot.png")  # Save instead of display for CI environments
    print("Successfully created a test plot: test_plot.png")
except ImportError:
    print("Matplotlib is not installed")

try:
    import bleak
    # Bleak does not have __version__ attribute, use alternative method
    import importlib.metadata
    try:
        bleak_version = importlib.metadata.version("bleak")
        print(f"Bleak version: {bleak_version}")
    except:
        print("Bleak is installed but version could not be determined")
except ImportError:
    print("Bleak is not installed") 