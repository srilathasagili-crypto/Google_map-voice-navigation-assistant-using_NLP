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
    page_title="NLP Voice Navigation Assistant",
    page_icon="🗺️",
    layout="centered"
)


# ============================================================
# SESSION STATE
# ============================================================

if "user_text" not in st.session_state:
    st.session_state.user_text = None

if "result" not in st.session_state:
    st.session_state.result = None


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

    buffer = io.BytesIO()

    tts = gTTS(
        text=text,
        lang="en"
    )

    tts.write_to_fp(buffer)

    buffer.seek(0)

    return buffer.read()


# ============================================================
# DISPLAY NAVIGATION MAP
# ============================================================

def display_route_map(route):

    if not route:
        return

    route_points = route.get(
        "route_points",
        []
    )

    if not route_points:

        st.warning(
            "No road route geometry was returned."
        )

        return

    start_lat = route.get("start_lat")
    start_lon = route.get("start_lon")

    end_lat = route.get("end_lat")
    end_lon = route.get("end_lon")

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


    # ========================================================
    # CREATE MAP
    # ========================================================

    navigation_map = folium.Map(

        location=[
            start_lat,
            start_lon
        ],

        zoom_start=10,

        control_scale=True
    )


    # ========================================================
    # START MARKER
    # ========================================================

    folium.Marker(

        location=[
            start_lat,
            start_lon
        ],

        popup=(
            "<b>📍 Start</b><br>"
            f"{route.get('origin', 'Starting Point')}"
        ),

        tooltip="Start",

        icon=folium.Icon(
            color="green",
            icon="home"
        )

    ).add_to(
        navigation_map
    )


    # ========================================================
    # DESTINATION MARKER
    # ========================================================

    folium.Marker(

        location=[
            end_lat,
            end_lon
        ],

        popup=(
            "<b>🏁 Destination</b><br>"
            f"{route.get('destination', 'Destination')}"
        ),

        tooltip="Destination",

        icon=folium.Icon(
            color="red",
            icon="flag"
        )

    ).add_to(
        navigation_map
    )


    # ========================================================
    # DRAW ROAD ROUTE
    # ========================================================

    folium.PolyLine(

        locations=route_points,

        color="blue",

        weight=6,

        opacity=0.8,

        tooltip="Driving Route"

    ).add_to(
        navigation_map
    )


    # ========================================================
    # FIT MAP
    # ========================================================

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


    # ========================================================
    # DISPLAY
    # ========================================================

    st_folium(

        navigation_map,

        width=700,

        height=500
    )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("⚙️ Settings")


mock_mode = st.sidebar.toggle(

    "Use mock Maps data",

    value=False,

    help=(
        "OFF = real Nominatim + OSRM routing. "
        "ON = mock/demo data."
    )
)


st.sidebar.markdown("---")


st.sidebar.markdown(
"""
### Supported Commands

**Navigation**

- Navigate to Charminar
- Navigate to Hyderabad railway station
- Navigate from Vijayawada to Guntur
- Directions from Hyderabad to Warangal
- Go from Secunderabad to Charminar

**Nearby**

- Find nearest hospital
- Find nearest ATM
- Find nearest restaurant
- Find nearest pharmacy

**Traffic**

- How is the traffic right now

**Route preference**

- Avoid tolls
- Take the fastest route

**Location**

- Where am I right now

**Cancel**

- Cancel navigation
"""
)


if mock_mode:

    st.sidebar.warning(
        "Mock Maps mode is ON"
    )

else:

    st.sidebar.success(
        "Real Maps mode is ON"
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
    "Classical NLP + OpenStreetMap + OSRM"
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


# ============================================================
# VOICE INPUT
# ============================================================

with tab_voice:

    st.subheader(
        "🎙️ Speak your command"
    )

    st.write(
        "Example: "
        "`Navigate from Vijayawada to Guntur`"
    )

    audio_value = st.audio_input(
        "Record your voice"
    )


    if audio_value is not None:

        with st.spinner(
            "Converting speech to text..."
        ):

            transcribed = transcribe_audio(
                audio_value.read()
            )


        if transcribed:

            st.success(
                f"Transcribed: **{transcribed}**"
            )

            st.session_state.user_text = transcribed

            # Process immediately
            try:

                st.session_state.result = (
                    pipeline.process(
                        transcribed
                    )
                )

            except Exception as e:

                st.error(
                    f"Something went wrong: {e}"
                )


        else:

            st.warning(
                "Couldn't understand the audio."
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

        placeholder=(
            "e.g. Navigate from Vijayawada to Guntur"
        )
    )


    submit_button = st.button(
        "🚀 Submit",
        key="text_submit"
    )


    if submit_button:

        if typed.strip():

            st.session_state.user_text = (
                typed.strip()
            )

            with st.spinner(
                "Understanding your command..."
            ):

                try:

                    st.session_state.result = (
                        pipeline.process(
                            st.session_state.user_text
                        )
                    )

                except Exception as e:

                    st.error(
                        f"Something went wrong: {e}"
                    )

        else:

            st.warning(
                "Please enter a command."
            )


# ============================================================
# SHOW RESULT
# ============================================================

if st.session_state.result:

    result = st.session_state.result

    user_text = st.session_state.user_text


    st.markdown("---")


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
    # ROUTE
    # ========================================================

    route = result.get(
        "route"
    )


    if route:

        st.markdown(
            "## 🗺️ Navigation"
        )


        # ====================================================
        # ORIGIN AND DESTINATION
        # ====================================================

        origin = route.get(
            "origin",
            "Starting point"
        )

        destination = route.get(
            "destination",
            "Destination"
        )


        st.write(
            f"📍 **{origin}**"
        )

        st.write(
            "⬇️"
        )

        st.write(
            "🚗 **Driving route**"
        )

        st.write(
            "⬇️"
        )

        st.write(
            f"🏁 **{destination}**"
        )


        # ====================================================
        # DISTANCE + TIME
        # ====================================================

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


        # ====================================================
        # ACTUAL MAP
        # ====================================================

        if route.get(
            "route_points"
        ):

            st.markdown(
                "### 🚗 Driving Route"
            )

            display_route_map(
                route
            )

        else:

            st.warning(
                "No road route was returned."
            )


        # ====================================================
        # TURN-BY-TURN DIRECTIONS
        # ====================================================

        directions = route.get(
            "directions",
            []
        )


        if directions:

            st.markdown(
                "### 🧭 Turn-by-Turn Directions"
            )


            for index, step in enumerate(
                directions,
                1
            ):

                instruction = step.get(
                    "instruction",
                    "Continue"
                )

                distance_m = step.get(
                    "distance_m",
                    0
                )


                if distance_m >= 1000:

                    distance_text = (
                        f"{distance_m / 1000:.2f} km"
                    )

                else:

                    distance_text = (
                        f"{distance_m:.0f} m"
                    )


                st.write(
                    f"**{index}.** "
                    f"{instruction} "
                    f"— `{distance_text}`"
                )


        else:

            st.info(
                "Turn-by-turn directions are "
                "not available for this route."
            )


    # ========================================================
    # VOICE PLAYBACK
    # ========================================================

    st.markdown(
        "### 🔊 Voice Playback"
    )


    with st.spinner(
        "Generating speech..."
    ):

        try:

            audio_bytes = (
                text_to_speech_bytes(
                    result["response"]
                )
            )


            st.audio(
                audio_bytes,
                format="audio/mp3"
            )


        except Exception as e:

            st.info(
                f"Voice playback unavailable: {e}"
            )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "NLP Voice Assistant | "
    "OpenStreetMap + OSRM"
)
