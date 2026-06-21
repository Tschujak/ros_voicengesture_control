from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'ros_gesture_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py'))
    ],  
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='remark',
    maintainer_email='remark@todo.todo',
    description='Gesture and voice control system for ROS',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'webcam_publisher = ros_gesture_control.webcam_publisher:main',
            'micro_ros_controller = ros_gesture_control.micro_ros_controller:main',
            'simple_virtual_camera = ros_gesture_control.simple_virtual_camera:main',
            'gesture_detector = ros_gesture_control.gesture_detector:main',
            'gesture_tester = ros_gesture_control.gesture_tester:main',
            'virtual_hand_camera = ros_gesture_control.virtual_hand_camera:main',
            'obs_webcam_publisher = ros_gesture_control.obs_webcam_publisher:main',
            'robot_controller = ros_gesture_control.robot_controller:main',
            'test_robot_controller = ros_gesture_control.test_robot_controller:main',
            'voice_recognizer = ros_gesture_control.voice_recognizer:main',
            'command_fusion = ros_gesture_control.command_fusion:main',
            'arduino_tester = ros_gesture_control.arduino_tester:main',
            'serial_bridge = ros_gesture_control.serial_bridge:main',
	    'arduino_serial_bridge = ros_gesture_control.arduino_serial_bridge:main',
            'arduino_command_fusion = ros_gesture_control.arduino_command_fusion:main',
	    'command_fusion_mr = ros_gesture_control.command_fusion_mr:main',
        ],
    },
)
