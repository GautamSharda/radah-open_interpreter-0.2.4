import time
import ctypes

kernel32 = ctypes.windll.kernel32
kernel32.SetConsoleCtrlHandler(None, False)


count = 0
while count < 5:
    try:
        print("In subprocess")
        time.sleep(1)
        count += 1
    except KeyboardInterrupt:
        print("Subprocess received Ctrl+C. Exiting...")
        break