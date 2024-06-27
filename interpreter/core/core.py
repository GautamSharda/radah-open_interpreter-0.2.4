"""
This file defines the Interpreter class.
It's the main file. `from interpreter import interpreter` will import an instance of this class.
"""
import json
import os
import requests
import threading
import time
import websocket
from datetime import datetime

from ..terminal_interface.terminal_interface import terminal_interface
from ..terminal_interface.utils.display_markdown_message import display_markdown_message
from ..terminal_interface.utils.local_storage_path import get_storage_path
from ..terminal_interface.utils.oi_dir import oi_dir
from .computer.computer import Computer
from .default_system_message import default_system_message
from .llm.llm import Llm
from .respond import respond
from .server import server
from .utils.telemetry import send_telemetry
from .utils.truncate_output import truncate_output


class OpenInterpreter:
    """
    This class (one instance is called an `interpreter`) is the "grand central station" of this project.

    Its responsibilities are to:

    1. Given some user input, prompt the language model.
    2. Parse the language models responses, converting them into LMC Messages.
    3. Send code to the computer.
    4. Parse the computer's response (which will already be LMC Messages).
    5. Send the computer's response back to the language model.
    ...

    The above process should repeat—going back and forth between the language model and the computer— until:

    6. Decide when the process is finished based on the language model's response.
    """

    def __init__(
        self,
        messages=None,
        offline=False,
        auto_run=False,
        verbose=False,
        debug=False,
        max_output=2800,
        safe_mode="off",
        shrink_images=False,
        force_task_completion=False,
        force_task_completion_message="""Proceed. You CAN run code on my machine. If you want to run code, start your message with "```"! If the entire task I asked for is done, say exactly 'The task is done.' If you need some specific information (like username or password) say EXACTLY 'Please provide more information.' If it's impossible, say 'The task is impossible.' (If I haven't provided a task, say exactly 'Let me know what you'd like to do next.') Otherwise keep going.""",
        force_task_completion_breakers=[
            "the task is done.",
            "the task is impossible.",
            "let me know what you'd like to do next.",
            "please provide more information.",
        ],
        anonymous_telemetry=os.getenv("ANONYMIZED_TELEMETRY", "True") == "True",
        in_terminal_interface=False,
        conversation_history=True,
        conversation_filename=None,
        conversation_history_path=get_storage_path("conversations"),
        os=False,
        speak_messages=False,
        llm=None,
        system_message=default_system_message,
        custom_instructions="",
        computer=None,
        sync_computer=True,
        import_computer_api=False,
        skills_path=None,
        import_skills=True,
        multi_line=False,
    ):
        # State
        self.messages = [] if messages is None else messages
        self.responding = False
        self.last_messages_count = 0

        # Radah
        self.websocket_server_url = "wss://agent-swarm-production.up.railway.app"
        self.agentID = "66039df5a8738d00a5260365"
        self.ws = None
        self.reconnect_count = 0

        # Settings
        self.offline = offline
        self.auto_run = auto_run
        self.verbose = verbose
        self.debug = debug
        self.max_output = max_output
        self.safe_mode = safe_mode
        self.shrink_images = shrink_images
        self.anonymous_telemetry = anonymous_telemetry
        self.in_terminal_interface = in_terminal_interface
        self.multi_line = multi_line

        # Loop messages
        self.force_task_completion = force_task_completion
        self.force_task_completion_message = force_task_completion_message
        self.force_task_completion_breakers = force_task_completion_breakers

        # Conversation history
        self.conversation_history = conversation_history
        self.conversation_filename = conversation_filename
        self.conversation_history_path = conversation_history_path

        # OS control mode related attributes
        self.os = os
        self.speak_messages = speak_messages

        # LLM
        self.llm = Llm(self) if llm is None else llm

        # These are LLM related
        self.system_message = system_message
        self.custom_instructions = custom_instructions

        # Computer
        self.computer = Computer(self) if computer is None else computer

        self.sync_computer = sync_computer
        self.computer.import_computer_api = import_computer_api

        # Skills
        if skills_path:
            self.computer.skills.path = skills_path

        self.import_skills = import_skills
        if import_skills:
            if self.verbose:
                print("Importing skills")
            self.computer.skills.import_skills()

    def connect_websocket(self):
        print("reached connect_websocket(): ", self.websocket_server_url)
        if self.websocket_server_url:
            print("[Debug, core.py, 138] Websocket server URL: ", self.websocket_server_url)
            self.ws = websocket.WebSocketApp(
                self.websocket_server_url,
                on_open=self.on_websocket_open,
                on_message=self.on_websocket_message,
                on_error=self.on_websocket_error,
                on_close=self.on_websocket_close
            )
            self.ws.run_forever()

    def on_websocket_open(self, ws):
        print("[DEBUG, core.py, line 148] Sending initial connection message to Radah websocket server")
        ws.send(json.dumps({ "type": "config", "promptRunning": False, "agentID": self.agentID, "connectionType": "workspace"}))
        print("[DEBUG, core.py, line 150] Web socket connection opened")

    def on_websocket_message(self, ws, message):
        print(f"[DEBUG, core.py, line 154] Received message: {message}")

    def on_websocket_error(self, ws, error):
        print(f"[DEBUG, core.py, line 157] WebSocket error: {error}")

    def on_websocket_close(self, ws, close_status_code, close_msg):
        print("[DEBUG, core.py, line 160] WebSocket connection closed")
        print(f"Close status code: {close_status_code}")
        print(f"Close message: {close_msg}")

        # questionable
        self.ws = None

        if self.reconnect_count > 10:
            print("[Debug, core.py, line 168] ", self.reconnect_count, " reconnect attempts... shutting down websocket connection.")
            return
        # Attempt to reconnect
        self.reconnect_websocket()

    def reconnect_websocket(self):

        print("Attempting to reconnect WebSocket...")
        
        # Close the existing connection if it's still open
        if self.ws:
            self.ws.close()
        
        # Reconnect to the WebSocket server
        time.sleep(0.1)
        self.reconnect_count += 1
        self.connect_websocket()


    def server(self, *args, **kwargs):
        server(self, *args, **kwargs)

    def wait(self):
        while self.responding:
            time.sleep(0.2)
        # Return new messages
        return self.messages[self.last_messages_count :]

    def chat(self, message=None, display=True, stream=False, blocking=True):
        try:
            self.responding = True
            if self.anonymous_telemetry and not self.offline:
                message_type = type(
                    message
                ).__name__  # Only send message type, no content
                send_telemetry(
                    "started_chat",
                    properties={
                        "in_terminal_interface": self.in_terminal_interface,
                        "message_type": message_type,
                        "os_mode": self.os,
                    },
                )

            print("[DEBUG, core.py, line 216] blocking=", blocking)
            if not blocking:
                chat_thread = threading.Thread(
                    target=self.chat, args=(message, display, stream, True)
                )  # True as in blocking = True
                chat_thread.start()
                chat_thread.daemon=True
                return

            if stream:
                return self._streaming_chat(message=message, display=display)

            # If stream=False, *pull* from the stream.
            for _ in self._streaming_chat(message=message, display=display):
                pass

            # Return new messages
            self.responding = False
            return self.messages[self.last_messages_count :]

        except Exception as e:
            self.responding = False
            if self.anonymous_telemetry and not self.offline:
                message_type = type(message).__name__
                send_telemetry(
                    "errored",
                    properties={
                        "error": str(e),
                        "in_terminal_interface": self.in_terminal_interface,
                        "message_type": message_type,
                        "os_mode": self.os,
                    },
                )

            raise

    def _streaming_chat(self, message=None, display=True):
        # Sometimes a little more code -> a much better experience!
        # Display mode actually runs interpreter.chat(display=False, stream=True) from within the terminal_interface.
        # wraps the vanilla .chat(display=False) generator in a display.
        # Quite different from the plain generator stuff. So redirect to that
        if display:
            yield from terminal_interface(self, message)
            return

        # One-off message
        if message or message == "":
            if message == "":
                message = "No entry from user - please suggest something to enter."

            ## We support multiple formats for the incoming message:
            # Dict (these are passed directly in)
            if isinstance(message, dict):
                if "role" not in message:
                    message["role"] = "user"
                self.messages.append(message)
            # String (we construct a user message dict)
            elif isinstance(message, str):
                self.messages.append(
                    {"role": "user", "type": "message", "content": message}
                )
            # List (this is like the OpenAI API)
            elif isinstance(message, list):
                self.messages = message

            # Now that the user's messages have been added, we set last_messages_count.
            # This way we will only return the messages after what they added.
            self.last_messages_count = len(self.messages)

            # DISABLED because I think we should just not transmit images to non-multimodal models?
            # REENABLE this when multimodal becomes more common:

            # Make sure we're using a model that can handle this
            # if not self.llm.supports_vision:
            #     for message in self.messages:
            #         if message["type"] == "image":
            #             raise Exception(
            #                 "Use a multimodal model and set `interpreter.llm.supports_vision` to True to handle image messages."
            #             )

            # This is where it all happens!
            yield from self._respond_and_store()

            # Save conversation if we've turned conversation_history on
            if self.conversation_history:
                # If it's the first message, set the conversation name
                if not self.conversation_filename:
                    first_few_words = "_".join(
                        self.messages[0]["content"][:25].split(" ")[:-1]
                    )
                    for char in '<>:"/\\|?*!':  # Invalid characters for filenames
                        first_few_words = first_few_words.replace(char, "")

                    date = datetime.now().strftime("%B_%d_%Y_%H-%M-%S")
                    self.conversation_filename = (
                        "__".join([first_few_words, date]) + ".json"
                    )

                # Check if the directory exists, if not, create it
                if not os.path.exists(self.conversation_history_path):
                    os.makedirs(self.conversation_history_path)
                # Write or overwrite the file
                with open(
                    os.path.join(
                        self.conversation_history_path, self.conversation_filename
                    ),
                    "w",
                ) as f:
                    json.dump(self.messages, f)
            return

        raise Exception(
            "`interpreter.chat()` requires a display. Set `display=True` or pass a message into `interpreter.chat(message)`."
        )

    def _respond_and_store(self):
        """
        Pulls from the respond stream, adding delimiters. Some things, like active_line, console, confirmation... these act specially.
        Also assembles new messages and adds them to `self.messages`.
        """

        # Utility function
        def is_active_line_chunk(chunk):
            return "format" in chunk and chunk["format"] == "active_line"

        last_flag_base = None

        for chunk in respond(self):

            if chunk["content"] == "":
                continue

            # Handle the special "confirmation" chunk, which neither triggers a flag or creates a message [Radah's versions runs on auto for now]
            if chunk["type"] == "confirmation":
                # Emit a end flag for the last message type, and reset last_flag_base
                if last_flag_base:
                    yield {**last_flag_base, "end": True}
                    last_flag_base = None
                yield chunk
                # We want to append this now, so even if content is never filled, we know that the execution didn't produce output.
                # ... rethink this though.
                self.messages.append(
                    {
                        "role": "computer",
                        "type": "console",
                        "format": "output",
                        "content": "",
                    }
                )
                continue

            # Check if the chunk's role, type, and format (if present) match the last_flag_base
            if (
                last_flag_base
                and "role" in chunk
                and "type" in chunk
                and last_flag_base["role"] == chunk["role"]
                and last_flag_base["type"] == chunk["type"]
                and (
                    "format" not in last_flag_base
                    or (
                        "format" in chunk
                        and chunk["format"] == last_flag_base["format"]
                    )
                )
            ):
                # If they match, append the chunk's content to the current message's content
                # (Except active_line, which shouldn't be stored)
                if not is_active_line_chunk(chunk):
                    self.messages[-1]["content"] += chunk["content"]
            else:
                # If they don't match, yield a end message for the last message type and a start message for the new one
                if last_flag_base:
                    print("[DEBUG, core.py, line 313] Sending chunk to Radah websocket: ", {**last_flag_base, "end": True})
                    self.ws.send(json.dumps({**last_flag_base, "end": True}))
                    yield {**last_flag_base, "end": True}

                last_flag_base = {"role": chunk["role"], "type": chunk["type"]}

                # Don't add format to type: "console" flags, to accomodate active_line AND output formats
                if "format" in chunk and chunk["type"] != "console":
                    last_flag_base["format"] = chunk["format"]

                print("[DEBUG, core.py, line 313] Sending chunk to Radah websocket: ", {**last_flag_base, "start": True})
                self.ws.send(json.dumps({**last_flag_base, "start": True}))
                yield {**last_flag_base, "start": True}

                # Add the chunk as a new message
                if not is_active_line_chunk(chunk):
                    self.messages.append(chunk)

            # Yield the chunk itself
            print("[DEBUG, core.py, line 313] Sending chunk to Radah websocket: ", chunk)
            self.ws.send(json.dumps(chunk))
            yield chunk

            # Truncate output if it's console output
            if chunk["type"] == "console" and chunk["format"] == "output":
                self.messages[-1]["content"] = truncate_output(
                    self.messages[-1]["content"], self.max_output
                )

        # Yield a final end flag
        if last_flag_base:
            print("[DEBUG, core.py, line 313] Sending chunk to Radah websocket: ", {**last_flag_base, "end": True})
            self.ws.send(json.dumps({**last_flag_base, "end": True}))
            print("[DEBUG, core.py, line 313] Sending stop agent message to Radah /PromptRunning")
            try:
                response = requests.get('https://agent-swarm-production.up.railway.app/workspace/promptComplete/' + self.agentID, headers={'Content-Type': 'application/json'})
                print("[Debug, core.py, line 352] GET /promptComplete response:", response.status_code)
            except Exception as e:
                print("Error occurred:", e)
            yield {**last_flag_base, "end": True}

    def reset(self):
        self.computer.terminate()  # Terminates all languages
        self.messages = []
        self.last_messages_count = 0

    def display_message(self, markdown):
        # This is just handy for start_script in profiles.
        display_markdown_message(markdown)

    def get_oi_dir(self):
        # Again, just handy for start_script in profiles.
        return oi_dir