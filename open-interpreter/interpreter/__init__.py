import signal
import sys
from .core.computer.terminal.base_language import BaseLanguage
from .core.core import OpenInterpreter


print('we are at init.py')
interpreter = OpenInterpreter()
computer = interpreter.computer

def signal_handler(sig, frame):
    print('WE HAVE RECIEVED A SIGNAL')
    print(interpreter)
    print("computer ^^")
    sys.stdout.flush()
    interpreter.computer.terminate()
    


#signal.signal(signal.SIGINT, signal_handler)



#     ____                      ____      __                            __
#    / __ \____  ___  ____     /  _/___  / /____  _________  ________  / /____  _____
#   / / / / __ \/ _ \/ __ \    / // __ \/ __/ _ \/ ___/ __ \/ ___/ _ \/ __/ _ \/ ___/
#  / /_/ / /_/ /  __/ / / /  _/ // / / / /_/  __/ /  / /_/ / /  /  __/ /_/  __/ /
#  \____/ .___/\___/_/ /_/  /___/_/ /_/\__/\___/_/  / .___/_/   \___/\__/\___/_/
#      /_/                                         /_/
