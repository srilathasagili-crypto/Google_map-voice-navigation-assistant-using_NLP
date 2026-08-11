```python
"""
Streamlit visual demo for the NLP Voice Assistant.

Features:
- Voice input
- Speech-to-text
- Text input
- Intent classification
- Entity extraction
- Nominatim geocoding
- OSRM driving directions
- Interactive Folium map
- Distance and travel time
- Text-to-speech

Run:
    streamlit run app.py
"""

import io

import streamlit as st
import speech_recognition as sr
from gtts import gTTS

import folium
from streamlit_folium import st_folium

from pipeline import VoiceAssistantPipeline


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Google Maps Voice Assistant",
    page_icon="🗺️",
    layout="centered"
)


# ============================================================
# LOAD PIPELINE
# ============================================================

@st.cache_resource
def load_pipeline(mock_maps: bool):
    return VoiceAssistantPipeline(
        mock_maps=mock_maps
    )


# ============================================================
# SPEECH TO TEXT
# ============================================================

def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Convert recorded microphone audio into text.
    """

    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(
            io.BytesIO(audio_bytes)
        ) as source:

            audio = recognizer.record(source)

        return recognizer.recognize_google(audio)

    except sr.UnknownValueError:
        return ""

    except sr.RequestError as e:
        st.error(
            f"Speech recognition service error: {e}"
        )
        return ""

    except Exception as e:
        st.error(
            f"Audio processing error: {e}"
        )
        return ""


# ============================================================
# TEXT TO SPEECH
# ============================================================

def text_to_speech_bytes(text: str) -> bytes:
    """
    Convert assistant response into MP3 audio.
    """

    buffer = io.BytesIO()

    tts = gTTS(
        text=text,
        lang="en"
    )

    tts.write_to_fp(buffer)

    buffer.seek(0)

    return buffer.read()


# ============================================================
# DRAW NAVIGATION MAP
# ============================================================

def display_route_map(route):
    """
    Display the driving route returned by OSRM.
    """

    if not route:
        return

    route_points = route.get(
        "route_points"
    )

    if not route_points:
        st.info(
            "No road route geometry is available."
        )
        return

    start_lat = route.get(
        "start_lat"
    )

    start_lon = route.get(
        "start_lon"
    )

    end_lat = route.get(
        "end_lat"
    )

    end_lon = route.get(
        "end_lon"
    )

    if (
        start_lat is None
        or start_lon is None
        or end_lat is None
        or end_lon is None
    ):
        st.warning(
            "Route coordinates are incomplete."
        )
        return

    # --------------------------------------------------------
    # CREATE MAP
    # --------------------------------------------------------

    navigation_map = folium.Map(
        location=[
            start_lat,
            start_lon
        ],
        zoom_start=13,
        control_scale=True
    )

    # --------------------------------------------------------
    # START MARKER
    # --------------------------------------------------------

    folium.Marker(
        location=[
            start_lat,
            start_lon
        ],
        popup=(
            "<b>📍 Start Location</b><br>"
            "Hyderabad, India"
        ),
        tooltip="📍 Start",
        icon=folium.Icon(
            color="green",
            icon="home"
        )
    ).add_to(
        navigation_map
    )

    # --------------------------------------------------------
    # DESTINATION MARKER
    # --------------------------------------------------------

    folium.Marker(
        location=[
            end_lat,
            end_lon
        ],
        popup=(
            "<b>🏁 Destination</b><br>"
            f"{route.get('destination', 'Destination')}"
        ),
        tooltip=(
            f"🏁 {route.get('destination', 'Destination')}"
        ),
        icon=folium.Icon(
            color="red",
            icon="flag"
        )
    ).add_to(
        navigation_map
    )

    # --------------------------------------------------------
    # DRAW DRIVING ROUTE
    # --------------------------------------------------------

    folium.PolyLine(
        locations=route_points,
        color="blue",
        weight=6,
        opacity=0.8,
        tooltip="🚗 Driving Route"
    ).add_to(
        navigation_map
    )

    # --------------------------------------------------------
    # FIT MAP
    # --------------------------------------------------------

    try:
        navigation_map.fit_bounds(
            [
                [
                    start_lat,
                    start_lon
                ],
                [
                    end_lat,
                    end_lon
                ]
            ]
        )
    except Exception:
        pass

    # --------------------------------------------------------
    # DISPLAY MAP
    # --------------------------------------------------------

    st_folium(
        navigation_map,
        width=700,
        height=500
    )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "⚙️ Settings"
)

mock_mode = st.sidebar.toggle(
    "Use mock Maps data",
    value=False,
    help=(
        "OFF = real Nominatim + OSRM routing. "
        "ON = demo/mock data."
    )
)

st.sidebar.markdown("---")

st.sidebar.markdown(
    """
### 🎯 Supported Commands

**Navigation**
- `navigate to Charminar`
- `navigate to Hyderabad railway station`

**Nearby places**
- `find nearest hospital`
- `find nearest ATM`
- `find nearest restaurant`

**Traffic**
- `how is the traffic right now`

**Route preference**
- `avoid tolls`
- `take the fastest route`

**Location**
- `where am i right now`

**Cancel**
- `cancel navigation`
"""
)

if mock_mode:
    st.sidebar.warning(
        "🧪 Mock Maps mode is ON"
    )
else:
    st.sidebar.success(
        "🌐 Real Maps mode is ON"
    )


# ============================================================
# LOAD PIPELINE
# ============================================================

pipeline = load_pipeline(
    mock_maps=mock_mode
)


# ============================================================
# MAIN TITLE
# ============================================================

st.title(
    "🗺️ NLP Voice Navigation Assistant"
)

st.caption(
    "Google Maps-style voice navigation "
    "using classical NLP + OpenStreetMap + OSRM."
)


# ============================================================
# INPUT TABS
# ============================================================

tab_voice, tab_text = st.tabs(
    [
        "🎙️ Voice Input",
        "⌨️ Text Input"
    ]
)

user_text = None


# ============================================================
# VOICE INPUT
# ============================================================

with tab_voice:

    st.subheader(
        "🎙️ Speak your command"
    )

    st.write(
        "Example: `Navigate to Charminar`"
    )

    audio_value = st.audio_input(
        "Record your voice"
    )

    if audio_value is not None:

        with st.spinner(
            "🎧 Converting speech to text..."
        ):

            transcribed = transcribe_audio(
                audio_value.read()
            )

        if transcribed:

            st.success(
                f"Transcribed: **{transcribed}**"
            )

            user_text = transcribed

        else:

            st.warning(
                "Couldn't understand the audio. "
                "Please try again."
            )


# ============================================================
# TEXT INPUT
# ============================================================

with tab_text:

    st.subheader(
        "⌨️ Type your command"
    )

    typed = st.text_input(
        "Enter navigation command",
        placeholder="e.g. navigate to Charminar"
    )

    submit_button = st.button(
        "🚀 Submit",
        key="text_submit"
    )

    if submit_button:

        if typed.strip():

            user_text = typed.strip()

        else:

            st.warning(
                "Please enter a command."
            )


# ============================================================
# PROCESS COMMAND
# ============================================================

if user_text:

    st.markdown("---")

    with st.spinner(
        "🧠 Understanding your command..."
    ):

        try:

            result = pipeline.process(
                user_text
            )

        except Exception as e:

            st.error(
                f"Something went wrong: {e}"
            )

            st.stop()


    # ========================================================
    # USER COMMAND
    # ========================================================

    st.markdown(
        "### 🗣️ Your Command"
    )

    st.info(
        user_text
    )


    # ========================================================
    # NLP ANALYSIS
    # ========================================================

    st.markdown(
        "### 🧠 NLP Analysis"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Detected Intent",
            result["intent"]
        )

    with col2:

        st.metric(
            "Confidence",
            f"{result['confidence'] * 100:.1f}%"
        )


    # ========================================================
    # ENTITIES
    # ========================================================

    st.markdown(
        "#### 🎯 Extracted Entities"
    )

    if result["entities"]:

        st.json(
            result["entities"]
        )

    else:

        st.write(
            "No entities detected."
        )


    # ========================================================
    # ASSISTANT RESPONSE
    # ========================================================

    st.markdown(
        "### 🔊 Assistant Response"
    )

    st.success(
        result["response"]
    )


    # ========================================================
    # NAVIGATION ROUTE
    # ========================================================

    route = result.get(
        "route"
    )

    if route:

        st.markdown(
            "### 🗺️ Navigation"
        )

        distance = route.get(
            "distance_km"
        )

        duration = route.get(
            "duration_min"
        )

        if (
            distance is not None
            and duration is not None
        ):

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "📏 Distance",
                    f"{distance:.2f} km"
                )

            with col2:

                st.metric(
                    "⏱️ Estimated Time",
                    f"{duration:.0f} min"
                )


        # ----------------------------------------------------
        # MAP
        # ----------------------------------------------------

        if route.get(
            "route_points"
        ):

            display_route_map(
                route
            )

        else:

            if mock_mode:

                st.info(
                    "🧪 Mock Maps is enabled. "
                    "Turn OFF 'Use mock Maps data' "
                    "to display the real driving route."
                )

            else:

                st.warning(
                    "The routing service did not "
                    "return route geometry."
                )


    # ========================================================
    # TEXT TO SPEECH
    # ========================================================

    st.markdown(
        "### 🔊 Voice Playback"
    )

    with st.spinner(
        "Generating speech..."
    ):

        try:

            audio_bytes = text_to_speech_bytes(
                result["response"]
            )

            st.audio(
                audio_bytes,
                format="audio/mp3"
            )

        except Exception as e:

            st.info(
                f"Voice playback unavailable "
                f"({e}). Response is shown above."
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "🗺️ NLP Voice Assistant | "
    "Classical NLP + OpenStreetMap + OSRM"
)
```

