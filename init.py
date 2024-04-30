import subprocess
import os

# Get the current working directory
current_dir = os.getcwd()

# Specify the path to the start.py file
start_py_path = os.path.join(current_dir, "start.py")

# Create a new startup info object
startup_info = subprocess.STARTUPINFO()
startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW

# Create a terminal process and run start.py without opening a GUI window
subprocess.Popen(["python", start_py_path], startupinfo=startup_info)