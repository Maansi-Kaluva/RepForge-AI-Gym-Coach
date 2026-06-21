# this file acts as a bridge between live video processor and Streamlit UI
# It takes the latest exercise metrics (angles, reps, posture status, etc.) from VideoProcessor and updates st.session_state so the sidebar/UI can display them live.

import streamlit as st
import time
from services.config.workout_config import METRICS_FIELDS
from services.persistence.exercise_repository import add_exercise, save_form_score, fatigue_detection

def _evaluate_risk(metrics_snapshot):
    """Derives a basic posture risk level from whichever spinal angle is present."""
    angle = metrics_snapshot.get("back_angle", metrics_snapshot.get("torso_angle"))

    if not isinstance(angle, (int, float)):
        return False, "Low"

    if angle < 120:
        return True, "High"
    elif angle < 140:
        return True, "Medium"
    return False, "Low"

def sync_metrics_update(context, voice_pipeline=None):
    if not context or not hasattr(context, "state") or not context.state.playing: # playing will be true only if the video is being played
        return
    
    processor = getattr(context, "video_processor", None)   # videoprocessor object - grtting it from "context" written in main.py

    if not processor:
        return
    
    # first the exercise the user has selected
    exercise = st.session_state.get("exercise_type")

    if not exercise:
        return
    
    processor.set_exercise(exercise)
    latest_metrics = processor.get_latest_metrics()

    if not latest_metrics:
        return
    
    reps = latest_metrics.get("reps", st.session_state.get("reps", 0))
    st.session_state.reps = reps

    field = METRICS_FIELDS.get(exercise)

    if not field:
        return

    for key, default in field.items():
        st.session_state[key] = latest_metrics.get(key, default)

    # posture safety check
    unsafe, risk_level = _evaluate_risk(latest_metrics)
    st.session_state.unsafe_posture_detected = unsafe
    st.session_state.risk_level = risk_level

    # Get workout plan values - values user selected before workout started and update the values on the sidebar UI
    reps_per_set = st.session_state.get("reps_per_set", 0) # default = 0
    target_sets = st.session_state.get("target_sets", 0)

    if reps_per_set > 0 and target_sets > 0:
        sets_completed = reps // reps_per_set 
        current_set_reps = reps % reps_per_set
        if current_set_reps == 0 and reps > 0:
            current_set_reps = reps_per_set
            
        workout_completed = sets_completed >= target_sets
    else:
        sets_completed = 0
        current_set_reps = 0
        workout_completed = False
    
    st.session_state.sets_completed = sets_completed
    st.session_state.current_set_reps = current_set_reps
    st.session_state.workout_completed = workout_completed

    user_id = st.session_state.get("user_id", 0)

    # log fatigue once per session, not every frame
    if latest_metrics.get("fatigue_detected") and not st.session_state.get("fatigue_logged", False):
        fatigue_detection(user_id, exercise)
        st.session_state.fatigue_logged = True
        st.session_state.fatigue_detected = True

    # Prevent duplicate database saves
    last_saved_sets = st.session_state.get("last_saved_sets_completed", 0)  # if not able to get, 0 (default) will be returned

    # if a set is completed call the add_exercise fcn
    if target_sets > 0 and reps_per_set > 0 and sets_completed > last_saved_sets:
        newly_completed = sets_completed - last_saved_sets
        now_ts = time.time()
        started_at = st.session_state.get("set_cycle_started_at", now_ts)
        time_taken = now_ts - started_at
        user_id = st.session_state.get("user_id", 0)

        add_exercise(user_id, exercise, newly_completed * reps_per_set, newly_completed, time_taken)
        save_form_score(user_id, exercise, latest_metrics.get("form_score", 0))

        st.session_state.set_cycle_started_at = now_ts
        st.session_state.last_saved_sets_completed = sets_completed

    # voice coaching: decide which event (if any) should be spoken for this frame
    if voice_pipeline:
        if not st.session_state.get("workout_announced", False) and latest_metrics.get("pose_detected", True):
            event = "workout_started"
            st.session_state.workout_announced = True

        elif not latest_metrics.get("pose_detected", True):
            event = "no_pose_detected"

        elif workout_completed and not st.session_state.get("last_notified_workout_completed", False):
            event = "workout_completed"
            st.session_state.last_notified_workout_completed = True

        elif sets_completed > st.session_state.get("last_notified_sets_completed", 0):
            event = "set_completed"
            st.session_state.last_notified_sets_completed = sets_completed

        elif reps > 1:
            event = "form_feedback"

        else:
            event = None

        if event:
            result = voice_pipeline.process_event(
                event,
                exercise,
                latest_metrics
            )

            if result:
                st.session_state.last_audio, st.session_state.last_feedback = result