try:
    import sounddevice as sd
    import soundfile as sf
    _AUDIO_AVAILABLE = True
except OSError:
    _AUDIO_AVAILABLE = False
def record_scratch_audio(duration=5, sample_rate=16000, out_file='voice_scratch.wav') -> str:
    if not _AUDIO_AVAILABLE:
        raise RuntimeError(
            'PortAudio library not found. '
            'Install it with: sudo apt-get update && sudo apt-get install portaudio19-dev (Linux) '
            'or: brew install portaudio (macOS)'
        )
    recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()
    sf.write(out_file, recording, sample_rate)
    return out_file
