import os
import cv2 # python interface library for openCV(Open Source Computer Vision Library). Open Source toolkit for image processing and computer vision
import av
import numpy as np
import threading
import mediapipe as mp
from streamlit_webrtc import VideoProcessorBase  # base class used to define custom video processing logic for real time video streams
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from detectors.squats import SquatDetector
from detectors.planks import PlankDetector
from detectors.pushups import PushUpDetector
from detectors.lunges import LungeDetector
from detectors.shoulderpress import ShoulderPressDetector
from detectors.bicepcurls import BicepCurlDetector
from detectors.deadlifts import DeadliftDetector
from services.config.workout_config import POSE_CONNECTIONS


class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self._lock = threading.Lock()
        self._latest_metrics = None     # None for now
        self._exercise_type = "Squats"   # default value is squats

        model_path = os.path.join(os.getcwd(), "ml_models", "pose_landmarker_full.task")
        base_options = python.BaseOptions(model_asset_path = model_path)

        options = vision.PoseLandmarkerOptions(
            base_options = base_options,
            running_mode = vision.RunningMode.VIDEO,
            min_pose_detection_confidence = 0.7,
            min_pose_presence_confidence = 0.7,
            min_tracking_confidence = 0.7,
            output_segmentation_masks = False
        ) 

        # configuring our model
        self._landmarker = vision.PoseLandmarker.create_from_options(options) # model will now have access to all the above set parameters
        # we'll use this to predict images (frames)

        # import all the detector classes here
        self._detector = {
            "Squats": SquatDetector(),
            "Push-ups": PushUpDetector(),
            "Bicep Curls (Dumbbell)": BicepCurlDetector(),
            "Planks": PlankDetector(),
            "Lunges": LungeDetector(),
            "Shoulder Press": ShoulderPressDetector(),
            "Deadlifts": DeadliftDetector()
        }

        self._frame_timestamps_ms = 0 
    
    # get and set method for latest_metrics and exercise type
    def set_latest_metrics(self, metrics):
        with self._lock:
            self._latest_metrics = metrics.copy()  # create a copy of metrics

    def get_latest_metrics(self):
        with self._lock:
            return None if self._latest_metrics is None else self._latest_metrics.copy()
        
    def set_exercise(self, exercise_type):
        with self._lock:
            self._exercise_type = exercise_type

    def get_exercise(self):
        with self._lock:
            return self._exercise_type
        
    # functions for image processing and predicting of frames recieved through "recv()" method
    def _draw_skeleton(self, img, landmarks): # unction that draws the body structure (skeleton) on the webcam frame using the pose landmarks detected by MediaPipe.
        h, w = img.shape[:2] # for a normal color image (every frame is treated as an image) img.shape contains height, width, color channels [RGB channels in openCV]. h, w - first two values. So [h,w]

        for start_idx, end_idx in POSE_CONNECTIONS:
            p1 = landmarks[start_idx]
            p2 = landmarks[end_idx]
            if p1.visibility > 0.7 and p2.visibility > 0.7:
                cv2.line(
                    img, 
                    (int(p1.x*w), 
                    int(p1.y*h)), 
                    (int(p2.x*w), int(p2.y*h)), 
                    (255, 220, 0), 
                    8
                )

        for lm in landmarks:
            if lm.visibility > 0.7:
                cv2.circle(
                    img, 
                    (int(lm.x*w), int(lm.y*h)), 
                    8, 
                    (0, 200, 255), 
                    -1
                ) 
    
    def _draw_no_pose_warnings(self, img):
            cv2.putText(
                img, 
                "NO POSE DETECTED",
                (30, 50), # text will appear 30 pixels from the left and 50 pixels from the top
                cv2.FONT_HERSHEY_SIMPLEX,  # OpenCV built-in font style
                1,
                (0, 100, 255), # orange-red - warnings
                2, # thickness of letters 
                cv2.LINE_AA  # Anti-aliased text → smoother text edges.
            )

    def _draw_form_bar(self, img, form_score):
        h, w = img.shape[:2]
        bar_width = int((form_score / 100) * (w - 40))

        # background bar
        cv2.rectangle(img, (20, 10), (w - 20, 30), (50, 50, 50), -1)

        # colored fill based on score
        if form_score >= 80:
            color = (0, 255, 100)    # green
        elif form_score >= 50:
            color = (0, 200, 255)    # yellow
        else:
            color = (0, 0, 255)      # red

        cv2.rectangle(img, (20, 10), (20 + bar_width, 30), color, -1)
        cv2.putText(
            img,
            f"FORM: {form_score}%",
            (w - 130, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255,255,255),
            2,
            cv2.LINE_AA
        )

    # function to choose which exercise-specific overlay function to run based on the selected workout type
    def _draw_overlays(self, img, metrics, ex_type):  
        if ex_type == "Squats":
            self._draw_squat_overlays(img, metrics)
        elif ex_type == "Push-ups":
            self._draw_pushup_overlays(img, metrics)
        elif ex_type == "Bicep Curls (Dumbbell)":
            self._draw_curl_overlays(img, metrics)
        elif ex_type == "Shoulder Press":
            self._draw_press_overlays(img, metrics)
        elif ex_type == "Lunges":
            self._draw_lunge_overlays(img, metrics)
        elif ex_type == "Deadlifts":
            self._draw_deadlift_overlays(img, metrics)
        elif ex_type == "Planks":
            self._draw_plank_overlays(img, metrics)

            # img - the webcam frame on which overlays are drawn
            # metrics - exercise data like reps, angles, stage, posture status, etc which have to displayed on the screen
            # ex_type - tells which exercise is currently selected
    
    def _draw_squat_overlays(self, img, metrics):   
        h, _ = img.shape[:2]    # h - height, _ - ignores width

        cv2.putText(
            img,
            f"DEPTH: {metrics['depth_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
    
    def _draw_pushup_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"BODY: {metrics['body_alignment']} | HIP: {metrics['hip_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

    def _draw_lunge_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"BALANCE: {metrics['balance_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    def _draw_curl_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"SWING: {metrics['swing_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
    
    def _draw_press_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"EXT: {metrics['extension_status']} | BACK: {metrics['back_arch_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
    
    def _draw_plank_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"POSTURE: {metrics['body_alignment']} | HIP: {metrics['hip_status']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

    def _draw_deadlift_overlays(self, img, metrics):
        h, _ = img.shape[:2]

        cv2.putText(
            img,
            f"HIP: {metrics['hip_status']} | BACK: {metrics['back_angle']}",
            (20, h - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )

    def recv(self, frame):
        image = np.asarray(
            cv2.flip(frame.to_ndarray(format = "bgr24"), 1),
            dtype = np.uint8
        )

        mp_image = mp.Image(      # MediaPipe needs its own image object "mp_image"
            image_format = mp.ImageFormat.SRGB,
            data = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Converts image color format for MediaPipe processing.
        )

        self._frame_timestamps_ms += 30
        result = self._landmarker.detect_for_video(mp_image, self._frame_timestamps_ms)  # detect_for_video - inbuilt MediaPipe PoseLandmarker method used for video-based pose detection and tracking.

        if result.pose_landmarks:
            landmarks = result.pose_landmarks[0]

            nose = landmarks[0]

            if nose.x < 0.15 or nose.x > 0.85:
                cv2.putText(
                    image,
                    "PLEASE FACE THE CAMERA",
                    (30, 100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 100, 255),
                    2,
                    cv2.LINE_AA
                )

            self._draw_skeleton(image, landmarks)

            ex_type = self.get_exercise()
            detector = self._detector.get(ex_type)

            if detector:
                metrics = detector.process(landmarks)
                metrics["pose_detected"] = True

                # rep counter on screen
                cv2.putText(
                    image, f"REPS: {metrics.get('reps', 0)}",
                    (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.9,
                    (255, 220, 0), 
                    3, 
                    cv2.LINE_AA
                )
                
                # fatigue warning
                if metrics.get("fatigue_detected"):
                    cv2.putText(
                        image, 
                        "FATIGUE DETECTED - CONSIDER STOPPING",
                        (20, 80), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7,
                        (0, 0, 255), 
                        2, 
                        cv2.LINE_AA
                    )
                
                # form bar
                self._draw_form_bar(image, metrics.get("form_score", 0))

                self._draw_overlays(image, metrics, ex_type)
                self.set_latest_metrics(metrics)

        else:
            self._draw_no_pose_warnings(image)
            with self._lock:
                if self._latest_metrics is not None:
                    self._latest_metrics["pose_detected"] = False
                else:
                    self._latest_metrics = {"pose_detected": False}

        return av.VideoFrame.from_ndarray(image, format="bgr24")
    