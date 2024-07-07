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
from methods.launchSubprocess import launchSubprocess
from methods.obs import start_obs_stream, start_obs_studio

print('at app.py')
time.sleep(5)
print('first sleep finished')
time.sleep(200)
print('second sleep finished')

DONE = True
app = Flask(__name__)
CORS(app)

open_interpreter_process = launchSubprocess()


# Start OBS Studio and then start the stream
start_obs_studio()
start_obs_stream()

@app.route('/message', methods=['POST'])
def handle_message():
    message = request.json['message']
    print("[DEBUG /message] Sending message to OI: ", message)
    try:
        open_interpreter_process.stdin.write(message + "\n")
        open_interpreter_process.stdin.flush()
    except Exception as e:
        print(f"Error sending message to subprocess: {str(e)}")
    return 'Message sent to subprocess'

@app.route('/stop', methods=['GET'])
def stop():
    #breakpoint()
    print("[DEBUG] Sending CTRL+C signal to the subprocess...")
    open_interpreter_process.send_signal(signal.CTRL_C_EVENT)
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