from core.base_exercise import BaseExercise

class DeadliftDetector(BaseExercise):
    UP_THRESHOLD = 160
    DOWN_THRESHOLD = 90
    MIN_VISIBILITY = 0.7
    BACK_ARCH_TOLERANCE = 150

    LEFT_SHOULDER = 11
    LEFT_HIP = 23
    LEFT_KNEE = 25
    LEFT_ANKLE = 27
    RIGHT_SHOULDER = 12
    RIGHT_HIP = 24
    RIGHT_KNEE = 26
    RIGHT_ANKLE = 28

    def __init__(self):
        super().__init__()

    def reset(self):
        self.reps = 0
        self.stage = None
        self.reset_fatigue_state()
    
    def _calculate_form_score(self, back_arch_status):
        penalties = []
        if back_arch_status == "EXCESSIVE ARCH":
            penalties.append(35)
        elif back_arch_status == "SLIGHT ARCH":
            penalties.append(10)
        return self._score(penalties)

    def process(self, landmarks):
        left_vis = landmarks[self.LEFT_HIP].visibility
        right_vis = landmarks[self.RIGHT_HIP].visibility

        if left_vis >= right_vis:
            shoulder_idx = self.LEFT_SHOULDER
            hip_idx = self.LEFT_HIP
            knee_idx = self.LEFT_KNEE
            ankle_idx = self.LEFT_ANKLE
        else:
            shoulder_idx = self.RIGHT_SHOULDER
            hip_idx = self.RIGHT_HIP
            knee_idx = self.RIGHT_KNEE
            ankle_idx = self.RIGHT_ANKLE

        hip_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, knee_idx),
        )

        torso_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, ankle_idx),
        )

        key_landmarks_visible = (
            landmarks[shoulder_idx].visibility >= self.MIN_VISIBILITY and
            landmarks[hip_idx].visibility >= self.MIN_VISIBILITY and
            landmarks[knee_idx].visibility >= self.MIN_VISIBILITY
        )

        if key_landmarks_visible:
            if hip_angle < self.DOWN_THRESHOLD:
                self.stage = "down"
            if hip_angle > self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self._record_rep()

        if torso_angle >= 160:
            back_arch_status = "NEUTRAL"
        elif torso_angle >= self.BACK_ARCH_TOLERANCE:
            back_arch_status = "SLIGHT ARCH"
        else:
            back_arch_status = "EXCESSIVE ARCH"

        hip_status = "HINGING" if self.stage == "down" else "STANDING"

        return {
            "reps": self.reps,
            "back_angle": int(torso_angle),
            "hip_status": hip_status,
            "torso_angle": int(torso_angle),
            "form_score": self._calculate_form_score(back_arch_status),
            "fatigue_detected": self.fatigue_detected,
            "back_arch_status": back_arch_status
        }