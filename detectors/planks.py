import time
from core.base_exercise import BaseExercise

class PlankDetector(BaseExercise):
    MIN_VISIBILITY = 0.7
    PLANK_ANGLE_MIN = 155
    HIP_SAG_TOLERANCE = 0.06

    LEFT_SHOULDER = 11
    LEFT_HIP = 23
    LEFT_ANKLE = 27
    RIGHT_SHOULDER = 12
    RIGHT_HIP = 24
    RIGHT_ANKLE = 28

    def __init__(self):
        super().__init__()
        self._plank_start = None
        self.hold_time = 0

    def reset(self):
        self.reps = 0
        self.stage = None
        self._plank_start = None
        self.hold_time = 0
        self.reset_fatigue_state()

    def _calculate_form_score(self, body_alignment, hip_status):
        penalties = []
        if body_alignment == "POOR FORM":
            penalties.append(35)
        elif body_alignment == "SLIGHT BEND":
            penalties.append(15)
        if hip_status == "SAGGING":
            penalties.append(20)
        return self._score(penalties)

    def process(self, landmarks):
        left_vis = landmarks[self.LEFT_HIP].visibility
        right_vis = landmarks[self.RIGHT_HIP].visibility

        if left_vis >= right_vis:
            shoulder_idx = self.LEFT_SHOULDER
            hip_idx = self.LEFT_HIP
            ankle_idx = self.LEFT_ANKLE
        else:
            shoulder_idx = self.RIGHT_SHOULDER
            hip_idx = self.RIGHT_HIP
            ankle_idx = self.RIGHT_ANKLE

        body_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, ankle_idx),
        )

        shoulder_y = landmarks[shoulder_idx].y
        ankle_y = landmarks[ankle_idx].y
        hip_y = landmarks[hip_idx].y
        expected_hip_y = (shoulder_y + ankle_y) / 2
        hip_deviation = abs(hip_y - expected_hip_y)

        in_plank = body_angle >= self.PLANK_ANGLE_MIN and hip_deviation <= self.HIP_SAG_TOLERANCE

        if in_plank:
            if self._plank_start is None:
                self._plank_start = time.time()
            self.hold_time = int(time.time() - self._plank_start)
        else:
            self._plank_start = None

        if body_angle >= self.PLANK_ANGLE_MIN:
            body_alignment = "STRAIGHT"
        elif body_angle >= 140:
            body_alignment = "SLIGHT BEND"
        else:
            body_alignment = "POOR FORM"

        hip_status = "LEVEL" if hip_deviation <= self.HIP_SAG_TOLERANCE else "SAGGING"

        return {
            "reps": self.hold_time,
            "back_angle": int(body_angle),
            "hip_status": hip_status,
            "body_alignment": body_alignment,
            "form_score": self._calculate_form_score(body_alignment, hip_status),
            "fatigue_detected": self.fatigue_detected,
        }