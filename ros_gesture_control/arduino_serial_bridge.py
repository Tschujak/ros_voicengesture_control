#!/usr/bin/env python3
# arduino_serial_bridge.py - Bridges ROS2 Twist commands to serial for Arduino/ESP32

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import serial.tools.list_ports
import time

class SerialBridge(Node):
    
    # Serial Bridge Node - Subscribes to /cmd_vel Twist messages and sends
    # corresponding single-character commands over serial to Arduino/ESP32.
    
    def __init__(self):
        super().__init__('arduino_serial_bridge')
        
        # ROS2 Parameters 
        self.declare_parameter('port', 'auto')      # Serial port: 'auto' for auto-discovery, or specific like '/dev/ttyUSB0'
        self.declare_parameter('baudrate', 115200)  # Baud rate for serial communication
        
        # Serial connection
        self.ser = None
        self.connected = False
        
        # Attempt to connect to serial port
        self.connect_serial()
        
        # Subscriber 
        # Subscribe to Twist commands from command_fusion.py
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_callback,
            10
        )
        
        # Timer to periodically check serial connection status (every 2 seconds)
        self.create_timer(2.0, self.check_connection)
        
        self.get_logger().info('Arduino Serial Bridge started')
        self.get_logger().info(f'Connected: {self.connected}')

    def connect_serial(self):
        
        # Connect to serial port. If port='auto', scan for common Arduino/ESP32
        # USB-to-serial chips (CH340, FTDI, etc.).
        
        port = self.get_parameter('port').value
        baudrate = self.get_parameter('baudrate').value
        
        # Auto-detect serial port if set to 'auto'
        if port == 'auto':
            ports = serial.tools.list_ports.comports()
            self.get_logger().info(f'Scanning {len(ports)} ports...')
            
            for p in ports:
                # Look for common Arduino/ESP32 USB-to-serial chips
                if any(x in p.description.upper() for x in 
                       ['CH340', 'FTDI', 'ARDUINO', 'UNO', 'USB']):
                    port = p.device
                    self.get_logger().info(f'Found on {port} ({p.description})')
                    break
            else:
                self.get_logger().warn('No Arduino found!')
        
        # Attempt to connect using the determined port
        if port and port != 'auto':
            try:
                self.ser = serial.Serial(port, baudrate, timeout=1)
                time.sleep(2)  # Wait for Arduino to reset after opening serial
                self.connected = True
                self.get_logger().info(f'CONNECTED to {port} @ {baudrate}')
                
                # Read any greeting message from Arduino
                if self.ser.in_waiting > 0:
                    greeting = self.ser.readline().decode().strip()
                    self.get_logger().info(f'Arduino: {greeting}')
                    
            except Exception as e:
                self.connected = False
                self.get_logger().error(f'Failed: {e}')
                self.get_logger().error('Check: ls -l /dev/ttyUSB*')
                self.get_logger().error('Run: sudo usermod -a -G dialout $USER')

    def check_connection(self):
        #Timer callback to check and reconnect serial if disconnected."""
        if not self.connected:
            self.connect_serial()
        elif self.ser and not self.ser.is_open:
            self.connected = False
            self.get_logger().warn('Disconnected!')

    def cmd_callback(self, msg):
        """
        Callback for Twist messages. Converts linear.x and angular.z to
        single-character serial commands:
        - F: Forward
        - B: Backward
        - R: Turn Right
        - L: Turn Left
        - S: Stop
        """
        self.get_logger().info(
            f'cmd_vel: x={msg.linear.x:.2f}, z={msg.angular.z:.2f}'
        )
        
        # Check if serial is connected
        if not self.connected or not self.ser:
            self.get_logger().warn('Cannot send: Not connected!')
            return
        
        try:
            # Determine which command to send based on Twist values
            if msg.linear.x > 0.1:
                # Move forward
                self.ser.write(b'F\n')
                self.get_logger().info('Sent: F (FORWARD)')
            elif msg.linear.x < -0.1:
                # Move backward
                self.ser.write(b'B\n')
                self.get_logger().info('Sent: B (BACKWARD)')
            elif msg.angular.z > 0.1:
                # Turn right (positive z = counter-clockwise in ROS, but mapped to right)
                self.ser.write(b'R\n')
                self.get_logger().info('Sent: R (TURN RIGHT)')
            elif msg.angular.z < -0.1:
                # Turn left (negative z = clockwise in ROS, but mapped to left)
                self.ser.write(b'L\n')
                self.get_logger().info('Sent: L (TURN LEFT)')
            else:
                # Stop (all values near zero)
                self.ser.write(b'S\n')
                self.get_logger().info('Sent: S (STOP)')
                
        except Exception as e:
            self.get_logger().error(f'Write error: {e}')
            self.connected = False

def main(args=None):
    # Main entry point for the ROS2 node
    rclpy.init(args=args)
    node = SerialBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()