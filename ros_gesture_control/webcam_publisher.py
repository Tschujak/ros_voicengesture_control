#!/usr/bin/env python3
# webcam_publisher.py - Captures webcam video and publishes as ROS2 Image messages

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import sys
import time

class WebcamPublisher(Node):
   
    # Webcam Publisher Node - Captures video from a webcam and publishes it
    # to the 'webcam/image_raw' topic as ROS2 Image messages.
    
    def __init__(self):
        super().__init__('webcam_publisher')
        
        # ROS2 Parameters 
        self.declare_parameter('camera_id', 0)            # Camera device ID (0, 1, 2, ...)
        self.declare_parameter('frame_width', 640)        # Desired frame width
        self.declare_parameter('frame_height', 480)       # Desired frame height
        self.declare_parameter('fps', 15)                 # Frames per second for VM/ROS timer
        self.declare_parameter('show_window', True)       # Show preview window
        self.declare_parameter('timeout_sec', 5)          # Timeout before falling back to test mode
        
        # Read parameters
        camera_id = self.get_parameter('camera_id').value
        self.show_window = self.get_parameter('show_window').value
        self.timeout = self.get_parameter('timeout_sec').value
        
        # Camera initialization with multiple backends 
        # Try different backend options for cross-platform support
        backends = [
            cv2.CAP_V4L2,      # Linux Video4Linux2
            cv2.CAP_ANY,       # Auto-detect
            cv2.CAP_DSHOW,     # Windows DirectShow
        ]
        
        self.cap = None
        for backend in backends:
            self.get_logger().info(f"Opening camera {camera_id} with backend {backend}")
            self.cap = cv2.VideoCapture(camera_id, backend)
            if self.cap.isOpened():
                self.get_logger().info(f"Successfully opened with backend {backend}")
                break
            time.sleep(0.5)
        
        # Fallback: if camera fails, use test video mode
        if not self.cap or not self.cap.isOpened():
            self.get_logger().error(f"Cannot open camera {camera_id}")
            self.get_logger().info("Falling back to test video mode...")
            self.use_test_video = True
            self.cap = cv2.VideoCapture(0)  # One more attempt
        else:
            self.use_test_video = False
        
        # Set camera properties 
        if not self.use_test_video:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 15)
        
        # CV Bridge for ROS2 image conversion 
        self.bridge = CvBridge()
        
        # Publisher
        # Publish webcam images to 'webcam/image_raw' topic
        self.publisher = self.create_publisher(Image, 'webcam/image_raw', 10)
        
        # Timer
        # Timer period ~0.066 seconds = ~15 FPS
        timer_period = 0.066
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
        # Statistics 
        self.frame_count = 0
        self.error_count = 0
        self.start_time = time.time()
        
        self.get_logger().info("Webcam Publisher is running")
        if self.use_test_video:
            self.get_logger().warning("Running in TEST mode - generating test frames")
    
    def timer_callback(self):
        
       # Timer callback - captures a frame from webcam and publishes it.
        # Falls back to test image generation if camera fails or times out.
        
        # Check for timeout - if no frames captured within timeout, switch to test mode
        if time.time() - self.start_time > self.timeout and self.frame_count == 0:
            self.get_logger().error(f"Timeout after {self.timeout} seconds - no frames captured")
            if not self.use_test_video:
                self.get_logger().info("Switching to test video mode...")
                self.use_test_video = True
        
        # Capture frame from camera or generate test image
        if self.use_test_video:
            # Generate synthetic test image
            frame = self.generate_test_image()
            ret = True
        else:
            # Read frame from actual webcam
            ret, frame = self.cap.read()
        
        # Handle read failure
        if not ret:
            self.error_count += 1
            if self.error_count > 10:
                self.get_logger().warn("Too many frame read errors - switching to test mode")
                self.use_test_video = True
            return
        
        # Increment frame counter and log FPS periodically
        self.frame_count += 1
        if self.frame_count % 30 == 0:
            self.get_logger().info(f"Published {self.frame_count} frames")
        
        # Publish the frame as ROS2 Image message
        try:
            # Convert OpenCV image to ROS2 Image message
            ros_image = self.bridge.cv2_to_imgmsg(frame, "bgr8")
            ros_image.header.stamp = self.get_clock().now().to_msg()
            ros_image.header.frame_id = "webcam"
            self.publisher.publish(ros_image)
            
            # Show preview window if enabled
            if self.show_window:
                cv2.imshow('Webcam', frame)
                cv2.waitKey(1)  # Required for window update
        except Exception as e:
            self.get_logger().error(f"Error in timer_callback: {e}")
    
    def generate_test_image(self):
        
        # Generate a synthetic test image with frame counter and status text.
        # Used when no camera is available.
       
        import numpy as np
        frame = np.zeros((480, 640, 3), dtype=np.uint8)  # Black image
        # Draw test information on the frame
        cv2.putText(frame, f"TEST FRAME {self.frame_count}", 
                   (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Camera not available", 
                   (50, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return frame
    
    def destroy_node(self):
        
        # Cleanup resources when node is destroyed.
        # Releases camera and closes OpenCV windows.
        
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.get_logger().info(f"Final stats - Frames: {self.frame_count}, Errors: {self.error_count}")
        super().destroy_node()

def main(args=None):
    # Main entry point for the ROS2 node
    rclpy.init(args=args)
    node = WebcamPublisher()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()