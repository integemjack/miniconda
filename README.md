# Miniconda Environment Setup

This repository contains scripts to automatically set up a Miniconda environment with Python 3.11 and run a Python script.

## Windows Users

1. Double-click the `setup_and_run.bat` file to run the script
2. You can also run in simple mode:
   ```
   setup_and_run.bat simple
   ```
3. The script will:
   - Check if Miniconda is installed, if not, download and install it
   - Create a Python 3.11 environment named `py311`
   - Install dependencies from `requirements.txt`
   - Run the `main.py` script (or `main_simple.py` in simple mode)

## macOS Users

1. Open Terminal
2. Navigate to the directory containing the script:
   ```
   cd /path/to/script/directory
   ```
3. Make the script executable:
   ```
   chmod +x setup_and_run.sh
   ```
4. Run the script (recommended method to avoid conda issues):
   ```
   bash ./setup_and_run.sh
   ```
5. For simple mode, use:
   ```
   bash ./setup_and_run.sh simple
   ```
   
   > ⚠️ **IMPORTANT**: Always use `bash ./setup_and_run.sh simple` instead of `./setup_and_run.sh simple` to prevent conda from misinterpreting "simple" as an environment name.
   
6. The script will:
   - Check if Miniconda is installed, if not, download and install it
   - Create a Python 3.11 environment named `py311`
   - Install dependencies from `requirements.txt`
   - Run the `main.py` script (or `main_simple.py` in simple mode)

## Note for Apple Silicon (M1/M2) Mac Users

The script automatically detects if you're using an Apple Silicon Mac and downloads the appropriate Miniconda installer.

## GitHub Actions Validation

This repository includes GitHub Actions workflows that validate the environment setup scripts:

- Windows validation: Tests the batch script on Windows
- macOS validation: Tests the shell script on macOS (Intel)
- Architecture detection: Validates that the script correctly detects Apple Silicon

To run the validation manually:
1. Go to the "Actions" tab in the GitHub repository
2. Select the "Test Miniconda Environment Setup" workflow
3. Click "Run workflow"

The validation ensures that the scripts work correctly across different platforms.

## Troubleshooting

- **Matplotlib Issues**: If you encounter errors related to matplotlib, make sure your environment includes all required dependencies. The scripts automatically install matplotlib and other dependencies.
  
- **macOS conda Activation Issues**: If you encounter `EnvironmentNameNotFound` errors, always use `bash ./setup_and_run.sh simple` instead of directly running the script with `./setup_and_run.sh simple`.

- **Missing Dependencies**: If the scripts fail to install dependencies, try running them again or manually install the required packages:
  ```
  conda activate py311
  pip install numpy pandas matplotlib bleak
  ```

- **Bleak Version Detection**: Unlike many Python packages, the bleak module doesn't have a `__version__` attribute. If you need to check its version, use the following code instead:
  ```python
  import importlib.metadata
  bleak_version = importlib.metadata.version("bleak")
  print(f"Bleak version: {bleak_version}")
  ``` 