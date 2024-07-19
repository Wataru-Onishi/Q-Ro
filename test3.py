import os
import time
import pygame
import RPi.GPIO as GPIO
from pygame.locals import *
from dynamixel_sdk import *  # Uses Dynamixel SDK library

# Pygame and controller initialization
pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

# GPIO setup
sensor_pins = [16, 19, 20, 26]
GPIO.setmode(GPIO.BCM)
for pin in sensor_pins:
    GPIO.setup(pin, GPIO.IN)

# Define button mappings
BUTTON_MOVE_TO_POSITION_X = 0
BUTTON_MOVE_TO_STANDARD_POSITION = 1
BUTTON_TOGGLE_CURRENT_LIMIT = 2
BUTTON_BRAKE_MOTORS = 4
BUTTON_TOGGLE_MODE = 5
BUTTON_EXIT_PROGRAM = 10

# Define hat (D-pad) mappings
HAT_UP = (0, 1)
HAT_DOWN = (0, -1)
HAT_RIGHT = (1, 0)
HAT_LEFT = (-1, 0)

# Timing constants for auto mode operations
STOP_DURATION = 1  # Time to stop in seconds
TURN_DURATION = 5  # Time to turn right in seconds
MOVE_FORWARD_DURATION = 3  # Time to move forward in seconds
SENSOR_SAMPLING_INTERVAL = 0.1  # Time between sensor checks in seconds

# Dynamixel control table addresses
ADDR_OPERATING_MODE = 11
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_CURRENT = 102
ADDR_GOAL_VELOCITY = 104
ADDR_GOAL_POSITION = 116
ADDR_PRESENT_POSITION = 132

# Protocol version
PROTOCOL_VERSION = 2.0

# Dynamixel settings
DXL_IDS = [1, 2, 3]
BAUDRATE = 57600
DEVICENAME = '/dev/DYNAMIXEL'
TORQUE_ENABLE = 1
TORQUE_DISABLE = 0

# Operating modes
CURRENT_BASED_POSITION_CONTROL = 5
POSITION_CONTROL_MODE = 3
VELOCITY_CONTROL_MODE = 1

# Current limit settings
CURRENT_LIMIT_HIGH = 12
CURRENT_LIMIT_LOW = 4
current_limit = CURRENT_LIMIT_HIGH

# Position and velocity settings
standard_position = 2048
forward_velocity = 300
backward_velocity = -300
turning_velocity = 100
new_goal_position = 4096

# Mode settings
MANUAL_MODE = 0
AUTO_MODE = 1
current_mode = MANUAL_MODE

# Initialize PortHandler and PacketHandler instances
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

# Open port and set baudrate
if not portHandler.openPort():
    print("Failed to open the port!")
    quit()
if not portHandler.setBaudRate(BAUDRATE):
    print("Failed to change the baudrate!")
    quit()

def enable_torque(ids, enable):
    for id in ids:
        packetHandler.write1ByteTxRx(portHandler, id, ADDR_TORQUE_ENABLE, enable)

def set_operating_mode(id, mode):
    enable_torque([id], TORQUE_DISABLE)
    packetHandler.write1ByteTxRx(portHandler, id, ADDR_OPERATING_MODE, mode)
    enable_torque([id], TORQUE_ENABLE)

def set_goal_current(id, current):
    packetHandler.write2ByteTxRx(portHandler, id, ADDR_GOAL_CURRENT, current)

def set_goal_position(id, position):
    packetHandler.write4ByteTxRx(portHandler, id, ADDR_GOAL_POSITION, position)

def set_goal_velocity(id, velocity):
    if id == 3:
        velocity = -velocity  # Reverse velocity for ID 3
    packetHandler.write4ByteTxRx(portHandler, id, ADDR_GOAL_VELOCITY, velocity)

def check_stop_signal():
    return GPIO.input(26)  # Return the current state of GPIO 26

# Enable torque for all motors
enable_torque(DXL_IDS, TORQUE_ENABLE)

print("Dynamixel has been successfully connected and controller is ready.")

try:
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == JOYBUTTONDOWN:
                if event.button == BUTTON_TOGGLE_MODE:
                    current_mode = AUTO_MODE if current_mode == MANUAL_MODE else MANUAL_MODE
                    if current_mode == AUTO_MODE:
                        set_goal_velocity(2, 0)  # Stop all motors when entering auto mode
                        set_goal_velocity(3, 0)
                        print("Switched to AUTO MODE. Motors stopped.")
                    else:
                        print("Switched to MANUAL MODE.")
                elif event.button == BUTTON_BRAKE_MOTORS:
                    set_goal_velocity(2, 0)
                    set_goal_velocity(3, 0)
                    print("Braking Motors 2 and 3.")
                elif event.button == BUTTON_EXIT_PROGRAM:
                    print("PS button pressed. Exiting program.")
                    running = False
                if current_mode == MANUAL_MODE:
                    if event.button == BUTTON_MOVE_TO_POSITION_X:
                        set_operating_mode(1, CURRENT_BASED_POSITION_CONTROL)
                        set_goal_current(1, current_limit)
                        set_goal_position(1, new_goal_position)
                        print(f"ID 1: Moving to position {new_goal_position} with {current_limit}mA.")
                    elif event.button == BUTTON_MOVE_TO_STANDARD_POSITION:
                        set_operating_mode(1, POSITION_CONTROL_MODE)
                        set_goal_position(1, standard_position)
                        print(f"ID 1: Moving to standard position {standard_position}.")
                    elif event.button == BUTTON_TOGGLE_CURRENT_LIMIT:
                        current_limit = CURRENT_LIMIT_LOW if current_limit == CURRENT_LIMIT_HIGH else CURRENT_LIMIT_HIGH
                        print(f"Current limit toggled to {current_limit}mA.")

            elif event.type == JOYHATMOTION:
                if current_mode == MANUAL_MODE:
                    if joystick.get_hat(0) == HAT_UP:
                        set_operating_mode(2, VELOCITY_CONTROL_MODE)
                        set_operating_mode(3, VELOCITY_CONTROL_MODE)
                        set_goal_velocity(2, forward_velocity)
                        set_goal_velocity(3, forward_velocity)
                        print("Motors 2 and 3 are set to move forward at controlled speed.")
                    elif joystick.get_hat(0) == HAT_DOWN:
                        set_operating_mode(2, VELOCITY_CONTROL_MODE)
                        set_operating_mode(3, VELOCITY_CONTROL_MODE)
                        set_goal_velocity(2, backward_velocity)
                        set_goal_velocity(3, backward_velocity)
                        print("Motors 2 and 3 are set to move backward at controlled speed.")
                    elif joystick.get_hat(0) == HAT_RIGHT:
                        set_operating_mode(2, VELOCITY_CONTROL_MODE)
                        set_operating_mode(3, VELOCITY_CONTROL_MODE)
                        set_goal_velocity(2, turning_velocity)
                        set_goal_velocity(3, -turning_velocity)
                        print("Turning right with Motors 2 and 3.")
                    elif joystick.get_hat(0) == HAT_LEFT:
                        set_operating_mode(2, VELOCITY_CONTROL_MODE)
                        set_operating_mode(3, VELOCITY_CONTROL_MODE)
                        set_goal_velocity(2, -turning_velocity)
                        set_goal_velocity(3, turning_velocity)
                        print("Turning left with Motors 2 and 3.")
                elif current_mode == AUTO_MODE and joystick.get_hat(0) == HAT_UP:
                    print("AUTO MODE: Executing predefined sequence.")
                    # Stop sequence
                    set_goal_velocity(2, 0)
                    set_goal_velocity(3, 0)
                    time.sleep(STOP_DURATION)
                    # Turn right sequence
                    set_goal_velocity(2, turning_velocity)
                    set_goal_velocity(3, -turning_velocity)
                    time.sleep(TURN_DURATION)
                    # Move forward sequence
                    set_goal_velocity(2, forward_velocity)
                    set_goal_velocity(3, forward_velocity)
                    time.sleep(MOVE_FORWARD_DURATION)
                    # Final turn right sequence
                    set_goal_velocity(2, turning_velocity)
                    set_goal_velocity(3, -turning_velocity)
                    time.sleep(TURN_DURATION)
                    set_goal_velocity(2, 0)
                    set_goal_velocity(3, 0)
                    print("Sequence complete. Motors stopped.")

finally:
    enable_torque(DXL_IDS, TORQUE_DISABLE)
    portHandler.closePort()
    pygame.quit()
    GPIO.cleanup()
