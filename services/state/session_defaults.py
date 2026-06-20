import streamlit as st

def initial_session_defaults():   # creates a fresh starting state for every new workout - resets all values to 0 when a user starts workout
    defaults = {
        "reps": 0,    # total reps done across all sets
        "target_sets": 0,    # how many sets the user planned
        "reps_per_set": 0,    # how many reps per set
        "sets_completed": 0,   # how many sets finished
        "current_set_reps": 0,    # reps done in the current set only
        "workout_completed": False,    # True/False flag, is the workout done
        "last_notified_sets_completed": 0,   # prevents the voice from repeating "set complete" multiple times
        "last_notified_workout_completed": False,  #  same but for workout completion notification
        "last_saved_sets_completed": 0,   # tracks what was last saved to DB, avoids duplicate saves
        "set_cycle_started_at": 0.0,   # timestamp of when current set started

        # workout plan (set before starting)
        "workout_started": False,   # has the user clicked Start Workout
        "plan_exercise": "Squats",  # which exercise they selected (Squats/Pushups etc)
        "plan_sets": 3,  # how many sets they chose
        "plan_reps":3,   # how many reps they chose

        # common angles
        "knee_angle": 0,
        "back_angle": 0,
        "elbow_angle": 0,
        "front_knee_angle": 0,
        "torso_angle": 0,  # real-time joint angles calculated from MediaPipe landmarks, used for form checking

        # status fields
        "depth_status": "N/A",
        "body_alignment": "N/A",
        "hip_status": "N/A",
        "shoulder_status": "N/A",
        "swing_status": "N/A",
        "extension_status": "N/A",
        "back_arch_status": "N/A",
        "balance_status": "N/A",   #  form feedback labels for each body part, shown on screen and spoken by the coach

        # form_scoring
        "form_score": 0,   # stores the session score

        # fatigue detection and injury/ safety monitoring
        "fatigue_detected": False,   # flags when rep speed drops
        "unsafe_posture_detected": False,
        "risk_level": "Not Assessed",    

        # AI feedback history and for session aware LLM coaching
        "last_feedback": "",
    }

    # assigning in streamlit
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
