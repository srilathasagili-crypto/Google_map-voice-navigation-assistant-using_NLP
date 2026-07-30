"""
Speech I/O layer: Speech-to-Text and Text-to-Speech.

This is intentionally kept as a thin wrapper — the "intelligence" of this
project is the NLP pipeline (intent classification + NER), not the speech
conversion itself. Uses:
  - SpeechRecognition (with Google's free Web Speech API) for STT
  - pyttsx3 (offline TTS engine) for TTS

Both gracefully fall back to text-based I/O if microphone/audio hardware
isn't available (e.g., in a headless server or this sandboxed environment),
so the rest of the pipeline can still be developed/tested without a mic.
"""

import sys

try:
    import speech_recognition as sr
    _SR_AVAILABLE = True
except ImportError:
    _SR_AVAILABLE = False

try:
    import pyttsx3
    _TTS_ENGINE = pyttsx3.init()
    _TTS_AVAILABLE = True
except Exception:
    _TTS_AVAILABLE = False


def listen(use_microphone: bool = True) -> str:
    """
    Capture voice input and convert to text.
    Falls back to keyboard input if no microphone is available/detected.
    """
    if use_microphone and _SR_AVAILABLE:
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                print("Listening... (speak now)")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text
        except Exception as e:
            print(f"[STT unavailable, falling back to text input] ({e})")

    # Fallback: text input (used for testing without a microphone,
    # e.g. in this sandboxed dev environment)
    return input("Type your command: ")


def speak(text: str, use_audio: bool = True):
    """
    Convert text response to speech.
    Falls back to printing if TTS engine/audio output isn't available.
    """
    print(f"Assistant: {text}")
    if use_audio and _TTS_AVAILABLE:
        try:
            _TTS_ENGINE.say(text)
            _TTS_ENGINE.runAndWait()
        except Exception as e:
            print(f"[TTS playback unavailable] ({e})")


if __name__ == "__main__":
    # Text-mode test (since this sandbox has no mic/speaker)
    user_text = listen(use_microphone=False)
    speak(f"You said: {user_text}", use_audio=False)
