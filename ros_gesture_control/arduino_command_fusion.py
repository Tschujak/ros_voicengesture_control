#!/usr/bin/env python3
# arduino_command_fusion.py - Fuses gesture and voice commands into unified robot control commands

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
import time

class CommandFusion(Node):
    
    # Command Fusion Node - Merges gesture and voice commands with priority management.
    # Subscribes to gesture_cmd and voice_cmd topics, publishes unified command to final_cmd and /cmd_vel.
    
    def __init__(self):
        super().__init__('arduino_command_fusion')
        
        # ROS2 Parameters with defaults
        self.declare_parameter('priority', 'gesture')           # 'gesture' or 'voice' - which input takes precedence
        self.declare_parameter('voice_timeout', 3.0)           # Seconds before voice command expires
        self.declare_parameter('gesture_timeout', 2.0)         # Seconds before gesture command expires
        self.declare_parameter('use_serial', True)             # Whether to publish serial commands
        
        # Read parameters from ROS2 parameter server
        self.priority = self.get_parameter('priority').value
        self.voice_timeout = self.get_parameter('voice_timeout').value
        self.gesture_timeout = self.get_parameter('gesture_timeout').value
        self.use_serial = self.get_parameter('use_serial').value
        
        # Subscribers
        # Subscribe to gesture commands from gesture_detector.py
        self.gesture_sub = self.create_subscription(
            String, 'gesture_cmd', self.gesture_callback, 10
        )
        # Subscribe to voice commands from voice_recognizer.py
        self.voice_sub = self.create_subscription(
            String, 'voice_cmd', self.voice_callback, 10
        )
        
        # Publishers
        # Publish final command string for debugging/other nodes
        self.final_publisher = self.create_publisher(String, 'final_cmd', 10)
        # Publish Twist message for robot movement (used by arduino_serial_bridge.py)
        self.twist_publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # State variables
        self.current_gesture = None       # Most recent gesture command
        self.current_voice = None         # Most recent voice command
        self.last_gesture_time = 0        # Timestamp of last gesture update
        self.last_voice_time = 0          # Timestamp of last voice update
        
        # Timer to run fusion logic at 10 Hz (0.1 seconds)
        self.timer = self.create_timer(0.1, self.fusion_loop)
        # Store command history for deduplication (last 20 commands)
        self.command_history = []
        
        # Command Mapping
        # Maps gesture/voice strings to standardized robot commands
        self.command_mapping = {
            'stop': 'STOP',
            'forward': 'FORWARD',
            'back': 'BACKWARD',
            'backward': 'BACKWARD',
            'left': 'TURN_LEFT',
            'right': 'TURN_RIGHT',
            'turn_left': 'TURN_LEFT',
            'turn_right': 'TURN_RIGHT',
            'open': 'STOP',           # Open hand gesture -> stop
            'ok': 'STOP',             # OK gesture -> stop
            'walk': 'FORWARD',
            'go': 'FORWARD',
        }
        
        # Twist Mapping
        # Maps standardized commands to linear.x and angular.z values
        self.twist_mapping = {
            'FORWARD': (0.5, 0.0),      # Move forward at 0.5 m/s
            'BACKWARD': (-0.5, 0.0),    # Move backward at -0.5 m/s
            'STOP': (0.0, 0.0),         # Stop movement
            'TURN_LEFT': (0.0, 0.5),    # Turn left at 0.5 rad/s
            'TURN_RIGHT': (0.0, -0.5),  # Turn right at -0.5 rad/s
        }
        
        self.get_logger().info("Command Fusion started")
        self.get_logger().info(f"Priority: {self.priority}")

    def gesture_callback(self, msg):
        # Callback for gesture commands. Updates current gesture with timestamp
        gesture = msg.data
        # If "no_hand" is received but gesture timeout hasn't expired, ignore it
        if gesture == "no_hand" and self.current_gesture:
            if time.time() - self.last_gesture_time < self.gesture_timeout:
                return
        self.current_gesture = gesture
        self.last_gesture_time = time.time()
        if gesture != "no_hand":
            self.get_logger().info(f"Gesture: {gesture}")

    def voice_callback(self, msg):
        # Callback for voice commands. Updates current voice with timestamp
        self.current_voice = msg.data
        self.last_voice_time = time.time()
        self.get_logger().info(f"Voice: {msg.data}")

    def fusion_loop(self):
        
        # Main fusion loop - called every 0.1 seconds.
        # Checks for expired commands, selects priority command, and publishes it
       
        current_time = time.time()
        
        # --- Expire old commands ---
        # Clear voice command if it's older than voice_timeout
        if self.current_voice and (current_time - self.last_voice_time) > self.voice_timeout:
            self.current_voice = None
        # Clear gesture command if it's older than gesture_timeout
        if self.current_gesture and (current_time - self.last_gesture_time) > self.gesture_timeout:
            self.current_gesture = None
        
        # Select the final command based on priority setting
        final_command = self.select_final_command()
     
        # Only publish if command changed (avoid spamming)
        if final_command and final_command != self.get_last_published():
            msg = String()
            msg.data = final_command
            self.final_publisher.publish(msg)
            
            # Convert to Twist and publish to /cmd_vel for serial bridge
            twist = self.command_to_twist(final_command)
            if twist:
                self.twist_publisher.publish(twist)
                self.get_logger().info(
                    f'Twist: x={twist.linear.x:.2f}, z={twist.angular.z:.2f}'
                )
            
            # Store in history (keep last 20)
            self.command_history.append({
                'time': current_time,
                'command': final_command
            })
            if len(self.command_history) > 20:
                self.command_history.pop(0)

    def select_final_command(self):
        
        # Select which command takes priority based on self.priority.
        # Returns the command string or "stop" as fallback.
        
        if self.priority == 'gesture':
            # Gesture first, voice as fallback
            if self.current_gesture and self.current_gesture != "no_hand":
                return self.current_gesture
            elif self.current_voice:
                return self.current_voice
        elif self.priority == 'voice':
            # Voice first, gesture as fallback
            if self.current_voice:
                return self.current_voice
            elif self.current_gesture and self.current_gesture != "no_hand":
                return self.current_gesture
        # Default fallback - always stop if no command
        return "stop"

    def command_to_twist(self, command):
        """
        Convert a command string to a Twist message.
        Uses command_mapping then twist_mapping.
        """
        # Map command to standardized robot command (e.g., "forward" -> "FORWARD")
        robot_cmd = self.command_mapping.get(command.lower(), 'STOP')
        # Get linear and angular values from mapping
        linear, angular = self.twist_mapping.get(robot_cmd, (0.0, 0.0))
        # Create and populate Twist message
        twist = Twist()
        twist.linear.x = linear
        twist.angular.z = angular
        return twist

    def get_last_published(self):
        # Get the last published command from history to avoid duplicate publishes
        if self.command_history:
            return self.command_history[-1]['command']
        return None

def main(args=None):
    # Main entry point for the ROS2 node
    rclpy.init(args=args)
    node = CommandFusion()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()