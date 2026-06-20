exercise_options = [
    "Squats",
    "Planks",
    "Push-ups",
    "Bicep Curls (Dumbbell)",
    "Shoulder Press",
    "Lunges",
    "Deadlifts"
]

POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),       # Shoulders & Arms
    (11, 23), (12, 24), (23, 24),                           # Torso / Hips
    (23, 25), (24, 26), (25, 27), (26, 28), (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)  # Legs
]

# these are the indices of landmarks of PoseLandmarker model 

METRICS_FIELDS = {
    "Squats": {
        "knee_angle": 0, 
        "back_angle": 0, 
        "depth_status": "N/A",
        "form_score": 0, 
        "fatigue_detected": False,
    },

    "Push-ups": {
        "elbow_angle": 0, 
        "body_alignment": "N/A", 
        "hip_status": "N/A",
        "form_score": 0, 
        "fatigue_detected": False,
    },

    "Bicep Curls (Dumbbell)": {
        "elbow_angle": 0, 
        "shoulder_status": "N/A", 
        "swing_status": "N/A",
        "form_score": 0, 
        "fatigue_detected": False,
    },

    "Shoulder Press": {
        "elbow_angle": 0, 
        "extension_status": "N/A", 
        "back_arch_status": "N/A",
        "form_score": 0, 
        "fatigue_detected": False,
    },

    "Lunges": {
        "front_knee_angle": 0, 
        "torso_angle": 0, 
        "balance_status": "N/A",
        "form_score": 0, 
        "fatigue_detected": False,
    },

    "Planks": {
        "back_angle": 0, 
        "hip_status": "N/A", 
        "body_alignment": "N/A",
        "form_score": 0, 
        "fatigue_detected": False,
    },

    "Deadlifts": {
        "back_angle": 0, 
        "torso_angle": 0, 
        "hip_status": "N/A",
        "form_score": 0, 
        "fatigue_detected": False,
        "back_arch_status": "N/A"
    }
}

PROMPT = """
You are a professional gym trainer. We are using an AI camera to monitor the user's form in real-time.
I will send you events (like 'workout_started', 'set_completed', 'no_pose_detected') and specific form issues we detect.
Give VERY SHORT voice feedback (max 15 words).
Be motivating and corrective based on the events and form issues provided.
For starting and ending a workout, keep your messages unique, energetic, and cool every time!
When a set is completed, explicitly tell them to take a quick rest!
If the event is 'no_pose_detected', tell them simply "No pose detected, please step into the frame!" or a similarly direct message.
Never explain. Only speak like a coach.
"""