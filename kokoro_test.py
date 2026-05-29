from kokoro import KPipeline
import sounddevice as sd

pipeline = KPipeline(lang_code='a')

text = """
hello there I am kokoro. how can I assist you today?


"""

generator = pipeline(
    text,
    voice='af_bella'
)

for _, _, audio in generator:

    sd.play(audio, 24000)
    sd.wait()