import pyautogui
pyautogui.FAILSAFE = False
import time
import os
import subprocess
import threading

def launchSubprocess():
    directory = r"C:\\Code\\open_interpreter-0.2.4"

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

    def read_from_process():
        for line in open_interpreter_process.stdout:
            print(line.strip())
        for line in open_interpreter_process.stderr:
            print(f"Error: {line.strip()}")

    threading.Thread(target=read_from_process, daemon=True).start()
    return open_interpreter_process


#poetry run interpreter --os --api_key sk-proj-mt9D5KEcHeqSrvV5NGGhT3BlbkFJ6wEkplsIDlew2QqNEgOg --model openai/gpt-4
