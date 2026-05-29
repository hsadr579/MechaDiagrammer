import threading as t
import time

import numpy as np
import sounddevice as sd

from kokoro import KPipeline
import json

# ==========================================
# CONFIG
# ==========================================
VOICE_FILE="voices/kokoro_voices.json"
with open(VOICE_FILE, 'r') as fp:
        VOICE_PERSONAS= json.load(fp)

LANG_CODE = "a"

REPO_ID = "hexgrad/Kokoro-82M"
VOICE_NAME="christopher"
CHUNK_SIZE = 2048
CONFIG_FILE="config.json"
try:
    
    with open(CONFIG_FILE, 'r') as fp:
        configs = json.load(fp)
        if "TTS_voice" in configs:VOICE_NAME=configs["TTS_voice"]

except Exception:
    pass

VOICE=VOICE_PERSONAS[VOICE_NAME][0]
VOICE_PERSONALITY=VOICE_PERSONAS[VOICE_NAME][1]

# ==========================================
# GLOBALS
# ==========================================

speech_queue = []

speech_thread = None

SPEAKING = False

pipeline = None

stop_event = t.Event()

engine_lock = t.Lock()

_active_stream = None          # <-- NEW: reference to the live OutputStream
_active_stream_lock = t.Lock() # <-- NEW: protect it across threads


# ==========================================
# LOAD MODEL
# ==========================================

def load_pipeline():

    global pipeline

    if pipeline:
        return

    print(
        "Loading Kokoro..."
    )

    pipeline = KPipeline(

        repo_id=REPO_ID,

        lang_code=LANG_CODE

    )

    print(
        "Kokoro loaded."
    )


# ==========================================
# TEXT PREPROCESSING
# ==========================================

def preprocess_text(text):

    text = text.replace(
        "\n",
        " ... "
    )

    text = text.replace(
        "...",
        " . . . "
    )

    text = text.replace(
        "*",
        ""
    )

    text = text.replace(
        "(",
        " "
    )

    text = text.replace(
        ")",
        " "
    )

    text = text.replace(
        "~",
        "..."
    )

    import re

    text = re.sub(

        r'([A-Za-z])\1{3,}',

        lambda m:
        m.group(1) * 3,

        text

    )

    return text.strip()


# ==========================================
# PLAYBACK
# ==========================================
def play_audio(audio):

    global _active_stream

    stop_event.clear()

    try:

        audio = np.asarray(
            audio,
            dtype=np.float32
        )

        with sd.OutputStream(
            samplerate=24000,
            channels=1,
            dtype='float32'
        ) as stream:

            with _active_stream_lock:
                _active_stream = stream   # <-- NEW: register stream

            pos = 0

            while pos < len(audio):

                if stop_event.is_set():
                    break

                end = min(
                    pos + CHUNK_SIZE,
                    len(audio)
                )

                stream.write(
                    audio[pos:end]
                )

                pos = end

    except Exception as e:

        print(
            "Playback error:",
            e
        )

    finally:

        with _active_stream_lock:        # <-- NEW: clear on exit
            _active_stream = None


# ==========================================
# SPEAK
# ==========================================
def speak_text(text):

    global SPEAKING

    text = preprocess_text(
        text
    )

    SPEAKING = True

    try:

        generator = pipeline(
            text,
            voice=VOICE
        )

        for item in generator:

            if stop_event.is_set():
                break

            audio = item[-1]

            play_audio(audio)

    finally:

        SPEAKING = False

# ==========================================
# MAIN SPEECH THREAD
# ==========================================

def SpeakText():

    global SPEAKING

    load_pipeline()

    while True:

        if not speech_queue:

            time.sleep(0.01)

            continue

        command = speech_queue.pop(0)

        if command is None:

            break

        try:

            with engine_lock:

                speak_text(command)

        except Exception as e:

            print(
                "Speech error:",
                e
            )

        finally:

            SPEAKING = False


# ==========================================
# INTERRUPT CURRENT SPEECH
# ==========================================

def stop():
    """Stop the current utterance only. Thread stays alive for next item."""
    global SPEAKING

    stop_event.set()
    SPEAKING = False

    with _active_stream_lock:
        if _active_stream is not None:
            try:
                _active_stream.abort()
            except Exception:
                pass

    # Reset immediately so the thread can speak again
    stop_event.clear()


def stop_and_clear():
    """Stop current utterance AND discard everything queued after it."""
    speech_queue.clear()
    stop()


# ==========================================
# START SPEAKER THREAD
# ==========================================

def run_speaker():

    global speech_thread

    if speech_thread:

        return

    speech_thread = t.Thread(

        target=SpeakText,

        daemon=True

    )

    speech_thread.start()


# ==========================================
# STOP SPEAKER THREAD
# ==========================================
def stop_speaker():

    global SPEAKING

    stop_event.set()

    SPEAKING = False

    speech_queue.clear()

    try:

        sd.stop()

    except:

        pass
# ==========================================
# CHANGE VOICE
# ==========================================

def set_voice(name):

    global VOICE

    VOICE = name


# ==========================================
# AVAILABLE VOICES
# ==========================================
AVAILABLE_VOICES = [

    # American female
    "af_alloy",
    "af_aoede",
    "af_bella",
    "af_heart",
    "af_jessica",
    "af_kore",
    "af_nicole",
    "af_nova",
    "af_river",
    "af_sarah",
    "af_sky",

    # American male
    "am_adam",
    "am_echo",
    "am_eric",
    "am_fenrir",
    "am_liam",
    "am_michael",
    "am_onyx",
    "am_puck",

    # British female
    "bf_alice",
    "bf_emma",
    "bf_isabella",
    "bf_lily",

    # British male
    "bm_daniel",
    "bm_fable",
    "bm_george",
    "bm_lewis",
]


# ==========================================
# TEST
# ==========================================

if __name__ == "__main__":

    run_speaker()

    speech_queue.append(

        """
        Hello.
        Kokoro is now working.
        """

    )

    time.sleep(5)

    speech_queue.append(

        """
        STOP RIGHT THERE!
        This voice should sound much more expressive than Piper.
        """

    )

    while True:

        time.sleep(1)