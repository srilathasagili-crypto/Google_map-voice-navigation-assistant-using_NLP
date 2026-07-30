# NLP-Based Google Maps Voice Assistant (No LLMs)

A voice-controlled navigation assistant built entirely with classical NLP
techniques — no Large Language Models. Speech in, structured NLP
processing, Maps API lookup, template-based speech out.

## Pipeline

```
Voice Input --> STT --> Text Preprocessing --> TF-IDF --> Intent Classifier (SVM)
                                                              |
                                                              v
                                                    Rule-based NER (entities)
                                                              |
                                                              v
                                                   Maps API (Nominatim/OSRM)
                                                              |
                                                              v
                                                    Response Template Engine
                                                              |
                                                              v
                                                             TTS --> Voice Output
```

## Project structure

```
maps_voice_assistant/
├── data/
│   └── intents.csv          # Labeled training data (text, intent)
├── models/
│   ├── intent_classifier.pkl
│   └── tfidf_vectorizer.pkl
├── src/
│   ├── preprocess.py        # Tokenization, stopwords, lemmatization
│   ├── intent_classifier.py # TF-IDF + SVM/LogReg training + inference
│   ├── ner_rules.py          # Rule-based entity extraction
│   ├── maps_api.py           # Nominatim geocoding + OSRM routing
│   ├── response_templates.py # Template-based NLG (no LLM)
│   ├── speech_io.py           # STT (SpeechRecognition) + TTS (pyttsx3)
│   └── pipeline.py            # Main orchestrator + CLI
└── requirements.txt
```

## Supported intents

| Intent | Example | Entities extracted |
|---|---|---|
| `navigate` | "take me to the airport" | destination |
| `search_nearby` | "find nearest hospital" | place_type |
| `traffic_info` | "how is the traffic right now" | — |
| `route_preference` | "avoid tolls please" | route_preference |
| `cancel` | "stop navigation" | — |
| `current_location` | "where am i right now" | — |

## Streamlit visual demo (recommended for interviews/portfolio)

`src/app.py` gives you a browser-based UI with **real in-browser
microphone recording** (via `st.audio_input`), a toggle to switch between
mock and live Maps data, and playable voice responses (via gTTS) — much
more demoable than the terminal CLI.

```bash
cd src
streamlit run app.py
```

This opens a local web page where you can:
- Record your voice directly in the browser (transcribed via
  SpeechRecognition + Google's free Web Speech API)
- Or type a command in the "Text input" tab
- See the detected intent, confidence score, and extracted entities
  rendered visually
- Hear the assistant's spoken response played back in-browser

Toggle **"Use mock Maps data"** off in the sidebar once you have a normal
internet connection to test real Nominatim/OSRM API calls.

## CLI demo (terminal mode)

```bash
pip install -r requirements.txt
cd src
python3 intent_classifier.py   # trains and saves the model
python3 pipeline.py            # runs the interactive assistant (text mode)
```

To use real microphone/speaker instead of text mode, run:
```python
from pipeline import run_cli
run_cli(use_microphone=True)
```
(Requires a working microphone and `pyaudio` installed.)

## Design notes / talking points

- **Why SVM over Logistic Regression**: `intent_classifier.py` trains both
  and picks the better performer — this is a real train/compare step,
  not an assumption.
- **Why rule-based NER instead of spaCy's statistical NER**: our entity
  set (place types, destinations, route preferences) is small,
  domain-specific, and closed — gazetteers/regex are more precise here
  than a general-purpose NER model trained on news text.
- **Why extractive templates instead of generative text (no LLM)**: fully
  deterministic, explainable, and zero hallucination risk — every
  response is traceable to a fixed template + real data.
- **MOCK_MAPS fallback**: Nominatim/OSRM are free public APIs with strict
  rate limits (and may be blocked on restricted networks). The pipeline
  falls back to realistic mock data so the NLP logic can still be fully
  demoed and tested offline.

## Evaluation results

Trained on an expanded dataset of 280 examples across 6 intents
(`src/generate_dataset.py` generates this from templates + slot values
for destinations/place-types/preferences, ensuring real phrasing variety
rather than duplicated examples).

| Model | Accuracy |
|---|---|
| Logistic Regression (baseline) | 91.07% |
| **SVM (deployed)** | **98.21%** |

SVM was selected for deployment based on this comparison. Confusion
matrix on the held-out test set (56 examples) showed only **one
misclassification** — a `current_location` example confused with
`search_nearby`, which makes sense given phrasing overlap ("where can I
find...") and is a reasonable, explainable error to discuss in an
interview.

To regenerate the dataset or retrain:
```bash
cd src
python3 generate_dataset.py   # regenerates data/intents.csv
python3 intent_classifier.py # retrains + prints accuracy + confusion matrix
```

## Further improvement ideas (good interview talking points)

- Add more real (non-templated) examples with typos/informal speech to
  test robustness beyond templated phrasing
- Try cross-validation instead of a single train/test split for more
  reliable accuracy estimates on this dataset size
- Expand the `current_location` vs `search_nearby` boundary with more
  contrastive examples, since that's the one confusion observed
