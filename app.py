import pyautogui
pyautogui.FAILSAFE = False
import time
from flask import Flask, request
from flask_cors import CORS
from werkzeug.serving import run_simple
import signal

from methods.obs import start_obs_studio, start_obs_stream 
from methods.launchSubprocess import launchSubprocess

DONE = True
IS_PATRICKS_MAC = True



## -------- Initialize Codebase -------


open_interpreter_process = launchSubprocess(IS_PATRICKS_MAC)

# Start OBS Studio and then start the stream
if not IS_PATRICKS_MAC:
    start_obs_studio()
    start_obs_stream()


## ------------------------------------


app = Flask(__name__)
CORS(app)

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
    try:
        try:
            # Send CTRL+C signal to the subprocess
            print("[DEBUG] Sending CTRL+C signal to the subprocess...")
            open_interpreter_process.send_signal(signal.CTRL_C_EVENT)


            # Wait for the subprocess to finish
            print("[DEBUG] Waiting for the subprocess to finish...")
            open_interpreter_process.wait()
            print(f"Wait")
        except KeyboardInterrupt:
            print("[DEBUG] Parent process received KeyboardInterrupt. Ignoring...")

        print("[DEBUG] Subprocess finished with exit code:", open_interpreter_process.returncode)
        print("[DEBUG] Parent process continues execution.")

        return 'Agent stopped'
    except Exception as e:
        print(f"Error sending CTRL+C signal to subprocess: {str(e)}")
        return 'Error stopping agent'

@app.route('/test', methods=['GET'])
def test():
    print('Live')
    return 'Live'

def signal_handler(sig, frame):
    print("[DEBUG] Parent process received SIGINT (CTRL-C). Ignoring...")



if __name__ == '__main__':
    # signal.signal(signal.SIGINT, signal_handler)
    run_simple('0.0.0.0', 8000, app)



