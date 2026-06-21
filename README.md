# 🏋️‍♀️ RepForge: Computer Vision Meets Live LLM Voice Coaching, Rep by Rep

A computer-vision fitness coach that watches you train through your webcam, scores your form rep-by-rep, detects fatigue before you do, and speaks live corrections powered by an LLM, all running in a Streamlit app.

Built from scratch to deliver real-time exercise tracking, biomechanical form analysis, fatigue detection, session-aware AI coaching, and persistent workout analytics, going beyond a typical rep-counter application.

---

## FEATURES

- **Real-time pose tracking**: MediaPipe `PoseLandmarker` processes the webcam feed frame-by-frame via `streamlit-webrtc`.
- **7 exercises supported**: Squats, Push-ups, Bicep Curls (Dumbbell), Shoulder Press, Lunges, Deadlifts, and Planks, each with a dedicated detector class.
- **Joint-angle form scoring**: every exercise calculates a live 0–100 form score from joint angles (e.g. knee angle, torso lean, elbow drift, back arch) using a penalty-based scoring model.
- **Fatigue detection**: compares the duration of recent reps against early reps in the set; if pace drops significantly, a fatigue flag is raised and logged.
- **Posture safety monitoring**: derives a basic injury-risk level (Low / Medium / High) from spinal angle in real time.
- **AI voice coaching**: a Groq-hosted LLM (`llama-3.3-70b-versatile`) generates short, motivating spoken feedback for key events (workout start, set complete, form issues, workout complete), converted to audio via Groq's Orpheus TTS model (with automatic gTTS fallback for resilience) and played back automatically.
- **Session-aware coaching**: the coach is given a summary of the user's recent sessions (reps, form score) so feedback can reference real progress, not just the current set.
- **Persistent workout history**: every user, session, set, and fatigue event is stored in SQLite, with an aggregated history table shown in the app.
- **Custom UI**: a midnight blue / glass-card themed interface with a custom font and live skeleton overlay drawn directly on the video feed.

---

## HOW IT WORKS

```
Webcam frame
     │
     ▼
MediaPipe PoseLandmarker  →  33 body landmarks per frame
     │
     ▼
Exercise Detector (e.g. SquatDetector)
     │   • calculates joint angles
     │   • tracks rep stage (up/down) → counts reps
     │   • calculates form score from penalties
     │   • checks rep-duration trend → flags fatigue
     ▼
Streamlit session_state  →  live sidebar metrics + safety panel
     │
     ▼
Voice Pipeline  →  decides if an event is worth speaking
     │
     ▼
LLM Coach (Groq)  →  short spoken feedback, aware of recent session history
     │
     ▼
Text-to-Speech  →  audio played back in the browser
```

Each detector returns a metrics dictionary (reps, joint angles, status labels, `form_score`, `fatigue_detected`) on every processed frame. `metrics.py` syncs this into Streamlit's session state, persists completed sets to SQLite, and decides which coaching event (if any) should trigger spoken feedback.

---

## SYSTEM ARCHITECTURE

```text
                                    USER
                                      │
                                      ▼
                        ┌─────────────────────────┐
                        │   Netlify Landing Page  │
                        │  Project Showcase Site  │
                        └─────────────┬───────────┘
                                      │
                             "Launch Application"
                                      │
                                      ▼
                        ┌─────────────────────────┐
                        │   Streamlit Cloud App   │
                        │      (main.py)          │
                        └─────────────┬───────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        ▼                             ▼                             ▼

┌────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│ Authentication │      │ Session Management  │      │ UI / Styling Layer  │
│  login_wall.py │      │ session_defaults.py │      │  style_loader.py    │
└────────┬───────┘      └──────────┬──────────┘      └──────────┬──────────┘
         │                         │                            │
         └──────────────┬──────────┴──────────────┬─────────────┘
                        │                         │
                        ▼                         ▼

                ┌────────────────────────────────────┐
                │ Streamlit WebRTC Video Stream      │
                │ Live Webcam Input                  │
                └─────────────────┬──────────────────┘
                                  │
                                  ▼

                ┌────────────────────────────────────┐
                │ VideoProcessor                     │
                │ exercise_video_processor.py        │
                └─────────────────┬──────────────────┘
                                  │
                                  ▼

                ┌────────────────────────────────────┐
                │ MediaPipe Pose Landmarker          │
                │ pose_landmarker_full.task          │
                │ 33 Body Landmarks                  │
                └─────────────────┬──────────────────┘
                                  │
                                  ▼

         ┌──────────────────────────────────────────────────────┐
         │              Exercise Detection Engine               │
         │              BaseExercise Framework                  │
         └───────────────────────┬──────────────────────────────┘
                                 │
         ┌───────────┬───────────┼───────────┬───────────┬───────────┐
         ▼           ▼           ▼           ▼           ▼           ▼

   Squats      Pushups     Bicep Curls  Lunges    Deadlifts   Shoulder Press
 detector      detector      detector   detector    detector      detector

                                  │
                                  ▼

                         ┌───────────────────┐
                         │ Plank Detector    │
                         └───────────────────┘
                                  │
                                  ▼

                  ┌─────────────────────────────────┐
                  │ Metrics Generation Layer        │
                  │                                 │
                  │ • Rep Counting                  │
                  │ • Joint Angles                  │
                  │ • Form Scoring                  │
                  │ • Posture Analysis              │
                  │ • Fatigue Detection             │
                  └─────────────────┬───────────────┘
                                    │
                                    ▼

                    ┌─────────────────────────────┐
                    │ metrics.py                  │
                    │ State Synchronization Layer │
                    └─────────────┬───────────────┘
                                  │
            ┌─────────────────────┼──────────────────────┐
            │                     │                      │
            ▼                     ▼                      ▼

     ┌────────────────┐   ┌────────────────┐   ┌───────────────────┐
     │ UI Dashboard   │   │ Risk Analysis  │   │ Goal Tracking     │
     │ Live Metrics   │   │ Injury Alerts  │   │ Sets / Reps       │
     └────────────────┘   └────────────────┘   └───────────────────┘

           │                     │                     │
           └─────────────┬───────┴──────────────┬──────┘
                         │                      │
                         ▼                      ▼

             ┌──────────────────┐   ┌────────────────────┐
             │ SQLite Database  │   │ Fatigue Event Log  │
             │ exercise_repo.py │   │ Session History    │
             └─────────┬────────┘   └─────────┬──────────┘
                       │                      │
                       └──────────┬───────────┘
                                  │
                                  ▼

                     ┌─────────────────────────┐
                     │ Recent Workout Context  │
                     │ Session Retrieval       │
                     └─────────────┬───────────┘
                                   │
                                   ▼

                     ┌─────────────────────────┐
                     │ Voice Pipeline          │
                     │ voice_pipeline.py       │
                     └─────────────┬───────────┘
                                   │
                                   ▼

                     ┌─────────────────────────┐
                     │ LLM Coach               │
                     │ Groq Llama-3.3-70B      │
                     │ Session-Aware Coaching  │
                     └─────────────┬───────────┘
                                   │
                                   ▼

                     ┌─────────────────────────┐
                     │ Text To Speech          │
                     │ Groq Orpheus TTS        │
                     │ (gTTS fallback)         │
                     └─────────────┬───────────┘
                                   │
                                   ▼

                     ┌─────────────────────────┐
                     │ Audio Feedback Output   │
                     │ Real-Time Coaching      │
                     └─────────────────────────┘
```


## TEXH STACK

| Layer | Technology |
|---|---|
| UI / App framework | [Streamlit](https://streamlit.io/) |
| Live video | [streamlit-webrtc](https://github.com/whitphx/streamlit-webrtc) |
| Pose estimation | [MediaPipe Tasks Vision](https://ai.google.dev/edge/mediapipe) (`PoseLandmarker`) |
| Image processing | OpenCV (headless) |
| LLM coaching | [Groq](https://groq.com/) (`llama-3.3-70b-versatile`) |
| Text-to-speech | [Groq Orpheus](https://console.groq.com/docs/text-to-speech/orpheus) (gTTS fallback) |
| Persistence | SQLite |
| Data display | pandas |

---

## PROJECT STRUCTURE

```
gym-ai-coach/
├── main.py                          # Streamlit entry point — UI, sidebar, session orchestration
├── core/
│   └── base_exercise.py             # Abstract base class: angle math, rep tracking, fatigue logic, scoring
├── detectors/
│   ├── squats.py
│   ├── pushups.py
│   ├── bicepcurls.py
│   ├── shoulderpress.py
│   ├── lunges.py
│   ├── deadlifts.py
│   └── planks.py                    # One detector per exercise, each subclassing BaseExercise
├── services/
│   ├── auth/
│   │   └── login_wall.py            # Lightweight username-based session login
│   ├── state/
│   │   └── session_defaults.py      # Initializes Streamlit session_state defaults
│   ├── config/
│   │   └── workout_config.py        # Exercise list, pose connections, metric field maps, LLM system prompt
│   ├── ui/
│   │   └── style_loader.py          # Custom CSS + font injection
│   ├── persistence/
│   │   └── exercise_repository.py   # SQLite schema + all DB read/write functions
│   ├── vision/
│   │   └── exercise_video_processor.py  # MediaPipe pipeline + on-frame overlays (VideoProcessorBase)
│   ├── tracking/
│   │   └── metrics.py               # Bridges VideoProcessor output → session_state + DB + voice pipeline
│   └── coaching/
│       ├── llm.py                   # LLMCoach — builds prompts, calls Groq, tracks feedback history
│       ├── tts.py                   # Groq Orpheus TTS wrapper, gTTS fallback on failure
│       └── voice_pipeline.py        # Decides what/when to speak based on exercise events
├── static/
│   ├── style.css                    # App theme (glass cards, midnight blue palette)
│   └── AdobeClean-SemiCn.ttf        # Custom font
├── ml_models/
│   └── pose_landmarker_full.task    # MediaPipe pose model
├── .streamlit/
│   └── config.toml                  # Streamlit theme config
└── data.db                          # SQLite database (created automatically on first run)
```

---

## SUPPORTED EXERCISES AND FORM CHECKS

| Exercise | Key Angles Tracked | Form Checks |
|---|---|---|
| Squats | Knee angle, back angle | Squat depth, forward lean |
| Push-ups | Elbow angle, body line | Body alignment, hip sag/pike |
| Bicep Curls | Elbow angle, torso sway | Elbow drift, body swing |
| Shoulder Press | Elbow angle, torso angle | Extension stage, lower-back arch |
| Lunges | Front knee angle, torso angle | Lateral balance |
| Deadlifts | Hip angle, torso angle | Spinal/back arch |
| Planks | Body line, hip deviation | Body alignment, hip sag (+ live hold timer) |

Every detector also feeds into a shared fatigue check: once at least 4 reps are completed, the average duration of the last 3 reps is compared against the first 3, a sustained ≥40% slowdown flags fatigue.

---

## SETUP AND INSTALLATION

### Prerequisites

- **Python 3.12**: MediaPipe's `PoseLandmarker` Tasks API is not yet compatible with Python 3.14, so 3.12 is required.
- A webcam
- A free [Groq API key](https://console.groq.com/) for the AI coaching feature

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/gym-ai-coach.git
cd gym-ai-coach
```

### 2. Create a virtual environment

Using [`uv`](https://github.com/astral-sh/uv) (recommended):

```bash
uv venv --python 3.12
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux
uv pip install -r requirements.txt
```

Or with standard `venv`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

(Alternatively, set `GROQ_API_KEY` in `.streamlit/secrets.toml`.)

### 4. Run the app

```bash
streamlit run main.py
```

Open the local URL Streamlit prints in your terminal, enter a username, set up your workout plan in the sidebar, and click **Start Workout**.

---

## DATABASE SCHEMA

SQLite (`data.db`) is created automatically on first launch with three tables:

- **`users`**: `id`, `username`, `created_at`
- **`exercises`**: `id`, `user_id`, `exercise_name`, `reps`, `sets`, `time`, `form_score`, `created_at`
- **`fatigue_events`**: `id`, `user_id`, `exercise_name`, `created_at`

This powers the workout history table on the dashboard and the session context fed to the LLM coach.

---

## FEATURE ENHANCEMENTS

- [ ] Adaptive fatigue-aware coaching that dynamically adjusts workout intensity and rest periods
- [ ] Exercise auto-detection to eliminate manual exercise selection
- [ ] Personalized form-improvement plans generated from historical posture and form data
- [ ] Exercise-specific injury-risk prediction using biomechanical movement patterns
- [ ] Long-term performance trend analysis to identify strength, endurance, and consistency improvements
