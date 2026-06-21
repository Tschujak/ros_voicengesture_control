#!/usr/bin/env python3
# voice_recognizer.py - Voice command recognition using Vosk offline speech-to-text

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import threading
import time

class VoiceRecognizer(Node):
    
    # Voice Recognizer Node - Uses Vosk offline speech recognition to detect
    # voice commands. Publishes recognized commands to 'voice_cmd' topic.
    
    def __init__(self):
        super().__init__('voice_recognizer')
        
        # ROS2 Parameters 
        self.declare_parameter('model_path', 'vosk-model-small-en-us-0.15')  # Path to Vosk model
        self.declare_parameter('sample_rate', 16000)    # Audio sample rate (Hz)
        self.declare_parameter('blocksize', 8000)       # Audio block size for processing
        self.declare_parameter('device', None)          # Audio input device (None = default)
        
        # Read parameters
        model_path = self.get_parameter('model_path').value
        self.sample_rate = self.get_parameter('sample_rate').value
        self.blocksize = self.get_parameter('blocksize').value
        device = self.get_parameter('device').value
        
        # Initialize Vosk 
        try:
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)  # Enable word-level recognition
        except Exception as e:
            self.get_logger().error(f"Vosk error: {e}")
            self.get_logger().info("Download: https://alphacephei.com/vosk/models")
            self.get_logger().info("Or use: vosk-model-small-en-us-0.15")
            raise
        
        # Audio queue for thread communication 
        self.q = queue.Queue()
        
        # Publisher
        # Publish recognized voice commands
        self.publisher = self.create_publisher(
            String,
            'voice_cmd',
            10
        )
        
        # Command mapping
        # Maps spoken phrases to standardized robot commands
        self.commands = {
            "forward": "FORWARD",
            "go": "FORWARD",
            "walk": "FORWARD",
            "ahead": "FORWARD",
            "stop": "STOP",
            "halt": "STOP",
            "neutral": "STOP",
            "reset": "STOP",
            "left": "TURN_LEFT",
            "turn left": "TURN_LEFT",
            "right": "TURN_RIGHT",
            "turn right": "TURN_RIGHT",
            "back": "BACKWARD",
            "backward": "BACKWARD",
            "reverse": "BACKWARD",
            "emergency stop": "STOP",
            "emergency": "STOP",
        }
        
        # Audio Thread 
        # Thread for capturing audio from microphone
        self.audio_thread = threading.Thread(target=self.audio_processing)
        self.audio_thread.daemon = True
        self.audio_thread.start()
        
        # Recognition Thread 
        # Thread for processing audio and performing speech recognition
        self.recognition_thread = threading.Thread(target=self.recognition_loop)
        self.recognition_thread.daemon = True
        self.recognition_thread.start()
        
        self.get_logger().info("Voice Recognizer is running!")
        self.get_logger().info("Say: 'forward', 'stop', 'left', 'right', 'back'")
    
    def audio_processing(self):
        
        # Thread function: Captures audio from microphone using sounddevice
        # and puts raw audio data into the queue.
        
        try:
            # Open audio input stream with callback
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=self.blocksize,
                device=None,          # Use default microphone
                dtype='int16',        # 16-bit PCM audio
                channels=1,           # Mono audio
                callback=self.audio_callback
            ):
                self.get_logger().info("Audioflow is running...")
                while rclpy.ok():
                    time.sleep(0.1)   # Keep thread alive
        except Exception as e:
            self.get_logger().error(f"Error: {e}")
    
    def audio_callback(self, indata, frames, time, status):
    
        # Callback for sounddevice audio stream. Puts each audio block into the queue.
        
        if status:
            self.get_logger().warn(f"Audio status: {status}")
        self.q.put(bytes(indata))
    
    def recognition_loop(self):
        
        # Thread function: Takes audio data from queue, processes with Vosk,
        # and handles recognized speech.
    
        while rclpy.ok():
            try:
                # Get audio data from queue
                data = self.q.get()
                
                # Process with Vosk recognizer
                if self.recognizer.AcceptWaveform(data):
                    # Final result - complete phrase detected
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').lower().strip()
                    
                    if text:
                        self.process_speech(text)
                else:
                    # Partial result - still listening
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get('partial', '')
                    if partial_text:
                        self.get_logger().debug(f"Partial: {partial_text}")
            
            except queue.Empty:
                time.sleep(0.01)  # Avoid busy-waiting
            except Exception as e:
                self.get_logger().error(f"Recognize error: {e}")
    
    def process_speech(self, text):
    
        # Process recognized text: match against command dictionary and publish.
        
        self.get_logger().info(f"Recognized: '{text}'")
        
        # Find matching command (contains voice command phrase in text)
        recognized_command = None
        for voice_cmd, ros_cmd in self.commands.items():
            if voice_cmd in text:
                recognized_command = ros_cmd
                break
        
        # Publish if a command was recognized
        if recognized_command:
            msg = String()
            msg.data = recognized_command
            self.publisher.publish(msg)
            
            self.get_logger().info(f"Command: {recognized_command}")
        else:
            self.get_logger().warn(f"Unknown command: '{text}'")
    
    def destroy_node(self):
        # Cleanup resources when node is destroyed
        self.get_logger().info("Ending of Voice Recognizer...")
        super().destroy_node()

def main(args=None):
    # Main entry point for the ROS2 node.
    rclpy.init(args=args)
    
    try:
        node = VoiceRecognizer()
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("\nVR is stopped")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()