import speech_recognition as sr

def transcribe_wav(file_path: str, client=None) -> str:
    """Transcribe a WAV file to text using Google's free speech recognition API."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "[Could not understand audio]"
    except sr.RequestError as e:
        return f"[Speech recognition error: {e}]"