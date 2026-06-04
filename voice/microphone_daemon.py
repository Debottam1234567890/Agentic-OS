# pyrefly: ignore [missing-import]
import sounddevice as sd
# pyrefly: ignore [missing-import]
import soundfile as sf
def record_scratch_audio(duration=5, sample_rate=16000, out_file="voice_scratch.wav") -> str:
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="int16")
    sd.wait()
    sf.write(out_file, recording, sample_rate)
    return out_file