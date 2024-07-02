import logging
import pyautogui
pyautogui.FAILSAFE = False
import time
from flask import Flask, request
from flask.cli import AppGroup
from flask_cors import CORS
import base64
import requests
import io
from io import BytesIO
from werkzeug.serving import run_simple
import sys
import os
import subprocess
import threading
import signal
import obsws_python as obs
import psutil

DONE = True
OBS_RESTART_COUNT = 0
app = Flask(__name__)
CORS(app)

directory = r"D:\\Users\\Demo2\\open_interpreter-0.2.4"
os.chdir(directory)

startup_info = subprocess.STARTUPINFO()
startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
# reka: a7dad22ea5b2e1b5059a882ff7fd0ed6454d24654c9734679cefdc9762990a04	
open_interpreter_process = subprocess.Popen(
    # ["poetry", "run", "interpreter", "--os", "--api_key", "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", "--model", "anthropic/claude-3-haiku-20240307"],
    ["poetry", "run", "interpreter", "--os", "--api_key", "sk-proj-mt9D5KEcHeqSrvV5NGGhT3BlbkFJ6wEkplsIDlew2QqNEgOg", "--model", "openai/gpt-4o"],
    # ["poetry", "run", "interpreter", "--os", "--api_key", "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", "--model", "huggingface/Efficient-Large-Model/Llama-3-VILA1.5-8B"],
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    startupinfo=startup_info,
    text=True,
    cwd=directory
)
print("[DEBUG] Started process: ", open_interpreter_process.pid)

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
        print(f"Error starting OBS stream: {str(e)}.")
        time.sleep(5)
        if OBS_RESTART_COUNT < 3:
            print("Retrying...")
            start_obs_stream()
            OBS_RESTART_COUNT += 1
        else:
            print("Retying limit exceeded.")

# Start OBS Studio and then start the stream
start_obs_studio()
start_obs_stream()

def read_from_process():
    for line in open_interpreter_process.stdout:
        print(line.strip())
    for line in open_interpreter_process.stderr:
        print(f"Error: {line.strip()}")

threading.Thread(target=read_from_process, daemon=True).start()

@app.route('/message', methods=['POST'])
def handle_message():
    # global DONE
    message = request.json['message']
    print("[DEBUG /message] Sending message to OI: ", message)
    try:
        open_interpreter_process.stdin.write(message + "\n")
        open_interpreter_process.stdin.flush()
        # DONE = False
    except Exception as e:
        print(f"Error sending message to subprocess: {str(e)}")
    # Can probably remove
    # while not DONE:
    #    time.sleep(0)
    return 'Message sent to subprocess'

@app.route('/done', methods=['GET'])
def doneFunction():
    global DONE
    print('reached /done')
    DONE = True
    return 'Done'

@app.route('/stop', methods=['GET'])
def stop():
    #breakpoint()
    print("[DEBUG] Sending CTRL+C signal to the subprocess...")
    open_interpreter_process.send_signal(signal.CTRL_C_EVENT)
            # try:
            #     try:
            #         # Send CTRL+C signal to the subprocess
            #         print("[DEBUG] Sending CTRL+C signal to the subprocess...")
            #         open_interpreter_process.send_signal(signal.CTRL_C_EVENT)


            # Wait for the subprocess to finish
            # print("[DEBUG] Waiting for the subprocess to finish...")
            #open_interpreter_process.wait()
            # print(f"Wait")
        # except KeyboardInterrupt:
        #     print("[DEBUG] Parent process received KeyboardInterrupt. Ignoring...")

    # print("[DEBUG] Subprocess finished with exit code:", open_interpreter_process.returncode)
    print("[DEBUG] Sent signal.")
    print("[DEBUG] Parent process continues execution.")

    return 'Agent stopped'

@app.route('/test', methods=['GET'])
def test():
    print('Live')
    return 'Live'

def signal_handler(sig, frame):
    os.write(sys.stdout.fileno(), b"[DEBUG] Parent process received SIGINT (CTRL-C). Ignoring...\n")
    # print("[DEBUG] Parent process received SIGINT (CTRL-C). Ignoring...")

if __name__ == '__main__':
    # signal.signal(signal.SIGINT, signal_handler)
    run_simple('0.0.0.0', 8000, app)