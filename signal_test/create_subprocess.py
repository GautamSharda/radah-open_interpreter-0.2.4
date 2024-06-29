import subprocess
import sys
import time
import psutil
import signal

print("Starting subprocess...")

# Start the subprocess and redirect its output to the current terminal
process = subprocess.Popen(["python", "child_process.py"], stdout=sys.stdout, stderr=sys.stderr)

print("Subprocess started with PID:", process.pid)

# Wait for 2-3 seconds before sending Ctrl+C
time.sleep(2.5)

print("Sending Ctrl+C to the subprocess...")

# Send Ctrl+C to the subprocess
# subprocess_process = psutil.Process(process.pid)
# subprocess_process.send_signal(psutil.signal.CTRL_C_EVENT)
process.send_signal(signal.CTRL_C_EVENT)

# Wait for the subprocess to finish
print("Waiting for the subprocess to finish...")
try:
    process.wait()
except KeyboardInterrupt:
    print("Parent process received KeyboardInterrupt. Ignoring...")

print("Subprocess finished with exit code:", process.returncode)
print("Parent process continues execution.")