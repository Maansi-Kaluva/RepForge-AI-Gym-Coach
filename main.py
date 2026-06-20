import streamlit as st
import os
import time
import pandas as pd
from groq import Groq
from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import exercise_options
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.exercise_repository import init_db, get_users_exercises, get_recent_sessions
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessor
from services.tracking.metrics import sync_metrics_update
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline

from dotenv import load_dotenv
load_dotenv()


@st.cache_resource
def get_voice_pipeline():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["GROQ_API_KEY"]
        except Exception:
            api_key = None
    client = Groq(api_key = api_key)
    return VoicePipeline(LLMCoach(client), TextToSpeech())


def main():      # main function of the app
    st.set_page_config( # To customize the webpage settings (title, icon, layout, sidebar).
        page_icon = "🏋️‍♀️",      # browser tab icon
        page_title = "AI Real-Time GYM Coach",   # webpage title shown in browser tab
        initial_sidebar_state = "expanded",
        layout = "centered"   # keeps webpage content centered
    )
    
    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean-SemiCn.ttf"), "AdobeClean")

    init_db()

    if not render_login_wall():
        return 
    
    initial_session_defaults()  # as soon as the app refreshes, all the variables would be set in streamlit's session_state

    voice_pipeline = get_voice_pipeline()

    workout_started = st.session_state.get("workout_started", False)
    
    # sidebar UI code
    with st.sidebar:
        st.title("Your AI guru")

        if st.session_state.username:
            st.caption(f"👤Logged in as {st.session_state.username}")
        
        st.divider()

        st.subheader("Workout Plan")

        if not workout_started:
            plan_exercise = st.selectbox("Exercise", options = exercise_options, key = "plan_exercise")
            plan_sets = st.number_input("Sets", min_value = 1, max_value = 50, key = "plan_sets", step = 1)
            plan_reps = st.number_input("Reps per Set", min_value = 1, max_value = 50, key = "plan_reps", step = 1)

            st.markdown("")

            start_session_button = st.button("Start Workout", key = "start_session_button", width = "stretch")

            if start_session_button:
                st.session_state.exercise_type = plan_exercise
                st.session_state.target_sets = int(plan_sets)
                st.session_state.reps_per_set = int(plan_reps)
                st.session_state.reps = 0
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at = time.time()
                st.session_state.last_saved_sets_completed = 0
                st.session_state.last_notified_sets_completed = 0
                st.session_state.last_notified_workout_completed = False
                st.session_state.fatigue_logged = False
                st.session_state.fatigue_detected = False

                if voice_pipeline:
                    recent_sessions = get_recent_sessions(st.session_state.user_id, limit = 5)
                    voice_pipeline.llm.set_session_context(recent_sessions)

                    result = voice_pipeline.process_event("workout_started", plan_exercise, {})
                    if result:
                        st.session_state.last_audio, st.session_state.last_feedback = result

                st.rerun()
        else: 
            exercise = st.session_state.get("exercise_type")
            sets = st.session_state.get("plan_sets")
            reps = st.session_state.get("plan_reps")
            
            st.info(f"**{exercise}** : {sets} Sets / {reps} Reps")

            end_session_button = st.button("End Workout", key = "end_session_button", width = "stretch")

            if end_session_button:
                st.session_state["workout_started"] = False
                st.session_state["reps"] = 0
                st.session_state["sets_completed"] = 0
                st.session_state["current_set_reps"] = 0
                st.rerun()
        
        if workout_started:
            st.divider()

            exercise = st.session_state.get("exercise_type")
            total_reps = st.session_state.get("reps")
            current_set_reps = st.session_state.get("current_set_reps")
            reps_per_set = st.session_state.get("plan_reps")
            sets_completed = st.session_state.get("sets_completed")
            target_sets = st.session_state.get("plan_sets")

            st.subheader("Progress")

            st.metric("Total Reps", f"{total_reps}")
            st.metric("Current Set Reps", f"{current_set_reps} / {reps_per_set}")
            st.metric("Sets Completed", f"{sets_completed} / {target_sets}")

            st.divider()

            if exercise == "Squats":
                st.subheader("Squat Metrics")
                st.metric("Knee Angle", f"{st.session_state.knee_angle}°")
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                st.metric("Depth Status", st.session_state.depth_status)

            elif exercise == "Planks":
                st.subheader("Plank Metrics")
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                st.metric("Hip Status", st.session_state.hip_status)
                st.metric("Body Alignment", st.session_state.body_alignment)

            elif exercise == "Push-ups":
                st.subheader("Push-up Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Body Alignment", st.session_state.body_alignment)
                st.metric("Hip Position", st.session_state.hip_status)

            elif exercise == "Bicep Curls (Dumbbell)":
                st.subheader("Bicep Curl Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Shoulder Status", st.session_state.shoulder_status)
                st.metric("Swing Status", st.session_state.swing_status)

            elif exercise == "Shoulder Press":
                st.subheader("Shoulder Press Metrics")
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Extension Status", st.session_state.extension_status)
                st.metric("Back Arch", st.session_state.back_arch_status)

            elif exercise == "Lunges":
                st.subheader("Lunge Metrics")
                st.metric("Front Knee Angle", f"{st.session_state.front_knee_angle}°")
                st.metric("Balance Status", st.session_state.balance_status)

            elif exercise == "Deadlifts":
                st.subheader("Deadlift Metrics")
                st.metric("Back Angle", f"{st.session_state.back_angle}°")
                st.metric("Hip Status", st.session_state.hip_status)
                st.metric("Torso Angle", f"{st.session_state.torso_angle}°")
                st.metric("Back Arch", st.session_state.back_arch_status)

            # Safety Monitoring
            # Safety Monitoring
            st.divider()
            st.subheader("Safety Monitoring")

            if st.session_state.get("workout_started", False):
                st.metric(
                    "Risk Level",
                    st.session_state.get("risk_level", "Not Assessed")
                )

                if st.session_state.get("risk_level") == "Not Assessed":
                    st.info("No posture analysis yet.")
                elif st.session_state.get("unsafe_posture_detected", False):
                    st.warning(
                        "⚠ Unsafe posture detected. Adjust your form to reduce injury risk."
                    )
                else:
                    st.success("✅ Posture appears safe.")
            else:
                st.info("Start a workout to assess posture safety.")


    # video input using StreamLit WebRTC                 
    st.title("Your Personal AI Fitness Coach")
    st.caption("Every rep counts. Every form matters. Your AI guru never misses a thing.")

    if not workout_started:
        st.markdown("""
        <div style = "
            border: 10px dashed #444;
            border-radius: 0px;
            padding: 48px 32px;
            text-align: center;
            color: #888;
            margin-top: 32px
        ">
            <h2 style = "color: #ccc; margin-bottom: 8px;">👈🏼 Set your workout plan</h2>
            <p style = "font-size: 1.05rem; color: #888">
                Choose your exercise, sets and reps in the sidebar, <br>
                then click <span style = "color: #ffffff; font-weight: 700;">Start Workout</span> to activate the camera and AI coach
            </p>
        </div>
        """,
        unsafe_allow_html = True
        )
    
    else:
        context = webrtc_streamer(
            key = "exercise_analysis",
            mode = WebRtcMode.SENDRECV,
            video_processor_factory = VideoProcessor,
            rtc_configuration = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints = {
                "video": True,
                "audio": False
            },
            async_processing = True    # streamlit runs on main thread and if any other thread works this won't block the main thread's execution.
        )

        sync_metrics_update(context, voice_pipeline)
        inject_webrtc_styles()

        if st.session_state.get("last_audio"):
            st.audio(st.session_state.last_audio, format="audio/mp3", autoplay=True)
            st.session_state.last_audio = None

        if st.session_state.get("last_feedback"):
            st.caption(f"🗣️ {st.session_state.last_feedback}")

        if context.state.playing:
            time.sleep(0.25)
            st.rerun()

    st.divider()
    st.markdown("#### Workout History")

    user_id = st.session_state.get("user_id", 0)

    if isinstance(user_id, int):     # checks whether user_id is an integer (int) datatype before running the code inside the if block.
        history_keys = get_users_exercises(user_id)

        history_keys_arr = [
            {
                "Id": key["id"],
                "Exercise": key["exercise_name"],
                "Reps": key["reps"],
                "Sets": key["sets"],
                "Time(sec)": key["time"],
                "Date": key["created_at"]
            }
            for key in history_keys
        ]

        # converting the above array into a dataframe
        workout_history_df = pd.DataFrame(history_keys_arr)

        if not workout_history_df.empty:
            workout_history_df["Date"] = pd.to_datetime(workout_history_df["Date"]).dt.date
            agg_df = workout_history_df.groupby(["Exercise", "Date"]).agg({
                "Reps": "sum",
                "Sets": "sum",
                "Time(sec)": "sum"
            }).reset_index()
            agg_df.index += 1
            st.table(agg_df, border = "horizontal")
        else:
            st.info("No workout history found.")

if  __name__ == "__main__":    # Start the app from here only when this file is the main file being run. This makes sure the main code runs only when this file is executed directly.
    main()  # starts the app by calling main function