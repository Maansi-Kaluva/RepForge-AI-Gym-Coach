# This file is the main voice feedback controller of your gym AI project. It decides:
# Should feedback be spoken now? What issue should be told? Generate voice and return it.

import time

MAX_VOICE_CHARS = 200  # Orpheus TTS hard limit — truncate once here so caption == audio always

class VoicePipeline:
    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.last_spoken_at = 0

    def _find_form_issue(self, exercise, metrics):
        if "issue" in metrics:
            return metrics["issue"]

        if exercise == "Squats":
            depth = metrics.get("depth_status", "")
            back_angle = metrics.get("back_angle", "")

            if depth == "TOO HIGH":
                return "The user's squat is not deep enough — knees are not bending sufficiently."
            if isinstance(back_angle, (int, float)) and back_angle < 130:
                return "The user is leaning too far forward during the squat."

        elif exercise == "Push-ups":
            alignment = metrics.get("body_alignment", "")
            hip_status = metrics.get("hip_status", "")

            if alignment == "Poor Form":
                return "The user's body is not straight during the push-up."
            if hip_status == "SAGGING":
                return "The user's hips are sagging down during the push-up."
            if hip_status == "PIKED UP":
                return "The user's hips are too high — lower them to form a straight line."

        elif exercise == "Bicep Curls (Dumbbell)":  # fixed: was "Biceps Curls (Dumbbell)"
            swing = metrics.get("swing_status", "")
            shoulder = metrics.get("shoulder_status", "")

            if swing == "SWINGING":
                return "The user is swinging their torso during the curl — keep the body still."
            if shoulder == "ELBOW DRIFTING":
                return "The user's elbow is drifting away from their side during the curl."

        elif exercise == "Shoulder Press":
            back_arch = metrics.get("back_arch_status", "")

            if back_arch == "Excessive Arch":
                return "The user is arching their lower back excessively during the press."
            if back_arch == "Slight Arch":
                return "Slight back arch detected — encourage the user to brace their core."

        elif exercise == "Lunges":
            balance = metrics.get("balance_status", "")

            if balance == "OFF BALANCE":
                return "The user is losing balance during the lunge — feet should be hip-width apart."

        elif exercise == "Deadlifts":
            back_arch = metrics.get("back_arch_status", "") or metrics.get("hip_status", "")

            if back_arch == "EXCESSIVE ARCH":
                return "The user's back is rounding during the deadlift — keep the spine neutral."

        elif exercise == "Planks":
            alignment = metrics.get("body_alignment", "")
            hip_status = metrics.get("hip_status", "")

            if alignment == "POOR FORM":
                return "The user's plank form has broken down — body is not in a straight line."
            if hip_status == "SAGGING":
                return "The user's hips are sagging in the plank — engage the core."

        return None

    def process_event(self, event, exercise, metrics):
        issue = self._find_form_issue(exercise, metrics)
        now = time.time()

        # only these fire instantly — they're already debounced upstream by session_state flags
        is_instant_event = event in ["workout_started", "set_completed", "workout_completed"]

        if is_instant_event:
            text = self.llm.give_feedback(event, issue)
            text = text[:MAX_VOICE_CHARS]
            voice = self.tts.speak(text)
            self.last_spoken_at = now
            return voice, text

        # no_pose_detected and ongoing form feedback share the same cooldown
        should_speak = event == "no_pose_detected" or issue is not None
        if not should_speak:
            return None

        if now - self.last_spoken_at < 5:
            return None

        if event == "form_feedback":
            feedback_map = {
                "The user's squat is not deep enough — knees are not bending sufficiently.": "Go a little deeper into the squat.",
                "The user is leaning too far forward during the squat.": "Keep your chest up and your back straighter.",
                "The user's body is not straight during the push-up.": "Keep your body in a straight line.",
                "The user's hips are sagging down during the push-up.": "Engage your core and lift your hips slightly.",
                "The user's hips are too high — lower them to form a straight line.": "Lower your hips and maintain a straight body line.",
                "The user is swinging their torso during the curl — keep the body still.": "Avoid swinging. Let your arms do the work.",
                "The user's elbow is drifting away from their side during the curl.": "Keep your elbows tucked close to your body.",
                "The user is arching their lower back excessively during the press.": "Brace your core and avoid excessive back arch.",
                "Slight back arch detected — encourage the user to brace their core.": "Keep your core tight throughout the movement.",
                "The user is losing balance during the lunge — feet should be hip-width apart.": "Widen your stance slightly for better balance.",
                "The user's back is rounding during the deadlift — keep the spine neutral.": "Keep your spine neutral and chest lifted.",
                "The user's plank form has broken down — body is not in a straight line.": "Maintain a straight line from shoulders to ankles.",
                "The user's hips are sagging in the plank — engage the core.": "Engage your core and lift your hips slightly."
            }

            text = feedback_map.get(issue, issue)
        else:
            text = self.llm.give_feedback(event, issue)

        text = text[:MAX_VOICE_CHARS]
        voice = self.tts.speak(text)
        self.last_spoken_at = now
        return voice, text