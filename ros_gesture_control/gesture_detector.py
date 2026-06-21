#!/usr/bin/env python3
# gesture_detector.py - Hand gesture recognition using MediaPipe for robot control

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
import cv2
import numpy as np
import time

import mediapipe as mp

class GestureDetector(Node):
    
    # Gesture Detector Node - Uses MediaPipe Hands to detect hand landmarks
    # and recognize gestures. Publishes gesture commands to 'gesture_cmd' topic.
    
    def __init__(self):
        super().__init__('gesture_detector')
        
        # --- MediaPipe initialization ---
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Configure MediaPipe Hands with high confidence thresholds
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,                      # Process only one hand at a time
            min_detection_confidence=0.7,         # Minimum confidence for detection
            min_tracking_confidence=0.5           # Minimum confidence for tracking
        )
        
        # CV Bridge for ROS2 image conversion 
        self.bridge = CvBridge()
        
        # Subscriber
        # Subscribe to webcam image stream from webcam_publisher.py
        self.subscription = self.create_subscription(
            Image,
            'webcam/image_raw',
            self.image_callback,
            10
        )
        
        # Publisher 
        # Publish recognized gesture commands
        self.gesture_publisher = self.create_publisher(
            String,
            'gesture_cmd',
            10
        )
        
        # State management
        self.last_published_gesture = None        # Last gesture published
        self.gesture_cooldown = 0.5               # Minimum time between publishes (seconds)
        self.last_publish_time = time.time()      # Timestamp of last publish
        
        # FPS tracking
        self.frame_count = 0
        self.prev_time = time.time()
        self.fps = 0
        
        self.get_logger().info("Gesture Detector is running!")
        self.get_logger().info(f"MediaPipe version: {mp.__version__}")
        self.get_logger().info("Gestures: STOP, FORWARD, TURN_LEFT, TURN_RIGHT, BACKWARD")
    
    def is_finger_up(self, landmarks, finger_tip_id, finger_pip_id):
        
        # Check if a finger is extended by comparing tip and pip y-coordinates.
        # Returns True if finger is raised (tip is higher than pip).
        
        return landmarks[finger_tip_id].y < landmarks[finger_pip_id].y
    
    def detect_simple_gesture(self, landmarks):
        
        # Detect gesture from hand landmarks using finger positions.
        # Returns command string: 'forward', 'left', 'right', 'backward', 'stop', or 'unknown'.
        
        # Check each finger state (up/raised or down)
        thumb_up = self.is_finger_up(landmarks, 4, 3)
        index_up = self.is_finger_up(landmarks, 8, 6)
        middle_up = self.is_finger_up(landmarks, 12, 10)
        ring_up = self.is_finger_up(landmarks, 16, 14)
        pinky_up = self.is_finger_up(landmarks, 20, 18)
        
        # Get thumb and index tip positions for OK/finger pinch detection
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        distance = ((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)**0.5
        
        # Gesture rules 
        # Fist (all fingers down) -> STOP
        if not index_up and not middle_up and not ring_up and not pinky_up:
            return "stop"
        
        # One finger (index only) -> FORWARD
        if index_up and not middle_up and not ring_up and not pinky_up:
            return "forward"
        
        # Two fingers (index + middle) -> TURN LEFT/RIGHT based on thumb position
        if index_up and middle_up and not ring_up and not pinky_up:
            wrist = landmarks[0]
            if thumb_tip.x < wrist.x:
                return "turn_left"
            else:
                return "turn_right"
        
        # All fingers up -> STOP (emergency stop gesture)
        if index_up and middle_up and ring_up and pinky_up:
            return "stop"
        
        # Pinch (thumb and index close together) -> STOP
        if distance < 0.05 and not middle_up and not ring_up and not pinky_up:
            return "stop"
        
        # Pinky only -> BACKWARD
        if pinky_up and not index_up and not middle_up and not ring_up:
            return "backward"
        
        return "unknown"
    
    def image_callback(self, msg):
        
        # Callback for incoming webcam images. Processes each frame for hand detection.
        
        try:
            # Convert ROS Image message to OpenCV BGR image
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            h, w = cv_image.shape[:2]
            
            # Convert BGR to RGB for MediaPipe
            rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
            
            # Process the image with MediaPipe
            rgb_image.flags.writeable = False
            results = self.hands.process(rgb_image)
            rgb_image.flags.writeable = True
            
            # Default state
            detected_gesture = "no_hand"
            hand_detected = False
            
            # If hand detected, process landmarks and detect gesture
            if results.multi_hand_landmarks:
                hand_detected = True
                for hand_landmarks in results.multi_hand_landmarks:
                    # Detect gesture from landmarks
                    gesture = self.detect_simple_gesture(hand_landmarks.landmark)
                    
                    # Map detected gesture to published command
                    if gesture == "forward":
                        detected_gesture = "forward"
                    elif gesture == "turn_left":
                        detected_gesture = "left"
                    elif gesture == "turn_right":
                        detected_gesture = "right"
                    elif gesture == "backward":
                        detected_gesture = "back"
                    elif gesture == "stop":
                        detected_gesture = "stop"
                    else:
                        detected_gesture = "stop"
                    
                    # Draw hand landmarks on the image
                    self.mp_drawing.draw_landmarks(
                        cv_image,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                        self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                    )
            
            # Publish logic with cooldown 
            current_time = time.time()
            time_diff = current_time - self.last_publish_time
            
            should_publish = False
            # Publish if gesture changed OR if cooldown expired and hand detected
            if detected_gesture != self.last_published_gesture:
                should_publish = True
            elif time_diff > self.gesture_cooldown and detected_gesture != "no_hand":
                should_publish = True
            
            if should_publish and detected_gesture != "unknown":
                gesture_msg = String()
                gesture_msg.data = detected_gesture
                self.gesture_publisher.publish(gesture_msg)
                
                self.last_published_gesture = detected_gesture
                self.last_publish_time = current_time
                
                if detected_gesture != "no_hand":
                    self.get_logger().info(f"Gesture: {detected_gesture}")
            
            # FPS calculation 
            self.frame_count += 1
            current_time_fps = time.time()
            time_diff_fps = current_time_fps - self.prev_time
            
            if time_diff_fps >= 1.0:
                self.fps = self.frame_count / time_diff_fps
                self.frame_count = 0
                self.prev_time = current_time_fps
            
            # Draw info overlay on image
            self.draw_info_panel(cv_image, detected_gesture, hand_detected)
            
            # Display the image window
            cv2.imshow('Gesture Detection', cv_image)
            
            # Check for quit key (Q or ESC)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                self.get_logger().info("Stopping...")
                raise KeyboardInterrupt
                
        except Exception as e:
            self.get_logger().error(f"Error image_callback: {str(e)}", throttle_duration_sec=5)
    
    def draw_info_panel(self, image, gesture, hand_detected):
        
        # Draw UI overlay on the image showing current gesture, FPS, and status.
        
        h, w = image.shape[:2]
        
        # Semi-transparent black panel at top
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (w, 100), (40, 40, 40), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)
        
        # Title
        cv2.putText(image, "GESTURE DETECTOR", 
                   (w//2 - 150, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.8, (0, 200, 255), 2)
        
        # Gesture text with color based on hand detection
        gesture_color = (0, 255, 0) if hand_detected else (0, 0, 255)
        
        # Format gesture for display
        display_gesture = gesture
        if gesture == "forward":
            display_gesture = "FORWARD"
        elif gesture == "left":
            display_gesture = "TURN LEFT"
        elif gesture == "right":
            display_gesture = "TURN RIGHT"
        elif gesture == "back":
            display_gesture = "BACKWARD"
        elif gesture == "stop":
            display_gesture = "STOP"
        elif gesture == "no_hand":
            display_gesture = "NO HAND"
        
        cv2.putText(image, f"Gesture: {display_gesture}", 
                   (w//2 - 100, 70), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.9, gesture_color, 2)
        
        # FPS counter (bottom-left)
        cv2.putText(image, f"FPS: {self.fps:.1f}", 
                   (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.6, (0, 255, 255), 1)
        
        # Hand detection status (bottom-left)
        hand_status = "Hand detected" if hand_detected else "No hand"
        status_color = (0, 255, 0) if hand_detected else (100, 100, 100)
        cv2.putText(image, hand_status, 
                   (10, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.6, status_color, 1)
        
        # Quit instruction (bottom-right)
        cv2.putText(image, "Press 'q' to quit", 
                   (w - 150, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.5, (200, 200, 200), 1)
        
        # Gesture legend (top-right below panel)
        cv2.putText(image, "1 finger: FWD | 2 fingers: TURN | Pinky: BACK | Fist: STOP", 
                   (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.5, (200, 200, 200), 1)
    
    def destroy_node(self):
        # Cleanup resources when node is destroyed
        self.get_logger().info("Gesture Detector is ending...")
        self.hands.close()
        cv2.destroyAllWindows()
        super().destroy_node()

def main(args=None):
    # Main entry point for the ROS2 node
    rclpy.init(args=args)
    
    try:
        node = GestureDetector()
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\nGesture Detector is stopped")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()