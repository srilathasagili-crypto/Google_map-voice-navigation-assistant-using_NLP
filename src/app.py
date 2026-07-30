"""
Streamlit visual demo for the NLP Voice Assistant.

Features:
- Real in-browser microphone recording (st.audio_input) transcribed via
  SpeechRecognition, OR type a command directly.
- Toggle between mock Maps data and live Nominatim/OSRM API calls.
- Visual breakdown of intent, confidence, and extracted entities.
- Spoken response playback via gTTS (browser-playable audio, works on
  any machine without needing a local TTS engine/speakers).

Run with:
    streamlit run app.py
"""

import io
import streamlit as st
import speech_recognition as sr
from gtts import gTTS

from pipeline import VoiceAssistantPipeline

st.set_page_config(page_title="NLP Voice Assistant", page_icon="🗺️", layout="centered")


@st.cache_resource
def load_pipeline(mock_maps: bool):
    return VoiceAssistantPipeline(mock_maps=mock_maps)


def transcribe_audio(audio_bytes: bytes) -> str:
    """Convert recorded audio bytes into text using Google's free STT API."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        st.error(f"STT service error: {e}")
        return ""


def text_to_speech_bytes(text: str) -> bytes:
    """Generate speech audio (mp3 bytes) from text using gTTS."""
    buf = io.BytesIO()
    tts = gTTS(text=text, lang="en")
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()


# --- Sidebar ---
st.sidebar.title("Settings")
mock_mode = st.sidebar.toggle(
    "Use mock Maps data",
    value=True,
    help="Turn off to make real calls to Nominatim/OSRM (requires internet access to those services).",
)
st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Supported commands:**\n"
    "- `navigate to <destination>`\n"
    "- `find nearest <hospital / atm / restaurant ...>`\n"
    "- `how is the traffic right now`\n"
    "- `avoid tolls` / `take the fastest route`\n"
    "- `where am i right now`\n"
    "- `cancel navigation`"
)

pipeline = load_pipeline(mock_maps=mock_mode)

st.title("🗺️ NLP Voice Assistant")
st.caption("Google Maps–style voice navigation — built with classical NLP, no LLMs.")

tab_voice, tab_text = st.tabs(["🎙️ Voice input", "⌨️ Text input"])

user_text = None

with tab_voice:
    st.write("Record a command using your microphone:")
    audio_value = st.audio_input("Speak your command")
    if audio_value is not None:
        with st.spinner("Transcribing..."):
            transcribed = transcribe_audio(audio_value.read())
        if transcribed:
            st.success(f"Transcribed: **{transcribed}**")
            user_text = transcribed
        else:
            st.warning("Couldn't understand the audio. Please try again or use text input.")

with tab_text:
    typed = st.text_input("Type a command", placeholder="e.g. navigate to central park")
    if st.button("Submit", key="text_submit") and typed:
        user_text = typed

if user_text:
    result = pipeline.process(user_text)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Detected Intent", result["intent"])
    with col2:
        st.metric("Confidence", f"{result['confidence']*100:.1f}%")

    if result["entities"]:
        st.write("**Extracted entities:**")
        st.json(result["entities"])
    else:
        st.write("**Extracted entities:** none")

    st.markdown("### 🔊 Assistant response")
    st.write(result["response"])

    with st.spinner("Generating speech..."):
        try:
            audio_bytes = text_to_speech_bytes(result["response"])
            st.audio(audio_bytes, format="audio/mp3")
        except Exception as e:
            st.info(f"Voice playback unavailable ({e}). Response shown as text above.")
