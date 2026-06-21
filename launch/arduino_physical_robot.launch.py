from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'arduino_port',
            default_value='auto',
            description='Port: auto, /dev/ttyUSB0'
        ),
        DeclareLaunchArgument(
            'baudrate',
            default_value='115200',
            description='Serial baudrate'
        ),
        DeclareLaunchArgument(
            'priority_mode',
            default_value='gesture',
            description='Priority: voice, gesture, mixed'
        ),
        
        Node(
            package='ros_gesture_control',
            executable='webcam_publisher',
            name='webcam_publisher',
            output='screen',
            parameters=[{
                'camera_id': 0,
                'frame_width': 640,
                'frame_height': 480
            }]
        ),
        
        Node(
            package='ros_gesture_control',
            executable='gesture_detector',
            name='gesture_detector',
            output='screen',
            parameters=[{
                'min_detection_confidence': 0.7,
                'min_tracking_confidence': 0.5
            }]
        ),
        
        Node(
            package='ros_gesture_control',
            executable='arduino_command_fusion',
            name='arduino_command_fusion',
            output='screen',
            parameters=[{
                'priority': LaunchConfiguration('priority_mode'),
                'voice_timeout': 3.0,
                'gesture_timeout': 2.0,
                'use_serial': True
            }]
        ),
        
        Node(
            package='ros_gesture_control',
            executable='arduino_serial_bridge',
            name='arduino_serial_bridge',
            output='screen',
            parameters=[{
                'port': LaunchConfiguration('arduino_port'),
                'baudrate': LaunchConfiguration('baudrate')
            }]
        ),

        Node(
            package='ros_gesture_control',
            executable='voice_recognizer',
            name='voice_recognizer',
            output='screen',
            parameters=[{
                'model_path': '/home/remark/vosk-model-small-en-us-0.15',
                'sample_rate': 16000
            }]
        ),

    ])
