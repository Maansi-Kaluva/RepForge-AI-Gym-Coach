from core.base_exercise import BaseExercise

class ShoulderPressDetector(BaseExercise):
    UP_THRESHOLD = 160
    DOWN_THRESHOLD = 90
    MIN_VISIBILITY = 0.7

    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15
    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26

    def __init__(self):
        super().__init__()

    def reset(self) -> None:
        self.reps = 0
        self.stage = None
        self.reset_fatigue_state()

    def _calculate_form_score(self, back_arch_status):
        penalties = []
        if back_arch_status == "Excessive Arch":
            penalties.append(30)
        elif back_arch_status == "Slight Arch":
            penalties.append(10)
        return self._score(penalties)

    def process(self, landmarks):      # return dictionary as output
        left_elbow_angle = self.calculate_angle(
            self.get_point(landmarks, self.LEFT_SHOULDER),
            self.get_point(landmarks, self.LEFT_ELBOW),
            self.get_point(landmarks, self.LEFT_WRIST)
        )

        right_elbow_angle = self.calculate_angle(
            self.get_point(landmarks, self.RIGHT_SHOULDER),
            self.get_point(landmarks, self.RIGHT_ELBOW),
            self.get_point(landmarks, self.RIGHT_WRIST)
        )

        left_elbow_vis = landmarks[self.LEFT_ELBOW].visibility
        right_elbow_vis = landmarks[self.RIGHT_ELBOW].visibility

        if left_elbow_vis >= right_elbow_vis:
            elbow_angle = left_elbow_angle
            shoulder_idx , elbow_idx, wrist_idx, hip_idx, knee_idx = self.LEFT_SHOULDER, self.LEFT_ELBOW, self.LEFT_WRIST, self.LEFT_HIP, self.LEFT_KNEE
        
        else:
            elbow_angle = right_elbow_angle
            shoulder_idx , elbow_idx, wrist_idx, hip_idx, knee_idx = self.RIGHT_SHOULDER, self.RIGHT_ELBOW, self.RIGHT_WRIST, self.RIGHT_HIP, self.RIGHT_KNEE

        key_landmarks_visible = landmarks[shoulder_idx].visibility >= self.MIN_VISIBILITY and landmarks[elbow_idx].visibility >= self.MIN_VISIBILITY and landmarks[wrist_idx].visibility >= self.MIN_VISIBILITY 
    
        if key_landmarks_visible:
            if elbow_angle > self.UP_THRESHOLD:
                self.stage = "up"

            if elbow_angle < self.DOWN_THRESHOLD and self.stage == "up":
                self.stage = "down"
                self._record_rep() 

        if elbow_angle >= self.UP_THRESHOLD:
            extension_status = "FULL EXTENSION"
        elif elbow_angle >= 130 and elbow_angle < self.UP_THRESHOLD:
            extension_status = "NEARLY EXTENDED"
        elif elbow_angle >= self.DOWN_THRESHOLD and elbow_angle < 130:
            extension_status = "PRESSING"
        else:
            extension_status = "START POSITION"

        torso_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, knee_idx)
        )

        if torso_angle >= 160:
            back_arch_status = "Neutral"
        elif 140<= torso_angle < 160:
            back_arch_status = "Slight Arch"
        else:
            back_arch_status = "Excessive Arch"

        return {
            "reps": self.reps,
            "elbow_angle": int(elbow_angle),
            "extension_status": extension_status,
            "back_arch_status": back_arch_status,
            "form_score": self._calculate_form_score(back_arch_status),
            "fatigue_detected": self.fatigue_detected,
        }