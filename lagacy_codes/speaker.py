import threading as t
import pyttsx3
import time
speech_queue = []
speech_thread=None
SPEAKING=False
def SpeakText():
    global SPEAKING
    engine = pyttsx3.init()
    while True:
        SPEAKING=False
        if not speech_queue:
            time.sleep(0.01)
            continue
        command = speech_queue.pop(0)
        if command is None:
            break
        
        try:
            
            engine.say(command)
            SPEAKING=True
            engine.runAndWait()
        except Exception as e:
            print(f"Speech error: {e}")
        
def run_speaker():
    global speech_thread
    speech_thread = t.Thread(target=SpeakText, daemon=True)
    speech_thread.start()
def stop_speaker():
    global speech_thread
    if(speech_thread):
        speech_queue.append(None)
        speech_thread.join()
        speech_thread=None