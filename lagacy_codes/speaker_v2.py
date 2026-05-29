import threading as t
import time

import numpy as np
import sounddevice as sd

from piper.voice import PiperVoice


# ======================
# CONFIG
# ======================

VOICE_MODEL = (
    "voices/"
    "en_US-kristin-medium.onnx"
)

CHUNK_SIZE = 2048


# ======================
# GLOBALS
# ======================

speech_queue = []

speech_thread = None

SPEAKING = False

voice = None

audio_stream = None

stop_event = t.Event()

engine_lock = t.Lock()


# ======================
# LOAD MODEL
# ======================

def load_voice():

    global voice

    if voice:
        return

    try:

        print(
            "Loading Piper voice..."
        )

        voice = PiperVoice.load(
            VOICE_MODEL
        )

        print(
            "Voice loaded."
        )

    except Exception:

        print(
            "\nVoice load failed."
        )

        print(
            "Need BOTH:"
        )

        print(
            VOICE_MODEL
        )

        print(
            VOICE_MODEL + ".json"
        )

        raise


# ======================
# GENERATE AUDIO
# ======================

def generate_audio(text):

    chunks = []

    sample_rate = None

    for audio_chunk in voice.synthesize(text):

        if sample_rate is None:

            sample_rate = (
                audio_chunk.sample_rate
            )

        pcm = np.frombuffer(

            audio_chunk.audio_int16_bytes,

            dtype=np.int16

        )

        pcm = pcm.astype(
            np.float32
        )

        pcm /= 32768.0

        chunks.append(
            pcm
        )

    if not chunks:

        return (

            np.array(
                [],
                dtype=np.float32
            ),

            22050

        )

    audio = np.concatenate(
        chunks
    )

    return (
        audio,
        sample_rate
    )


# ======================
# PLAYBACK
# ======================

def play_audio(
    audio,
    samplerate
):

    global SPEAKING
    global audio_stream

    stop_event.clear()

    SPEAKING = True

    try:

        with sd.OutputStream(

            samplerate=samplerate,

            channels=1,

            dtype='float32'

        ) as stream:

            audio_stream = stream

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

        SPEAKING = False

        audio_stream = None


# ======================
# MAIN THREAD
# ======================

def SpeakText():

    load_voice()

    while True:

        if not speech_queue:

            time.sleep(
                0.01
            )

            continue

        command = speech_queue.pop(
            0
        )

        if command is None:

            break

        try:

            with engine_lock:

                audio, sr = generate_audio(
                    command
                )

                if len(audio):

                    play_audio(
                        audio,
                        sr
                    )

        except Exception as e:

            print(
                "Speech error:",
                e
            )

        finally:

            global SPEAKING

            SPEAKING = False


# ======================
# INTERRUPT
# ======================

def stop():

    global SPEAKING

    stop_event.set()

    SPEAKING = False

    speech_queue.clear()

    try:

        sd.stop()

    except:

        pass


# ======================
# START THREAD
# ======================

def run_speaker():

    global speech_thread

    if speech_thread:

        return

    speech_thread = t.Thread(

        target=SpeakText,

        daemon=True

    )

    speech_thread.start()


# ======================
# SHUTDOWN
# ======================

def stop_speaker():

    global speech_thread

    stop()

    if speech_thread:

        speech_queue.append(
            None
        )

        speech_thread.join()

        speech_thread = None


# ======================
# TEST
# ======================

if __name__=="__main__":

    run_speaker()

    speech_queue.append(
        "Hello. Piper is working."
    )

    time.sleep(2)

    stop()

    time.sleep(1)

    speech_queue.append(
        "This speech should work after interruption."
    )

    while True:

        time.sleep(1)