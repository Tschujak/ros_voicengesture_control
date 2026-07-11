#include <Arduino.h>
#include <AFMotor.h>

// Motor object initialization with port numbers (M1-M4)
AF_DCMotor frontLeftMotor(1);   
AF_DCMotor frontRightMotor(2);  
AF_DCMotor rearLeftMotor(3);    
AF_DCMotor rearRightMotor(4);   

const int SPEED_FORWARD = 200;
const int SPEED_BACKWARD = 180;
const int SPEED_TURN = 180;


void setAllMotors(uint8_t direction, int speed) {
  // Set direction for all motors
  frontLeftMotor.run(direction);
  frontRightMotor.run(direction);
  rearLeftMotor.run(direction);
  rearRightMotor.run(direction);

   // Set speed for all motors
  frontLeftMotor.setSpeed(speed);
  frontRightMotor.setSpeed(speed);
  rearLeftMotor.setSpeed(speed);
  rearRightMotor.setSpeed(speed);
}

void moveForward() {
  setAllMotors(FORWARD, SPEED_FORWARD);
}

void moveBackward() {
  setAllMotors(BACKWARD, SPEED_BACKWARD);
}

void turnLeft() {
   // Left side motors backward, right side motors forward for left turn
  frontLeftMotor.run(BACKWARD);
  frontRightMotor.run(FORWARD);
  rearLeftMotor.run(BACKWARD);
  rearRightMotor.run(FORWARD);
  
  frontLeftMotor.setSpeed(SPEED_TURN);
  frontRightMotor.setSpeed(SPEED_TURN);
  rearLeftMotor.setSpeed(SPEED_TURN);
  rearRightMotor.setSpeed(SPEED_TURN);
}

void turnRight() {
  // Left side motors forward, right side motors backward for right turn
  frontLeftMotor.run(FORWARD);
  frontRightMotor.run(BACKWARD);
  rearLeftMotor.run(FORWARD);
  rearRightMotor.run(BACKWARD);
  
  frontLeftMotor.setSpeed(SPEED_TURN);
  frontRightMotor.setSpeed(SPEED_TURN);
  rearLeftMotor.setSpeed(SPEED_TURN);
  rearRightMotor.setSpeed(SPEED_TURN);
}

void stopMotors() {
  frontLeftMotor.run(RELEASE);
  frontRightMotor.run(RELEASE);
  rearLeftMotor.run(RELEASE);
  rearRightMotor.run(RELEASE);
}


void setup() {
  Serial.begin(115200);
  delay(100); // Small delay for system stabilization
  
  // All motors are initially stopped
  stopMotors();
  
  Serial.println("ARDUINO_READY_4WD");
}


void loop() {
  // Read commands from Serial
  while (Serial.available() > 0) {
    char cmd = Serial.read(); // Read single character from serial buffer
    
   // Skip control characters (newline, carriage return, space)
    if (cmd == '\n' || cmd == '\r' || cmd == ' ') {
      continue;
    }
    
   // Process the command using switch-case
    switch (cmd) {
      case 'F':  
        moveForward();
        Serial.println("CMD:F");
        break;
        
      case 'B':  
        moveBackward();
        Serial.println("CMD:B");
        break;
        
      case 'L':  
        turnLeft();
        Serial.println("CMD:L");
        break;
        
      case 'R':  
        turnRight();
        Serial.println("CMD:R");
        break;
        
      case 'S':
        stopMotors();
        Serial.println("CMD:S");
        break;
        
        
      default:
       // Ignore any unrecognized commands
        break;
    }
  }
  
  // Small delay to prevent overwhelming the serial buffer
  delay(10);
}