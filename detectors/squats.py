from core.base_exercise import BaseExercise

class SquatDetector(BaseExercise):
    DOWN_THRESHOLD = 100  # if the knee angle becomes less than around 100 degrees then the person is in sitting position
    UP_THRESHOLD = 160  # if the knee angle becomes greater than around 160 degrees then the person is in sitting position
    MIN_VISIBILITY = 0.7

    LEFT_HIP = 23   
    LEFT_KNEE = 25
    LEFT_ANKLE = 27
    RIGHT_HIP = 24
    RIGHT_KNEE = 26
    RIGHT_ANKLE = 28
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12     # indices of every landmark provided used by pose landmarker model

    def __init__(self):
        super().__init__()     # variables of parent (BaseExercise) class's init variables will be called

    def reset(self):
        self.reps = 0
        self.stage = None
        self.reset_fatigue_state()

    def _calculate_form_score(self, depth_status, back_angle):
        penalties = []
        if depth_status == "TOO HIGH":
            penalties.append(25)
        if back_angle < 150:
            penalties.append(20)
        return self._score(penalties)

    def  process(self, landmarks):
        # both of the knee angles will be captured in any position (front facing the camera, slightly turned left or right) Whichever side is more visible, will be considered
        left_knee_angle = self.calculate_angle(
            self.get_point(landmarks, self.LEFT_HIP),
            self.get_point(landmarks, self.LEFT_KNEE),
            self.get_point(landmarks, self.LEFT_ANKLE)
        )

        right_knee_angle = self.calculate_angle(
            self.get_point(landmarks, self.RIGHT_HIP),
            self.get_point(landmarks, self.RIGHT_KNEE),
            self.get_point(landmarks, self.RIGHT_ANKLE)
        )

        # check visibility
        left_knee_vis = landmarks[self.LEFT_KNEE].visibility      # .visibility - property/attribute that stores MediaPipe's confidence score for how clearly landmark is visible in the frame  
        right_knee_vis = landmarks[self.RIGHT_KNEE].visibility

        if left_knee_vis >= right_knee_vis:
            knee_angle = left_knee_angle
            hip_idx, knee_idx, ankle_idx, shoulder_idx = self.LEFT_HIP, self.LEFT_KNEE, self.LEFT_ANKLE, self.LEFT_SHOULDER
        else:
            knee_angle = right_knee_angle
            hip_idx, knee_idx, ankle_idx, shoulder_idx = self.RIGHT_HIP, self.RIGHT_KNEE, self.RIGHT_ANKLE, self.RIGHT_SHOULDER

        back_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, hip_idx),
            self.get_point(landmarks, knee_idx),
        )

        key_landmarks_visibile = landmarks[hip_idx].visibility >= self.MIN_VISIBILITY and landmarks[knee_idx].visibility >= self.MIN_VISIBILITY and landmarks[ankle_idx].visibility >= self.MIN_VISIBILITY

        if key_landmarks_visibile: # if landmarks are visible - update reps and stage
            if knee_angle < self.DOWN_THRESHOLD:
                self.stage = "down"

            if knee_angle >= self.UP_THRESHOLD and self.stage == "down":
                self.stage = "up"
                self._record_rep()

        if self.stage == "down":
            depth_status = "GOOD DEPTH" if knee_angle <= self.DOWN_THRESHOLD else "TOO HIGH"
        elif self.stage == "up":
            depth_status = "STANDING"
        else:
            depth_status = "N/A"

        return {
            "reps": self.reps,
            "knee_angle": int(knee_angle),
            "back_angle": int(back_angle),
            "depth_status": depth_status,
            "form_score": self._calculate_form_score(depth_status, back_angle),
            "fatigue_detected": self.fatigue_detected,
            }