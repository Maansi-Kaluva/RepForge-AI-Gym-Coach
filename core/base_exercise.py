from abc import ABC, abstractmethod # ABC is used to create an abstract base class (a blueprint class), @abstractmethod forces child classes to implement a specific method before they can be used.
import math
import time

class BaseExercise(ABC):    # inheriting ABC class for BaseExercise class
    def __init__(self):
        self.reps = 0
        self.stage = None    # stage - user's current position (standing, sitting)
        self._rep_start_time = time.time()
        self._rep_durations = []
        self.last_rep_duration = 0
        self.fatigue_detected = False

    def calculate_angle(self, a, b, c):
        ax, ay = a[0] - b[0], a[1] - b[1]
        cx, cy = c[0] - b[0], c[1] - b[1]

        dot_product = (ax * cx) + (ay * cy)

        mag_a = math.sqrt(ax ** 2 + ay ** 2)
        mag_c = math.sqrt(cx ** 2 + cy ** 2)

        if mag_a * mag_c == 0:
            return 0.0

        cos_angle = max(-1.0, min(1.0, dot_product / (mag_a * mag_c)))  # clamping it - cos value should always be between -1, 1 - Prevents math errors due to tiny decimal inaccuracies.

        return math.degrees(math.acos(cos_angle))
    
    def get_point(self, landmarks, idx):
        p = landmarks[idx]     # landmarks[idx] is the landmarks class returned by MediaPipe Pose once imported and implemented
        return (p.x, p.y) 
    
    def _record_rep(self):
        now = time.time()
        duration = now - self._rep_start_time
        self._rep_durations.append(duration)
        self._rep_start_time = now
        self.last_rep_duration = round(duration, 2)
        self.reps += 1
        self._check_fatigue()

    def _check_fatigue(self):
        if len(self._rep_durations) >= 4:  # need at least 4 reps to compare
            recent = self._rep_durations[-3:]
            early = self._rep_durations[:3]
            avg_recent = sum(recent) / len(recent)
            avg_early = sum(early) / len(early)
            if avg_recent > avg_early * 1.4:
                self.fatigue_detected = True

    def _score(self, penalties):
        """Takes a list of point deductions and returns a clamped 0-100 form score."""
        return max(0, 100 - sum(penalties))

    def reset_fatigue_state(self):
        """Clears fatigue-tracking state. Call this from every subclass's reset()."""
        self.fatigue_detected = False
        self._rep_durations = []
        self.last_rep_duration = 0
        self._rep_start_time = time.time()
    
    # absract methods
    @abstractmethod               # every exercise must define its own process logic
    def process(self, landmarks):  # "landmarks" is an array which contains 2D and 3D coordinates about the position of each of the landmark
        pass   # pass means :empty for now"
    
    @abstractmethod 
    def reset(self):      # Every exercise MUST also define how to reset itself.
        pass