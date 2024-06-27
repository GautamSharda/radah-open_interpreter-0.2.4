import psutil
import os
import subprocess
import time
import obsws_python as obs


def kill_obs_processes():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'obs64.exe':
            proc.kill()
            print("Existing OBS process killed")

# Start OBS Studio
def start_obs_studio():
    directory = r"C:\\Program Files\\obs-studio\\bin\\64bit"  # Replace with the actual path to your OBS Studio executable
    os.chdir(directory)

    kill_obs_processes()

    # Start OBS Studio without opening the user interface
    subprocess.Popen(["obs64.exe", "--disable-shutdown-check", "--minimize-to-tray"], creationflags=subprocess.DETACHED_PROCESS) # , "--startstreaming"
    time.sleep(6) # Wait for open

# Start OBS stream
def start_obs_stream():
    host = "localhost"
    port = 4444
    # password = "your_obs_websocket_password"
    cl = obs.ReqClient(host=host, port=port) #, password=password)

    try:
        # print(cl.get_output_list().outputs)
        # Set the stream settings
        # stream_settings = {
        #     "server": "rtmp://173.255.225.188/stream",
        #     "key": "teststream?pwd=Gautam151102"
        # }
        # cl.set_output_settings("rtmp_output", stream_settings)

        # Start streaming
        cl.start_stream()
        print("OBS streaming started")
    except Exception as e:
        print(f"Error starting OBS stream: {str(e)}")