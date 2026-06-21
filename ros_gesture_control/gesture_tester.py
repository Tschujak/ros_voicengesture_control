#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class GestureTester(Node):
    def __init__(self):
        super().__init__('gesture_tester')
        
        self.subscription = self.create_subscription(
            String,
            'gesture_cmd',
            self.gesture_callback,
            10
        )
        
        self.get_logger().info("Gesture Tester is running..")
    
    def gesture_callback(self, msg):
        self.get_logger().info(f"Gesture received: {msg.data}")
        
        if msg.data == "forward":
            self.get_logger().info("GO!")
        elif msg.data == "stop":
            self.get_logger().info("STOP!")
        elif msg.data == "turn_left":
            self.get_logger().info("LEFT!")
        elif msg.data == "turn_right":
            self.get_logger().info("RIGHT!")
        elif msg.data == "no_hand":
            self.get_logger().info("No hand:(")
        else:
            self.get_logger().info(f"What a gesture: {msg.data}")

def main(args=None):
    rclpy.init(args=args)
    node = GestureTester()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
