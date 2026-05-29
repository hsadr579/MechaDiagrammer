import openai
from colorama import *
import pyttsx3
import threading as t
import time
import json
import os
def get_current_weather(args):
    print(f"@@@weather@@@{args["location"]}")

def open_notepad(args):
    os.system("notepad &")
TOOL_MAP = {
    "get_current_weather": {
        "function": get_current_weather,
        "description": "Fetches the current weather information for a specified location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "The city and state, e.g., 'San Francisco, CA'."},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"], "description": "The temperature unit, 'celsius' or 'fahrenheit'."}
            },
            "required": ["location"]
        }
    },
    "open_notepad": {
        "function": open_notepad,
        "description":"opens notepad app",
        "parameters": {
            "type": "object",
            "properties": {},
        },
        "required":[]
    }
}
def format_tools_for_prompt(tool_map):
    tools_list = []
    for name, tool_info in tool_map.items():
        tools_list.append({
            "type": "function",
            "function": {
                "name": name,
                "description": tool_info["description"],
                "parameters": tool_info["parameters"]
            }
        })
    return json.dumps(tools_list, indent=2)
_SYSTEM_PROMPT="""you are a home assistant which should answer general question and trigger some events using provided tools.
these are your tools:
{tools}
If you realized that user request is related to one of your available tools start your message with @(do not send anything before this) and then provide ONLY a JSON object containing the tool call.
your message must be in the following format(DO NOT SEND any explanation before or after this and do not use ```json {{}}``` format):

@{{"name": "tool_name", "arguments": {{"arg1": "value1", ...}}}}

otherwise(if user was just chatting or asking something unrelated to provided tools) just answer in plain text without reminding about your tools (no @ and no json no tool use offer) and try to answer in a concise way unless user asks you for more details.

when you are calling a tool, you should not try to answer users request based on your knowledge. just call the tool using provided method above and start with @.
"""
SYSTEM_PROMPT=_SYSTEM_PROMPT.format(tools=format_tools_for_prompt(TOOL_MAP))
# Queue to manage speech requests
speech_queue = []

# Function to convert text to speech
def SpeakText():
    engine = pyttsx3.init()
    while True:
        if len(speech_queue) == 0:
            time.sleep(0.005)
            continue
        command = speech_queue.pop(0) # Pop immediately after getting
        if command is None:
            break
        try:
            
            engine.say(command)
            engine.runAndWait()
        except Exception as e:
            print(f"Error during speech synthesis: {e}")
        

# Start a thread to process the speech queue
speech_thread = t.Thread(target=SpeakText)
speech_thread.start()

client = openai.OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="nokeyneeded"
)

noExit = True
# Changed to store message dictionaries for proper history management
conversation_history = []
init()
voice = True
history_enable=False

while noExit:
    # Limit history size (e.g., last 20 turns)
    if len(conversation_history) > 10:
        conversation_history = conversation_history[2:] # Remove the oldest user/assistant pair

    user_input = input(Fore.LIGHTRED_EX + "[you]: " + Fore.RESET)

    if user_input.startswith("\\"):
        command = user_input[1:]
        if command == "exit":
            noExit = False
        elif command == "voice_off":
            voice = False
            print(Fore.YELLOW + "\nVoice turned off\n" + Fore.RESET)
        elif command == "voice_on":
            voice = True
            print(Fore.YELLOW + "\nVoice turned on\n" + Fore.RESET)
        elif command == "hist":
            conv_display = ""
            for i, msg in enumerate(conversation_history):
                role = "[you]" if msg['role'] == 'user' else "[AI]"
                conv_display += f"{i+1}. {role}: {msg['content']}\n"
            print(Fore.YELLOW + "\nChat history:\n" + conv_display + Fore.RESET)
        elif command == "clear_hist":
            conversation_history = []
            print(Fore.YELLOW + "\nHistory cleared\n" + Fore.RESET)
        elif command =="hist_off":
            history_enable=False
            print(Fore.YELLOW + "\nHistory disabled\n" + Fore.RESET)
        elif command=='hist_on':
            history_enable=True
            print(Fore.YELLOW + "\nHistory enabled\n" + Fore.RESET)
        elif command == "del_hist_number":
            try:
                num_to_delete = int(input(Fore.YELLOW + "\nEnter message number to delete: " + Fore.RESET))
                if 1 <= num_to_delete <= len(conversation_history):
                    # Adjust index for 0-based list and consider pairs if needed
                    # For simplicity, deleting a single message entry. If you want to delete a user-AI turn, you'd delete two items.
                    del conversation_history[num_to_delete - 1]
                    print(Fore.YELLOW + "Message deleted.\n" + Fore.RESET)
                else:
                    print(Fore.RED + "Invalid message number.\n" + Fore.RESET)
            except ValueError:
                print(Fore.RED + "Please enter a valid number.\n" + Fore.RESET)
        continue
    

    # Add user message to history
    current_message={"role": "user", "content": user_input}
    if history_enable:
        conversation_history.append(current_message)

    # Prepare messages for the API, including the system prompt and conversation history
    messages_for_api = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] +( conversation_history if history_enable else [current_message])

    full_reply = ""
    try:
        # Use stream=True for streaming responses
        stream = client.chat.completions.create(
            model="phi3",
            temperature=0.1,
            messages=messages_for_api,
            stream=True,
            extra_body={"context": []}
        )
        
        print(Fore.GREEN + "\n[AI]: " + Fore.RESET, end="")
        i=0
        action=0
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if(not i and content ):
                if(content[0]=="@"):
                    action=1
            if content:
                if not action :print(content, end="", flush=True) # Print chunks as they arrive
                
                full_reply += content
            if(content):i+=1
        if not action:
            print("\n") # Newline after the full response

        # Add assistant's full reply to history
            conversation_history.append({"role": "assistant", "content": full_reply})

        # Add the response to the speech queue if voice is enabled
            if voice:
            #engine.stop()
                speech_queue.append(full_reply)
        else:
            if history_enable:conversation_history.pop()

            full_reply=full_reply[1:]
            end_j=0
            bracket_counter=0
            
            for i in full_reply:
                if(i=="{"):bracket_counter+=1
                elif (i=="}"):bracket_counter-=1
                if(bracket_counter==0):
                    break
                end_j+=1
            print(full_reply[:end_j+1])
            called_tool=json.loads(full_reply[:end_j+1])
            tool_args={}
            if "arguments" in called_tool.keys():
                tool_args=called_tool["arguments"]
            TOOL_MAP[called_tool["name"]]["function"](tool_args)
    except Exception as e:
        print(Fore.RED + f"\nError getting response from AI: {e}\n" + Fore.RESET)
        # Remove the last user message if API call failed to avoid incomplete history
        if conversation_history and conversation_history[-1]['role'] == 'user':
            conversation_history.pop()

# Stop the speech thread
speech_queue.append(None)
speech_thread.join()
